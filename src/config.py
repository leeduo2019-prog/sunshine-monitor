#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集中配置管理，从环境变量/.env 读取配置
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（项目根目录）
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


def setup_logging(level=logging.INFO, log_to_file=True):
    """统一日志配置，控制台 + 可选文件输出（logs/monitor.log）"""
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    if log_to_file:
        try:
            AppPaths.ensure_dirs()
            log_file = AppPaths.LOG_DIR / "monitor.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except Exception as e:
            print(f"[setup_logging] 文件日志初始化失败: {e}")


class CrawlerConfig:
    TARGET_URL = os.getenv(
        "TARGET_URL",
        "https://www.qdygcg.com/web-portal/#/trade-info?purchaseProjectType=&noticeType=&tradePatternId=&publishTime="
    )
    MAX_PAGES = int(os.getenv("MAX_PAGES", "10"))
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "120"))
    ELEMENT_WAIT_TIMEOUT = int(os.getenv("ELEMENT_WAIT_TIMEOUT", "30"))
    PAGE_NAVIGATION_TIMEOUT = int(os.getenv("PAGE_NAVIGATION_TIMEOUT", "15"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))


class FilterConfig:
    KEYWORDS = os.getenv(
        "FILTER_KEYWORDS",
        "造价,审计,决算,财务,预算"
    ).split(",")


class DingTalkConfig:
    WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")
    SECRET = os.getenv("DINGTALK_SECRET", "")
    TIMEOUT = int(os.getenv("DINGTALK_TIMEOUT", "10"))


class AppPaths:
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    HISTORY_FILE = DATA_DIR / "project_history.json"
    LOG_DIR = BASE_DIR / "logs"

    @classmethod
    def ensure_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
