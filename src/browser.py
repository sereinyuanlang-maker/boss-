import os
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.anti_detect import AntiDetection
from src.config import StrategyConfig
from src.logger import logger


class BrowserManager:
    def __init__(self, strategy: StrategyConfig):
        self.strategy = strategy
        self.driver: uc.Chrome | None = None
        self.anti_detect: AntiDetection | None = None

    def start(self) -> uc.Chrome:
        logger.info("正在启动浏览器...")
        options = Options()

        if self.strategy.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        user_data_dir = Path(__file__).resolve().parent.parent / "browser_data"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = uc.Chrome(service=service, options=options)
        except Exception as e:
            logger.warning(f"使用webdriver-manager失败，尝试直接启动: {e}")
            self.driver = uc.Chrome(options=options)

        self.driver.implicitly_wait(self.strategy.implicit_wait)
        self.driver.set_page_load_timeout(self.strategy.page_load_timeout)

        self.anti_detect = AntiDetection(
            driver=self.driver,
            min_interval=self.strategy.min_interval_seconds,
            max_interval=self.strategy.max_interval_seconds,
            random_click=self.strategy.random_click,
            scroll_randomly=self.strategy.scroll_randomly,
        )
        self.anti_detect.apply_anti_detection_measures()

        logger.info("浏览器启动成功")
        return self.driver

    def get_anti_detect(self) -> AntiDetection:
        if self.anti_detect is None:
            raise RuntimeError("浏览器尚未启动")
        return self.anti_detect

    def quit(self):
        if self.driver:
            logger.info("正在关闭浏览器...")
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")
            finally:
                self.driver = None
                self.anti_detect = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
