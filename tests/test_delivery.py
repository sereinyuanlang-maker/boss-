import pytest

from src.delivery_engine import DeliveryRecord, DeliveryStatus
from src.job_filter import JobInfo


class TestDeliveryRecord:
    def test_delivery_record_creation(self):
        job = JobInfo(
            job_id="123",
            title="Python开发",
            company="Test公司",
            salary="20-30K",
            city="北京",
            url="https://example.com/job/123"
        )
        
        record = DeliveryRecord(job, DeliveryStatus.SUCCESS, "投递成功")
        
        assert record.job_id == "123"
        assert record.job_title == "Python开发"
        assert record.company == "Test公司"
        assert record.status == DeliveryStatus.SUCCESS
        assert record.message == "投递成功"
        assert record.delivered_at is not None

    def test_delivery_record_to_dict(self):
        job = JobInfo(
            job_id="456",
            title="Java开发",
            company="ABC公司",
            salary="25-35K",
            city="上海",
            url="https://example.com/job/456"
        )
        
        record = DeliveryRecord(job, DeliveryStatus.FAILED, "未找到按钮")
        data = record.to_dict()
        
        assert data["job_id"] == "456"
        assert data["job_title"] == "Java开发"
        assert data["status"] == "投递失败"
        assert data["message"] == "未找到按钮"
        assert "delivered_at" in data

    def test_delivery_status_enum(self):
        assert DeliveryStatus.PENDING.value == "待投递"
        assert DeliveryStatus.SUCCESS.value == "投递成功"
        assert DeliveryStatus.FAILED.value == "投递失败"
        assert DeliveryStatus.ALREADY_DELIVERED.value == "已投递过"
        assert DeliveryStatus.ERROR.value == "发生错误"
