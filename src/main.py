#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主入口 - 编排爬虫、解析、筛选、去重和通知发送
"""

import logging
from datetime import datetime

from config import CrawlerConfig, DingTalkConfig, setup_logging
from crawler import get_all_pages_html
from parser import parse_projects, filter_projects
from dedup import filter_new_projects
from dingtalk_notifier import send_project_notifications

logger = logging.getLogger(__name__)


def _check_config():
    """启动时检查关键配置"""
    errors = []
    if not DingTalkConfig.WEBHOOK_URL:
        errors.append("DINGTALK_WEBHOOK_URL 为空")
    if not DingTalkConfig.SECRET:
        errors.append("DINGTALK_SECRET 为空")
    if not CrawlerConfig.TARGET_URL:
        errors.append("TARGET_URL 为空")
    if errors:
        for e in errors:
            logger.error(f"配置缺失: {e}")
        logger.error("请检查 .env 文件是否存在以及内容是否正确")
        logger.error(f".env 文件路径应为: {DingTalkConfig.__module__}")
        return False
    return True


def main():
    """主函数"""
    setup_logging()
    logger.info("=" * 50)
    logger.info("阳光平台监控任务启动")
    logger.info("=" * 50)

    # 检查关键配置
    if not _check_config():
        logger.error("配置检查未通过，退出")
        return

    try:
        # 1. 获取 HTML
        logger.info(f"目标 URL: {CrawlerConfig.TARGET_URL}")
        result = get_all_pages_html(CrawlerConfig.TARGET_URL)
        html_content, id_map = result if isinstance(result, tuple) else (result, {})

        if not html_content or len(html_content) < 100:
            logger.error("未能获取有效页面内容")
            send_project_notifications([], is_crawler_failure=True)
            return

        logger.info(f"获取 HTML 成功，长度: {len(html_content)}，ID映射: {len(id_map)} 条")

        # 2. 解析项目
        projects = parse_projects(html_content, id_map=id_map)
        logger.info(f"解析出 {len(projects)} 个项目")

        # 3. 关键词筛选
        filtered = filter_projects(projects)
        logger.info(f"关键词筛选后: {len(filtered)} 个项目")

        # 4. 去重
        new_projects = filter_new_projects(filtered)
        logger.info(f"去重后新项目: {len(new_projects)} 个")

        # 5. 发送通知（只在有匹配的新项目时才通知，避免刷屏）
        if new_projects:
            logger.info(f"发送 {len(new_projects)} 个新项目通知")
            success = send_project_notifications(new_projects, is_crawler_failure=False)
            logger.info(f"钉钉通知发送 {'成功' if success else '失败'}")
        else:
            logger.info("无新项目，发送完成通知")
            success = send_project_notifications([], is_crawler_failure=False)
            logger.info(f"钉钉完成通知发送 {'成功' if success else '失败'}")

    except Exception as e:
        logger.error(f"任务执行异常: {e}", exc_info=True)
        try:
            send_project_notifications([], is_crawler_failure=True)
        except Exception:
            logger.error("异常通知发送也失败")

    logger.info("监控任务结束")


if __name__ == "__main__":
    main()
