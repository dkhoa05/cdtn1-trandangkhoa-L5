# Deployment Guide (Assignment 3, track SE)

This guide brings the L5 spare-parts stock system up on a machine that has only Docker and Git. It was followed step by step on 09/11/2026 from an empty database, and every result quoted below is what that run printed.

## 1. Requirements

| Item | Requirement |
|---|---|
| Operating system | Windows 11, macOS or Linux. Tested on Windows 11 with Docker Desktop (WSL 2 backend) |
| Docker | Docker Engine 29.9 and Docker Compose 5.6 (any Compose v2 or later should work) |
| Git | Any recent version, to clone the repository |
| Disk space | About 2 GB free (images: app 243 MB, PostgreSQL 16 642 MB, plus data) |
| Network | Internet access on the first build to pull `python:3.10-slim` and `postgres:16` from Docker Hub |
| Ports | Host port 5000 must be free. The database port 5432 is not published to the host |

No Python or PostgreSQL installation is needed. Docker Desktop must be running before step 4.

## 2. Setup steps

Run each command from a terminal (PowerShell, Git Bash or a Linux shell; in Windows `cmd` replace `cp` with `copy`). Do not skip or reorder steps.

1. `git clone --branch v1.0 https://github.com/dkhoa05/cdtn1-trandangkhoa-L5.git`
2. `cd cdtn1-trandangkhoa-L5`
3. `cp .env.example .env`
4. `docker compose up -d --build`

Steps 3 and 4 are the only two commands that build and start the system. The first build takes a few minutes. The `app` container waits until `db` is healthy, then runs `python -m src.db_init` (creates the tables and loads the sample data) before it starts the web server, so no manual migration step exists.

To stop the system run `docker compose down`. To delete its data as well and start again from an empty database run `docker compose down -v`.

## 3. Environment variables

`.env.example` already contains working sample values, so step 3 needs no editing. Change the three secrets (`DB_PASSWORD`, `SECRET_KEY`, `DEMO_PASSWORD`) before any real deployment.

| Variable | Meaning | Sample value | Required |
|---|---|---|---|
| `DB_NAME` | Database name; created by the `db` container | `cdtn1_l5_dev` | no (default shown) |
| `DB_USER` | PostgreSQL user; created by the `db` container | `postgres` | no (default shown) |
| `DB_PASSWORD` | PostgreSQL password, used by both containers | `doi_mat_khau_o_day` | yes |
| `SECRET_KEY` | Key that signs login tokens; anyone who knows it can forge a token, so use a random string of at least 32 characters | `doi_chuoi_bi_mat_o_day` | yes |
| `DEMO_PASSWORD` | Password given to every sample account; stored only as a salted scrypt hash. The sample value is for trying the system out, change it before any real deployment | `MatKhauMau@2026` | yes |
| `PORT` | Host port that serves the web page and the API | `5000` | no (default shown) |
| `LOG_LEVEL` | Log level: `INFO`, or `DEBUG` when investigating; logs never contain passwords or tokens | `INFO` | no (default shown) |
| `DB_HOST`, `DB_PORT` | Database address. Only used when running without Docker; Docker Compose sets them to `db` and `5432` | `127.0.0.1`, `5432` | no |
| `FLASK_DEBUG` | Flask debugger. Only used when running without Docker and must stay `0` elsewhere; the containers never enable it | `0` | no |

If a required variable is missing, `docker compose up` stops at once with the message `Chua co .env - hay chep tu .env.example`.

## 4. Sample data

The data comes from `seeds/001_demo.sql` and is loaded automatically at every container start. The load is repeatable: running it again does not create duplicates. After a fresh start the tables hold exactly these numbers of rows (printed by `docker compose logs app`):

| Table | Rows |
|---|---|
| `service_center` | 6 |
| `app_user` | 44 |
| `part` | 180 |
| `part_stock` | 717 |
| `ticket` | 874 |
| `part_transaction` | 387 |

Two accounts are ready to use on the login page (the page has one button for each): user `101` is a center manager of center 1, and user `2` is a technician of center 4. Any other user id of the table `app_user` also works. All sample accounts share one password, the value of `DEMO_PASSWORD` (`MatKhauMau@2026` with the sample `.env.example`). It is set only for accounts that have none yet, so changing `DEMO_PASSWORD` later does not change an existing password; to reset them run `docker compose down -v` and step 4. The database stores only salted scrypt hashes, never the password itself.

## 5. How to check that the system runs correctly

1. List the services:

   ```
   docker compose ps
   ```

   Expected: `app` and `db` both show `Up ... (healthy)`; `app` shows `0.0.0.0:5000->5000/tcp`.

2. Call the health endpoint:

   ```
   curl http://localhost:5000/health
   ```

   Expected body: `{"db":"ok","status":"ok"}` with HTTP 200. (In Windows PowerShell use `curl.exe` or open the address in a browser.)

3. Open `http://localhost:5000` and press the "Quản lý trung tâm" or the "Kỹ thuật viên" button. Expected: you are logged in and the stock list of that user's center is shown.

4. Run the automated tests inside the container:

   ```
   docker compose exec app pytest
   ```

   Expected last line: `58 passed, 4 skipped`. The 4 skipped tests need the real database and run with `docker compose exec -e RUN_PG_TESTS=1 app pytest tests/test_tich_hop_pg.py`, expected `4 passed`.

5. Check that loading the data twice is safe:

   ```
   docker compose exec app python -m src.db_init
   ```

   Expected: no error, the line `da dat mat khau mau cho 0 tai khoan` (every account already has a password) and the same six row counts as in section 4.

### Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Bind for 0.0.0.0:5000 failed: port is already allocated` | Another program uses port 5000. Set `PORT=5001` in `.env`, run step 4 again and use `http://localhost:5001` |
| `docker compose up` stops with `Chua co .env` | Step 3 was skipped. Run `cp .env.example .env` |
| The page loads but the lists are empty or tables are missing | An old volume holds old data. Run `docker compose down -v`, then step 4 |
| The login page rejects the sample password | The account was created with another `DEMO_PASSWORD` earlier (the password is set only once). Run `docker compose down -v`, then step 4 |
| `docker compose ps` shows `unhealthy` | Read the reason with `docker compose logs app --tail 50`, fix it, and run step 4 again |

### Known limits

The service speaks plain HTTP on localhost. In a real deployment it should sit behind a reverse proxy that terminates TLS; the app keeps its token in the `Authorization` header and sets no cookies, so no cookie flag needs changing. The container runs Flask's built-in server, which is enough for a demonstration; a production WSGI server is not part of this assignment. A public demo on Render's free plan is described in section 6.


## 6. Optional: public demo on Render (free tier)

A public copy of the system runs at **https://kho-linh-kien.onrender.com**. It was created on 12/11/2026 on Render's free plan from the file `render.yaml` in this repository, which describes one Docker web service (`kho-linh-kien`) and one PostgreSQL database (`kho-linh-kien-db`). Sections 1 to 5 above are the required way to run the system; this section only records what was done for the public demo.

### 6.1. Steps that were done

1. Push the repository to GitHub with `render.yaml` and `docker-start.sh` at the root (the repository is public).
2. Sign up at https://render.com using the GitHub account. No payment method was added, because both resources use the Free plan.
3. In the Render Dashboard click New, then Blueprint, choose the repository `dkhoa05/cdtn1-trandangkhoa-L5`, branch `main`, and type a name for the Blueprint.
4. Render reads `render.yaml` and lists the two resources to create. It asks for one value, `DEMO_PASSWORD`; the sample value from `.env.example` was typed there, so the password is not stored in the repository.
5. Click Deploy Blueprint. Render builds the image from the `Dockerfile`, creates the database and starts the service with `sh docker-start.sh`, which runs `python -m src.db_init` and then the web server on the port Render provides. The first start loads the same sample data as in section 4.
6. When the service shows Live, check it as in section 5 (the commands below use the public address).

```
curl -s https://kho-linh-kien.onrender.com/health
```

Expected: `{"db":"ok","status":"ok"}`. Then open the address in a browser and log in as user `101` with the sample password; the stock list of center 1 shows 123 parts.

### 6.2. Environment variables on the platform

| Variable | Where the value comes from |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Read from the Render database by `render.yaml` (`fromDatabase`); never written in the repository |
| `SECRET_KEY` | Generated randomly by Render (`generateValue: true`) |
| `DEMO_PASSWORD` | Typed in the Dashboard when the Blueprint is created (`sync: false`) |
| `LOG_LEVEL` | `INFO`, set in `render.yaml` |
| `PORT` | Set by Render; `docker-start.sh` uses it |

No real secret is in the repository or in the Docker image.

### 6.3. Limits of the free plan and of this demo

- The free web service goes to sleep after 15 minutes without traffic. The first request after that takes about one minute; open the address once before using it.
- The free database expires 30 days after creation (12/12/2026 for this one) and is deleted 14 days later unless upgraded. To keep the demo longer, delete the expired database, create a new one and deploy again; `db_init` loads the sample data again.
- Anyone who knows the sample password can log in and change the sample data. The data can be rebuilt by redeploying, so this is accepted for a demo.
- The service runs Flask's built-in server behind Render's HTTPS endpoint, which is enough for a demonstration and not meant for production.

### 6.4. Problem met during the deploy

| Symptom | Cause and fix |
|---|---|
| The first deploy failed with `sh: 1: python -m src.db_init && flask ... not found` and `Exited with status 127` | `render.yaml` first used `dockerCommand: sh -c "python ... && flask ..."`. Render kept the quotes, so the shell took the whole text as one command name. The commands were moved into `docker-start.sh` and the command became `sh docker-start.sh`; the next deploy went Live |
