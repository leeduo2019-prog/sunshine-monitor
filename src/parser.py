#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析器模块 - 解析 HTML 并提取项目信息

优先使用 BeautifulSoup 选择器定位字段，规避字符串切分脆弱性。
"""

import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup

from config import FilterConfig

logger = logging.getLogger(__name__)

# 无效关键词常量（出现在项目名称中应剔除）
_INVALID_KEYWORDS = [
    '条/页', '10条', '20条', '50条', '100条',
    '监督举报', '请先登录', '返回首页', '国家企业信用信息公示系统'
]

# 项目名称合法后缀
_NAME_SUFFIXES = ['公示', '公告', '邀请函']

# 日期匹配模式（带可选年份）
_DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})')


def parse_projects(html_content, id_map=None):
    """
    解析 HTML 内容，提取项目信息

    Args:
        html_content: 页面 HTML 内容
        id_map: 项目名称 → ID 的映射字典，用于构造详情页 URL

    Returns:
        list: 项目列表，每个项目包含 name、owner、date、url 字段
    """
    projects = []

    if not html_content or len(html_content) < 100:
        logger.warning("HTML 内容过短，跳过解析")
        return projects

    try:
        if "暂无数据" in html_content:
            logger.info("页面显示暂无数据")
            return projects

        soup = BeautifulSoup(html_content, 'lxml')

        # 通过结构化选择器定位卡片，避免依赖特定 class 名
        project_items = soup.select('div.show-item') or soup.find_all(
            'div', attrs={'class': lambda v: v and 'show-item' in v}
        )
        logger.info(f"找到 {len(project_items)} 个项目卡片")

        for item in project_items:
            project = _extract_project(item, id_map or {})
            if project:
                projects.append(project)

        logger.info(f"成功解析 {len(projects)} 个项目")
        return projects

    except Exception as e:
        logger.error(f"解析 HTML 异常: {e}", exc_info=True)
        return []


def _extract_project(item, id_map):
    """从单个项目卡片 DOM 中提取结构化字段"""
    try:
        name = _extract_name_from_dom(item)
        if not name or not _is_valid_name(name):
            return None

        owner = _extract_owner_from_dom(item)

        full_text = item.get_text(separator=' ', strip=True)
        date = _extract_date(full_text)

        return {
            'name': name,
            'owner': owner,
            'date': date,
            'url': _extract_url(item, name, id_map),
        }
    except Exception as e:
        logger.debug(f"解析单个项目卡片异常: {e}")
        return None


def _extract_name_from_dom(item):
    """从 DOM 提取项目名称"""
    title_el = item.find(lambda tag: tag.name in ('h1', 'h2', 'h3', 'h4', 'p', 'div', 'span')
                         and tag.get_text(strip=True)
                         and '招标编号' in tag.get_text())
    if title_el:
        full = title_el.get_text(separator=' ', strip=True)
        idx = full.find('招标编号')
        if idx > 0:
            candidate = full[:idx].strip()
            if _is_valid_name(candidate):
                return candidate

    full_text = item.get_text(separator=' ', strip=True)
    if '招标编号' in full_text:
        candidate = full_text[:full_text.find('招标编号')].strip()
        if _is_valid_name(candidate):
            return candidate

    for suffix in _NAME_SUFFIXES:
        if suffix in full_text:
            candidate = full_text[:full_text.find(suffix) + len(suffix)].strip()
            if _is_valid_name(candidate):
                return candidate

    return None


def _extract_owner_from_dom(item):
    """从 DOM 提取招标人"""
    label_el = item.find(lambda tag: tag.name
                         and '招标人' in tag.get_text()
                         and len(tag.get_text(strip=True)) < 200)
    if label_el:
        text = label_el.get_text(separator=' ', strip=True)
        m = re.search(r'招标人\s*[:：]?\s*(.+?)(?=\s*(?:发布时间|招标编号|$))', text)
        if m:
            owner = m.group(1).strip()
            if owner:
                return owner

    full_text = item.get_text(separator=' ', strip=True)
    m = re.search(r'招标人\s*[:：]?\s*([^\s]{2,50}?)(?=\s*(?:发布时间|招标编号|$))', full_text)
    return m.group(1).strip() if m else '未知'


def _extract_date(text):
    """从文本中提取第一个日期字符串"""
    m = _DATE_PATTERN.search(text)
    if not m:
        return '未知'
    raw = m.group(1)
    # 短格式 mm-dd 补全年份
    if len(raw) == 5:
        return f"{datetime.now().year}-{raw}"
    return raw


_BASE_URL = "https://www.qdygcg.com/web-portal/"


def _extract_url(item, name='', id_map=None):
    """提取项目详情链接（若存在）"""
    id_map = id_map or {}

    # 优先用 ID 映射构造详情页 URL（含 noticeType/publishStatus/systemStatus 参数）
    if name and name in id_map:
        info = id_map[name]
        if isinstance(info, dict):
            project_id = info.get('id', '')
            notice_type = info.get('noticeType', '')
            publish_status = info.get('publishStatus', '')
            system_status = info.get('systemStatus')
            # null/None → false
            system_status_str = str(system_status).lower() if system_status is not None else 'false'
            url = (f"{_BASE_URL}#/trade-info-detail?id={project_id}"
                   f"&noticeType={notice_type}"
                   f"&publishStatus={publish_status}"
                   f"&systemStatus={system_status_str}")
        else:
            url = f"{_BASE_URL}#/trade-info-detail?id={info}"
        logger.info(f"URL构造: ID映射 → {url}")
        return url

    a = item.find('a', href=True)
    if a:
        href = a['href'].strip()
        if not href or href == 'javascript:void(0)':
            pass
        elif href.startswith('http'):
            logger.info(f"URL提取: 绝对链接 → {href}")
            return href
        elif href.startswith('/'):
            full = f"https://www.qdygcg.com{href}"
            logger.info(f"URL提取: 根相对 → {full}")
            return full
        elif href.startswith('#/') or href.startswith('#!'):
            full = f"{_BASE_URL}{href}"
            logger.info(f"URL提取: hash路由 → {full}")
            return full
        else:
            full = f"{_BASE_URL}{href}"
            logger.info(f"URL提取: 相对路径 → {full}")
            return full

    # 无 <a> 标签：尝试从 data 属性或 onclick 提取线索
    for attr in ('data-href', 'data-url', 'data-id'):
        val = item.get(attr)
        if val:
            logger.info(f"URL提取: {attr} → {val}")
            return val if val.startswith('http') else f"{_BASE_URL}{val}"

    logger.info(f"URL构造: 未找到ID映射(name={name[:20]}...)，回退到列表页")
    return f"{_BASE_URL}#/trade-info"


def _is_valid_name(name):
    """验证项目名称是否有效"""
    if not name or len(name) < 5 or len(name) > 200:
        return False
    if any(kw in name for kw in _INVALID_KEYWORDS):
        return False
    if not any('一' <= ch <= '鿿' for ch in name):
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
