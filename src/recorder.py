import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from src.logger import logger


class StatusRecorder:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(__file__).resolve().parent.parent / data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.applied_file = self.data_dir / "applied_jobs.json"
        self.daily_file = self.data_dir / f"applications_{datetime.now().strftime('%Y%m%d')}.json"
        self.applied_ids = self._load_applied_ids()

    def _load_applied_ids(self) -> set:
        if self.applied_file.exists():
            try:
                with open(self.applied_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.keys())
            except Exception as e:
                logger.warning(f"加载已投递记录失败: {e}")
        return set()

    def is_applied(self, job_id: str) -> bool:
        return job_id in self.applied_ids

    def record(
        self,
        job_id: str,
        status: str,
        job_info: Optional[dict] = None,
        error_msg: Optional[str] = None,
    ):
        record = {
            "job_id": job_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "job_info": job_info or {},
            "error": error_msg,
        }

        self._append_to_daily_file(record)
        self._update_applied_ids(job_id, status)
        logger.debug(f"记录投递状态: {job_id} -> {status}")

    def _append_to_daily_file(self, record: dict):
        records = []
        if self.daily_file.exists():
            try:
                with open(self.daily_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                pass
        records.append(record)
        with open(self.daily_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def _update_applied_ids(self, job_id: str, status: str):
        data = {}
        if self.applied_file.exists():
            try:
                with open(self.applied_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        data[job_id] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        self.applied_ids.add(job_id)

        with open(self.applied_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_to_excel(self, output_file: Optional[str] = None):
        if output_file is None:
            output_file = self.data_dir / f"applications_{datetime.now().strftime('%Y%m%d')}.xlsx"

        if not self.daily_file.exists():
            logger.warning("今日暂无投递记录")
            return

        try:
            with open(self.daily_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            df = pd.DataFrame(records)
            df.to_excel(output_file, index=False, engine="openpyxl")
            logger.info(f"投递记录已导出至: {output_file}")
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")

    def get_daily_stats(self) -> dict:
        if not self.daily_file.exists():
            return {"total": 0, "success": 0, "failed": 0}

        try:
            with open(self.daily_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            total = len(records)
            success = sum(1 for r in records if r.get("status") == "success")
            failed = sum(1 for r in records if r.get("status") == "failed")

            return {"total": total, "success": success, "failed": failed}
        except Exception:
            return {"total": 0, "success": 0, "failed": 0}
