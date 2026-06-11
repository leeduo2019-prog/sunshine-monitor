#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块 - 使用 Selenium 获取页面 HTML
"""

import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from config import CrawlerConfig, setup_logging

logger = logging.getLogger(__name__)


def _create_driver():
    """创建 Chrome WebDriver 实例"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu-compositing')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    chrome_options.page_load_strategy = 'normal'

    # 计划任务环境下，webdriver_manager 可能无法正常下载，添加容错
    try:
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver 路径: {driver_path}")
    except Exception as e:
        logger.warning(f"webdriver_manager 失败，尝试系统 ChromeDriver: {e}")
        driver_path = "chromedriver"

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(CrawlerConfig.PAGE_LOAD_TIMEOUT)
    driver.set_script_timeout(CrawlerConfig.PAGE_LOAD_TIMEOUT)
    driver.set_window_size(1920, 1080)
    return driver


def _wait_for_page_ready(driver, timeout=None):
    """智能等待页面元素就绪，替代固定 sleep"""
    timeout = timeout or CrawlerConfig.ELEMENT_WAIT_TIMEOUT
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.number'))
            )
            logger.debug("分页组件已加载")
        except TimeoutException:
            logger.debug("未检测到分页组件，可能无数据或单页")
    except TimeoutException:
        logger.warning("页面元素等待超时")


def _click_radio(driver, label_text, wait_timeout=10):
    """点击单选按钮（如"采购公告"、"今天"）"""
    try:
        radio = WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//label[contains(@class, 'el-radio') and contains(., '{label_text}')]")
            )
        )
        radio.click()
        logger.info(f"成功点击 '{label_text}'")
        _wait_for_page_ready(driver, timeout=15)
        return True
    except Exception as e:
        logger.warning(f"点击 '{label_text}' 失败: {e}")
        return False


def get_current_page_number(driver):
    """获取当前页码"""
    try:
        active = driver.find_element(By.CSS_SELECTOR, 'li.number.active')
        return int(active.text.strip())
    except Exception:
        return 1


def has_next_page(driver):
    """检查是否有下一页"""
    try:
        current = get_current_page_number(driver)
        pages = driver.find_elements(By.CSS_SELECTOR, 'li.number')
        max_page = 0
        for p in pages:
            try:
                max_page = max(max_page, int(p.text.strip()))
            except ValueError:
                continue
        return current < max_page
    except Exception:
        return False


def click_next_page_number(driver):
    """点击下一页"""
    try:
        next_page = get_current_page_number(driver) + 1
        for p in driver.find_elements(By.CSS_SELECTOR, 'li.number'):
            try:
                if int(p.text.strip()) == next_page:
                    p.click()
                    logger.info(f"成功点击第 {next_page} 页")
                    return True
            except ValueError:
                continue
        logger.warning(f"未找到第 {next_page} 页")
        return False
    except Exception as e:
        logger.warning(f"点击下一页失败: {e}")
        return False


def get_all_pages_html(url, max_pages=None):
    """
    获取所有页面的 HTML（带重试机制）

    Args:
        url: 目标 URL
        max_pages: 最大爬取页数，默认使用配置值

    Returns:
        str: 合并后的 HTML 内容
    """
    max_pages = max_pages or CrawlerConfig.MAX_PAGES

    for attempt in range(1, CrawlerConfig.MAX_RETRIES + 1):
        driver = None
        try:
            logger.info(f"爬虫尝试 {attempt}/{CrawlerConfig.MAX_RETRIES}")
            driver = _create_driver()

            logger.info(f"正在访问 URL: {url}")
            driver.get(url)

            _wait_for_page_ready(driver)

            # 点击筛选条件：按"公告类型 → 全部重置 → 时间"顺序，
            # 时间类筛选放最后，避免后续点击把"今天"覆盖。
            # 每个 click 之间显式等待分页组件刷新。
            if not _click_radio(driver, "采购公告"):  # 公告类型
                logger.warning("未点击到 '采购公告'，可能已是默认")
            if not _click_radio(driver, "全部"):  # 交易领域（重置）
                logger.warning("未点击到 '全部'(交易领域)")
            if not _click_radio(driver, "全部"):  # 采购方式（重置）
                logger.warning("未点击到 '全部'(采购方式)")
            if not _click_radio(driver, "今天"):  # 发布时间（最后，避免被覆盖）
                logger.warning("未点击到 '今天'，将拉取全部时间数据")

            # 分页爬取（爬到最后一页，不受 max_pages 限制）
            all_html = ""
            page_num = 1
            while True:
                logger.info(f"正在爬取第 {page_num} 页...")
                current_html = driver.page_source
                all_html += f"\n<!-- 第 {page_num} 页 -->\n" + current_html
                logger.info(f"第 {page_num} 页 HTML 长度: {len(current_html)}")

                if not has_next_page(driver):
                    logger.info("没有下一页，停止爬取")
                    break

                if not click_next_page_number(driver):
                    logger.warning("点击下一页失败，停止爬取")
                    break

                _wait_for_page_ready(driver, timeout=CrawlerConfig.PAGE_NAVIGATION_TIMEOUT)
                page_num += 1

            logger.info(f"总共爬取 {page_num} 页，合并 HTML 长度: {len(all_html)}")
            return all_html

        except (TimeoutException, WebDriverException) as e:
            logger.warning(f"爬虫异常 (尝试 {attempt}/{CrawlerConfig.MAX_RETRIES}): {e}")
            if attempt < CrawlerConfig.MAX_RETRIES:
                time.sleep(CrawlerConfig.RETRY_DELAY * attempt)
        except Exception as e:
            logger.error(f"爬虫未知异常: {e}", exc_info=True)
            return ""
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    logger.error(f"爬虫在 {CrawlerConfig.MAX_RETRIES} 次尝试后仍失败")
    return ""


def get_page_html(url):
    """单页版本（保持向后兼容）"""
    return get_all_pages_html(url, max_pages=1)


if __name__ == "__main__":
    setup_logging()
    target_url = os.getenv(
        "TARGET_URL",
        "https://www.qdygcg.com/web-portal/#/trade-info?purchaseProjectType=&noticeType=采购公告&tradePatternId=&publishTime="
    )
    html = get_all_pages_html(target_url)
    if html:
        logger.info(f"HTML 总长度: {len(html)}")
    else:
        logger.error("未能获取页面内容")
