import gevent.monkey
gevent.monkey.patch_all()

from loguru import logger

from src.client.client import IRCClient
from src.config.config import get_config


def main():

    logger.info("Loading app config...")
    app_config = get_config()
    logger.debug(f"App config: {app_config}")

    # move somewhere idk
    app_config.user_logs_path.parent.mkdir(parents=True, exist_ok=True)
    app_config.user_logs_path.touch(exist_ok=True)

    # make it dirty
    logger.info("Starting IRC client...")
    client = IRCClient(app_config)
    client.start()


if __name__ == "__main__":
    main()

