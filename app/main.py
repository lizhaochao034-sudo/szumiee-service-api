from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import Settings

settings = Settings()
app = FastAPI(title=settings.app_title, version="0.1.0")
app.include_router(health_router)
