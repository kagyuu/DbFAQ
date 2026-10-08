"""GET /api/pdb(docs/P002-frontend-spec.md §3.14)。※CR-005により追加"""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..schemas import PdbInfoResponse

router = APIRouter()


@router.get("/api/pdb", response_model=PdbInfoResponse)
async def pdb_info(request: Request):
    return await request.app.state.pdb_service.info(request.app.state.now())
