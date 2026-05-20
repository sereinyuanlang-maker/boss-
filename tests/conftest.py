import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        yield str(config_path)


@pytest.fixture
def mock_browser():
    class MockBrowser:
        def __init__(self):
            self.driver = MockDriver()
    
    class MockDriver:
        def __init__(self):
            self.current_url = "https://www.zhipin.com"
        
        def get(self, url):
            self.current_url = url
        
        def find_elements(self, by, value):
            return []
        
        def execute_script(self, script, *args):
            return 0
        
        def quit(self):
            pass
    
    return MockBrowser()


@pytest.fixture(autouse=True)
def clean_env():
    keys = ["BOSS_USERNAME", "BOSS_PASSWORD"]
    old_values = {}
    for key in keys:
        old_values[key] = os.environ.pop(key, None)
    yield
    for key, value in old_values.items():
        if value is not None:
            os.environ[key] = value
