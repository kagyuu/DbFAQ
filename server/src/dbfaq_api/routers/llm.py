"""POST /api/llm/sql(docs/P002-frontend-spec.md §3.15)。※CR-007により追加"""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..schemas import LlmSqlRequest, LlmSqlResponse

router = APIRouter()


@router.post("/api/llm/sql", response_model=LlmSqlResponse)
async def generate_sql(request: Request, body: LlmSqlRequest):
    return await request.app.state.llm_service.generate(body.request, body.scope, body.owner, body.table)
