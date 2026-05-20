import time
from unittest.mock import MagicMock, patch

import pytest

from src.anti_detection import AntiDetection


class TestAntiDetection:
    def test_add_random_delays(self):
        mock_browser = MagicMock()
        mock_config = MagicMock()
        
        anti = AntiDetection(mock_browser, mock_config)
        
        start = time.time()
        delay = anti.add_random_delays(0.1)
        elapsed = time.time() - start
        
        assert delay > 0
        assert elapsed >= 0.05

    def test_random_user_agent_rotation(self):
        mock_browser = MagicMock()
        mock_config = MagicMock()
        
        anti = AntiDetection(mock_browser, mock_config)
        
        ua1 = anti.random_user_agent_rotation()
        ua2 = anti.random_user_agent_rotation()
        
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)
        assert "Mozilla" in ua1
        assert "Mozilla" in ua2

    def test_simulate_reading_time(self):
        mock_browser = MagicMock()
        mock_config = MagicMock()
        
        anti = AntiDetection(mock_browser, mock_config)
        
        start = time.time()
        anti.simulate_reading_time(text_length=0)
        elapsed = time.time() - start
        
        assert elapsed >= 1.5

    @patch('time.sleep')
    def test_simulate_human_behavior(self, mock_sleep):
        mock_browser = MagicMock()
        mock_config = MagicMock()
        mock_driver = MagicMock()
        mock_browser.driver = mock_driver
        
        mock_driver.execute_script.return_value = 1000
        mock_driver.find_elements.return_value = []
        
        anti = AntiDetection(mock_browser, mock_config)
        
        anti.simulate_human_behavior(duration=0.5)
        
        assert mock_sleep.called
