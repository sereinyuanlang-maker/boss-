import os
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

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

    @validator("keywords", "cities", pre=True)
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


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


class StrategyConfig(BaseModel):
    max_applications_per_day: int = Field(50, ge=1, le=200, description="每日最大投递数")
    min_interval_seconds: int = Field(5, ge=1, description="最小请求间隔(秒)")
    max_interval_seconds: int = Field(15, ge=1, description="最大请求间隔(秒)")
    random_click: bool = Field(True, description="是否模拟随机点击")
    scroll_randomly: bool = Field(True, description="是否随机滚动页面")
    headless: bool = Field(False, description="是否无头模式运行")
    implicit_wait: int = Field(10, ge=1, description="隐式等待时间(秒)")
    page_load_timeout: int = Field(30, ge=1, description="页面加载超时(秒)")
    retry_times: int = Field(3, ge=1, description="失败重试次数")


class NotificationConfig(BaseModel):
    enable_email: bool = Field(False, description="是否启用邮件通知")
    smtp_server: Optional[str] = Field(None, description="SMTP服务器地址")
    smtp_port: int = Field(587, description="SMTP端口")
    sender_email: Optional[str] = Field(None, description="发件人邮箱")
    sender_password: Optional[str] = Field(None, description="发件人邮箱密码")
    receiver_email: Optional[str] = Field(None, description="收件人邮箱")


class AppConfig(BaseModel):
    search: SearchConfig = Field(default_factory=SearchConfig)
    resume: ResumeConfig = Field(default_factory=ResumeConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return AppConfig(**data)


def get_account_credentials() -> dict:
    return {
        "username": os.getenv("BOSS_USERNAME", ""),
        "password": os.getenv("BOSS_PASSWORD", ""),
    }
