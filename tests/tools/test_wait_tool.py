import pytest
from unittest.mock import MagicMock, patch
from src.tools.wait_tool import WaitTool

@pytest.fixture
def wait_tool():
    return WaitTool()

def test_wait_seconds(wait_tool):
    with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
        result = wait_tool.execute(wait_type="seconds", seconds=5)
        assert result["status"] == "success"
        mock_sleep.assert_called_once_with(5)

@patch("src.tools.wait_tool.WindowManager")
def test_wait_until_window_success(mock_wm, wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
            # Simulate window found on first try
            mock_wm.find_windows.return_value = [{"title": "Steam", "hwnd": 123}]
            result = wait_tool.execute(wait_type="window", window_name="steam", timeout=30)
            
            assert result["status"] == "success"
            assert "appeared" in result["message"]
            mock_wm.find_windows.assert_called_with("steam")
            mock_sleep.assert_not_called()

@patch("src.tools.wait_tool.WindowManager")
def test_wait_until_window_polling(mock_wm, wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
            # First try fails, second try succeeds
            mock_wm.find_windows.side_effect = [[], [{"title": "Steam", "hwnd": 123}]]
            result = wait_tool.execute(wait_type="window", window_name="steam", timeout=30)
            
            assert result["status"] == "success"
            assert mock_sleep.call_count == 1

@patch("src.tools.wait_tool.WindowManager")
def test_wait_until_window_timeout(mock_wm, wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 31]):
        with patch("src.tools.wait_tool.time.sleep") as mock_sleep:
            mock_wm.find_windows.return_value = []
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

@patch("src.tools.wait_tool.WindowManager")
def test_wait_until_window_closed_success(mock_wm, wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 1]):
        with patch("src.tools.wait_tool.time.sleep"):
            mock_wm.find_windows.return_value = []
            result = wait_tool.execute(wait_type="window_closed", window_name="steam", timeout=30)
            
            assert result["status"] == "success"
            assert "closed" in result["message"]

@patch("src.tools.wait_tool.WindowManager")
def test_wait_until_window_closed_timeout(mock_wm, wait_tool):
    with patch("src.tools.wait_tool.time.time", side_effect=[0, 0, 31]):
        with patch("src.tools.wait_tool.time.sleep"):
            mock_wm.find_windows.return_value = [{"title": "Steam", "hwnd": 123}]
            result = wait_tool.execute(wait_type="window_closed", window_name="steam", timeout=30)
            
            assert result["status"] == "failed"
            assert "Timeout" in result["message"]
