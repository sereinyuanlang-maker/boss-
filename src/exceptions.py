"""自定义异常模块"""


class BossAutoApplyError(Exception):
    """基础异常类"""
    pass


class ConfigError(BossAutoApplyError):
    """配置错误"""
    pass


class LoginError(BossAutoApplyError):
    """登录失败"""
    pass


class BrowserError(BossAutoApplyError):
    """浏览器错误"""
    pass


class JobSearchError(BossAutoApplyError):
    """职位搜索错误"""
    pass


class SendResumeError(BossAutoApplyError):
    """投递简历错误"""
    pass


class AntiDetectError(BossAutoApplyError):
    """反检测错误"""
    pass


class ValidationError(BossAutoApplyError):
    """数据验证错误"""
    pass
