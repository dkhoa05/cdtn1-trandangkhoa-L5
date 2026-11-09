# API documentation (Assignment 3, track SE)

This document describes every endpoint of the L5 spare-parts stock service as it is implemented in this repository. All request and response examples were copied from a real run against the Docker Compose system on 09/11/2026 (fresh database, 17 endpoints, every business error code). Part 181 and ticket 7724 in the examples are real rows of that run; the demo part was created and deleted by the same run.

## Conventions

- **Base URL:** `http://localhost:5000` (the port is set by `PORT`). All business endpoints live under `/api`; `/health` does not.
- **Format:** JSON requests (`Content-Type: application/json`) and JSON responses. Field names are `snake_case`. Money (`unit_price`) is an integer amount in Vietnamese dong. Timestamps are ISO 8601 strings with a UTC offset.
- **Authentication:** call `POST /api/auth/login` with a user id, then send `Authorization: Bearer <token>` on every other `/api` call. The prototype has no passwords (design change TD-05). A token is signed with `SECRET_KEY` and expires after 8 hours.
- **Roles:** `QUAN_LY_TT` (center manager) and `KY_THUAT_VIEN` (technician). Every endpoint states which roles may call it. The server enforces roles; the web menu only hides links.
- **Center scope (rule QT-14):** a user can only read or change data of their own service center. Asking for another center answers `403 FORBIDDEN`.
- **Pagination:** list endpoints take `page` (default 1) and `size` (default 20, maximum 100) and return `{"data": [...], "page": n, "size": n, "total": n}`.
- **Errors:** every failure uses one shape, `{"error": {"code": "...", "message": "...", "fields": {...}}}`. `code` is stable and meant for programs; `message` is a Vietnamese sentence for end users and may change; `fields` appears only for validation errors and names each wrong field. A database outage answers `503 DB_UNAVAILABLE` and any unexpected failure answers `500 INTERNAL_ERROR`, both with a `requestId` and never with stack traces, table names or connection strings.
- **Soft delete:** deleting a part or a stock row sets `is_active` to false and keeps the row (rule QT-13). A deactivated part answers `404 PART_NOT_FOUND`.

### Error code summary

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_FAILED` | 400 | Input is missing, has the wrong type or is outside the allowed range; `fields` names each wrong field |
| `UNAUTHORIZED` | 401 | Token missing, invalid or expired, or the user is deactivated |
| `FORBIDDEN` | 403 | Role not allowed, or the data belongs to another service center |
| `TICKET_NOT_FOUND` | 404 | No warranty ticket with that id |
| `PART_NOT_FOUND` | 404 | No active part with that id, or the part is not in the caller's center stock |
| `INSUFFICIENT_STOCK` | 409 | The requested quantity is larger than the stock on hand (rule QT-09); nothing is changed |
| `PART_CODE_EXISTS` | 409 | The part code is already used, including by a deactivated part |
| `PART_HAS_STOCK` | 409 | The part is still listed in a center's stock |
| `STOCK_EXISTS` | 409 | The part is already in this center's stock |
| `STOCK_NOT_EMPTY` | 409 | The stock row still has quantity above 0 |
| `TICKET_NOT_PROCESSING` | 422 | Parts can only be issued to a ticket whose status is `DANG_XU_LY` |
| `DB_UNAVAILABLE` | 503 | The database cannot be reached |
| `INTERNAL_ERROR` | 500 | Unexpected server failure |

## Endpoints

| # | Method and path | Who | Purpose |
|---|---|---|---|
| 1 | `GET /health` | anyone | Health check |
| 2 | `POST /api/auth/login` | anyone | Get a token |
| 3 | `GET /api/parts` | both roles | Search stock of the caller's center |
| 4 | `GET /api/parts/low-stock` | both roles | Parts below their alert threshold |
| 5 | `POST /api/parts` | manager | Create a part |
| 6 | `GET /api/parts/{part_id}` | both roles | Read one part with its stock |
| 7 | `PUT /api/parts/{part_id}` | manager | Edit name and price |
| 8 | `DELETE /api/parts/{part_id}` | manager | Deactivate a part |
| 9 | `POST /api/stock` | manager | Put a part into the center stock |
| 10 | `PATCH /api/stock/{part_id}` | manager | Change the alert threshold |
| 11 | `DELETE /api/stock/{part_id}` | manager | Remove a part from the center stock |
| 12 | `POST /api/parts/{part_id}/stock-in` | manager | Receive stock |
| 13 | `GET /api/parts/{part_id}/transactions` | manager | Transaction history of a part |
| 14 | `GET /api/parts/{part_id}/transactions/summary` | manager | Total in and out for a date range |
| 15 | `GET /api/tickets` | both roles | List tickets of the caller's center |
| 16 | `GET /api/tickets/{ticket_id}/parts` | both roles | Parts already issued to a ticket |
| 17 | `POST /api/tickets/{ticket_id}/parts` | both roles | Issue a part to a ticket |

### 1. Health check

1. **Method and path:** `GET /health`
2. **Description:** Tells whether the service and its database are reachable. Used by the Docker healthcheck.
3. **Authentication:** None.
4. **Parameters and request body:**

None.

5. **Success response:** `200` with `{"status": "ok", "db": "ok"}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| (no code) | 503 | Database unreachable; body is `{"status": "degraded", "db": "unreachable"}` with no connection details |

7. **Notes and limits:** Runs `SELECT 1`; it never returns connection strings.

**Example: healthy system**

```http
GET /health
```

Response `200 OK`:

```json
{
  "db": "ok",
  "status": "ok"
}
```


### 2. Log in

1. **Method and path:** `POST /api/auth/login`
2. **Description:** Exchanges a user id for a signed token. There is no password in this prototype.
3. **Authentication:** None.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `user_id` | body | integer | yes | Positive integer |

5. **Success response:** `200` with `token` and `user` (`user_id`, `full_name`, `role`, `center_id`, `center_name`).

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `VALIDATION_FAILED` | 400 | `user_id` missing or not a positive integer |
| `UNAUTHORIZED` | 401 | No such user, or the user is deactivated |

7. **Notes and limits:** The token expires after 8 hours. In the examples the token value is shortened to its first characters.

**Example: manager logs in**

```http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": 101
}
```

Response `200 OK`:

```json
{
  "token": "eyJ1aWQiOjEwMX...",
  "user": {
    "center_id": 1,
    "center_name": "TTBH Quận 10",
    "full_name": "Quản lý TT01",
    "role": "QUAN_LY_TT",
    "user_id": 101
  }
}
```

**Example: unknown user**

```http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": 999999
}
```

Response `401 Unauthorized`:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
  }
}
```

**Example: invalid body**

```http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": 0
}
```

Response `400 Bad Request`:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "fields": {
      "user_id": "Phải là số nguyên dương"
    },
    "message": "Dữ liệu không hợp lệ"
  }
}
```


### 3. Search stock of the center

1. **Method and path:** `GET /api/parts`
2. **Description:** Lists active parts that are in the stock of the caller's center, with quantity and alert threshold, filtered by text and stock status.
3. **Authentication:** Bearer token, both roles.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `q` | query | string | no | Case-insensitive match on part code or name; `%` and `_` are treated as plain characters |
| `status` | query | string | no | `all` (default), `low` (quantity below threshold), `out` (quantity 0) or `ok` (quantity at or above threshold) |
| `sort` | query | string | no | `code` (default), `name`, `qty_asc` or `qty_desc` |
| `center_id` | query | integer | no | Must equal the caller's own center |
| `page` | query | integer | no | Default 1, at least 1 |
| `size` | query | integer | no | Default 20, from 1 to 100 |

5. **Success response:** `200` with a page of `{part_id, part_code, part_name, unit_price, quantity, min_threshold}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Bad `page`, `size`, `status`, `sort` or `center_id` |
| `FORBIDDEN` | 403 | `center_id` is another center |

7. **Notes and limits:** `status` and `sort` only select from fixed lists in the code; the values are never placed into SQL.

**Example: first two parts**

```http
GET /api/parts?size=2
Authorization: Bearer <technician token (user 2)>
```

Response `200 OK`:

```json
{
  "data": [
    {
      "min_threshold": 8,
      "part_code": "CAM-AP-01",
      "part_id": 70,
      "part_name": "Camera sau Apple loại 1",
      "quantity": 42,
      "unit_price": 420000
    },
    {
      "min_threshold": 5,
      "part_code": "CAM-AP-02",
      "part_id": 71,
      "part_name": "Camera sau Apple loại 2",
      "quantity": 9,
      "unit_price": 420000
    }
  ],
  "page": 1,
  "size": 2,
  "total": 128
}
```

**Example: below threshold, lowest quantity first**

```http
GET /api/parts?status=low&sort=qty_asc&size=2
Authorization: Bearer <technician token (user 2)>
```

Response `200 OK`:

```json
{
  "data": [
    {
      "min_threshold": 5,
      "part_code": "CMH-RM-01",
      "part_id": 136,
      "part_name": "Cáp màn hình realme loại 1",
      "quantity": 0,
      "unit_price": 150000
    },
    {
      "min_threshold": 5,
      "part_code": "CMH-SS-01",
      "part_id": 127,
      "part_name": "Cáp màn hình Samsung loại 1",
      "quantity": 0,
      "unit_price": 280000
    }
  ],
  "page": 1,
  "size": 2,
  "total": 18
}
```

**Example: unknown status**

```http
GET /api/parts?status=zzz
Authorization: Bearer <technician token (user 2)>
```

Response `400 Bad Request`:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "fields": {
      "status": "Chỉ nhận một trong: all, low, out, ok"
    },
    "message": "Dữ liệu không hợp lệ"
  }
}
```

**Example: another center**

```http
GET /api/parts?center_id=1
Authorization: Bearer <technician token (user 2)>
```

Response `403 Forbidden`:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Bạn chỉ thao tác được trên dữ liệu của trung tâm mình"
  }
}
```


### 4. Parts below the alert threshold

1. **Method and path:** `GET /api/parts/low-stock`
2. **Description:** Same as `GET /api/parts` with `status=low` fixed.
3. **Authentication:** Bearer token, both roles.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `q` | query | string | no | Same as endpoint 3 |
| `sort` | query | string | no | Same as endpoint 3 |
| `center_id` | query | integer | no | Same as endpoint 3 |
| `page` | query | integer | no | Default 1, at least 1 |
| `size` | query | integer | no | Default 20, from 1 to 100 |

5. **Success response:** `200` with the same page shape as endpoint 3.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Bad query parameter |
| `FORBIDDEN` | 403 | `center_id` is another center |

7. **Notes and limits:** A part with quantity 0 is included only when its threshold is above 0.

**Example: first two low-stock parts**

```http
GET /api/parts/low-stock?size=2
Authorization: Bearer <technician token (user 2)>
```

Response `200 OK`:

```json
{
  "data": [
    {
      "min_threshold": 5,
      "part_code": "CMH-OP-01",
      "part_id": 133,
      "part_name": "Cáp màn hình OPPO loại 1",
      "quantity": 3,
      "unit_price": 280000
    },
    {
      "min_threshold": 5,
      "part_code": "CMH-RM-01",
      "part_id": 136,
      "part_name": "Cáp màn hình realme loại 1",
      "quantity": 0,
      "unit_price": 150000
    }
  ],
  "page": 1,
  "size": 2,
  "total": 18
}
```


### 5. Create a part

1. **Method and path:** `POST /api/parts`
2. **Description:** Adds a part to the catalog. It does not touch any stock row; use endpoint 9 for that.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_code` | body | string | yes | Letters, digits and hyphens, starts with a letter or digit, at most 30 characters |
| `part_name` | body | string | yes | 1 to 120 characters |
| `unit_price` | body | integer | yes | 0 to 999999999999 |

5. **Success response:** `201` with `{part_id, part_code, part_name, unit_price}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | A field is missing or invalid |
| `FORBIDDEN` | 403 | Caller is not a manager |
| `PART_CODE_EXISTS` | 409 | Code already used |

7. **Notes and limits:** Codes stay reserved after a part is deactivated.

**Example: create**

```http
POST /api/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_code": "LK-DEMO-01",
  "part_name": "Loa ngoài demo",
  "unit_price": 120000
}
```

Response `201 Created`:

```json
{
  "part_code": "LK-DEMO-01",
  "part_id": 181,
  "part_name": "Loa ngoài demo",
  "unit_price": 120000
}
```

**Example: duplicate code**

```http
POST /api/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_code": "LK-DEMO-01",
  "part_name": "Trùng mã",
  "unit_price": 1000
}
```

Response `409 Conflict`:

```json
{
  "error": {
    "code": "PART_CODE_EXISTS",
    "message": "Mã linh kiện LK-DEMO-01 đã tồn tại"
  }
}
```

**Example: technician is not allowed**

```http
POST /api/parts
Authorization: Bearer <technician token (user 2)>
Content-Type: application/json

{
  "part_code": "LK-DEMO-KT",
  "part_name": "Thử",
  "unit_price": 1000
}
```

Response `403 Forbidden`:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Chỉ quản lý trung tâm được thêm linh kiện"
  }
}
```

**Example: invalid data**

```http
POST /api/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_code": "@@",
  "part_name": "",
  "unit_price": -1
}
```

Response `400 Bad Request`:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "fields": {
      "part_code": "Mã gồm chữ, số, dấu gạch ngang, tối đa 30 ký tự",
      "part_name": "Tên từ 1 đến 120 ký tự",
      "unit_price": "Đơn giá phải là số nguyên từ 0 đến 999999999999"
    },
    "message": "Dữ liệu không hợp lệ"
  }
}
```


### 6. Read one part

1. **Method and path:** `GET /api/parts/{part_id}`
2. **Description:** Returns a part and its stock in the caller's center.
3. **Authentication:** Bearer token, both roles.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |

5. **Success response:** `200` with `{part_id, part_code, part_name, unit_price, stock}`; `stock` is `{quantity, min_threshold}` or `null`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `PART_NOT_FOUND` | 404 | No active part with that id |

7. **Notes and limits:** `stock` is `null` when the part is not in the caller's center stock; that is different from a quantity of 0.

**Example: part not yet in stock**

```http
GET /api/parts/181
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "part_code": "LK-DEMO-01",
  "part_id": 181,
  "part_name": "Loa ngoài demo",
  "stock": null,
  "unit_price": 120000
}
```

**Example: part in stock**

```http
GET /api/parts/181
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "part_code": "LK-DEMO-01",
  "part_id": 181,
  "part_name": "Loa ngoài demo v2",
  "stock": {
    "min_threshold": 6,
    "quantity": 0
  },
  "unit_price": 135000
}
```

**Example: unknown part**

```http
GET /api/parts/99999
Authorization: Bearer <manager token (user 101)>
```

Response `404 Not Found`:

```json
{
  "error": {
    "code": "PART_NOT_FOUND",
    "message": "Không tìm thấy linh kiện 99999"
  }
}
```


### 7. Edit a part

1. **Method and path:** `PUT /api/parts/{part_id}`
2. **Description:** Changes the name and unit price of a part. The part code cannot be changed.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |
| `part_name` | body | string | yes | 1 to 120 characters |
| `unit_price` | body | integer | yes | 0 to 999999999999 |

5. **Success response:** `200` with `{part_id, part_code, part_name, unit_price}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | A field is invalid |
| `FORBIDDEN` | 403 | Caller is not a manager |
| `PART_NOT_FOUND` | 404 | No active part |

7. **Notes and limits:** Both fields are required (full replace).

**Example: rename and reprice**

```http
PUT /api/parts/181
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_name": "Loa ngoài demo v2",
  "unit_price": 135000
}
```

Response `200 OK`:

```json
{
  "part_code": "LK-DEMO-01",
  "part_id": 181,
  "part_name": "Loa ngoài demo v2",
  "unit_price": 135000
}
```


### 8. Deactivate a part

1. **Method and path:** `DELETE /api/parts/{part_id}`
2. **Description:** Soft-deletes a part (`is_active` becomes false). The row is kept.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |

5. **Success response:** `200` with `{part_id, is_active: false}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `FORBIDDEN` | 403 | Caller is not a manager |
| `PART_NOT_FOUND` | 404 | No active part |
| `PART_HAS_STOCK` | 409 | The part is still in a center's stock; remove it from stock first |

7. **Notes and limits:** After this call the part is hidden from every read endpoint.

**Example: part is still in stock**

```http
DELETE /api/parts/181
Authorization: Bearer <manager token (user 101)>
```

Response `409 Conflict`:

```json
{
  "error": {
    "code": "PART_HAS_STOCK",
    "message": "Linh kiện vẫn còn tồn kho ở trung tâm, chưa thể ngừng sử dụng"
  }
}
```

**Example: deactivate**

```http
DELETE /api/parts/181
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "is_active": false,
  "part_id": 181
}
```

**Example: read after deactivation**

```http
GET /api/parts/181
Authorization: Bearer <manager token (user 101)>
```

Response `404 Not Found`:

```json
{
  "error": {
    "code": "PART_NOT_FOUND",
    "message": "Không tìm thấy linh kiện 181"
  }
}
```


### 9. Put a part into the center stock

1. **Method and path:** `POST /api/stock`
2. **Description:** Creates the stock row of a part in the caller's center with quantity 0 and the chosen alert threshold.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | body | integer | yes | Positive integer |
| `min_threshold` | body | integer | yes | 0 to 2147483647 |

5. **Success response:** `201` with `{part_id, center_id, quantity, min_threshold}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | A field is invalid |
| `FORBIDDEN` | 403 | Caller is not a manager |
| `PART_NOT_FOUND` | 404 | No active part |
| `STOCK_EXISTS` | 409 | Already in this center's stock |

7. **Notes and limits:** Quantity starts at 0; use endpoint 12 to receive stock.

**Example: add to stock**

```http
POST /api/stock
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "min_threshold": 4
}
```

Response `201 Created`:

```json
{
  "center_id": 1,
  "min_threshold": 4,
  "part_id": 181,
  "quantity": 0
}
```

**Example: already in stock**

```http
POST /api/stock
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "min_threshold": 4
}
```

Response `409 Conflict`:

```json
{
  "error": {
    "code": "STOCK_EXISTS",
    "message": "Linh kiện đã có trong kho trung tâm này"
  }
}
```


### 10. Change the alert threshold

1. **Method and path:** `PATCH /api/stock/{part_id}`
2. **Description:** Changes `min_threshold` of a part in the caller's center.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |
| `min_threshold` | body | integer | yes | 0 to 2147483647 |

5. **Success response:** `200` with `{part_id, center_id, quantity, min_threshold}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Invalid threshold |
| `FORBIDDEN` | 403 | Caller is not a manager |
| `PART_NOT_FOUND` | 404 | Part is not in this center's stock |

7. **Notes and limits:** Alerts are computed when parts are issued, so a new threshold applies to later issues.

**Example: raise threshold to 6**

```http
PATCH /api/stock/181
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "min_threshold": 6
}
```

Response `200 OK`:

```json
{
  "center_id": 1,
  "min_threshold": 6,
  "part_id": 181,
  "quantity": 0
}
```


### 11. Remove a part from the center stock

1. **Method and path:** `DELETE /api/stock/{part_id}`
2. **Description:** Soft-deletes the stock row of a part in the caller's center.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |

5. **Success response:** `200` with `{part_id, center_id, is_active: false}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `FORBIDDEN` | 403 | Caller is not a manager |
| `PART_NOT_FOUND` | 404 | Part is not in this center's stock |
| `STOCK_NOT_EMPTY` | 409 | Quantity is still above 0 |

7. **Notes and limits:** Empty the stock first, for example by issuing the remaining quantity.

**Example: stock is not empty**

```http
DELETE /api/stock/181
Authorization: Bearer <manager token (user 101)>
```

Response `409 Conflict`:

```json
{
  "error": {
    "code": "STOCK_NOT_EMPTY",
    "message": "Kho còn 3 linh kiện, chưa thể gỡ"
  }
}
```

**Example: remove an empty stock row**

```http
DELETE /api/stock/181
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "center_id": 1,
  "is_active": false,
  "part_id": 181
}
```


### 12. Receive stock

1. **Method and path:** `POST /api/parts/{part_id}/stock-in`
2. **Description:** Adds a quantity to the stock of a part and records an `NHAP` transaction. Both changes succeed or fail together.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |
| `center_id` | body | integer | yes | Must equal the caller's center |
| `quantity` | body | integer | yes | 1 to 2147483647 |

5. **Success response:** `201` with `{transaction_id, part_id, center_id, quantity, new_stock, created_at}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Quantity or center is invalid, or the quantity is above the column limit |
| `FORBIDDEN` | 403 | Caller is not a manager, or the center is not the caller's |
| `PART_NOT_FOUND` | 404 | No active part, or not in this center's stock |

7. **Notes and limits:** The upper limit of `quantity` is the size of the integer column; larger values are rejected with 400 instead of reaching the database (bug BUG-006).

**Example: receive 3**

```http
POST /api/parts/181/stock-in
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "center_id": 1,
  "quantity": 3
}
```

Response `201 Created`:

```json
{
  "center_id": 1,
  "created_at": "2026-11-09T00:54:44.077150+00:00",
  "new_stock": 3,
  "part_id": 181,
  "quantity": 3,
  "transaction_id": 4955
}
```

**Example: quantity above the limit**

```http
POST /api/parts/181/stock-in
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "center_id": 1,
  "quantity": 100000000000
}
```

Response `400 Bad Request`:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "fields": {
      "quantity": "Số lượng nhập tối đa là 2147483647"
    },
    "message": "Dữ liệu không hợp lệ"
  }
}
```

**Example: technician is not allowed**

```http
POST /api/parts/181/stock-in
Authorization: Bearer <technician token (user 2)>
Content-Type: application/json

{
  "center_id": 4,
  "quantity": 1
}
```

Response `403 Forbidden`:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Chỉ quản lý trung tâm được ghi nhận nhập kho"
  }
}
```


### 13. Transaction history of a part

1. **Method and path:** `GET /api/parts/{part_id}/transactions`
2. **Description:** Lists receipts (`NHAP`) and issues (`XUAT`) of a part in the caller's center, newest first.
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |
| `center_id` | query | integer | no | Must equal the caller's center |
| `page` | query | integer | no | Default 1, at least 1 |
| `size` | query | integer | no | Default 20, from 1 to 100 |

5. **Success response:** `200` with a page of `{transaction_id, created_at, txn_type, quantity, ticket_id, created_by_name}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Bad query parameter |
| `FORBIDDEN` | 403 | Caller is not a manager, or another center |

7. **Notes and limits:** `ticket_id` is `null` for receipts. A part with no transactions gives an empty `data` list.

**Example: history after receiving 3**

```http
GET /api/parts/181/transactions?size=5
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "data": [
    {
      "created_at": "2026-11-09T00:54:44.077150+00:00",
      "created_by_name": "Quản lý TT01",
      "quantity": 3,
      "ticket_id": null,
      "transaction_id": 4955,
      "txn_type": "NHAP"
    }
  ],
  "page": 1,
  "size": 5,
  "total": 1
}
```

**Example: technician is not allowed**

```http
GET /api/parts/181/transactions
Authorization: Bearer <technician token (user 2)>
```

Response `403 Forbidden`:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Chỉ quản lý trung tâm được xem lịch sử nhập–xuất"
  }
}
```


### 14. Total in and out for a date range

1. **Method and path:** `GET /api/parts/{part_id}/transactions/summary`
2. **Description:** Sums receipts and issues of a part between two dates (inclusive).
3. **Authentication:** Bearer token, manager only.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `part_id` | path | integer | yes | Part id |
| `from` | query | date | yes | `YYYY-MM-DD` |
| `to` | query | date | yes | `YYYY-MM-DD`, not before `from` |
| `center_id` | query | integer | no | Must equal the caller's center |

5. **Success response:** `200` with `{part_id, center_id, from, to, total_in, total_out, net_change}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Bad date format, `from` after `to`, or bad `center_id` |
| `FORBIDDEN` | 403 | Caller is not a manager, or another center |

7. **Notes and limits:** `net_change` equals `total_in - total_out` and can be negative.

**Example: summary for today**

```http
GET /api/parts/181/transactions/summary?from=2026-11-09&to=2026-11-09
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "center_id": 1,
  "from": "2026-11-09",
  "net_change": 3,
  "part_id": 181,
  "to": "2026-11-09",
  "total_in": 3,
  "total_out": 0
}
```

**Example: invalid date**

```http
GET /api/parts/181/transactions/summary?from=2026-13-01&to=2026-11-09
Authorization: Bearer <manager token (user 101)>
```

Response `400 Bad Request`:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "fields": {
      "from": "Phải là ngày dạng YYYY-MM-DD"
    },
    "message": "Dữ liệu không hợp lệ"
  }
}
```


### 15. List tickets

1. **Method and path:** `GET /api/tickets`
2. **Description:** Lists warranty tickets of the caller's center, newest first, optionally by status. Used to pick a ticket when issuing parts.
3. **Authentication:** Bearer token, both roles.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `status` | query | string | no | For example `DANG_XU_LY` (in progress), `DA_DONG` (closed), `HOAN_TAT` (done); an unknown value gives an empty list |
| `page` | query | integer | no | Default 1, at least 1 |
| `size` | query | integer | no | Default 20, from 1 to 100 |

5. **Success response:** `200` with a page of `{ticket_id, ticket_code, center_id, status}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | Bad `page` or `size` |

7. **Notes and limits:** Only tickets of the caller's center are returned.

**Example: tickets in progress**

```http
GET /api/tickets?status=DANG_XU_LY&size=2
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "data": [
    {
      "center_id": 1,
      "status": "DANG_XU_LY",
      "ticket_code": "BH-007724/2024",
      "ticket_id": 7724
    },
    {
      "center_id": 1,
      "status": "DANG_XU_LY",
      "ticket_code": "BH-007608/2025",
      "ticket_id": 7608
    }
  ],
  "page": 1,
  "size": 2,
  "total": 96
}
```


### 16. Parts issued to a ticket

1. **Method and path:** `GET /api/tickets/{ticket_id}/parts`
2. **Description:** Returns the ticket and the parts already issued to it, newest first.
3. **Authentication:** Bearer token, both roles.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `ticket_id` | path | integer | yes | Ticket id |

5. **Success response:** `200` with `{ticket: {...}, data: [{transaction_id, part_id, part_code, part_name, quantity, created_at}]}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `FORBIDDEN` | 403 | The ticket belongs to another center |
| `TICKET_NOT_FOUND` | 404 | No such ticket |

7. **Notes and limits:** `data` is empty when nothing has been issued yet.

**Example: before issuing**

```http
GET /api/tickets/7724/parts
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "data": [],
  "ticket": {
    "center_id": 1,
    "status": "DANG_XU_LY",
    "ticket_code": "BH-007724/2024",
    "ticket_id": 7724
  }
}
```

**Example: after issuing 3**

```http
GET /api/tickets/7724/parts
Authorization: Bearer <manager token (user 101)>
```

Response `200 OK`:

```json
{
  "data": [
    {
      "created_at": "2026-11-09T00:54:44.400949+00:00",
      "part_code": "LK-DEMO-01",
      "part_id": 181,
      "part_name": "Loa ngoài demo v2",
      "quantity": 3,
      "transaction_id": 4956
    }
  ],
  "ticket": {
    "center_id": 1,
    "status": "DANG_XU_LY",
    "ticket_code": "BH-007724/2024",
    "ticket_id": 7724
  }
}
```


### 17. Issue a part to a ticket

1. **Method and path:** `POST /api/tickets/{ticket_id}/parts`
2. **Description:** Takes a quantity out of stock for a ticket and records an `XUAT` transaction. The stock row is locked while the check and the update run, so concurrent requests cannot oversell; the update and the record succeed or fail together (rules QT-09, QT-14).
3. **Authentication:** Bearer token, both roles; the ticket must belong to the caller's center.
4. **Parameters and request body:**

| Name | In | Type | Required | Rules |
|---|---|---|---|---|
| `ticket_id` | path | integer | yes | Ticket id |
| `part_id` | body | integer | yes | Positive integer |
| `quantity` | body | integer | yes | Positive integer |

5. **Success response:** `201` with `{transaction_id, ticket_id, part_id, quantity, remaining_stock, low_stock_alert, created_at}`.

6. **Error codes:**

| Code | HTTP | When |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, malformed, expired or tampered token, or the user is deactivated |
| `VALIDATION_FAILED` | 400 | A field is missing, not a positive integer, or too large |
| `FORBIDDEN` | 403 | The ticket belongs to another center |
| `TICKET_NOT_FOUND` | 404 | No such ticket |
| `PART_NOT_FOUND` | 404 | The part is not in this center's stock |
| `INSUFFICIENT_STOCK` | 409 | Quantity is larger than the stock; nothing changes |
| `TICKET_NOT_PROCESSING` | 422 | Ticket status is not `DANG_XU_LY` |

7. **Notes and limits:** Issuing exactly the quantity on hand is allowed and leaves 0. `low_stock_alert` is true when `remaining_stock` falls below the part's threshold.

**Example: issue 3, stock becomes 0**

```http
POST /api/tickets/7724/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "quantity": 3
}
```

Response `201 Created`:

```json
{
  "created_at": "2026-11-09T00:54:44.400949+00:00",
  "low_stock_alert": true,
  "part_id": 181,
  "quantity": 3,
  "remaining_stock": 0,
  "ticket_id": 7724,
  "transaction_id": 4956
}
```

**Example: more than the stock**

```http
POST /api/tickets/7724/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "quantity": 4
}
```

Response `409 Conflict`:

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Vượt quá tồn kho: còn 3, yêu cầu xuất 4"
  }
}
```

**Example: ticket is closed**

```http
POST /api/tickets/7692/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "quantity": 1
}
```

Response `422 Unprocessable Entity`:

```json
{
  "error": {
    "code": "TICKET_NOT_PROCESSING",
    "message": "Phiếu BH-007692/2026 không ở trạng thái đang xử lý"
  }
}
```

**Example: unknown ticket**

```http
POST /api/tickets/99999999/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "quantity": 1
}
```

Response `404 Not Found`:

```json
{
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "Không tìm thấy phiếu 99999999"
  }
}
```

**Example: ticket of another center**

```http
POST /api/tickets/51/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "quantity": 1
}
```

Response `403 Forbidden`:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Bạn chỉ thao tác được trên dữ liệu của trung tâm mình"
  }
}
```

**Example: quantity 0**

```http
POST /api/tickets/7724/parts
Authorization: Bearer <manager token (user 101)>
Content-Type: application/json

{
  "part_id": 181,
  "quantity": 0
}
```

Response `400 Bad Request`:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "fields": {
      "quantity": "Phải là số nguyên dương"
    },
    "message": "Dữ liệu không hợp lệ"
  }
}
```

