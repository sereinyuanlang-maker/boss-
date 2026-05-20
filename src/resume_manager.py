import os
from pathlib import Path
from typing import Dict, Optional

from selenium.webdriver.common.by import By

from src.browser_manager import BrowserManager
from src.config_manager import ConfigManager
from src.logger import setup_logger

logger = setup_logger(ConfigManager())


class ResumeManager:
    def __init__(self, browser_manager: BrowserManager, config: ConfigManager):
        self.browser = browser_manager
        self.config = config
        self.resume_config = config.config.resume

    def upload_resume(self) -> bool:
        try:
            resume_path = Path(self.resume_config.file_path)
            if not resume_path.exists():
                logger.warning(f"简历文件不存在: {resume_path}")
                return False
            
            logger.info("开始上传简历")
            
            upload_input = self.browser.safe_find(
                (By.CSS_SELECTOR, "input[type='file'], .upload-resume input"), timeout=10
            )
            if upload_input:
                upload_input.send_keys(str(resume_path.absolute()))
                self.browser.random_delay(3, 5)
                logger.info("简历上传成功")
                return True
            else:
                logger.warning("未找到简历上传输入框")
                return False
        except Exception as e:
            logger.error(f"上传简历失败: {e}")
            return False

    def fill_personal_info(self) -> bool:
        try:
            logger.info("开始填写个人信息")
            
            if self.resume_config.name:
                self._fill_field("input[placeholder*='姓名' i], input[name='name']", self.resume_config.name)
            
            if self.resume_config.phone:
                self._fill_field("input[placeholder*='手机' i], input[name='phone']", self.resume_config.phone)
            
            if self.resume_config.email:
                self._fill_field("input[placeholder*='邮箱' i], input[name='email']", self.resume_config.email)
            
            if self.resume_config.expected_salary:
                self._fill_field("input[placeholder*='期望薪资' i]", self.resume_config.expected_salary)
            
            if self.resume_config.expected_city:
                self._fill_field("input[placeholder*='期望城市' i]", self.resume_config.expected_city)
            
            if self.resume_config.self_evaluation:
                self._fill_textarea("textarea[placeholder*='自我评价' i], textarea[name='evaluation']", 
                                   self.resume_config.self_evaluation)
            
            logger.info("个人信息填写完成")
            return True
        except Exception as e:
            logger.error(f"填写个人信息失败: {e}")
            return False

    def _fill_field(self, selector: str, value: str):
        try:
            element = self.browser.safe_find((By.CSS_SELECTOR, selector), timeout=3)
            if element:
                element.clear()
                self.browser.human_like_typing(element, value)
                self.browser.random_delay(0.5, 1)
        except Exception as e:
            logger.debug(f"填写字段失败 {selector}: {e}")

    def _fill_textarea(self, selector: str, value: str):
        try:
            element = self.browser.safe_find((By.CSS_SELECTOR, selector), timeout=3)
            if element:
                element.clear()
                self.browser.human_like_typing(element, value)
                self.browser.random_delay(0.5, 1)
        except Exception as e:
            logger.debug(f"填写文本域失败 {selector}: {e}")

    def get_resume_status(self) -> Dict:
        status = {
            "resume_file_exists": False,
            "resume_file_path": "",
            "file_size": 0,
            "personal_info_complete": False,
        }
        
        try:
            resume_path = Path(self.resume_config.file_path)
            if resume_path.exists():
                status["resume_file_exists"] = True
                status["resume_file_path"] = str(resume_path)
                status["file_size"] = resume_path.stat().st_size
            
            info_fields = [
                self.resume_config.name,
                self.resume_config.phone,
                self.resume_config.email,
            ]
            status["personal_info_complete"] = all(info_fields)
            
        except Exception as e:
            logger.error(f"获取简历状态失败: {e}")
        
        return status

    def update_resume_online(self) -> bool:
        try:
            logger.info("尝试更新在线简历")
            self.browser.driver.get("https://www.zhipin.com/web/geek/resume")
            self.browser.random_delay(3, 5)
            
            edit_btn = self.browser.safe_find(
                (By.CSS_SELECTOR, ".edit-resume, .btn-edit, a[href*='resume/edit']"), timeout=10
            )
            if edit_btn:
                self.browser.human_like_click(edit_btn)
                self.browser.random_delay(2, 3)
                
                self.fill_personal_info()
                
                save_btn = self.browser.safe_find(
                    (By.CSS_SELECTOR, ".btn-save, button[type='submit']"), timeout=5
                )
                if save_btn:
                    self.browser.human_like_click(save_btn)
                    self.browser.random_delay(2, 3)
                    logger.info("在线简历更新成功")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"更新在线简历失败: {e}")
            return False
