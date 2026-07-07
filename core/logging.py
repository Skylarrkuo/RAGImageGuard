"""全局日志配置"""

import logging
import sys


def setup_logging():
    """初始化日志配置，输出到 stdout"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger("rag_png")
