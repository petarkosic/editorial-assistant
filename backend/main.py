from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.settings import settings

app = FastAPI(
    title="Editorial Assistant API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routers import health as health_router  # noqa: E402
from backend.routers import runs as runs_router  # noqa: E402

app.include_router(health_router.router, prefix="/api")
app.include_router(runs_router.router, prefix="/api")
