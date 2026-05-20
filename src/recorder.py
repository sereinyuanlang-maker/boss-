import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.logger import logger
from src.utils import calculate_success_rate, sanitize_filename


class StatusRecorder:
    """投递状态记录器"""

    _lock = threading.Lock()

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(__file__).resolve().parent.parent / data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.applied_file = self.data_dir / "applied_jobs.json"
        self.daily_file = self.data_dir / f"applications_{datetime.now().strftime('%Y%m%d')}.json"
        self._cache: Dict[str, dict] = {}
        self._loaded = False
        self._load_data()

    def _load_data(self):
        """加载已投递数据"""
        if self._loaded:
            return

        with self._lock:
            if self.applied_file.exists():
                try:
                    with open(self.applied_file, "r", encoding="utf-8") as f:
                        self._cache = json.load(f)
                    logger.info(f"已加载 {len(self._cache)} 条投递记录")
                except Exception as e:
                    logger.warning(f"加载已投递记录失败: {e}")
                    self._cache = {}
            self._loaded = True

    def is_applied(self, job_id: str) -> bool:
        """检查是否已投递"""
        return job_id in self._cache

    def record(
        self,
        job_id: str,
        status: str,
        job_info: Optional[dict] = None,
        error_msg: Optional[str] = None,
    ):
        """记录投递状态"""
        record = {
            "job_id": job_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "job_info": job_info or {},
            "error": error_msg,
        }

        with self._lock:
            self._append_to_daily_file(record)
            self._update_cache(job_id, status)

        logger.debug(f"记录投递状态: {job_id} -> {status}")

    def _append_to_daily_file(self, record: dict):
        """追加到每日文件"""
        records = []
        if self.daily_file.exists():
            try:
                with open(self.daily_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                pass
        records.append(record)

        try:
            with open(self.daily_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存每日记录失败: {e}")

    def _update_cache(self, job_id: str, status: str):
        """更新缓存并持久化"""
        self._cache[job_id] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            with open(self.applied_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存投递记录失败: {e}")

    def get_job_status(self, job_id: str) -> Optional[str]:
        """获取职位投递状态"""
        if job_id in self._cache:
            return self._cache[job_id].get("status")
        return None

    def get_applied_jobs(self, days: int = 7) -> List[dict]:
        """获取最近投递的职位"""
        cutoff = datetime.now() - timedelta(days=days)
        result = []
        for job_id, info in self._cache.items():
            try:
                timestamp = datetime.fromisoformat(info.get("timestamp", ""))
                if timestamp >= cutoff:
                    result.append({"job_id": job_id, **info})
            except ValueError:
                continue
        return result

    def export_to_excel(self, output_file: Optional[str] = None) -> Optional[Path]:
        """导出到Excel"""
        if output_file is None:
            output_file = self.data_dir / f"applications_{datetime.now().strftime('%Y%m%d')}.xlsx"
        else:
            output_file = Path(output_file)

        if not self.daily_file.exists():
            logger.warning("今日暂无投递记录")
            return None

        try:
            with open(self.daily_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            if not records:
                logger.warning("记录为空")
                return None

            df = pd.DataFrame(records)

            # 展开 job_info
            if "job_info" in df.columns:
                job_info_df = pd.json_normalize(df["job_info"])
                job_info_df.columns = [f"job_{col}" for col in job_info_df.columns]
                df = df.drop("job_info", axis=1)
                df = pd.concat([df, job_info_df], axis=1)

            df.to_excel(output_file, index=False, engine="openpyxl")
            logger.info(f"投递记录已导出至: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return None

    def get_daily_stats(self) -> dict:
        """获取每日统计"""
        if not self.daily_file.exists():
            return {"total": 0, "success": 0, "failed": 0, "success_rate": 0.0}

        try:
            with open(self.daily_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            total = len(records)
            success = sum(1 for r in records if r.get("status") == "success")
            failed = sum(1 for r in records if r.get("status") == "failed")

            return {
                "total": total,
                "success": success,
                "failed": failed,
                "success_rate": calculate_success_rate(success, total),
            }
        except Exception:
            return {"total": 0, "success": 0, "failed": 0, "success_rate": 0.0}

    def get_overall_stats(self) -> dict:
        """获取总体统计"""
        total = len(self._cache)
        success = sum(1 for v in self._cache.values() if v.get("status") == "success")
        failed = sum(1 for v in self._cache.values() if v.get("status") == "failed")

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": calculate_success_rate(success, total),
        }

    def clear_old_records(self, days: int = 30):
        """清理旧记录"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0

        with self._lock:
            to_remove = []
            for job_id, info in self._cache.items():
                try:
                    timestamp = datetime.fromisoformat(info.get("timestamp", ""))
                    if timestamp < cutoff:
                        to_remove.append(job_id)
                except ValueError:
                    continue

            for job_id in to_remove:
                del self._cache[job_id]
                removed += 1

            if removed > 0:
                try:
                    with open(self.applied_file, "w", encoding="utf-8") as f:
                        json.dump(self._cache, f, ensure_ascii=False, indent=2)
                    logger.info(f"已清理 {removed} 条旧记录")
                except Exception as e:
                    logger.error(f"保存清理后的记录失败: {e}")

        return removed
