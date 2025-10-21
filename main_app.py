import uvicorn
import asyncio
import logging
from utils import get_server_certificate, Logger

logger = Logger("main_app")


def run_app():
    logger.info("============ Starting server ============")
    key, pem = get_server_certificate()
    logger.debug(f"Loading server certificate from {pem}")
    config = {
        "app": "app:app",
        "host": "0.0.0.0",
        "port": 443,
        "server_header": False,
        "log_level": logging.DEBUG,
        "reload": True,
        "ssl_certfile": pem,
        "ssl_keyfile": key
    }
    logger.debug(f"Starting server with {config=}")
    app_config = uvicorn.Config(**config)
    logger.debug(f"Starting server with {app_config=}")
    server = uvicorn.Server(config=app_config)
    logger.debug(f"asyncio run {server=}")
    asyncio.run(server.serve())


if __name__ == '__main__':
    run_app()
