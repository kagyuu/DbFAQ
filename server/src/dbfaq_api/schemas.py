"""API のレスポンス型(docs/P002-frontend-spec.md §3)。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_SQL_CHARS = 100_000
MAX_QUERY_NAME_CHARS = 100
MAX_QUERY_DESCRIPTION_CHARS = 1_000


class SnapshotSummary(BaseModel):
    owner: str
    fetched_at: str
    oracle_version: str
    table_count: int
    relation_count: int


class ErColumn(BaseModel):
    name: str
    column_id: int
    data_type_display: str
    nullable: bool
    is_pk: bool
    is_fk: bool


class ErTable(BaseModel):
    owner: str
    name: str
    comment: str | None
    num_rows: int | None
    columns: list[ErColumn]


class Relation(BaseModel):
    name: str
    from_owner: str
    from_table: str
    from_columns: list[str]
    to_owner: str | None
    to_table: str | None
    to_columns: list[str | None]


class ErViewResponse(BaseModel):
    loaded: bool
    snapshot: SnapshotSummary | None
    tables: list[ErTable]
    relations: list[Relation]


class RefreshResponse(BaseModel):
    snapshot: SnapshotSummary


class DetailSnapshot(BaseModel):
    owner: str
    fetched_at: str


class DetailTable(BaseModel):
    owner: str
    name: str
    comment: str | None
    num_rows: int | None
    last_analyzed: str | None
    iot: bool


class DetailColumn(BaseModel):
    column_id: int
    name: str
    data_type: str
    data_type_display: str
    data_length: int | None
    data_precision: int | None
    data_scale: int | None
    nullable: bool
    data_default: str | None
    comment: str | None
    pk_position: int | None
    is_fk: bool


class KeyConstraint(BaseModel):
    name: str
    columns: list[str]


class ForeignKey(BaseModel):
    name: str
    columns: list[str]
    ref_owner: str | None
    ref_table: str | None
    ref_columns: list[str | None]
    delete_rule: str | None
    ref_in_snapshot: bool


class ReferencedBy(BaseModel):
    name: str
    from_owner: str
    from_table: str
    from_columns: list[str]
    columns: list[str | None]


class IndexColumn(BaseModel):
    name: str
    descending: bool


class Index(BaseModel):
    name: str
    unique: bool
    index_type: str
    columns: list[IndexColumn]


class TableDetailResponse(BaseModel):
    snapshot: DetailSnapshot
    table: DetailTable
    columns: list[DetailColumn]
    primary_key: KeyConstraint | None
    unique_keys: list[KeyConstraint]
    foreign_keys: list[ForeignKey]
    referenced_by: list[ReferencedBy]
    indexes: list[Index]


class RowColumn(BaseModel):
    name: str
    data_type: str


class RowsResponse(BaseModel):
    owner: str
    table: str
    columns: list[RowColumn]
    rows: list[list[str | None]]
    truncated: list[list[int]]
    offset: int
    limit: int
    has_next: bool
    order_basis: str
    order_by: list[str]
    elapsed_ms: int


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=MAX_SQL_CHARS)

    @field_validator("sql")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SQL を入力してください")
        return v


class QueryResponse(BaseModel):
    columns: list[RowColumn]
    rows: list[list[str | None]]
    truncated: list[list[int]]
    row_count: int
    has_more: bool
    max_rows: int
    elapsed_ms: int


# ---- 保存済み Query・PDB(P002 §3.10〜§3.14。※CR-005により追加) -------------------------


def _not_blank_sql(v: str) -> str:
    if not v.strip():
        raise ValueError("SQL を入力してください")
    return v


class SavedQueryBody(BaseModel):
    """PUT の本文。名前・説明は前後の空白を除いてから長さを検査する。"""

    name: str
    description: str = ""
    sql: str = Field(min_length=1, max_length=MAX_SQL_CHARS)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("名前を入力してください")
        if len(v) > MAX_QUERY_NAME_CHARS:
            raise ValueError(f"{MAX_QUERY_NAME_CHARS} 文字以内で入力してください")
        return v

    @field_validator("description")
    @classmethod
    def _description(cls, v: str) -> str:
        v = v.strip()
        if len(v) > MAX_QUERY_DESCRIPTION_CHARS:
            raise ValueError(f"{MAX_QUERY_DESCRIPTION_CHARS} 文字以内で入力してください")
        return v

    @field_validator("sql")
    @classmethod
    def _sql(cls, v: str) -> str:
        return _not_blank_sql(v)


class SavedQueryUpdate(SavedQueryBody):
    description: str


class SavedQueryCreate(SavedQueryBody):
    scope: Literal["table", "pdb"]
    owner: str | None = Field(default=None, min_length=1, max_length=128)
    table: str | None = Field(default=None, min_length=1, max_length=128)


class SavedQuery(BaseModel):
    id: int
    scope: str
    owner: str | None
    table: str | None
    name: str
    description: str
    sql: str
    is_template: bool
    created_at: str
    updated_at: str


class SavedQueryList(BaseModel):
    items: list[SavedQuery]


class PdbSectionError(BaseModel):
    code: str
    message: str
    ora_code: str | None = None


class PdbSection(BaseModel):
    key: str
    title: str
    columns: list[RowColumn]
    rows: list[list[str | None]]
    truncated: list[list[int]]
    error: PdbSectionError | None


class PdbInfoResponse(BaseModel):
    sections: list[PdbSection]
    fetched_at: str
    elapsed_ms: int


class BackendHealth(BaseModel):
    status: str
    version: str


class OracleHealth(BaseModel):
    status: str
    version: str | None = None
    user: str | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    status: str
    backend: BackendHealth
    oracle: OracleHealth
    config: dict[str, object]
    checked_at: str


class ErrorPosition(BaseModel):
    offset: int
    line: int
    column: int


class ErrorBody(BaseModel):
    code: str
    message: str
    ora_code: str | None = None
    position: ErrorPosition | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
