# AGENTS.md

## Cursor Cloud specific instructions

LitterLog is a cat litterbox monitoring system with two parts:
- `backend/` — Python 3.12 / Flask REST API (port `8000`) plus an IoT data pipeline (simulator → RabbitMQ → persister → PostgreSQL). Managed by Poetry (in-project venv at `backend/.venv`).
- `frontend/` — Next.js 15 dashboard (port `3000`). Standard commands are in `frontend/package.json` (`npm run dev`, `build`, `lint`).

The update script keeps dependencies fresh (`poetry install` + `npm install`). Services below are NOT started by the update script — start them yourself when needed.

### Infrastructure services (installed locally; start each session if down)
- PostgreSQL 16 runs as a local cluster on the **non-standard port `5435`** (matches the app's default `DATABASE_URL`). Start: `sudo pg_ctlcluster 16 main start`. DB/creds: `example_db` / `example_user` / `example_password`. Check: `sudo pg_lsclusters`.
- RabbitMQ 3.12. Start: `sudo rabbitmq-server -detached` (takes ~10s). App connects on `5672` as `user` / `password`. Check: `sudo rabbitmqctl status`.

### Running the backend API
From `backend/`, `src` must be on `PYTHONPATH`:
`PYTHONPATH=src poetry run flask --app app run --port 8000 --host 0.0.0.0`
Defaults already point `DATABASE_URL` to `localhost:5435`; no `.env` is required for local dev (set `JWT_SECRET_KEY` for anything beyond throwaway dev).

### Database tables (gotcha)
The Flask API does NOT create tables. Tables are created by `data_persister` on startup (`Base.metadata.create_all`). Before using the API on a fresh DB, run the persister once (it also creates tables):
`PYTHONPATH=src poetry run python src/data_persister/data_persister.py` (long-running; needs RabbitMQ + Postgres up).

### Data pipeline (gotcha)
The simulator publishes usage records with a hardcoded edge-device id `12345678-1234-5678-9012-123456789abc`. Because `litterbox_usage_data.litterbox_edge_device_id` is a foreign key, you must first register an edge device with that exact id via the API (`POST /edge_devices` after creating a user → cat → litterbox) or the persister's inserts fail with FK violations. Then run the simulator to populate data:
`PYTHONPATH=src poetry run python src/data_source/litterbox_edge_device_simulator.py` (generates ~1 week of data immediately, then schedules). The persister flushes partial batches after `BATCH_TIMEOUT` (default 30s), so usage rows may take ~30s to appear.

### Frontend
`cd frontend && npm run dev`. Defaults: `NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_APP_ORIGIN=http://localhost:3000`; no env file needed.

### Lint / test (backend)
From `backend/`: `poetry run flake8 .` and `poetry run pytest tests/`.
Known caveat: `tests/test_data_source_simulator.py::test_process_data` FAILS when RabbitMQ is running locally — it asserts the file-only fallback path that only happens when the broker is unreachable (CI has no broker, so it passes there). The other 51 tests pass. To reproduce CI exactly, stop RabbitMQ before running pytest.

### Optional services
`docker compose up` (Postgres/RabbitMQ/persister/Prometheus/Grafana) is an alternative to the local services above, but Docker is not installed here — the local cluster + rabbitmq-server setup is used instead. The `db_ask` Claude CLI (`poetry run db-ask`) needs `ANTHROPIC_API_KEY` and is optional.
