#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析器模块 - 解析 HTML 并提取项目信息
"""

import logging
import re
from bs4 import BeautifulSoup

from config import FilterConfig

logger = logging.getLogger(__name__)

# 无效关键词常量
_INVALID_KEYWORDS = [
    '条/页', '10条', '20条', '50条', '100条',
    '监督举报', '请先登录', '返回首页', '国家企业信用信息公示系统'
]


def parse_projects(html_content):
    """
    解析 HTML 内容，提取项目信息

    Args:
        html_content: 页面 HTML 内容

    Returns:
        list: 项目列表，每个项目包含 name、owner、date 字段
    """
    projects = []

    if not html_content or len(html_content) < 100:
        logger.warning("HTML 内容过短，跳过解析")
        return projects

    try:
        soup = BeautifulSoup(html_content, 'lxml')

        if "暂无数据" in html_content:
            logger.info("页面显示暂无数据")
            return projects

        project_items = soup.find_all('div', class_='show-item')
        logger.info(f"找到 {len(project_items)} 个项目卡片")

        for i, item in enumerate(project_items):
            item_text = item.get_text(separator=' ', strip=True)

            project_name = _extract_project_name(item_text)
            if not project_name:
                continue

            owner = _extract_owner(item_text)
            date = _extract_date(item_text)

            projects.append({
                'name': project_name,
                'owner': owner,
                'date': date
            })

        logger.info(f"成功解析 {len(projects)} 个项目")
        return projects

    except Exception as e:
        logger.error(f"解析 HTML 异常: {e}", exc_info=True)
        return []


def _extract_project_name(item_text):
    """提取项目名称"""
    if '招标编号' in item_text:
        idx = item_text.find('招标编号')
        name = item_text[:idx].strip()
        if name and len(name) >= 5:
            return name

    suffixes = ['公示', '公告', '邀请函']
    for suffix in suffixes:
        if suffix in item_text:
            name = item_text[:item_text.find(suffix) + len(suffix)].strip()
            if name and len(name) >= 5:
                return name

    return None


def _extract_owner(item_text):
    """提取招标人"""
    match = re.search(r'招标人[:：\s]*([^\s发布时间]{2,50})', item_text)
    return match.group(1).strip() if match else '未知'


def _extract_date(item_text):
    """提取发布时间"""
    match = re.search(r'发布时间[:：\s]*(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})', item_text)
    return match.group(1) if match else '未知'


def _is_valid_project(name):
    """验证项目名称是否有效"""
    if any(kw in name for kw in _INVALID_KEYWORDS):
        return False
    if not any('\u4e00' <= char <= '\u9fff' for char in name):
        return False
    return True


def filter_projects(projects, keywords=None):
    """
    根据关键词筛选项目

    Args:
        projects: 项目列表
        keywords: 关键词列表，默认使用配置值

    Returns:
        list: 筛选后的项目列表
    """
    if keywords is None:
        keywords = FilterConfig.KEYWORDS

    filtered = []
    for project in projects:
        name = project.get('name', '')
        owner = project.get('owner', '')
        if any(kw in name or kw in owner for kw in keywords):
            filtered.append(project)

    logger.info(f"筛选出 {len(filtered)} 个项目 (关键词: {keywords})")
    return filtered


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        with open('page_saved.html', 'r', encoding='utf-8') as f:
            html = f.read()
        projects = parse_projects(html)
        logger.info(f"总项目数: {len(projects)}")
        filtered = filter_projects(projects)
        logger.info(f"筛选后项目数: {len(filtered)}")
    except Exception as e:
        logger.error(f"测试失败: {e}")
