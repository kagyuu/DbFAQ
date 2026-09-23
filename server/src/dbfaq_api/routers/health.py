"""GET /api/health(docs/P002-frontend-spec.md §3.7)。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..schemas import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health(request: Request):
    return await request.app.state.service.health(request.app.state.now())
