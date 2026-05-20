#!/usr/bin/env python3
"""
Boss直聘自动投简历工具主程序
"""

import argparse
import sys
from typing import Optional

from src.browser import BrowserManager
from src.config import AppConfig, get_account_credentials, load_config
from src.exceptions import BossAutoApplyError
from src.filter import JobFilter, JobInfo
from src.logger import logger
from src.recorder import StatusRecorder
from src.sender import ResumeSender
from src.utils import is_within_business_hours


def check_business_hours(config: AppConfig) -> bool:
    """检查是否在业务时间内"""
    if not config.strategy.business_hours_only:
        return True

    if not is_within_business_hours(
        config.strategy.business_start_hour,
        config.strategy.business_end_hour,
    ):
        logger.warning(
            f"当前不在业务时间内 ({config.strategy.business_start_hour}:00-"
            f"{config.strategy.business_end_hour}:00)，跳过投递"
        )
        return False
    return True


def run_application(config_path: Optional[str] = None):
    """运行应用程序"""
    try:
        config: AppConfig = load_config(config_path)
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        logger.info("请复制 config.example.yaml 为 config.yaml 并填写您的配置")
        sys.exit(1)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        sys.exit(1)

    # 检查账号
    credentials = get_account_credentials()
    if not credentials["username"]:
        logger.error("未设置Boss直聘账号，请在 .env 文件中配置 BOSS_USERNAME")
        sys.exit(1)

    # 检查业务时间
    if not check_business_hours(config):
        return

    # 检查今日投递上限
    recorder = StatusRecorder()
    stats = recorder.get_daily_stats()
    if stats["success"] >= config.strategy.max_applications_per_day:
        logger.info(f"今日已投递 {stats['success']} 份简历，达到上限")
        return

    # 启动浏览器并执行投递
    with BrowserManager(config.strategy, config.proxy) as browser:
        sender = ResumeSender(
            browser_manager=browser,
            resume_config=config.resume,
            strategy_config=config.strategy,
            recorder=recorder,
        )

        # 登录
        if not sender.login(credentials["username"], credentials["password"]):
            logger.error("登录失败，程序退出")
            sys.exit(1)

        # 搜索职位
        logger.info("开始搜索职位...")
        all_jobs = sender.search_jobs(
            keywords=config.search.keywords,
            cities=config.search.cities,
        )
        logger.info(f"共找到 {len(all_jobs)} 个职位")

        if not all_jobs:
            logger.warning("未找到任何职位，请检查搜索条件")
            return

        # 筛选职位
        job_filter = JobFilter(config.search)
        filtered_jobs = job_filter.filter_jobs(all_jobs)

        if not filtered_jobs:
            logger.warning("筛选后无符合条件的职位")
            return

        # 投递简历
        logger.info(f"开始投递简历，目标 {len(filtered_jobs)} 个职位")

        for idx, job in enumerate(filtered_jobs, 1):
            logger.info(
                f"[{idx}/{len(filtered_jobs)}] 正在投递: {job.title} @ {job.company}"
            )

            sender.send_resume(job)

            if sender.daily_count >= config.strategy.max_applications_per_day:
                logger.info("已达到今日投递上限")
                break

            if idx < len(filtered_jobs):
                sender.anti_detect.random_sleep()
                sender.anti_detect.random_scroll(times=1)

        # 输出统计
        final_stats = recorder.get_daily_stats()
        sender_stats = sender.get_stats()

        logger.info("=" * 60)
        logger.info("投递任务完成")
        logger.info(f"本次成功: {sender_stats['success_count']}  失败: {sender_stats['failed_count']}")
        logger.info(
            f"今日总计: {final_stats['total']}  "
            f"成功: {final_stats['success']}  "
            f"失败: {final_stats['failed']}  "
            f"成功率: {final_stats['success_rate']}%"
        )
        logger.info("=" * 60)

        # 导出记录
        recorder.export_to_excel()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Boss直聘自动投简历工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 使用默认配置运行
  python main.py -c config.yaml     # 指定配置文件
  python main.py -v                 # 查看版本
        """,
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="配置文件路径 (默认: config.yaml)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 1.0.0",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出",
    )
    args = parser.parse_args()

    if args.verbose:
        from src.logger import setup_logger
        setup_logger(level="DEBUG", console_level="DEBUG")

    logger.info("Boss直聘自动投简历工具启动 v1.0.0")

    try:
        run_application(args.config)
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except BossAutoApplyError as e:
        logger.error(f"应用错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
