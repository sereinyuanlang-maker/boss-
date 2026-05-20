import pytest
from unittest.mock import MagicMock

from src.job_filter import JobFilter, JobInfo


class TestJobFilter:
    def _create_filter(self):
        mock_config = MagicMock()
        mock_config.config.filters = MagicMock()
        mock_config.config.data.job_cache = "./test_job_cache.json"
        return JobFilter(None, mock_config)

    def test_parse_salary(self):
        filter_obj = self._create_filter()
        
        assert filter_obj._parse_salary("15-25K") == (15, 25)
        assert filter_obj._parse_salary("20K以上") == (20, 999)
        assert filter_obj._parse_salary("15K以下") == (0, 15)
        assert filter_obj._parse_salary("30K") == (30, 30)
        assert filter_obj._parse_salary("") == (0, 0)

    def test_parse_experience(self):
        filter_obj = self._create_filter()
        
        assert filter_obj._parse_experience("3-5年") == (3, 5)
        assert filter_obj._parse_experience("5年以上") == (5, 99)
        assert filter_obj._parse_experience("1年以下") == (0, 1)
        assert filter_obj._parse_experience("应届生") == (0, 0)
        assert filter_obj._parse_experience("经验不限") == (0, 0)

    def test_extract_job_id(self):
        filter_obj = self._create_filter()
        
        url = "https://www.zhipin.com/job_detail/1234567890.html"
        assert filter_obj._extract_job_id(url) == "1234567890"
        
        assert filter_obj._extract_job_id("") == ""

    def test_job_info_dataclass(self):
        job = JobInfo(
            job_id="123",
            title="Python开发",
            company="Test公司",
            salary="20-30K",
            city="北京"
        )
        
        assert job.job_id == "123"
        assert job.title == "Python开发"
        assert job.salary == "20-30K"
        
        data = job.to_dict()
        assert data["job_id"] == "123"
        assert data["title"] == "Python开发"
        
        job2 = JobInfo.from_dict(data)
        assert job2.job_id == "123"
        assert job2.title == "Python开发"
