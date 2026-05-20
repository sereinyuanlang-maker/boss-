import atexit
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.anti_detect import AntiDetection
from src.config import ProxyConfig, StrategyConfig
from src.exceptions import BrowserError
from src.logger import logger


class BrowserManager:
    """浏览器管理器，负责Chrome浏览器的生命周期管理"""

    _instance: Optional["BrowserManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, strategy: StrategyConfig, proxy: Optional[ProxyConfig] = None):
        if self._initialized:
            return

        self.strategy = strategy
        self.proxy = proxy or ProxyConfig()
        self.driver: Optional[uc.Chrome] = None
        self.anti_detect: Optional[AntiDetection] = None
        self._cleanup_registered = False
        self._initialized = True

    def start(self) -> uc.Chrome:
        """启动浏览器"""
        if self.driver is not None:
            logger.warning("浏览器已启动，返回现有实例")
            return self.driver

        logger.info("正在启动浏览器...")
        options = Options()

        if self.strategy.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")

        # 基础配置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # 禁用扩展和插件
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")

        # 设置User-Agent
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument(f"--user-agent={user_agent}")

        # 代理配置
        if self.proxy.enabled and self.proxy.http_proxy:
            options.add_argument(f"--proxy-server={self.proxy.http_proxy}")
            logger.info(f"使用代理: {self.proxy.http_proxy}")

        # 用户数据目录
        user_data_dir = Path(__file__).resolve().parent.parent / "browser_data"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # 禁用自动化提示
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = uc.Chrome(service=service, options=options)
        except Exception as e:
            logger.warning(f"使用webdriver-manager失败，尝试直接启动: {e}")
            try:
                self.driver = uc.Chrome(options=options)
            except Exception as e2:
                raise BrowserError(f"浏览器启动失败: {e2}")

        # 设置超时
        self.driver.implicitly_wait(self.strategy.implicit_wait)
        self.driver.set_page_load_timeout(self.strategy.page_load_timeout)
        self.driver.set_script_timeout(self.strategy.page_load_timeout)

        # 初始化反检测
        self.anti_detect = AntiDetection(
            driver=self.driver,
            min_interval=self.strategy.min_interval_seconds,
            max_interval=self.strategy.max_interval_seconds,
            random_click=self.strategy.random_click,
            scroll_randomly=self.strategy.scroll_randomly,
        )
        self.anti_detect.apply_anti_detection_measures()

        # 注册清理
        if not self._cleanup_registered:
            atexit.register(self.quit)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            self._cleanup_registered = True

        logger.info("浏览器启动成功")
        return self.driver

    def get_anti_detect(self) -> AntiDetection:
        """获取反检测实例"""
        if self.anti_detect is None:
            raise BrowserError("浏览器尚未启动")
        return self.anti_detect

    def get_driver(self) -> uc.Chrome:
        """获取浏览器驱动"""
        if self.driver is None:
            raise BrowserError("浏览器尚未启动")
        return self.driver

    def quit(self):
        """关闭浏览器"""
        if self.driver:
            logger.info("正在关闭浏览器...")
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")
            finally:
                self.driver = None
                self.anti_detect = None

    def _signal_handler(self, signum: int, frame: Optional[FrameType]):
        """信号处理"""
        logger.info(f"接收到信号 {signum}，正在清理...")
        self.quit()
        sys.exit(0)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def __del__(self):
        """析构时确保浏览器关闭"""
        if self.driver:
            self.quit()
