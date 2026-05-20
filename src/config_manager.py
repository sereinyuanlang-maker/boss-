import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class AccountConfig(BaseModel):
    username: str = ""
    password: str = ""
    captcha_mode: str = "manual"


class BrowserConfig(BaseModel):
    type: str = "chrome"
    headless: bool = False
    width: int = 1920
    height: int = 1080
    user_data_dir: str = "./browser_data"
    use_undetected: bool = True


class DeliveryConfig(BaseModel):
    daily_limit: int = 50
    interval_min: int = 5
    interval_max: int = 15
    random_delay_min: int = 1
    random_delay_max: int = 3
    use_custom_greeting: bool = True
    custom_greeting: str = ""
    active_hours: Dict[str, str] = Field(default_factory=lambda: {"start": "09:00", "end": "18:00"})


class FilterConfig(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)
    salary_min: int = 15
    salary_max: int = 50
    experience_min: int = 1
    experience_max: int = 5
    education: str = "本科"
    company_size: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    finance_stage: List[str] = Field(default_factory=list)
    job_type: str = "全职"
    exclude_keywords: List[str] = Field(default_factory=list)


class ResumeConfig(BaseModel):
    file_path: str = "./resume.pdf"
    name: str = ""
    phone: str = ""
    email: str = ""
    expected_salary: str = ""
    expected_city: str = ""
    self_evaluation: str = ""


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "./logs/boss_automation.log"
    max_size: str = "10MB"
    backup_count: int = 5


class DataConfig(BaseModel):
    delivery_record: str = "./data/delivery_records.xlsx"
    job_cache: str = "./data/job_cache.json"
    delivered_ids: str = "./data/delivered_ids.txt"


class Config(BaseModel):
    account: AccountConfig = Field(default_factory=AccountConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    resume: ResumeConfig = Field(default_factory=ResumeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    data: DataConfig = Field(default_factory=DataConfig)


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._apply_env_overrides()
        self._ensure_directories()

    def _load_config(self) -> Config:
        if not self.config_path.exists():
            return Config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        return Config(**data)

    def _apply_env_overrides(self):
        if os.getenv("BOSS_USERNAME"):
            self.config.account.username = os.getenv("BOSS_USERNAME")
        if os.getenv("BOSS_PASSWORD"):
            self.config.account.password = os.getenv("BOSS_PASSWORD")

    def _ensure_directories(self):
        dirs_to_create = [
            Path(self.config.browser.user_data_dir),
            Path(self.config.logging.file).parent,
            Path(self.config.data.delivery_record).parent,
            Path(self.config.data.job_cache).parent,
        ]
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            target = getattr(target, k)
        setattr(target, keys[-1], value)

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config.model_dump(), f, allow_unicode=True, sort_keys=False)

    def validate(self) -> List[str]:
        errors = []
        if not self.config.account.username:
            errors.append("账号用户名不能为空")
        if not self.config.account.password:
            errors.append("账号密码不能为空")
        if not self.config.filters.keywords:
            errors.append("职位搜索关键词不能为空")
        if not self.config.filters.cities:
            errors.append("目标城市不能为空")
        return errors
