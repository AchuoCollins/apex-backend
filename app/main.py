from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.auth.routes        import router as auth_router
from app.api.users.routes       import router as users_router
from app.api.metrics.routes     import router as metrics_router
from app.api.exercises.routes   import router as exercises_router
from app.api.training.routes    import router as training_router
from app.api.health.routes      import router as health_router
from app.api.analysis.routes    import router as analysis_router
from app.api.focus_areas.routes import router as focus_areas_router
from app.api.events.routes      import router as events_router
from app.api.dashboard.routes   import router as dashboard_router


import sys, traceback

_imports = [
    "app.core.config",
    "app.api.auth.routes",
    "app.api.users.routes",
    "app.api.metrics.routes",
    "app.api.exercises.routes",
    "app.api.training.routes",
    "app.api.health.routes",
    "app.api.analysis.routes",
    "app.api.focus_areas.routes",
    "app.api.events.routes",
    "app.api.dashboard.routes",
]

for _mod in _imports:
    try:
        __import__(_mod)
        print(f"OK: {_mod}", flush=True)
    except Exception:
        print(f"FAILED: {_mod}", flush=True)
        traceback.print_exc()
        sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Future: seed database, warm ML models, etc.
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-ready backend for APEX AI Physique & Training Analyzer",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handlers ────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again."},
        )

    # ── Routers ──────────────────────────────────────────
    prefix = settings.API_V1_PREFIX
    app.include_router(health_router,       prefix=prefix)
    app.include_router(auth_router,         prefix=prefix)
    app.include_router(users_router,        prefix=prefix)
    app.include_router(metrics_router,      prefix=prefix)
    app.include_router(exercises_router,    prefix=prefix)
    app.include_router(training_router,     prefix=prefix)
    app.include_router(analysis_router,     prefix=prefix)
    app.include_router(focus_areas_router,  prefix=prefix)
    app.include_router(events_router,       prefix=prefix)
    app.include_router(dashboard_router,    prefix=prefix)

    return app


app = create_app()
 