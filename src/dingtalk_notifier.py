#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉群机器人 Webhook 推送模块
支持加签验证、Markdown 格式、异常捕获、超时设置
"""

import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional

from config import DingTalkConfig

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉消息推送器"""
    
    def __init__(self):
        self.webhook = DingTalkConfig.WEBHOOK_URL
        self.secret = DingTalkConfig.SECRET
        self.timeout = DingTalkConfig.TIMEOUT

        if not self.webhook:
            logger.error("钉钉 Webhook URL 为空，请检查 .env 文件中的 DINGTALK_WEBHOOK_URL")
        if not self.secret:
            logger.error("钉钉 Secret 为空，请检查 .env 文件中的 DINGTALK_SECRET")
    
    def _generate_sign(self) -> tuple:
        """
        生成钉钉加签参数
        
        Returns:
            tuple: (timestamp, sign)
        """
        if not self.secret:
            return None, None
        
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return timestamp, sign
    
    def _build_url(self) -> str:
        """构建带加签参数的 Webhook URL"""
        timestamp, sign = self._generate_sign()
        
        if timestamp and sign:
            return f'{self.webhook}&timestamp={timestamp}&sign={sign}'
        return self.webhook
    
    def send_markdown(
        self,
        title: str,
        text: str,
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False
    ) -> bool:
        """
        发送 Markdown 格式消息
        
        Args:
            title: 消息标题（首屏展示）
            text: Markdown 格式正文
            at_mobiles: @指定手机号列表
            at_all: 是否 @所有人
            
        Returns:
            bool: 发送是否成功
        """
        url = self._build_url()
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "atAll": at_all
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"钉钉 API 原始响应: {result}")
            if result.get('errcode') == 0:
                logger.info(f"钉钉消息发送成功: {title}")
                return True
            else:
                logger.error(f"钉钉消息发送失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"钉钉消息发送超时（{self.timeout}s）")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"钉钉消息发送异常: {e}")
            return False
        except Exception as e:
            logger.error(f"钉钉消息发送未知异常: {e}")
            return False


def send_project_notifications(projects, is_crawler_failure=False):
    """
    将筛选出的项目通过钉钉推送
    
    Args:
        projects: 筛选后的项目列表
        is_crawler_failure: 是否是爬虫失败通知
        
    Returns:
        bool: 发送是否成功
    """
    notifier = DingTalkNotifier()
    
    # 构建消息内容
    if is_crawler_failure:
        title = "【阳光平台监控】爬虫失败通知"
        text = (
            "## ⚠️ 爬虫失败通知\n\n"
            f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "> 青岛阳光采购平台爬虫执行失败，请检查网络或平台状态。"
        )
    elif not projects:
        title = "【阳光平台监控】无匹配项目"
        text = (
            f"## 📋 今日监控结果\n\n"
            f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "> 今日爬取青岛阳光采购平台采购公告，未发现包含关键词的项目。"
        )
    else:
        title = f"【阳光平台监控】发现 {len(projects)} 个匹配项目"
        
        # 构建项目列表 Markdown
        project_list = "\n\n".join([
            f"### {i}. {project.get('name', '未知')}\n"
            f"- **招标人**: {project.get('owner', '未知')}\n"
            f"- **发布时间**: {project.get('date', '未知')}\n"
            f"- **详情**: [点击查看]({project.get('url', '#')})"
            for i, project in enumerate(projects, 1)
        ])

        for p in projects:
            logger.debug(f"通知项目: {p.get('name', '?')[:30]}... URL={p.get('url', '#')}")
        
        text = (
            f"## 🎯 今日找到 {len(projects)} 个匹配项目\n\n"
            f"**监控时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"---\n\n"
            f"{project_list}"
        )
    
    return notifier.send_markdown(title=title, text=text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
    
    test_projects = [
        {
            "name": "测试造价项目",
            "owner": "测试公司",
            "date": "2026-02-26",
            "url": "https://www.qdygcg.com/example/1"
        },
        {
            "name": "测试审计项目",
            "owner": "审计局",
            "date": "2026-02-26",
            "url": "https://www.qdygcg.com/example/2"
        }
    ]
    
    print("正在测试钉钉推送功能...")
    success = send_project_notifications(test_projects)
    print("钉钉推送测试成功！" if success else "钉钉推送测试失败，请检查 Webhook 配置。")
