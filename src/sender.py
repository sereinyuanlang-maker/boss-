import time
from typing import List, Optional

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.anti_detect import AntiDetection
from src.browser import BrowserManager
from src.config import ResumeConfig, StrategyConfig
from src.exceptions import LoginError, SendResumeError
from src.filter import JobInfo
from src.logger import logger
from src.recorder import StatusRecorder
from src.utils import retry


class ResumeSender:
    """简历投递器"""

    BASE_URL = "https://www.zhipin.com"
    LOGIN_URL = f"{BASE_URL}/web/user/?ka=header-login"
    SEARCH_URL = f"{BASE_URL}/web/geek/job"

    def __init__(
        self,
        browser_manager: BrowserManager,
        resume_config: ResumeConfig,
        strategy_config: StrategyConfig,
        recorder: StatusRecorder,
    ):
        self.browser = browser_manager
        self.resume = resume_config
        self.strategy = strategy_config
        self.recorder = recorder
        self.driver = browser_manager.get_driver()
        self.anti_detect = browser_manager.get_anti_detect()
        self.daily_count = 0
        self.success_count = 0
        self.failed_count = 0

    @retry(max_attempts=3, delay=2.0, exceptions=(TimeoutException, WebDriverException))
    def login(self, username: str, password: str) -> bool:
        """登录Boss直聘"""
        if not username:
            raise LoginError("用户名不能为空")

        logger.info("开始登录Boss直聘...")
        self.driver.get(self.LOGIN_URL)
        self.anti_detect.random_sleep(3, 5)

        try:
            # 输入手机号
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='手机号']"))
            )
            self.anti_detect.simulate_human_typing(phone_input, username)
            self.anti_detect.random_sleep(1, 2)

            # 勾选协议
            try:
                agreement = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if not agreement.is_selected():
                    agreement.click()
                    self.anti_detect.random_sleep(0.5, 1)
            except NoSuchElementException:
                logger.debug("未找到协议勾选框")

            # 发送验证码
            send_code_btn = self.driver.find_element(By.CSS_SELECTOR, "button[ka='login_sendsms_click']")
            send_code_btn.click()
            self.anti_detect.random_sleep(2, 3)

            logger.warning("请手动输入短信验证码完成登录...")
            input("按回车键确认已登录...")

            # 验证登录状态
            if "login" not in self.driver.current_url:
                logger.info("登录成功")
                return True
            else:
                raise LoginError("登录失败，仍在登录页面")

        except Exception as e:
            raise LoginError(f"登录过程出错: {e}")

    def search_jobs(self, keywords: List[str], cities: List[str]) -> List[JobInfo]:
        """搜索职位"""
        jobs = []
        for keyword in keywords:
            for city in cities:
                try:
                    page_jobs = self._search_single_page(keyword, city)
                    jobs.extend(page_jobs)
                    logger.info(f"[{keyword}@{city}] 找到 {len(page_jobs)} 个职位")
                    self.anti_detect.random_sleep()
                except Exception as e:
                    logger.error(f"搜索职位出错 [{keyword}@{city}]: {e}")
        return jobs

    @retry(max_attempts=2, delay=3.0, exceptions=(TimeoutException, WebDriverException))
    def _search_single_page(self, keyword: str, city: str) -> List[JobInfo]:
        """搜索单页职位"""
        search_url = f"{self.SEARCH_URL}?query={keyword}&city={city}"
        self.driver.get(search_url)
        self.anti_detect.random_sleep(3, 5)
        self.anti_detect.random_scroll(times=2)

        job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-wrapper")
        jobs = []
        for card in job_cards[:20]:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"解析职位卡片失败: {e}")

        return jobs

    def _parse_job_card(self, card) -> Optional[JobInfo]:
        """解析职位卡片"""
        try:
            def get_text(selector, default=""):
                try:
                    return card.find_element(By.CSS_SELECTOR, selector).text
                except NoSuchElementException:
                    return default

            return JobInfo(
                title=get_text(".job-name"),
                salary=get_text(".salary"),
                company=get_text(".company-name"),
                city=get_text(".job-area"),
                experience=get_text(".tag-list li:nth-child(1)"),
                degree=get_text(".tag-list li:nth-child(2)"),
                company_size=get_text(".company-tag-list li:nth-child(1)"),
                financing_stage=get_text(".company-tag-list li:nth-child(2)"),
                element=card,
            )
        except Exception:
            return None

    def send_resume(self, job: JobInfo) -> bool:
        """投递简历"""
        if self.daily_count >= self.strategy.max_applications_per_day:
            logger.warning("已达到今日投递上限")
            return False

        job_id = f"{job.company}_{job.title}"
        if self.recorder.is_applied(job_id):
            logger.info(f"已投递过该职位，跳过: {job.title} @ {job.company}")
            return False

        try:
            return self._do_send_resume(job, job_id)
        except Exception as e:
            logger.error(f"投递失败: {job.title} @ {job.company} - {e}")
            self.recorder.record(job_id, "failed", job.to_dict(), str(e))
            self.failed_count += 1
            return False

    def _do_send_resume(self, job: JobInfo, job_id: str) -> bool:
        """执行投递操作"""
        # 模拟随机行为
        self.anti_detect.random_click_on_page()
        self.anti_detect.random_mouse_movement()

        # 点击职位卡片
        if job.element:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                job.element,
            )
            self.anti_detect.random_sleep(1, 2)
            job.element.click()
            self.anti_detect.random_sleep(2, 4)

        # 点击沟通按钮
        chat_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-startchat"))
        )
        chat_btn.click()
        self.anti_detect.random_sleep(2, 3)

        # 发送打招呼消息
        if self.resume.greeting_template:
            self._send_greeting(job)

        # 记录成功
        self.daily_count += 1
        self.success_count += 1
        self.recorder.record(job_id, "success", job.to_dict())
        logger.info(
            f"投递成功 [{self.daily_count}/{self.strategy.max_applications_per_day}]: "
            f"{job.title} @ {job.company}"
        )
        return True

    def _send_greeting(self, job: JobInfo):
        """发送打招呼消息"""
        try:
            greeting = self._format_greeting(job)
            input_box = self.driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            self.anti_detect.simulate_human_typing(input_box, greeting)
            self.anti_detect.random_sleep(1, 2)

            send_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-send")
            send_btn.click()
            self.anti_detect.random_sleep(1, 2)
            logger.debug("打招呼消息已发送")
        except (NoSuchElementException, ElementNotInteractableException) as e:
            logger.warning(f"发送打招呼消息失败: {e}")

    def _format_greeting(self, job: JobInfo) -> str:
        """格式化打招呼消息"""
        template = (
            self.resume.greeting_template
            or "您好，我是{name}，对贵公司的{position}职位非常感兴趣，希望能有机会加入。"
        )
        return template.format(
            name=self.resume.name,
            company=job.company,
            position=job.title,
        )

    def get_stats(self) -> dict:
        """获取投递统计"""
        return {
            "daily_count": self.daily_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "max_per_day": self.strategy.max_applications_per_day,
        }
