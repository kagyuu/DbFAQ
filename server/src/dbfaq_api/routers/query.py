"""Query タブの API(docs/P002-frontend-spec.md §3.8・§3.9)。※CR-004により追加"""

from __future__ import annotations

from collections.abc import Iterator
from typing import IO

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..schemas import QueryRequest, QueryResponse
from ..services import QueryService

router = APIRouter(prefix="/api/query")

CHUNK = 64 * 1024


def _service(request: Request) -> QueryService:
    return request.app.state.query_service


def _iter_file(f: IO[bytes]) -> Iterator[bytes]:
    try:
        while chunk := f.read(CHUNK):
            yield chunk
    finally:
        f.close()  # 送り終えたとき・利用者が切断したとき


@router.post("", response_model=QueryResponse)
async def run_query(request: Request, body: QueryRequest):
    return await _service(request).run(body.sql)


@router.post("/csv")
async def export_csv(request: Request, body: QueryRequest):
    spool, count = await _service(request).csv(body.sql)
    return StreamingResponse(
        _iter_file(spool),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="query.csv"', "X-Row-Count": str(count)},
    )
