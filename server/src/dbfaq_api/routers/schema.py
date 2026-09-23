"""スキーマの API(docs/P002-frontend-spec.md §3.2〜§3.5)。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from ..schemas import ErViewResponse, RefreshResponse, RowsResponse, TableDetailResponse
from ..services import SchemaService

router = APIRouter(prefix="/api/schema")

Ident = Annotated[str, Path(min_length=1, max_length=128)]


def _service(request: Request) -> SchemaService:
    return request.app.state.service


@router.get("", response_model=ErViewResponse)
async def get_schema(request: Request):
    return await _service(request).er_view()


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_schema(request: Request):
    return await _service(request).refresh()


@router.get("/tables/{owner}/{table}", response_model=TableDetailResponse)
async def get_table_detail(request: Request, owner: Ident, table: Ident):
    return await _service(request).table_detail(owner, table)


@router.get("/tables/{owner}/{table}/rows", response_model=RowsResponse)
async def get_table_rows(
    request: Request,
    owner: Ident,
    table: Ident,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
):
    return await _service(request).rows(owner, table, offset, limit)
