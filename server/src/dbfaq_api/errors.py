"""API エラー(docs/P002-frontend-spec.md §3.1、docs/P003-backend-spec.md §4.4)。"""

from __future__ import annotations

VALIDATION_ERROR = "VALIDATION_ERROR"
SCHEMA_NOT_LOADED = "SCHEMA_NOT_LOADED"
TABLE_NOT_FOUND = "TABLE_NOT_FOUND"
REFRESH_IN_PROGRESS = "REFRESH_IN_PROGRESS"
SQL_REJECTED = "SQL_REJECTED"
SAVED_QUERY_NOT_FOUND = "SAVED_QUERY_NOT_FOUND"  # ※CR-005により追加
QUERY_NAME_CONFLICT = "QUERY_NAME_CONFLICT"  # ※CR-005により追加
ORACLE_ERROR = "ORACLE_ERROR"
ORACLE_TIMEOUT = "ORACLE_TIMEOUT"
INTERNAL_ERROR = "INTERNAL_ERROR"

HTTP_STATUS = {
    VALIDATION_ERROR: 422,
    SCHEMA_NOT_LOADED: 404,
    TABLE_NOT_FOUND: 404,
    REFRESH_IN_PROGRESS: 409,
    SQL_REJECTED: 422,
    SAVED_QUERY_NOT_FOUND: 404,
    QUERY_NAME_CONFLICT: 409,
    ORACLE_ERROR: 502,
    ORACLE_TIMEOUT: 504,
    INTERNAL_ERROR: 500,
}


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        ora_code: str | None = None,
        http_status: int | None = None,
        position: dict[str, int] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.ora_code = ora_code
        self.http_status = http_status or HTTP_STATUS[code]
        self.position = position

    def body(self) -> dict:
        err: dict = {"code": self.code, "message": self.message}
        if self.ora_code:
            err["ora_code"] = self.ora_code
        if self.position:
            err["position"] = self.position
        return {"error": err}

