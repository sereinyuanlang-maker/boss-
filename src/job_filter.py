import json
import random
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from src.browser_manager import BrowserManager
from src.config_manager import ConfigManager
from src.logger import setup_logger

logger = setup_logger(ConfigManager())


@dataclass
class JobInfo:
    job_id: str = ""
    title: str = ""
    company: str = ""
    salary: str = ""
    salary_min: int = 0
    salary_max: int = 0
    city: str = ""
    district: str = ""
    experience: str = ""
    experience_min: int = 0
    experience_max: int = 0
    education: str = ""
    company_size: str = ""
    industry: str = ""
    finance_stage: str = ""
    job_tags: List[str] = None
    job_desc: str = ""
    recruiter: str = ""
    recruiter_title: str = ""
    publish_time: str = ""
    url: str = ""
    source: str = "boss"
    created_at: str = ""
    
    def __post_init__(self):
        if self.job_tags is None:
            self.job_tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'JobInfo':
        return cls(**data)


class JobFilter:
    def __init__(self, browser_manager: BrowserManager, config: ConfigManager):
        self.browser = browser_manager
        self.config = config
        self.filters = config.config.filters
        self.cache_file = Path(config.config.data.job_cache)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.job_cache: Dict[str, JobInfo] = {}
        self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.job_cache = {k: JobInfo.from_dict(v) for k, v in data.items()}
                logger.info(f"加载职位缓存: {len(self.job_cache)} 条")
            except Exception as e:
                logger.warning(f"加载职位缓存失败: {e}")

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                data = {k: v.to_dict() for k, v in self.job_cache.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存职位缓存失败: {e}")

    def search_jobs(self, keyword: str, city: str, page: int = 1) -> List[JobInfo]:
        jobs = []
        try:
            search_url = self._build_search_url(keyword, city, page)
            logger.info(f"搜索职位: {keyword} - {city} - 第{page}页")
            
            self.browser.driver.get(search_url)
            self.browser.random_delay(3, 6)
            
            job_cards = self.browser.safe_finds(
                (By.CSS_SELECTOR, ".job-card-wrapper, .job-list-box .job-card"), timeout=15
            )
            
            if not job_cards:
                job_cards = self.browser.safe_finds(
                    (By.CSS_SELECTOR, "[class*='job-card']"), timeout=10
                )
            
            logger.info(f"找到 {len(job_cards)} 个职位卡片")
            
            for card in job_cards:
                try:
                    job = self._parse_job_card(card, keyword, city)
                    if job and job.job_id:
                        jobs.append(job)
                        self.job_cache[job.job_id] = job
                except Exception as e:
                    logger.warning(f"解析职位卡片失败: {e}")
                    continue
            
            self._save_cache()
            
        except Exception as e:
            logger.error(f"搜索职位失败: {e}")
        
        return jobs

    def _build_search_url(self, keyword: str, city: str, page: int) -> str:
        city_code = self._get_city_code(city)
        return f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city_code}&page={page}"

    def _get_city_code(self, city: str) -> str:
        city_map = {
            "北京": "101010100",
            "上海": "101020100",
            "广州": "101280100",
            "深圳": "101280600",
            "杭州": "101210100",
            "成都": "101270100",
            "武汉": "101200100",
            "西安": "101110100",
            "南京": "101190100",
            "重庆": "101040100",
            "天津": "101030100",
            "苏州": "101190400",
            "长沙": "101250100",
            "郑州": "101180100",
            "东莞": "101281600",
            "青岛": "101120200",
            "沈阳": "101070100",
            "宁波": "101210400",
            "昆明": "101290100",
            "厦门": "101230200",
        }
        return city_map.get(city, "101010100")

    def _parse_job_card(self, card, keyword: str, city: str) -> Optional[JobInfo]:
        try:
            job = JobInfo()
            job.source = "boss"
            job.city = city
            
            try:
                link = card.find_element(By.CSS_SELECTOR, "a[href*='/job_detail/']")
                job.url = link.get_attribute("href")
                job.job_id = self._extract_job_id(job.url)
            except:
                pass
            
            try:
                job.title = card.find_element(By.CSS_SELECTOR, ".job-name, .title, h3").text.strip()
            except:
                pass
            
            try:
                job.salary = card.find_element(By.CSS_SELECTOR, ".salary, .job-salary").text.strip()
                job.salary_min, job.salary_max = self._parse_salary(job.salary)
            except:
                pass
            
            try:
                job.company = card.find_element(By.CSS_SELECTOR, ".company-name, .name").text.strip()
            except:
                pass
            
            try:
                info_text = card.find_element(By.CSS_SELECTOR, ".job-info, .info").text
                job.experience, job.education = self._parse_job_info(info_text)
                job.experience_min, job.experience_max = self._parse_experience(job.experience)
            except:
                pass
            
            try:
                tags = card.find_elements(By.CSS_SELECTOR, ".tag, .job-tag")
                job.job_tags = [tag.text.strip() for tag in tags if tag.text.strip()]
            except:
                pass
            
            try:
                job.recruiter = card.find_element(By.CSS_SELECTOR, ".recruiter, .boss-name").text.strip()
            except:
                pass
            
            try:
                job.company_size = card.find_element(By.CSS_SELECTOR, ".company-size").text.strip()
            except:
                pass
            
            try:
                job.industry = card.find_element(By.CSS_SELECTOR, ".company-industry").text.strip()
            except:
                pass
            
            return job
        except Exception as e:
            logger.warning(f"解析职位卡片异常: {e}")
            return None

    def _extract_job_id(self, url: str) -> str:
        match = re.search(r'/job_detail/([^.]+)', url)
        return match.group(1) if match else ""

    def _parse_salary(self, salary_text: str) -> Tuple[int, int]:
        try:
            salary_text = salary_text.replace('K', '').replace('k', '')
            if '-' in salary_text:
                parts = salary_text.split('-')
                return int(parts[0].strip()), int(parts[1].strip())
            elif '以上' in salary_text:
                num = re.search(r'\d+', salary_text)
                return int(num.group()) if num else 0, 999
            elif '以下' in salary_text:
                num = re.search(r'\d+', salary_text)
                return 0, int(num.group()) if num else 0
            else:
                num = re.search(r'\d+', salary_text)
                val = int(num.group()) if num else 0
                return val, val
        except:
            return 0, 0

    def _parse_job_info(self, info_text: str) -> Tuple[str, str]:
        experience = ""
        education = ""
        
        parts = info_text.split('\n')
        for part in parts:
            part = part.strip()
            if any(x in part for x in ['年', '经验', '应届']):
                experience = part
            elif any(x in part for x in ['学历', '本科', '硕士', '大专', '博士']):
                education = part
        
        return experience, education

    def _parse_experience(self, exp_text: str) -> Tuple[int, int]:
        try:
            if '应届' in exp_text or '不限' in exp_text:
                return 0, 0
            
            numbers = re.findall(r'\d+', exp_text)
            if len(numbers) >= 2:
                return int(numbers[0]), int(numbers[1])
            elif len(numbers) == 1:
                if '以上' in exp_text:
                    return int(numbers[0]), 99
                elif '以下' in exp_text:
                    return 0, int(numbers[0])
                else:
                    return int(numbers[0]), int(numbers[0])
            return 0, 0
        except:
            return 0, 0

    def filter_jobs(self, jobs: List[JobInfo]) -> List[JobInfo]:
        filtered = []
        for job in jobs:
            if self._match_filters(job):
                filtered.append(job)
        return filtered

    def _match_filters(self, job: JobInfo) -> bool:
        if self.filters.salary_min > 0 and job.salary_max < self.filters.salary_min:
            return False
        if self.filters.salary_max > 0 and job.salary_min > self.filters.salary_max:
            return False
        
        if self.filters.experience_min > 0 and job.experience_max < self.filters.experience_min:
            return False
        if self.filters.experience_max > 0 and job.experience_min > self.filters.experience_max:
            return False
        
        if self.filters.education and self.filters.education != "不限":
            if self.filters.education not in job.education:
                return False
        
        if self.filters.exclude_keywords:
            job_text = f"{job.title} {job.company} {job.job_desc}"
            for exclude in self.filters.exclude_keywords:
                if exclude in job_text:
                    return False
        
        if self.filters.company_size and job.company_size:
            if job.company_size not in self.filters.company_size:
                return False
        
        if self.filters.industries and job.industry:
            if not any(ind in job.industry for ind in self.filters.industries):
                return False
        
        return True

    def get_job_detail(self, job: JobInfo) -> JobInfo:
        try:
            if not job.url:
                return job
            
            self.browser.driver.get(job.url)
            self.browser.random_delay(3, 5)
            
            try:
                desc_element = self.browser.safe_find(
                    (By.CSS_SELECTOR, ".job-sec-text, .job-description, .detail-content"), timeout=10
                )
                if desc_element:
                    job.job_desc = desc_element.text.strip()
            except:
                pass
            
            try:
                company_info = self.browser.safe_find(
                    (By.CSS_SELECTOR, ".company-info, .sider-company"), timeout=5
                )
                if company_info:
                    text = company_info.text
                    if not job.company_size:
                        size_match = re.search(r'(\d+-\d+人|\d+人以上)', text)
                        if size_match:
                            job.company_size = size_match.group(1)
                    if not job.finance_stage:
                        stages = ['已上市', 'D轮及以上', 'C轮', 'B轮', 'A轮', '天使轮', '未融资', '不需要融资']
                        for stage in stages:
                            if stage in text:
                                job.finance_stage = stage
                                break
            except:
                pass
            
            self.job_cache[job.job_id] = job
            self._save_cache()
            
        except Exception as e:
            logger.warning(f"获取职位详情失败: {e}")
        
        return job

    def search_all_keywords(self, max_pages: int = 3) -> List[JobInfo]:
        all_jobs = []
        
        for keyword in self.filters.keywords:
            for city in self.filters.cities:
                logger.info(f"开始搜索: {keyword} - {city}")
                for page in range(1, max_pages + 1):
                    jobs = self.search_jobs(keyword, city, page)
                    if not jobs:
                        break
                    all_jobs.extend(jobs)
                    self.browser.random_delay(5, 10)
        
        unique_jobs = {}
        for job in all_jobs:
            if job.job_id and job.job_id not in unique_jobs:
                unique_jobs[job.job_id] = job
        
        filtered_jobs = self.filter_jobs(list(unique_jobs.values()))
        logger.info(f"筛选后职位数量: {len(filtered_jobs)}")
        return filtered_jobs
