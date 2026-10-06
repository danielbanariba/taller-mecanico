"""Application factory and ASGI entry point for the Taller Mecanico API."""

from fastapi import FastAPI

from taller.health.router import router as health_router
from taller.identity.adapters.router import router as identity_router


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(title="Taller Mecanico API")
    app.include_router(health_router, prefix="/api")
    app.include_router(identity_router, prefix="/api")
    return app


app = create_app()
