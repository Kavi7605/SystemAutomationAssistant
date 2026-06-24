import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_engine():
    parser = MagicMock()
    task_planner = MagicMock()
    executor = MagicMock()
    
    resolver = MagicMock()
    history_manager = MagicMock()
    
    # Create engine and mock its components
    from src.automation.engine import AutomationEngine
    engine = AutomationEngine(
        parser=parser, 
        task_planner=task_planner, 
        executor=executor,
        resolver=resolver,
        history_manager=history_manager
    )
    
    return engine, parser, task_planner, executor

@pytest.mark.parametrize("command, expected_feature", [
    ("turn on night light", "night_light"),
    ("turn off night light", "night_light"),
    ("enable night light", "night_light"),
    ("disable night light", "night_light"),
    ("night light on", "night_light"),
    ("night light off", "night_light"),
    
    # Bluetooth
    ("turn on bluetooth", "bluetooth"),
    ("turn off bluetooth", "bluetooth"),
    ("turn on the bluetooth", "bluetooth"),
    ("turn off the bluetooth", "bluetooth"),
    ("bluetooth on", "bluetooth"),
    ("bluetooth off", "bluetooth"),
    ("bluetooth status", "bluetooth"),
    ("show bluetooth status", "bluetooth"),
    ("is bluetooth on", "bluetooth"),
    ("bluetooth information", "bluetooth"),
    
    # Hotspot Toggles
    ("turn on hotspot", "hotspot"),
    ("turn off hotspot", "hotspot"),
    ("turn on mobile hotspot", "hotspot"),
    ("turn off mobile hotspot", "hotspot"),
    ("hotspot on", "hotspot"),
    ("hotspot off", "hotspot"),
    
    # Airplane Mode
    ("turn on airplane mode", "airplane_mode"),
    ("turn off airplane mode", "airplane_mode"),
    ("enable airplane mode", "airplane_mode"),
    ("disable airplane mode", "airplane_mode"),
    ("airplane mode on", "airplane_mode"),
    ("airplane mode off", "airplane_mode"),
    ("airplane mode status", "airplane_mode"),
    ("show airplane mode status", "airplane_mode"),
    ("is airplane mode enabled", "airplane_mode"),
    
    # Battery Saver Toggles
    ("turn on battery saver mode", "battery_saver"),
    ("turn off battery saver mode", "battery_saver"),
    ("turn on the battery saver mode", "battery_saver"),
    ("turn off the battery saver mode", "battery_saver"),
    ("turn on battery saver", "battery_saver"),
    ("turn off battery saver", "battery_saver"),
    
    # Fan Mode
    ("current fan mode", "fan_mode")
])
def test_unsupported_features_bypass_planner(mock_engine, command, expected_feature):
    engine, parser, task_planner, executor = mock_engine
    
    engine.process_command(command)
    
    # Assert bypass
    assert task_planner.plan_tasks.call_count == 0
    assert parser.parse_command.call_count == 0
    
    # Assert exact execution json
    executor.execute.assert_called_once()
    executed_command = executor.execute.call_args[0][0]
    
    assert executed_command["action"] == "unsupported_feature"
    assert executed_command["parameters"]["feature"] == expected_feature
