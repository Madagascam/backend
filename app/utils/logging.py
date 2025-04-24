import sys

from loguru import logger


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="[{time:YYYY-MM-DD HH:mm:ss}] <b><level>{level:^10}</level></b>{message}",
        backtrace=True,
        diagnose=True,
        colorize=True,
    )

    # For now data is not being logged, maybe we will refuse db logging

    logger.configure(extra={"user_id": 0, "name": "System"})

    logger.level("TRACE", color="<cyan>")
    logger.level("DEBUG", color="<cyan>")
    logger.level("INFO", color="<blue>")
    logger.level("SUCCESS", color="<green>")
    logger.level("WARNING", color="<yellow>")
    logger.level("ERROR", color="<light-red>")
    logger.level("CRITICAL", color="<red>")
