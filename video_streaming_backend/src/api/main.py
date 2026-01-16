from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.auth import router as auth_router
from src.db.session import check_db_connection
from src.settings import get_settings

settings = get_settings()

openapi_tags = [
    {"name": "Health", "description": "Service health and readiness endpoints."},
    {"name": "Auth", "description": "User registration/login and JWT token management."},
]

app = FastAPI(
    title="StreamView Backend API",
    description="Backend API for authentication, video upload/streaming, search, and admin operations.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth_router)


@app.on_event("startup")
async def _startup_db_check() -> None:
    """Validate DB connectivity at startup.

    This fails fast if DATABASE_URL is missing/incorrect or DB is unavailable.
    """
    check_db_connection()


@app.get("/", tags=["Health"])
def health_check():
    return {"message": "Healthy"}
