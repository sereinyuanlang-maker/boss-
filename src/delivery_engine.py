import random
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
from selenium.webdriver.common.by import By

from src.browser_manager import BrowserManager
from src.config_manager import ConfigManager
from src.job_filter import JobFilter, JobInfo
from src.logger import setup_logger

logger = setup_logger(ConfigManager())


class DeliveryStatus(Enum):
    PENDING = "待投递"
    SUCCESS = "投递成功"
    FAILED = "投递失败"
    ALREADY_DELIVERED = "已投递过"
    FILTERED = "被过滤"
    ERROR = "发生错误"


class DeliveryRecord:
    def __init__(self, job: JobInfo, status: DeliveryStatus, message: str = ""):
        self.job_id = job.job_id
        self.job_title = job.title
        self.company = job.company
        self.salary = job.salary
        self.city = job.city
        self.url = job.url
        self.status = status
        self.message = message
        self.delivered_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "salary": self.salary,
            "city": self.city,
            "url": self.url,
            "status": self.status.value,
            "message": self.message,
            "delivered_at": self.delivered_at,
        }


class DeliveryEngine:
    def __init__(self, browser_manager: BrowserManager, config: ConfigManager, job_filter: JobFilter):
        self.browser = browser_manager
        self.config = config
        self.delivery_config = config.config.delivery
        self.job_filter = job_filter
        self.records: List[DeliveryRecord] = []
        self.delivered_ids: Set[str] = set()
        self._load_delivered_ids()

    def _load_delivered_ids(self):
        delivered_file = Path(self.config.config.data.delivered_ids)
        if delivered_file.exists():
            try:
                with open(delivered_file, 'r', encoding='utf-8') as f:
                    self.delivered_ids = set(line.strip() for line in f if line.strip())
                logger.info(f"加载已投递记录: {len(self.delivered_ids)} 条")
            except Exception as e:
                logger.warning(f"加载已投递记录失败: {e}")

    def _save_delivered_id(self, job_id: str):
        self.delivered_ids.add(job_id)
        delivered_file = Path(self.config.config.data.delivered_ids)
        delivered_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(delivered_file, 'a', encoding='utf-8') as f:
                f.write(f"{job_id}\n")
        except Exception as e:
            logger.warning(f"保存已投递记录失败: {e}")

    def _save_records_to_excel(self):
        if not self.records:
            return
        
        try:
            record_file = Path(self.config.config.data.delivery_record)
            record_file.parent.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame([r.to_dict() for r in self.records])
            
            if record_file.exists():
                existing_df = pd.read_excel(record_file)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_excel(record_file, index=False, engine='openpyxl')
            logger.info(f"投递记录已保存到: {record_file}")
        except Exception as e:
            logger.error(f"保存投递记录失败: {e}")

    def is_in_active_hours(self) -> bool:
        try:
            now = datetime.now()
            start_str = self.delivery_config.active_hours.get("start", "09:00")
            end_str = self.delivery_config.active_hours.get("end", "18:00")
            
            start_hour, start_min = map(int, start_str.split(":"))
            end_hour, end_min = map(int, end_str.split(":"))
            
            start_time = now.replace(hour=start_hour, minute=start_min, second=0)
            end_time = now.replace(hour=end_hour, minute=end_min, second=0)
            
            return start_time <= now <= end_time
        except Exception as e:
            logger.warning(f"检查投递时间失败: {e}")
            return True

    def deliver_job(self, job: JobInfo) -> DeliveryRecord:
        if job.job_id in self.delivered_ids:
            logger.info(f"职位已投递过，跳过: {job.title} - {job.company}")
            return DeliveryRecord(job, DeliveryStatus.ALREADY_DELIVERED, "已投递过")
        
        try:
            logger.info(f"开始投递: {job.title} - {job.company}")
            
            self.browser.driver.get(job.url)
            self.browser.random_delay(3, 5)
            
            chat_btn = self._find_chat_button()
            if not chat_btn:
                record = DeliveryRecord(job, DeliveryStatus.FAILED, "未找到投递按钮")
                self.records.append(record)
                return record
            
            self.browser.human_like_click(chat_btn)
            self.browser.random_delay(2, 4)
            
            if self.delivery_config.use_custom_greeting and self.delivery_config.custom_greeting:
                self._send_greeting()
            
            self._save_delivered_id(job.job_id)
            
            record = DeliveryRecord(job, DeliveryStatus.SUCCESS, "投递成功")
            self.records.append(record)
            logger.info(f"投递成功: {job.title} - {job.company}")
            return record
            
        except Exception as e:
            logger.error(f"投递失败: {job.title} - {e}")
            record = DeliveryRecord(job, DeliveryStatus.ERROR, str(e))
            self.records.append(record)
            return record

    def _find_chat_button(self):
        selectors = [
            ".btn-startchat",
            ".btn-chat",
            "button:contains('立即沟通')",
            "[class*='chat']",
            "[class*='communicate']",
            ".job-op .op-btn",
            ".btn-apply",
        ]
        
        for selector in selectors:
            try:
                btn = self.browser.safe_find((By.CSS_SELECTOR, selector), timeout=3)
                if btn and btn.is_displayed():
                    return btn
            except:
                continue
        
        try:
            buttons = self.browser.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                text = btn.text.strip()
                if any(kw in text for kw in ["沟通", "投递", "申请", "立即", "chat"]):
                    if btn.is_displayed():
                        return btn
        except:
            pass
        
        return None

    def _send_greeting(self):
        try:
            greeting = self.delivery_config.custom_greeting
            if not greeting:
                return
            
            input_box = self.browser.safe_find(
                (By.CSS_SELECTOR, ".chat-input, .message-input, textarea[placeholder]"), timeout=10
            )
            if input_box:
                self.browser.human_like_typing(input_box, greeting)
                self.browser.random_delay(1, 2)
                
                send_btn = self.browser.safe_find(
                    (By.CSS_SELECTOR, ".btn-send, .send-btn, button[type='submit']"), timeout=5
                )
                if send_btn:
                    self.browser.human_like_click(send_btn)
                    logger.info("已发送自定义打招呼语")
        except Exception as e:
            logger.warning(f"发送打招呼语失败: {e}")

    def deliver_batch(self, jobs: List[JobInfo], max_count: Optional[int] = None) -> List[DeliveryRecord]:
        if max_count is None:
            max_count = self.delivery_config.daily_limit
        
        results = []
        delivered_count = 0
        
        for i, job in enumerate(jobs):
            if delivered_count >= max_count:
                logger.info(f"已达到每日投递上限: {max_count}")
                break
            
            if not self.is_in_active_hours():
                logger.info("当前不在投递时间段内，暂停投递")
                break
            
            if job.job_id in self.delivered_ids:
                continue
            
            result = self.deliver_job(job)
            results.append(result)
            
            if result.status == DeliveryStatus.SUCCESS:
                delivered_count += 1
            
            if i < len(jobs) - 1:
                interval = random.uniform(
                    self.delivery_config.interval_min,
                    self.delivery_config.interval_max
                )
                logger.info(f"等待 {interval:.1f} 秒后投递下一个...")
                time.sleep(interval)
            
            if (i + 1) % 10 == 0:
                self._save_records_to_excel()
                long_break = random.uniform(30, 60)
                logger.info(f"已投递 {i + 1} 个职位，休息 {long_break:.1f} 秒...")
                time.sleep(long_break)
        
        self._save_records_to_excel()
        logger.info(f"批量投递完成: 成功 {delivered_count} 个")
        return results

    def get_statistics(self) -> Dict:
        stats = {
            "total": len(self.records),
            "success": 0,
            "failed": 0,
            "already_delivered": 0,
            "error": 0,
            "pending": 0,
        }
        
        for record in self.records:
            if record.status == DeliveryStatus.SUCCESS:
                stats["success"] += 1
            elif record.status == DeliveryStatus.FAILED:
                stats["failed"] += 1
            elif record.status == DeliveryStatus.ALREADY_DELIVERED:
                stats["already_delivered"] += 1
            elif record.status == DeliveryStatus.ERROR:
                stats["error"] += 1
            elif record.status == DeliveryStatus.PENDING:
                stats["pending"] += 1
        
        return stats

    def generate_report(self) -> str:
        stats = self.get_statistics()
        report = f"""
========================================
Boss直聘自动投递报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================
总投递数: {stats['total']}
投递成功: {stats['success']}
投递失败: {stats['failed']}
已投递过: {stats['already_delivered']}
发生错误: {stats['error']}
待投递:   {stats['pending']}
========================================
"""
        return report
