import random
import time
from typing import Optional

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.logger import logger


class AntiDetection:
    def __init__(
        self,
        driver: WebDriver,
        min_interval: int = 5,
        max_interval: int = 15,
        random_click: bool = True,
        scroll_randomly: bool = True,
    ):
        self.driver = driver
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.random_click = random_click
        self.scroll_randomly = scroll_randomly

    def random_sleep(self, min_sec: Optional[int] = None, max_sec: Optional[int] = None):
        min_s = min_sec if min_sec is not None else self.min_interval
        max_s = max_sec if max_sec is not None else self.max_interval
        sleep_time = random.uniform(min_s, max_s)
        logger.debug(f"随机等待 {sleep_time:.2f} 秒")
        time.sleep(sleep_time)

    def simulate_human_typing(self, element: WebElement, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

    def random_scroll(self, times: int = 3):
        if not self.scroll_randomly:
            return
        for _ in range(times):
            scroll_amount = random.randint(200, 800)
            direction = random.choice([1, -1])
            self.driver.execute_script(
                f"window.scrollBy(0, {scroll_amount * direction});"
            )
            self.random_sleep(1, 3)

    def random_mouse_movement(self):
        if not self.random_click:
            return
        try:
            action = ActionChains(self.driver)
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")
            x = random.randint(100, viewport_width - 100)
            y = random.randint(100, viewport_height - 100)
            action.move_by_offset(x, y).perform()
            self.random_sleep(0.5, 1.5)
        except Exception as e:
            logger.warning(f"模拟鼠标移动失败: {e}")

    def simulate_reading(self):
        read_time = random.uniform(3, 8)
        logger.debug(f"模拟阅读，等待 {read_time:.2f} 秒")
        time.sleep(read_time)

    def random_click_on_page(self):
        if not self.random_click:
            return
        try:
            clickable_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a, button, div[role='button']",
            )
            if clickable_elements:
                element = random.choice(clickable_elements[:10])
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                self.random_sleep(1, 2)
                ActionChains(self.driver).move_to_element(element).pause(random.uniform(0.2, 0.5)).click().perform()
                logger.debug("执行随机点击")
                self.random_sleep(2, 4)
        except Exception as e:
            logger.warning(f"随机点击失败: {e}")

    def bypass_slider_captcha(self) -> bool:
        try:
            slider = self.driver.find_element(By.CSS_SELECTOR, ".nc_iconfont.btn_slide")
            action = ActionChains(self.driver)
            action.click_and_hold(slider).perform()
            action.move_by_offset(300, 0).perform()
            action.release().perform()
            self.random_sleep(2, 4)
            logger.info("尝试通过滑块验证码")
            return True
        except Exception:
            logger.debug("未检测到滑块验证码")
            return False

    def apply_anti_detection_measures(self):
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                """
            },
        )
        logger.info("已应用反检测措施")
