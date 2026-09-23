"""python -m dbfaq_mcp — stdio の MCP サーバとして起動する。標準出力には何も print しない。"""

import logging
import sys

from dbfaq_common.config import load_config
from dbfaq_common.logging import setup_logging

from .server import create_server


def main() -> None:
    cfg = load_config()
    setup_logging(cfg.app.log_level, stream=sys.stderr)
    logger = logging.getLogger("dbfaq_mcp")
    o = cfg.oracle
    logger.info(
        "MCP server starting",
        extra={"schema": o.target_schema, "host": o.host, "port": o.port, "service_name": o.service_name},
    )
    try:
        create_server(cfg).run(show_banner=False)
    finally:
        logger.info("MCP server stopped")


if __name__ == "__main__":
    main()
