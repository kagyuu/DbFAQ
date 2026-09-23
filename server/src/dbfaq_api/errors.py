"""API エラー(docs/P002-frontend-spec.md §3.1、docs/P003-backend-spec.md §4.4)。"""

from __future__ import annotations

VALIDATION_ERROR = "VALIDATION_ERROR"
SCHEMA_NOT_LOADED = "SCHEMA_NOT_LOADED"
TABLE_NOT_FOUND = "TABLE_NOT_FOUND"
REFRESH_IN_PROGRESS = "REFRESH_IN_PROGRESS"
ORACLE_ERROR = "ORACLE_ERROR"
ORACLE_TIMEOUT = "ORACLE_TIMEOUT"
MCP_UNAVAILABLE = "MCP_UNAVAILABLE"
INTERNAL_ERROR = "INTERNAL_ERROR"

HTTP_STATUS = {
    VALIDATION_ERROR: 422,
    SCHEMA_NOT_LOADED: 404,
    TABLE_NOT_FOUND: 404,
    REFRESH_IN_PROGRESS: 409,
    ORACLE_ERROR: 502,
    ORACLE_TIMEOUT: 504,
    MCP_UNAVAILABLE: 503,
    INTERNAL_ERROR: 500,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, ora_code: str | None = None, http_status: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.ora_code = ora_code
        self.http_status = http_status or HTTP_STATUS[code]

    def body(self) -> dict:
        err: dict = {"code": self.code, "message": self.message}
        if self.ora_code:
            err["ora_code"] = self.ora_code
        return {"error": err}


class McpToolError(Exception):
    """MCP ツールがエラーを返した(docs/P003-backend-spec.md §3.2 の JSON)。"""

    def __init__(self, code: str, message: str, ora_code: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.ora_code = ora_code


class McpUnavailable(Exception):
    """MCP サーバを起動できない、または通信できない。"""
