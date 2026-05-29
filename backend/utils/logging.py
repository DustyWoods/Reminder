import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别，默认 INFO
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        Logger 实例
    """
    return logging.getLogger(name)


logger = get_logger(__name__)
