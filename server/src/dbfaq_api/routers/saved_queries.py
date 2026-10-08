"""保存済み Query の API(docs/P002-frontend-spec.md §3.10〜§3.13)。※CR-005により追加"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Path, Query, Request, Response

from ..schemas import SavedQuery, SavedQueryCreate, SavedQueryList, SavedQueryUpdate
from ..services import SavedQueryService

router = APIRouter(prefix="/api/saved-queries")

Ident = Annotated[str | None, Query(min_length=1, max_length=128)]
QueryId = Annotated[int, Path(ge=1)]


def _service(request: Request) -> SavedQueryService:
    return request.app.state.saved_query_service


@router.get("", response_model=SavedQueryList)
async def list_saved_queries(
    request: Request, scope: Literal["table", "pdb"], owner: Ident = None, table: Ident = None
):
    return await _service(request).list(scope, owner, table)


@router.post("", response_model=SavedQuery, status_code=201)
async def create_saved_query(request: Request, body: SavedQueryCreate):
    return await _service(request).create(body.scope, body.owner, body.table, body.name, body.description, body.sql)


@router.put("/{query_id}", response_model=SavedQuery)
async def update_saved_query(request: Request, query_id: QueryId, body: SavedQueryUpdate):
    return await _service(request).update(query_id, body.name, body.description, body.sql)


@router.delete("/{query_id}", status_code=204)
async def delete_saved_query(request: Request, query_id: QueryId):
    await _service(request).delete(query_id)
    return Response(status_code=204)
