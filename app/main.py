from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.orders import router as orders_router
from app.core.config import settings
from app.db.database import engine
from app.api.v1.endpoints.categories import (
    router as category_router,
)

from app.api.v1.endpoints.products import (
    router as product_router,
)

from app.api.v1.endpoints.test_permissions import (
    router as permissions_router,
)
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import setup_logging


setup_logging()

app = FastAPI(
    title=settings.app_name,
    description="Clothing E-Commerce Platform",
    version=settings.app_version,
)

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/media",
    StaticFiles(directory=static_dir),
    name="media",
)


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    admin_router,
    prefix="/api/v1",
)

app.include_router(
    orders_router,
    prefix="/api/v1",
)

app.include_router(
    category_router,
    prefix="/api/v1",
)

app.include_router(
    product_router,
    prefix="/api/v1",
)

app.include_router(
    permissions_router,
    prefix="/api/v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stylehub-frontend-v2ei.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Welcome to StyleHub",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/db-health")
def database_health():

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        value = result.scalar()

    return {
        "database": "connected",
        "result": value,
    }