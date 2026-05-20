import re
from dataclasses import dataclass
from typing import Callable, List, Optional

from src.config import SearchConfig
from src.logger import logger


@dataclass
class JobInfo:
    """职位信息数据类"""
    title: str = ""
    salary: str = ""
    company: str = ""
    city: str = ""
    experience: str = ""
    degree: str = ""
    company_size: str = ""
    financing_stage: str = ""
    job_type: str = ""
    publish_date: str = ""
    description: str = ""
    element: Optional[object] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "salary": self.salary,
            "company": self.company,
            "city": self.city,
            "experience": self.experience,
            "degree": self.degree,
            "company_size": self.company_size,
            "financing_stage": self.financing_stage,
            "job_type": self.job_type,
            "publish_date": self.publish_date,
            "description": self.description,
        }


class JobFilter:
    """职位筛选器"""

    def __init__(self, config: SearchConfig):
        self.config = config
        self._matchers: List[Callable[[JobInfo], bool]] = self._build_matchers()

    def _build_matchers(self) -> List[Callable[[JobInfo], bool]]:
        """构建匹配器列表"""
        matchers = []

        if self.config.keywords:
            matchers.append(self._match_keywords)
        if self.config.exclude_keywords:
            matchers.append(self._match_exclude_keywords)
        if self.config.cities:
            matchers.append(self._match_city)
        if self.config.salary_range:
            matchers.append(self._match_salary)
        if self.config.experience:
            matchers.append(self._match_experience)
        if self.config.degree:
            matchers.append(self._match_degree)
        if self.config.company_size:
            matchers.append(self._match_company_size)
        if self.config.financing_stage:
            matchers.append(self._match_financing)

        return matchers

    def filter_jobs(self, jobs: List[JobInfo]) -> List[JobInfo]:
        """筛选职位列表"""
        if not self._matchers:
            logger.info("未设置筛选条件，返回所有职位")
            return jobs

        filtered = []
        for job in jobs:
            if self._match_job(job):
                filtered.append(job)

        logger.info(f"筛选结果: {len(filtered)}/{len(jobs)} 个职位符合条件")
        return filtered

    def _match_job(self, job: JobInfo) -> bool:
        """判断单个职位是否匹配"""
        for matcher in self._matchers:
            if not matcher(job):
                return False
        return True

    def _match_keywords(self, job: JobInfo) -> bool:
        title = job.title.lower()
        return any(kw.lower() in title for kw in self.config.keywords)

    def _match_exclude_keywords(self, job: JobInfo) -> bool:
        title = job.title.lower()
        return not any(kw.lower() in title for kw in self.config.exclude_keywords)

    def _match_city(self, job: JobInfo) -> bool:
        city = job.city.lower()
        return any(c.lower() in city for c in self.config.cities)

    def _match_salary(self, job: JobInfo) -> bool:
        return self._parse_salary(job.salary, self.config.salary_range)

    def _match_experience(self, job: JobInfo) -> bool:
        job_exp = job.experience.lower()
        target = self.config.experience.lower()
        if "不限" in target:
            return True
        return target in job_exp

    def _match_degree(self, job: JobInfo) -> bool:
        job_degree = job.degree.lower()
        target = self.config.degree.lower()
        if "不限" in target:
            return True
        return target in job_degree

    def _match_company_size(self, job: JobInfo) -> bool:
        size = job.company_size.lower()
        return self.config.company_size.lower() in size

    def _match_financing(self, job: JobInfo) -> bool:
        stage = job.financing_stage.lower()
        return self.config.financing_stage.lower() in stage

    @staticmethod
    def _parse_salary(job_salary: str, target_range: str) -> bool:
        """解析并比较薪资范围"""
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

    @staticmethod
    def from_dict(job_dict: dict) -> JobInfo:
        """从字典创建JobInfo"""
        return JobInfo(
            title=job_dict.get("title", ""),
            salary=job_dict.get("salary", ""),
            company=job_dict.get("company", ""),
            city=job_dict.get("city", ""),
            experience=job_dict.get("experience", ""),
            degree=job_dict.get("degree", ""),
            company_size=job_dict.get("company_size", ""),
            financing_stage=job_dict.get("financing_stage", ""),
            job_type=job_dict.get("job_type", ""),
            publish_date=job_dict.get("publish_date", ""),
            description=job_dict.get("description", ""),
            element=job_dict.get("element"),
        )
