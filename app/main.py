from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine


app = FastAPI(
    title=settings.app_name,
    description="Clothing E-Commerce Platform",
    version=settings.app_version,
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
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "result": value,
    }