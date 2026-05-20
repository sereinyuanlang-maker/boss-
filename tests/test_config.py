import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config_manager import ConfigManager


class TestConfigManager:
    def test_load_default_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = ConfigManager(str(config_path))
            
            assert config.config.account.username == ""
            assert config.config.browser.type == "chrome"
            assert config.config.delivery.daily_limit == 50

    def test_load_from_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            data = {
                "account": {
                    "username": "13800138000",
                    "password": "test123"
                },
                "delivery": {
                    "daily_limit": 30
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f)
            
            config = ConfigManager(str(config_path))
            assert config.config.account.username == "13800138000"
            assert config.config.delivery.daily_limit == 30

    def test_env_override(self):
        os.environ["BOSS_USERNAME"] = "env_user"
        os.environ["BOSS_PASSWORD"] = "env_pass"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = ConfigManager(str(config_path))
            
            assert config.config.account.username == "env_user"
            assert config.config.account.password == "env_pass"
        
        del os.environ["BOSS_USERNAME"]
        del os.environ["BOSS_PASSWORD"]

    def test_get_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = ConfigManager(str(config_path))
            
            assert config.get("browser.type") == "chrome"
            assert config.get("nonexistent.key", "default") == "default"
            
            config.set("delivery.daily_limit", 100)
            assert config.config.delivery.daily_limit == 100

    def test_validate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = ConfigManager(str(config_path))
            
            errors = config.validate()
            assert len(errors) > 0
            assert any("用户名" in e for e in errors)
            
            config.set("account.username", "test")
            config.set("account.password", "test")
            config.set("filters.keywords", ["Python"])
            config.set("filters.cities", ["北京"])
            
            errors = config.validate()
            assert len(errors) == 0

    def test_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = ConfigManager(str(config_path))
            
            config.set("account.username", "saved_user")
            config.save()
            
            config2 = ConfigManager(str(config_path))
            assert config2.config.account.username == "saved_user"
