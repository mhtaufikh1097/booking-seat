from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import database_status
from app.api.routes.auth import router as auth_router
from app.api.routes.master_data import router as master_data_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Whoosh Employee Seat Availability API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["health"])
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": database_status(),
    }


api_router.include_router(auth_router)
api_router.include_router(master_data_router)
app.include_router(api_router)
