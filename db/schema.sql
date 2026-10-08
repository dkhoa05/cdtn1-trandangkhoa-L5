-- SQL DDL skeleton — Luồng L5: Kho linh kiện thay thế (PostgreSQL)
-- Tên bảng/cột khớp bảng thuật ngữ mục 1 của docs/srs.md và dataset case study.

CREATE TABLE service_center (
    center_id    SERIAL       PRIMARY KEY,
    center_code  VARCHAR(10)  NOT NULL UNIQUE,
    center_name  VARCHAR(120) NOT NULL,
    city         VARCHAR(60)  NOT NULL
);

CREATE TABLE app_user (
    user_id    BIGSERIAL    PRIMARY KEY,
    full_name  VARCHAR(120) NOT NULL,
    role       VARCHAR(20)  NOT NULL
               CHECK (role IN ('KY_THUAT_VIEN', 'QUAN_LY_TT')),
    center_id  INT          NOT NULL REFERENCES service_center(center_id), -- QT-14, NFR3
    is_active  BOOLEAN      NOT NULL DEFAULT true                         -- QT-13
);

CREATE TABLE part (
    part_id     BIGSERIAL     PRIMARY KEY,
    part_code   VARCHAR(30)   NOT NULL UNIQUE,
    part_name   VARCHAR(120)  NOT NULL,
    unit_price  NUMERIC(12,0) NOT NULL CHECK (unit_price >= 0)
);

-- Tồn kho theo trung tâm. Cảnh báo dưới ngưỡng (FR4, FR6) TÍNH từ quantity < min_threshold,
-- không lưu bảng cảnh báo riêng để tránh lưu giá trị tính được.
CREATE TABLE part_stock (
    center_id      INT    NOT NULL REFERENCES service_center(center_id),
    part_id        BIGINT NOT NULL REFERENCES part(part_id),
    quantity       INT    NOT NULL CHECK (quantity >= 0),       -- QT-09: không xuất quá tồn
    min_threshold  INT    NOT NULL CHECK (min_threshold >= 0),
    PRIMARY KEY (center_id, part_id)                            -- NFR1: tra cứu theo trung tâm
);

-- Bảng tham chiếu từ luồng L2 — chỉ giữ các cột luồng L5 cần dùng.
CREATE TABLE ticket (
    ticket_id    BIGSERIAL   PRIMARY KEY,
    ticket_code  VARCHAR(20) NOT NULL UNIQUE,
    center_id    INT         NOT NULL REFERENCES service_center(center_id),
    status       VARCHAR(20) NOT NULL
);

-- Lịch sử nhập–xuất: chỉ thêm, không sửa/xóa (QT-13). Sai thì ghi giao dịch bù.
CREATE TABLE part_transaction (
    transaction_id  BIGSERIAL   PRIMARY KEY,
    center_id       INT         NOT NULL,
    part_id         BIGINT      NOT NULL,
    txn_type        VARCHAR(4)  NOT NULL CHECK (txn_type IN ('NHAP', 'XUAT')),
    quantity        INT         NOT NULL CHECK (quantity > 0),
    ticket_id       BIGINT      REFERENCES ticket(ticket_id),
    created_by      BIGINT      NOT NULL REFERENCES app_user(user_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (center_id, part_id) REFERENCES part_stock(center_id, part_id),
    -- Xuất phải gắn phiếu bảo hành (FR2); nhập thì không.
    CONSTRAINT chk_ticket_by_type CHECK (
        (txn_type = 'XUAT' AND ticket_id IS NOT NULL) OR
        (txn_type = 'NHAP' AND ticket_id IS NULL))
);

CREATE INDEX idx_txn_part_time ON part_transaction(center_id, part_id, created_at); -- FR7, FR8
CREATE INDEX idx_txn_ticket    ON part_transaction(ticket_id);                       -- AC2.2
