import pytest
from unittest.mock import MagicMock, patch
from src.tools.wait_tool import WaitTool
import time

@pytest.fixture
def wait_tool():
    wm = MagicMock()
    return WaitTool(window_manager=wm)

def test_wait_seconds(wait_tool):
    with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
        result = wait_tool.execute(wait_type="seconds", seconds=5)
        assert result["status"] == "success"
        mock_sleep.assert_called_once_with(5)

def test_wait_until_window_success(wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
            # Simulate window found on first try
            wait_tool.window_manager.find_window.return_value = {"title": "Steam"}
            result = wait_tool.execute(wait_type="window", window_name="steam", timeout=30)
            
            assert result["status"] == "success"
            assert "appeared" in result["message"]
            wait_tool.window_manager.find_window.assert_called_with("steam")
            mock_sleep.assert_not_called()

def test_wait_until_window_polling(wait_tool):
    # time.time() returns:
    # 1. start_time = 0
    # 2. condition check 1 = 0
    # 3. condition check 2 = 1
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
            # First try fails, second try succeeds
            wait_tool.window_manager.find_window.side_effect = [None, {"title": "Steam"}]
            result = wait_tool.execute(wait_type="window", window_name="steam", timeout=30)
            
            assert result["status"] == "success"
            assert mock_sleep.call_count == 1

def test_wait_until_window_timeout(wait_tool):
    # Simulate timeout immediately by making time.time skip past 30
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 31]):
        with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
            wait_tool.window_manager.find_window.return_value = None
            result = wait_tool.execute(wait_type="window", window_name="steam", timeout=30)
            
            assert result["status"] == "failed"
            assert "Timeout" in result["message"]

def test_wait_until_app_open_success(wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep"):
            with patch("src.tools.wait_tool.psutil.process_iter") as mock_iter:
                mock_proc = MagicMock()
                mock_proc.info = {"name": "steam.exe"}
                mock_iter.return_value = [mock_proc]
                
                result = wait_tool.execute(wait_type="app", app_name="steam", timeout=30)
                assert result["status"] == "success"

def test_wait_until_window_closed_success(wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep"):
            wait_tool.window_manager.find_window.return_value = None
            result = wait_tool.execute(wait_type="window_closed", window_name="steam", timeout=30)
            
            assert result["status"] == "success"
            assert "closed" in result["message"]

def test_wait_until_window_closed_timeout(wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 31]):
        with patch("src.tools.wait_tool.time.sleep"):
            wait_tool.window_manager.find_window.return_value = {"title": "Steam"}
            result = wait_tool.execute(wait_type="window_closed", window_name="steam", timeout=30)
            
            assert result["status"] == "failed"
            assert "Timeout" in result["message"]
