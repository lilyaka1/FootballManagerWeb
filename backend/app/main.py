from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import ensure_schema
from app.routers.auth import router as auth_router
from app.routers.analytics import router as analytics_router
from app.routers.catalog import clubs_router, players_router, transfers_router
from app.routers.admin import router as admin_router
from app.routers.favorites import router as favorites_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    yield


settings = get_settings()
app = FastAPI(
    title="Football Transfers API",
    description="Учебная информационная система учета и анализа трансферов футболистов",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(players_router)
app.include_router(clubs_router)
app.include_router(transfers_router)
app.include_router(analytics_router)
app.include_router(favorites_router)
app.include_router(admin_router)
app.include_router(users_router)


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
