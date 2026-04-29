# this is always the first import; do not alter
import gevent.monkey
gevent.monkey.patch_all()

import sys
import traceback

from loguru import logger

from src.client.client import IRCClient
from src.config.config import get_config


def main():
    """Entry point for the application."""

    logger.info("Loading app config...")
    app_config = get_config()
    logger.debug(f"App config: {app_config}")

    # move somewhere idk
    app_config.user_logs_path.parent.mkdir(parents=True, exist_ok=True)
    app_config.user_logs_path.touch(exist_ok=True)

    # make it dirty
    logger.info("Starting IRC client...")
    client = IRCClient(app_config)
    try:
        client.start()
    except Exception as e:
        logger.error(f"Client crashed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

