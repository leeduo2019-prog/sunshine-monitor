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


def setup_logging(level=logging.INFO):
    """统一日志配置，各模块调用 getLogger 即可"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


class CrawlerConfig:
    """爬虫配置"""
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
    """筛选配置"""
    KEYWORDS = os.getenv(
        "FILTER_KEYWORDS",
        "造价,审计,决算,财务,预算"
    ).split(",")


class DingTalkConfig:
    """钉钉机器人配置"""
    WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")
    SECRET = os.getenv("DINGTALK_SECRET", "")
    TIMEOUT = int(os.getenv("DINGTALK_TIMEOUT", "10"))


class AppPaths:
    """路径配置"""
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    HISTORY_FILE = DATA_DIR / "project_history.json"

    @classmethod
    def ensure_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
