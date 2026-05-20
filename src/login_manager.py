import time
from pathlib import Path
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.browser_manager import BrowserManager
from src.config_manager import ConfigManager
from src.logger import setup_logger

logger = setup_logger(ConfigManager())


class LoginManager:
    LOGIN_URL = "https://www.zhipin.com/web/user/?ka=header-login"
    HOME_URL = "https://www.zhipin.com"
    
    def __init__(self, browser_manager: BrowserManager, config: ConfigManager):
        self.browser = browser_manager
        self.config = config
        self.account = config.config.account

    def check_login_status(self) -> bool:
        try:
            self.browser.driver.get(self.HOME_URL)
            self.browser.random_delay(2, 4)
            
            user_elements = self.browser.driver.find_elements(By.CSS_SELECTOR, ".user-info")
            if user_elements:
                logger.info("用户已登录")
                return True
            
            login_btn = self.browser.driver.find_elements(By.CSS_SELECTOR, ".btn-login")
            if not login_btn:
                avatar = self.browser.driver.find_elements(By.CSS_SELECTOR, ".avatar")
                if avatar:
                    logger.info("用户已登录(通过头像检测)")
                    return True
            
            logger.info("用户未登录")
            return False
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    def login(self) -> bool:
        if self.check_login_status():
            return True
        
        try:
            logger.info("开始登录流程")
            self.browser.driver.get(self.LOGIN_URL)
            self.browser.random_delay(3, 5)
            
            self._switch_to_password_login()
            self._input_credentials()
            
            if self._handle_captcha():
                return self._verify_login_success()
            
            return False
        except Exception as e:
            logger.error(f"登录过程发生错误: {e}")
            return False

    def _switch_to_password_login(self):
        try:
            password_tab = self.browser.safe_find(
                (By.CSS_SELECTOR, ".sign-tab .password-login"), timeout=5
            )
            if password_tab:
                self.browser.human_like_click(password_tab)
                logger.info("切换到密码登录")
                self.browser.random_delay(1, 2)
        except Exception as e:
            logger.warning(f"切换密码登录失败: {e}")

    def _input_credentials(self):
        try:
            phone_input = self.browser.safe_find(
                (By.CSS_SELECTOR, "input[placeholder*='手机号' i], input[name='phone']"), timeout=10
            )
            if phone_input:
                self.browser.human_like_typing(phone_input, self.account.username)
                logger.info("输入手机号")
            
            self.browser.random_delay(1, 2)
            
            password_input = self.browser.safe_find(
                (By.CSS_SELECTOR, "input[type='password'], input[placeholder*='密码' i]"), timeout=10
            )
            if password_input:
                self.browser.human_like_typing(password_input, self.account.password)
                logger.info("输入密码")
            
            self.browser.random_delay(1, 2)
            
            login_btn = self.browser.safe_find(
                (By.CSS_SELECTOR, ".btn-login, button[type='submit'], .sign-btn"), timeout=10
            )
            if login_btn:
                self.browser.human_like_click(login_btn)
                logger.info("点击登录按钮")
            
            self.browser.random_delay(3, 5)
        except Exception as e:
            logger.error(f"输入账号密码失败: {e}")
            raise

    def _handle_captcha(self) -> bool:
        try:
            captcha_elements = self.browser.driver.find_elements(
                By.CSS_SELECTOR, ".captcha, .verify-code, .slide-verify, .geetest"
            )
            
            if not captcha_elements:
                return True
            
            logger.warning("检测到验证码")
            
            if self.account.captcha_mode == "manual":
                logger.info("请手动完成验证码验证...")
                input("按回车键继续(完成验证码后)...")
                return True
            elif self.account.captcha_mode == "skip":
                logger.warning("跳过验证码")
                return False
            else:
                logger.warning("自动验证码识别暂未实现")
                return False
        except Exception as e:
            logger.error(f"处理验证码失败: {e}")
            return False

    def _verify_login_success(self) -> bool:
        try:
            self.browser.random_delay(3, 5)
            
            user_elements = self.browser.driver.find_elements(By.CSS_SELECTOR, ".user-info, .avatar")
            if user_elements:
                logger.info("登录成功")
                return True
            
            error_elements = self.browser.driver.find_elements(
                By.CSS_SELECTOR, ".error-msg, .toast-error"
            )
            if error_elements:
                error_msg = error_elements[0].text
                logger.error(f"登录失败: {error_msg}")
                return False
            
            current_url = self.browser.driver.current_url
            if "login" not in current_url and "user" not in current_url:
                logger.info("登录成功(通过URL检测)")
                return True
            
            logger.warning("登录状态未知")
            return False
        except Exception as e:
            logger.error(f"验证登录状态失败: {e}")
            return False

    def logout(self):
        try:
            self.browser.driver.get(self.HOME_URL)
            self.browser.random_delay(2, 3)
            
            user_menu = self.browser.safe_find((By.CSS_SELECTOR, ".user-info, .avatar"))
            if user_menu:
                self.browser.human_like_click(user_menu)
                self.browser.random_delay(1, 2)
                
                logout_btn = self.browser.safe_find(
                    (By.CSS_SELECTOR, ".logout, .exit, a[href*='logout']")
                )
                if logout_btn:
                    self.browser.human_like_click(logout_btn)
                    logger.info("已退出登录")
        except Exception as e:
            logger.error(f"退出登录失败: {e}")

    def save_login_state(self):
        try:
            cookies = self.browser.driver.get_cookies()
            cookie_path = Path("./data/cookies.json")
            cookie_path.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            logger.info("登录状态已保存")
        except Exception as e:
            logger.error(f"保存登录状态失败: {e}")

    def load_login_state(self) -> bool:
        try:
            cookie_path = Path("./data/cookies.json")
            if not cookie_path.exists():
                return False
            
            import json
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            self.browser.driver.get(self.HOME_URL)
            for cookie in cookies:
                try:
                    self.browser.driver.add_cookie(cookie)
                except Exception:
                    pass
            
            self.browser.driver.get(self.HOME_URL)
            self.browser.random_delay(2, 3)
            
            if self.check_login_status():
                logger.info("使用保存的登录状态成功")
                return True
            return False
        except Exception as e:
            logger.error(f"加载登录状态失败: {e}")
            return False
