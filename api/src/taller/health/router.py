"""Health check endpoint: reports whether the API and its database are up."""

from typing import Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from taller.shared.db import get_db

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    """Response body for ``GET /api/health``."""

    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


@router.get("/health", response_model=HealthStatus)
def get_health(response: Response, db: Session = Depends(get_db)) -> HealthStatus:
    """Report API health, including a live ``SELECT 1`` against the database.

    Returns 200 when the database is reachable, 503 otherwise. The database
    error itself is never included in the response body.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthStatus(status="degraded", database="unavailable")
    return HealthStatus(status="ok", database="ok")
