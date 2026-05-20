import os
from pathlib import Path
from typing import List, Optional, Union

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator

from src.exceptions import ConfigError
from src.logger import logger

load_dotenv()


class SearchConfig(BaseModel):
    keywords: List[str] = Field(default_factory=list, description="职位关键词列表")
    cities: List[str] = Field(default_factory=list, description="目标城市列表")
    salary_range: Optional[str] = Field(None, description="薪资范围，如 '15k-30k'")
    experience: Optional[str] = Field(None, description="经验要求，如 '3-5年'")
    degree: Optional[str] = Field(None, description="学历要求，如 '本科'")
    company_size: Optional[str] = Field(None, description="公司规模，如 '100-499人'")
    financing_stage: Optional[str] = Field(None, description="融资阶段，如 'A轮'")
    job_type: Optional[str] = Field(None, description="工作类型，如 '全职'")
    publish_date: Optional[str] = Field(None, description="发布日期，如 '最近3天'")
    exclude_keywords: List[str] = Field(default_factory=list, description="排除关键词")

    @field_validator("keywords", "cities", "exclude_keywords", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    @model_validator(mode="after")
    def validate_search_config(self):
        if not self.keywords:
            logger.warning("未设置职位关键词，将搜索所有职位")
        if not self.cities:
            logger.warning("未设置目标城市，将搜索所有城市")
        return self


class ResumeConfig(BaseModel):
    name: str = Field(..., description="求职者姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="电子邮箱")
    self_introduction: Optional[str] = Field(None, description="自我介绍/求职意向")
    greeting_template: Optional[str] = Field(
        None,
        description="打招呼模板，支持占位符如 {name}, {company}, {position}",
    )
    resume_pdf_path: Optional[str] = Field(None, description="简历PDF文件路径")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()

    @field_validator("resume_pdf_path")
    @classmethod
    def validate_resume_path(cls, v):
        if v and not Path(v).exists():
            logger.warning(f"简历文件不存在: {v}")
        return v


class StrategyConfig(BaseModel):
    max_applications_per_day: int = Field(50, ge=1, le=200, description="每日最大投递数")
    min_interval_seconds: int = Field(5, ge=1, le=300, description="最小请求间隔(秒)")
    max_interval_seconds: int = Field(15, ge=1, le=600, description="最大请求间隔(秒)")
    random_click: bool = Field(True, description="是否模拟随机点击")
    scroll_randomly: bool = Field(True, description="是否随机滚动页面")
    headless: bool = Field(False, description="是否无头模式运行")
    implicit_wait: int = Field(10, ge=1, le=60, description="隐式等待时间(秒)")
    page_load_timeout: int = Field(30, ge=1, le=120, description="页面加载超时(秒)")
    retry_times: int = Field(3, ge=1, le=10, description="失败重试次数")
    business_hours_only: bool = Field(False, description="仅在业务时间投递")
    business_start_hour: int = Field(9, ge=0, le=23, description="业务开始时间")
    business_end_hour: int = Field(18, ge=0, le=23, description="业务结束时间")

    @model_validator(mode="after")
    def validate_intervals(self):
        if self.min_interval_seconds > self.max_interval_seconds:
            raise ValueError("最小间隔不能大于最大间隔")
        if self.business_start_hour >= self.business_end_hour:
            raise ValueError("业务开始时间必须小于结束时间")
        return self


class NotificationConfig(BaseModel):
    enable_email: bool = Field(False, description="是否启用邮件通知")
    smtp_server: Optional[str] = Field(None, description="SMTP服务器地址")
    smtp_port: int = Field(587, ge=1, le=65535, description="SMTP端口")
    sender_email: Optional[str] = Field(None, description="发件人邮箱")
    sender_password: Optional[str] = Field(None, description="发件人邮箱密码")
    receiver_email: Optional[str] = Field(None, description="收件人邮箱")
    notify_on_success: bool = Field(True, description="成功时通知")
    notify_on_failure: bool = Field(True, description="失败时通知")

    @model_validator(mode="after")
    def validate_email_config(self):
        if self.enable_email:
            required_fields = ["smtp_server", "sender_email", "sender_password", "receiver_email"]
            for field in required_fields:
                if not getattr(self, field):
                    raise ValueError(f"启用邮件通知时，{field} 不能为空")
        return self


class ProxyConfig(BaseModel):
    enabled: bool = Field(False, description="是否启用代理")
    http_proxy: Optional[str] = Field(None, description="HTTP代理地址")
    https_proxy: Optional[str] = Field(None, description="HTTPS代理地址")
    socks_proxy: Optional[str] = Field(None, description="SOCKS代理地址")


class AppConfig(BaseModel):
    search: SearchConfig = Field(default_factory=SearchConfig)
    resume: ResumeConfig = Field(default_factory=ResumeConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)


def load_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """加载配置文件

    Args:
        config_path: 配置文件路径，默认为环境变量 CONFIG_PATH 或 config.yaml

    Returns:
        AppConfig: 应用配置对象

    Raises:
        ConfigError: 配置文件不存在或格式错误
    """
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")

    config_file = Path(config_path)
    if not config_file.exists():
        raise ConfigError(f"配置文件不存在: {config_path}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML格式错误: {e}")
    except Exception as e:
        raise ConfigError(f"读取配置文件失败: {e}")

    try:
        return AppConfig(**data)
    except Exception as e:
        raise ConfigError(f"配置验证失败: {e}")


def get_account_credentials() -> dict:
    """获取账号凭证

    Returns:
        dict: 包含 username 和 password 的字典
    """
    return {
        "username": os.getenv("BOSS_USERNAME", ""),
        "password": os.getenv("BOSS_PASSWORD", ""),
    }


def save_example_config(output_path: str = "config.example.yaml") -> None:
    """生成配置文件示例"""
    example = AppConfig(
        search=SearchConfig(
            keywords=["Python开发", "后端工程师"],
            cities=["北京", "上海"],
            salary_range="15k-30k",
        ),
        resume=ResumeConfig(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
        ),
    )
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(example.model_dump(), f, allow_unicode=True, sort_keys=False)
    logger.info(f"配置文件示例已保存至: {output_path}")
