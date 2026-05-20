import random
import time
from typing import Optional

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.logger import logger
from src.utils import sleep_with_jitter


class AntiDetection:
    """反检测模块，模拟真实用户行为"""

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
        self._action_count = 0

    def random_sleep(self, min_sec: Optional[int] = None, max_sec: Optional[int] = None):
        """随机等待一段时间"""
        min_s = min_sec if min_sec is not None else self.min_interval
        max_s = max_sec if max_sec is not None else self.max_interval
        sleep_time = random.uniform(min_s, max_s)
        logger.debug(f"随机等待 {sleep_time:.2f} 秒")
        time.sleep(sleep_time)

    def simulate_human_typing(self, element: WebElement, text: str, error_rate: float = 0.02):
        """模拟人类打字，支持随机错误和修正"""
        typed = ""
        for char in text:
            if random.random() < error_rate and char.isalpha():
                wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                element.send_keys(wrong_char)
                sleep_with_jitter(0.1, 0.3)
                element.send_keys("\b")
                sleep_with_jitter(0.05, 0.2)

            element.send_keys(char)
            typed += char
            sleep_with_jitter(0.05, 0.5)

        self._action_count += 1
        logger.debug(f"模拟输入完成，共 {len(text)} 个字符")

    def random_scroll(self, times: int = 3, smooth: bool = True):
        """随机滚动页面"""
        if not self.scroll_randomly:
            return

        for _ in range(times):
            scroll_amount = random.randint(200, 800)
            direction = random.choice([1, -1])

            if smooth:
                steps = random.randint(3, 8)
                step_amount = scroll_amount // steps
                for _ in range(steps):
                    self.driver.execute_script(
                        f"window.scrollBy(0, {step_amount * direction});"
                    )
                    sleep_with_jitter(0.1, 0.3)
            else:
                self.driver.execute_script(
                    f"window.scrollBy(0, {scroll_amount * direction});"
                )

            self.random_sleep(1, 3)

        self._action_count += 1

    def random_mouse_movement(self, moves: int = 2):
        """模拟随机鼠标移动"""
        if not self.random_click:
            return

        try:
            action = ActionChains(self.driver)
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")

            for _ in range(moves):
                x = random.randint(100, max(200, viewport_width - 100))
                y = random.randint(100, max(200, viewport_height - 100))
                action.move_by_offset(x, y).perform()
                sleep_with_jitter(0.3, 0.8)

            self._action_count += 1
            logger.debug("鼠标移动模拟完成")
        except Exception as e:
            logger.warning(f"模拟鼠标移动失败: {e}")

    def simulate_reading(self, min_time: float = 3.0, max_time: float = 8.0):
        """模拟阅读停留"""
        read_time = random.uniform(min_time, max_time)
        logger.debug(f"模拟阅读，等待 {read_time:.2f} 秒")
        time.sleep(read_time)
        self._action_count += 1

    def random_click_on_page(self, max_elements: int = 10):
        """在页面上随机点击"""
        if not self.random_click:
            return

        try:
            selectors = [
                "a[href]",
                "button",
                "div[role='button']",
                "span[role='button']",
            ]
            all_elements = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                all_elements.extend(elements)

            if all_elements:
                element = random.choice(all_elements[:max_elements])
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                    element,
                )
                self.random_sleep(1, 2)
                ActionChains(self.driver).move_to_element(element).pause(
                    random.uniform(0.2, 0.5)
                ).click().perform()
                logger.debug("执行随机点击")
                self.random_sleep(2, 4)
                self._action_count += 1
        except Exception as e:
            logger.warning(f"随机点击失败: {e}")

    def bypass_slider_captcha(self) -> bool:
        """尝试通过滑块验证码"""
        try:
            slider = self.driver.find_element(By.CSS_SELECTOR, ".nc_iconfont.btn_slide")
            action = ActionChains(self.driver)
            action.click_and_hold(slider).perform()

            distance = 300
            steps = random.randint(15, 25)
            for i in range(steps):
                offset = distance // steps
                if i == steps - 1:
                    offset = distance - (distance // steps) * (steps - 1)
                action.move_by_offset(offset, random.randint(-2, 2)).perform()
                sleep_with_jitter(0.01, 0.05)

            action.release().perform()
            self.random_sleep(2, 4)
            logger.info("尝试通过滑块验证码")
            return True
        except Exception:
            logger.debug("未检测到滑块验证码")
            return False

    def apply_anti_detection_measures(self):
        """应用反检测措施，隐藏自动化特征"""
        scripts = [
            # 隐藏 webdriver 属性
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            # 模拟 Chrome 运行时
            """
            window.chrome = {
                runtime: {},
                app: {},
                csi: function() {},
                loadTimes: function() {}
            };
            """,
            # 模拟插件列表
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    {name: 'Native Client', filename: 'internal-nacl-plugin'}
                ]
            });
            """,
            # 模拟语言
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            """,
            # 隐藏 selenium 标志
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
            );
            """,
        ]

        for script in scripts:
            try:
                self.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {"source": script},
                )
            except Exception as e:
                logger.warning(f"应用反检测脚本失败: {e}")

        logger.info("已应用反检测措施")

    def get_action_count(self) -> int:
        """获取已执行的操作次数"""
        return self._action_count

    def reset_action_count(self):
        """重置操作计数"""
        self._action_count = 0
