import time
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.anti_detect import AntiDetection
from src.browser import BrowserManager
from src.config import ResumeConfig, StrategyConfig
from src.logger import logger
from src.recorder import StatusRecorder


class ResumeSender:
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
        self.driver = browser_manager.driver
        self.anti_detect = browser_manager.get_anti_detect()
        self.daily_count = 0

    def login(self, username: str, password: str) -> bool:
        logger.info("开始登录Boss直聘...")
        self.driver.get(self.LOGIN_URL)
        self.anti_detect.random_sleep(3, 5)

        try:
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='手机号']"))
            )
            self.anti_detect.simulate_human_typing(phone_input, username)
            self.anti_detect.random_sleep(1, 2)

            agreement = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            if not agreement.is_selected():
                agreement.click()
                self.anti_detect.random_sleep(0.5, 1)

            send_code_btn = self.driver.find_element(By.CSS_SELECTOR, "button[ka='login_sendsms_click']")
            send_code_btn.click()
            self.anti_detect.random_sleep(2, 3)

            logger.warning("请手动输入短信验证码完成登录...")
            input("按回车键确认已登录...")

            if "login" not in self.driver.current_url:
                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                return False

        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False

    def search_jobs(self, keywords: List[str], cities: List[str]) -> List[dict]:
        jobs = []
        for keyword in keywords:
            for city in cities:
                try:
                    page_jobs = self._search_single_page(keyword, city)
                    jobs.extend(page_jobs)
                    self.anti_detect.random_sleep()
                except Exception as e:
                    logger.error(f"搜索职位出错 [{keyword}@{city}]: {e}")
        return jobs

    def _search_single_page(self, keyword: str, city: str) -> List[dict]:
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

    def _parse_job_card(self, card) -> Optional[dict]:
        try:
            title = card.find_element(By.CSS_SELECTOR, ".job-name").text
            salary = card.find_element(By.CSS_SELECTOR, ".salary").text
            company = card.find_element(By.CSS_SELECTOR, ".company-name").text
            city = card.find_element(By.CSS_SELECTOR, ".job-area").text
            experience = card.find_element(By.CSS_SELECTOR, ".tag-list li:nth-child(1)").text
            degree = card.find_element(By.CSS_SELECTOR, ".tag-list li:nth-child(2)").text
            company_size = card.find_element(By.CSS_SELECTOR, ".company-tag-list li:nth-child(1)").text

            return {
                "title": title,
                "salary": salary,
                "company": company,
                "city": city,
                "experience": experience,
                "degree": degree,
                "company_size": company_size,
                "element": card,
            }
        except Exception:
            return None

    def send_resume(self, job: dict) -> bool:
        if self.daily_count >= self.strategy.max_applications_per_day:
            logger.warning("已达到今日投递上限")
            return False

        job_id = f"{job['company']}_{job['title']}"
        if self.recorder.is_applied(job_id):
            logger.info(f"已投递过该职位，跳过: {job['title']} @ {job['company']}")
            return False

        try:
            self.anti_detect.random_click_on_page()
            self.anti_detect.random_mouse_movement()

            card = job.get("element")
            if card:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                self.anti_detect.random_sleep(1, 2)
                card.click()
                self.anti_detect.random_sleep(2, 4)

            chat_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-startchat"))
            )
            chat_btn.click()
            self.anti_detect.random_sleep(2, 3)

            if self.resume.greeting_template:
                greeting = self._format_greeting(job)
                try:
                    input_box = self.driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
                    self.anti_detect.simulate_human_typing(input_box, greeting)
                    self.anti_detect.random_sleep(1, 2)

                    send_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-send")
                    send_btn.click()
                    self.anti_detect.random_sleep(1, 2)
                except Exception as e:
                    logger.warning(f"发送打招呼消息失败: {e}")

            self.daily_count += 1
            self.recorder.record(job_id, "success", job)
            logger.info(f"投递成功 [{self.daily_count}/{self.strategy.max_applications_per_day}]: {job['title']} @ {job['company']}")
            return True

        except Exception as e:
            logger.error(f"投递失败: {job['title']} @ {job['company']} - {e}")
            self.recorder.record(job_id, "failed", job, str(e))
            return False

    def _format_greeting(self, job: dict) -> str:
        template = self.resume.greeting_template or "您好，我对贵公司的{position}职位很感兴趣，希望能有机会加入。"
        return template.format(
            name=self.resume.name,
            company=job.get("company", ""),
            position=job.get("title", ""),
        )
