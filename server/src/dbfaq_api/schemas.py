"""API のレスポンス型(docs/P002-frontend-spec.md §3)。"""

from __future__ import annotations

from pydantic import BaseModel


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


class ErrorBody(BaseModel):
    code: str
    message: str
    ora_code: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
