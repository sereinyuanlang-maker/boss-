#!/usr/bin/env python3
"""
Boss直聘自动投简历工具主程序
"""

import sys
import time
from typing import Optional

from src.browser import BrowserManager
from src.config import AppConfig, get_account_credentials, load_config
from src.filter import JobFilter
from src.logger import logger
from src.recorder import StatusRecorder
from src.sender import ResumeSender


def run_application(config_path: Optional[str] = None):
    try:
        config: AppConfig = load_config(config_path)
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        logger.info("请复制 config.example.yaml 为 config.yaml 并填写您的配置")
        sys.exit(1)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        sys.exit(1)

    credentials = get_account_credentials()
    if not credentials["username"]:
        logger.error("未设置Boss直聘账号，请在 .env 文件中配置 BOSS_USERNAME")
        sys.exit(1)

    recorder = StatusRecorder()
    stats = recorder.get_daily_stats()
    if stats["success"] >= config.strategy.max_applications_per_day:
        logger.info(f"今日已投递 {stats['success']} 份简历，达到上限")
        return

    with BrowserManager(config.strategy) as browser:
        sender = ResumeSender(
            browser_manager=browser,
            resume_config=config.resume,
            strategy_config=config.strategy,
            recorder=recorder,
        )

        if not sender.login(credentials["username"], credentials["password"]):
            logger.error("登录失败，程序退出")
            sys.exit(1)

        logger.info("开始搜索职位...")
        all_jobs = sender.search_jobs(
            keywords=config.search.keywords,
            cities=config.search.cities,
        )
        logger.info(f"共找到 {len(all_jobs)} 个职位")

        if not all_jobs:
            logger.warning("未找到任何职位，请检查搜索条件")
            return

        job_filter = JobFilter(config.search)
        filtered_jobs = job_filter.filter_jobs(all_jobs)

        if not filtered_jobs:
            logger.warning("筛选后无符合条件的职位")
            return

        logger.info(f"开始投递简历，目标 {len(filtered_jobs)} 个职位")
        success_count = 0
        failed_count = 0

        for idx, job in enumerate(filtered_jobs, 1):
            logger.info(f"[{idx}/{len(filtered_jobs)}] 正在投递: {job['title']} @ {job['company']}")

            if sender.send_resume(job):
                success_count += 1
            else:
                failed_count += 1

            if sender.daily_count >= config.strategy.max_applications_per_day:
                logger.info("已达到今日投递上限")
                break

            if idx < len(filtered_jobs):
                sender.anti_detect.random_sleep()
                sender.anti_detect.random_scroll(times=1)

        final_stats = recorder.get_daily_stats()
        logger.info("=" * 50)
        logger.info("投递任务完成")
        logger.info(f"本次成功: {success_count}  失败: {failed_count}")
        logger.info(f"今日总计: {final_stats['total']}  成功: {final_stats['success']}  失败: {final_stats['failed']}")
        logger.info("=" * 50)

        recorder.export_to_excel()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Boss直聘自动投简历工具")
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
    args = parser.parse_args()

    logger.info("Boss直聘自动投简历工具启动")
    try:
        run_application(args.config)
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.exception(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
