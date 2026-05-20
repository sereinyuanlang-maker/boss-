import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from src.anti_detection import AntiDetection
from src.browser_manager import BrowserManager
from src.config_manager import ConfigManager
from src.delivery_engine import DeliveryEngine
from src.job_filter import JobFilter
from src.login_manager import LoginManager
from src.logger import setup_logger
from src.resume_manager import ResumeManager

logger = None


class BossAutoApply:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = ConfigManager(config_path)
        global logger
        logger = setup_logger(self.config)
        
        self.browser = BrowserManager(self.config)
        self.login_manager = None
        self.job_filter = None
        self.resume_manager = None
        self.delivery_engine = None
        self.anti_detection = None

    def initialize(self):
        logger.info("=" * 50)
        logger.info("Boss直聘自动投简历工具启动")
        logger.info("=" * 50)
        
        errors = self.config.validate()
        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            return False
        
        self.browser.init_browser()
        self.login_manager = LoginManager(self.browser, self.config)
        self.job_filter = JobFilter(self.browser, self.config)
        self.resume_manager = ResumeManager(self.browser, self.config)
        self.delivery_engine = DeliveryEngine(self.browser, self.config, self.job_filter)
        self.anti_detection = AntiDetection(self.browser, self.config)
        
        logger.info("初始化完成")
        return True

    def run_login(self) -> bool:
        if not self.login_manager:
            logger.error("登录管理器未初始化")
            return False
        
        if self.login_manager.load_login_state():
            return True
        
        return self.login_manager.login()

    def run_search(self, max_pages: int = 3) -> list:
        if not self.job_filter:
            logger.error("职位筛选器未初始化")
            return []
        
        logger.info("开始搜索职位...")
        jobs = self.job_filter.search_all_keywords(max_pages=max_pages)
        logger.info(f"共找到 {len(jobs)} 个符合条件的职位")
        return jobs

    def run_deliver(self, jobs: list, max_count: int = None):
        if not self.delivery_engine:
            logger.error("投递引擎未初始化")
            return
        
        if not jobs:
            logger.warning("没有可投递的职位")
            return
        
        logger.info("开始批量投递...")
        results = self.delivery_engine.deliver_batch(jobs, max_count=max_count)
        
        report = self.delivery_engine.generate_report()
        logger.info(report)
        
        return results

    def run_full_workflow(self, max_pages: int = 3, max_deliver: int = None):
        try:
            if not self.initialize():
                return False
            
            if not self.run_login():
                logger.error("登录失败，退出程序")
                return False
            
            self.anti_detection.simulate_human_behavior(5)
            
            jobs = self.run_search(max_pages=max_pages)
            if not jobs:
                logger.info("未找到符合条件的职位")
                return True
            
            self.run_deliver(jobs, max_count=max_deliver)
            
            self.login_manager.save_login_state()
            
            logger.info("工作流程完成")
            return True
            
        except KeyboardInterrupt:
            logger.info("用户中断操作")
            return False
        except Exception as e:
            logger.error(f"工作流程发生错误: {e}")
            return False
        finally:
            self.cleanup()

    def run_resume_update(self):
        try:
            if not self.initialize():
                return False
            
            if not self.run_login():
                logger.error("登录失败")
                return False
            
            return self.resume_manager.update_resume_online()
            
        except Exception as e:
            logger.error(f"更新简历失败: {e}")
            return False
        finally:
            self.cleanup()

    def run_statistics(self):
        try:
            if not self.delivery_engine:
                self.delivery_engine = DeliveryEngine(None, self.config, None)
            
            stats = self.delivery_engine.get_statistics()
            print("\n" + "=" * 40)
            print("投递统计")
            print("=" * 40)
            print(f"总投递数: {stats['total']}")
            print(f"投递成功: {stats['success']}")
            print(f"投递失败: {stats['failed']}")
            print(f"已投递过: {stats['already_delivered']}")
            print(f"发生错误: {stats['error']}")
            print("=" * 40 + "\n")
            
        except Exception as e:
            logger.error(f"获取统计失败: {e}")

    def cleanup(self):
        if self.browser:
            self.browser.close()
        logger.info("资源清理完成")


def main():
    parser = argparse.ArgumentParser(description="Boss直聘自动投简历工具")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["full", "search", "deliver", "login", "resume", "stats"],
        default="full",
        help="运行模式 (默认: full)"
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=3,
        help="搜索页数 (默认: 3)"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=None,
        help="投递上限数量"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行"
    )
    
    args = parser.parse_args()
    
    app = BossAutoApply(config_path=args.config)
    
    if args.headless:
        app.config.config.browser.headless = True
    
    if args.mode == "full":
        success = app.run_full_workflow(max_pages=args.pages, max_deliver=args.limit)
        sys.exit(0 if success else 1)
    
    elif args.mode == "login":
        if app.initialize():
            success = app.run_login()
            app.cleanup()
            sys.exit(0 if success else 1)
    
    elif args.mode == "search":
        if app.initialize() and app.run_login():
            jobs = app.run_search(max_pages=args.pages)
            app.cleanup()
            print(f"\n找到 {len(jobs)} 个职位")
            for i, job in enumerate(jobs[:10], 1):
                print(f"{i}. {job.title} | {job.company} | {job.salary} | {job.city}")
    
    elif args.mode == "deliver":
        if app.initialize() and app.run_login():
            jobs = app.run_search(max_pages=args.pages)
            app.run_deliver(jobs, max_count=args.limit)
            app.cleanup()
    
    elif args.mode == "resume":
        success = app.run_resume_update()
        sys.exit(0 if success else 1)
    
    elif args.mode == "stats":
        app.run_statistics()


if __name__ == "__main__":
    main()
