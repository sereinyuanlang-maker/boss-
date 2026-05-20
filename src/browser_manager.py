import random
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from src.config_manager import ConfigManager
from src.logger import setup_logger

logger = setup_logger(ConfigManager())


class BrowserManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.browser_config = config.config.browser
        self.driver: Optional[WebDriver] = None
        self.wait: Optional[WebDriverWait] = None

    def init_browser(self) -> WebDriver:
        browser_type = self.browser_config.type.lower()
        
        if browser_type == "chrome":
            self.driver = self._init_chrome()
        elif browser_type == "firefox":
            self.driver = self._init_firefox()
        else:
            raise ValueError(f"不支持的浏览器类型: {browser_type}")
        
        self.driver.set_window_size(self.browser_config.width, self.browser_config.height)
        self.wait = WebDriverWait(self.driver, 10)
        logger.info(f"浏览器初始化完成: {browser_type}")
        return self.driver

    def _init_chrome(self) -> WebDriver:
        options = ChromeOptions()
        
        if self.browser_config.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--lang=zh-CN")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.browser_config.user_data_dir:
            user_data_path = Path(self.browser_config.user_data_dir).absolute()
            user_data_path.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={user_data_path}")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        prefs = {
            "profile.default_content_setting_values.images": 2,
            "profile.managed_default_content_settings.images": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            if self.browser_config.use_undetected:
                import undetected_chromedriver as uc
                driver = uc.Chrome(options=options)
            else:
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.warning(f"使用undetected-chromedriver失败: {e}, 尝试普通模式")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = {
                    runtime: {}
                };
            """
        })
        
        return driver

    def _init_firefox(self) -> WebDriver:
        options = FirefoxOptions()
        
        if self.browser_config.headless:
            options.add_argument("--headless")
        
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        options.set_preference("general.useragent.override", 
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)

    def random_delay(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
        if min_seconds is None:
            min_seconds = self.config.config.delivery.random_delay_min
        if max_seconds is None:
            max_seconds = self.config.config.delivery.random_delay_max
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def human_like_typing(self, element: WebElement, text: str):
        for char in text:
            element.send_keys(char)
            self.random_delay(0.05, 0.2)

    def human_like_click(self, element: WebElement):
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.pause(random.uniform(0.1, 0.3))
        actions.click()
        actions.perform()

    def human_like_scroll(self, scroll_amount: Optional[int] = None):
        if scroll_amount is None:
            scroll_amount = random.randint(300, 800)
        
        current_position = self.driver.execute_script("return window.pageYOffset;")
        target_position = current_position + scroll_amount
        
        steps = random.randint(5, 15)
        step_size = (target_position - current_position) / steps
        
        for i in range(steps):
            self.driver.execute_script(f"window.scrollBy(0, {step_size});")
            self.random_delay(0.05, 0.15)

    def safe_click(self, locator, timeout: int = 10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            self.human_like_click(element)
            return True
        except Exception as e:
            logger.warning(f"点击元素失败 {locator}: {e}")
            return False

    def safe_input(self, locator, text: str, timeout: int = 10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            element.clear()
            self.human_like_typing(element, text)
            return True
        except Exception as e:
            logger.warning(f"输入文本失败 {locator}: {e}")
            return False

    def safe_find(self, locator, timeout: int = 10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except Exception as e:
            logger.warning(f"查找元素失败 {locator}: {e}")
            return None

    def safe_finds(self, locator, timeout: int = 10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(locator)
            )
        except Exception as e:
            logger.warning(f"查找多个元素失败 {locator}: {e}")
            return []

    def wait_for_page_load(self, timeout: int = 30):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")

    def __enter__(self):
        self.init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
