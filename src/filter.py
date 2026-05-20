import re
from typing import List, Optional

from src.config import SearchConfig
from src.logger import logger


class JobFilter:
    def __init__(self, config: SearchConfig):
        self.config = config

    def filter_jobs(self, jobs: List[dict]) -> List[dict]:
        filtered = []
        for job in jobs:
            if self._match_job(job):
                filtered.append(job)
        logger.info(f"筛选结果: {len(filtered)}/{len(jobs)} 个职位符合条件")
        return filtered

    def _match_job(self, job: dict) -> bool:
        if self.config.keywords and not self._match_keywords(job):
            return False
        if self.config.cities and not self._match_city(job):
            return False
        if self.config.salary_range and not self._match_salary(job):
            return False
        if self.config.experience and not self._match_experience(job):
            return False
        if self.config.degree and not self._match_degree(job):
            return False
        if self.config.company_size and not self._match_company_size(job):
            return False
        if self.config.financing_stage and not self._match_financing(job):
            return False
        return True

    def _match_keywords(self, job: dict) -> bool:
        title = job.get("title", "").lower()
        return any(kw.lower() in title for kw in self.config.keywords)

    def _match_city(self, job: dict) -> bool:
        city = job.get("city", "").lower()
        return any(c.lower() in city for c in self.config.cities)

    def _match_salary(self, job: dict) -> bool:
        job_salary = job.get("salary", "")
        return self._parse_salary(job_salary, self.config.salary_range)

    def _match_experience(self, job: dict) -> bool:
        job_exp = job.get("experience", "")
        return self.config.experience.lower() in job_exp.lower()

    def _match_degree(self, job: dict) -> bool:
        job_degree = job.get("degree", "")
        return self.config.degree.lower() in job_degree.lower()

    def _match_company_size(self, job: dict) -> bool:
        size = job.get("company_size", "")
        return self.config.company_size.lower() in size.lower()

    def _match_financing(self, job: dict) -> bool:
        stage = job.get("financing_stage", "")
        return self.config.financing_stage.lower() in stage.lower()

    @staticmethod
    def _parse_salary(job_salary: str, target_range: str) -> bool:
        def extract_numbers(s: str) -> List[int]:
            nums = re.findall(r"(\d+)", s)
            return [int(n) for n in nums]

        job_nums = extract_numbers(job_salary)
        target_nums = extract_numbers(target_range)

        if not job_nums or not target_nums:
            return True

        job_min, job_max = job_nums[0], job_nums[-1]
        target_min, target_max = target_nums[0], target_nums[-1]

        return not (job_max < target_min or job_min > target_max)
