#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目去重模块 - 基于 JSON 持久化存储
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from config import AppPaths

logger = logging.getLogger(__name__)

# 历史记录保留天数
HISTORY_RETENTION_DAYS = 30


def load_history():
    """加载历史记录"""
    AppPaths.ensure_dirs()
    if not AppPaths.HISTORY_FILE.exists():
        return {}
    try:
        with open(AppPaths.HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"加载历史记录失败: {e}")
        return {}


def save_history(history):
    """保存历史记录"""
    AppPaths.ensure_dirs()
    try:
        with open(AppPaths.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"保存历史记录失败: {e}")


def _cleanup_old_entries(history):
    """清理过期的历史记录"""
    cutoff = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    original_count = len(history)
    history = {k: v for k, v in history.items() if v >= cutoff_str}
    removed = original_count - len(history)
    if removed > 0:
        logger.info(f"清理了 {removed} 条过期历史记录")
    return history


def filter_new_projects(projects):
    """
    过滤出未通知过的新项目

    Args:
        projects: 解析出的项目列表

    Returns:
        list: 仅包含新项目
    """
    if not projects:
        return []

    history = load_history()
    history = _cleanup_old_entries(history)

    new_projects = []
    today = datetime.now().strftime("%Y-%m-%d")

    for project in projects:
        name = project.get('name', '').strip()
        if not name:
            continue

        if name not in history:
            new_projects.append(project)
            history[name] = today
            logger.info(f"新项目: {name}")
        else:
            logger.debug(f"已通知过，跳过: {name}")

    if new_projects:
        save_history(history)
        logger.info(f"发现 {len(new_projects)} 个新项目")

    return new_projects
