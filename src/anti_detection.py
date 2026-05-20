import random
import time
from typing import Optional

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from src.browser_manager import BrowserManager
from src.config_manager import ConfigManager
from src.logger import setup_logger

logger = setup_logger(ConfigManager())


class AntiDetection:
    def __init__(self, browser_manager: BrowserManager, config: ConfigManager):
        self.browser = browser_manager
        self.config = config

    def simulate_human_behavior(self, duration: Optional[float] = None):
        if duration is None:
            duration = random.uniform(5, 15)
        
        start_time = time.time()
        actions_count = 0
        
        while time.time() - start_time < duration:
            action_type = random.choice([
                "scroll",
                "mouse_move",
                "pause",
                "small_scroll",
            ])
            
            try:
                if action_type == "scroll":
                    self._random_scroll()
                elif action_type == "mouse_move":
                    self._random_mouse_move()
                elif action_type == "small_scroll":
                    self._small_random_scroll()
                elif action_type == "pause":
                    time.sleep(random.uniform(0.5, 2))
                
                actions_count += 1
            except Exception as e:
                logger.debug(f"模拟人类行为失败: {e}")
            
            time.sleep(random.uniform(0.5, 2))
        
        logger.debug(f"模拟人类行为完成: {actions_count} 个动作")

    def _random_scroll(self):
        scroll_amount = random.randint(-500, 500)
        self.browser.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

    def _small_random_scroll(self):
        scroll_amount = random.randint(-100, 100)
        self.browser.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

    def _random_mouse_move(self):
        try:
            elements = self.browser.driver.find_elements(By.CSS_SELECTOR, "a, button, div, span")
            if elements:
                target = random.choice(elements)
                actions = ActionChains(self.browser.driver)
                actions.move_to_element(target)
                actions.pause(random.uniform(0.1, 0.5))
                actions.perform()
        except Exception:
            pass

    def random_page_interaction(self):
        try:
            interactions = [
                self._click_random_link,
                self._hover_random_element,
                self._random_page_scroll,
            ]
            
            interaction = random.choice(interactions)
            interaction()
        except Exception as e:
            logger.debug(f"随机页面交互失败: {e}")

    def _click_random_link(self):
        try:
            links = self.browser.driver.find_elements(By.TAG_NAME, "a")
            if links:
                link = random.choice(links[:10])
                if link.is_displayed():
                    self.browser.human_like_click(link)
                    time.sleep(random.uniform(2, 4))
                    self.browser.driver.back()
                    time.sleep(random.uniform(1, 2))
        except Exception:
            pass

    def _hover_random_element(self):
        try:
            elements = self.browser.driver.find_elements(By.CSS_SELECTOR, "div, span, a")
            if elements:
                element = random.choice(elements[:20])
                actions = ActionChains(self.browser.driver)
                actions.move_to_element(element)
                actions.pause(random.uniform(0.5, 1.5))
                actions.perform()
        except Exception:
            pass

    def _random_page_scroll(self):
        scroll_type = random.choice(["top", "bottom", "random"])
        
        if scroll_type == "top":
            self.browser.driver.execute_script("window.scrollTo(0, 0);")
        elif scroll_type == "bottom":
            self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            scroll_y = random.randint(0, self.browser.driver.execute_script("return document.body.scrollHeight;"))
            self.browser.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
        
        time.sleep(random.uniform(0.5, 1.5))

    def add_random_delays(self, base_delay: float = 1.0) -> float:
        jitter = random.uniform(-0.3, 0.5)
        delay = max(0.1, base_delay + jitter)
        time.sleep(delay)
        return delay

    def simulate_reading_time(self, text_length: int = 0):
        if text_length == 0:
            reading_time = random.uniform(3, 8)
        else:
            reading_time = max(2, text_length / 200 * random.uniform(0.8, 1.5))
        
        logger.debug(f"模拟阅读时间: {reading_time:.1f} 秒")
        time.sleep(reading_time)

    def random_viewport_change(self):
        try:
            width = self.config.config.browser.width + random.randint(-100, 100)
            height = self.config.config.browser.height + random.randint(-50, 50)
            self.browser.driver.set_window_size(width, height)
            time.sleep(random.uniform(0.5, 1))
        except Exception:
            pass

    def bypass_detection_scripts(self):
        try:
            scripts = [
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """,
                """
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                """,
                """
                window.chrome = {
                    runtime: {}
                };
                """,
                """
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                """,
            ]
            
            for script in scripts:
                self.browser.driver.execute_script(script)
        except Exception as e:
            logger.debug(f"绕过检测脚本失败: {e}")

    def random_user_agent_rotation(self):
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        
        return random.choice(user_agents)
