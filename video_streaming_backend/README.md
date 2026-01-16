# video_streaming_backend

FastAPI backend for StreamView.

## Required environment variables

These must be provided via `.env` (managed by orchestrator/deployment):

- `DATABASE_URL` (PostgreSQL URL, e.g. `postgresql://user:pass@host:port/dbname`)
- `JWT_SECRET` (secret used to sign JWTs)

Optional:

- `JWT_ALG` (default `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default `15`)
- `REFRESH_TOKEN_EXPIRE_DAYS` (default `30`)
- `CORS_ORIGINS` (default `*`; otherwise comma-separated list)
- `BACKEND_BASE_URL` (optional)

## Install

```bash
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Run API

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

## Database migrations (Alembic)

Migrations are configured to read `DATABASE_URL` from environment/settings.

### Run migrations

```bash
alembic upgrade head
```

### Create a new migration (autogenerate)

After you change ORM models in `src/db/models.py`:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Notes

- The application performs a DB connectivity check on startup and will fail fast if the DB is unavailable or `DATABASE_URL` is not set.
