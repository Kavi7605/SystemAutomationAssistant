import pytest
from src.parser.condition_parser import ConditionParser

def test_condition_if_then():
    parser = ConditionParser()
    res = parser.parse(["if discord is running focus it"])
    assert len(res) == 1
    assert res[0]["condition"] == "discord is running"
    assert res[0]["action"] == "focus it"

def test_condition_if_not():
    parser = ConditionParser()
    res = parser.parse(["if discord is not running open discord"])
    assert len(res) == 1
    assert res[0]["condition"] == "discord is not running"
    assert res[0]["action"] == "open discord"

def test_condition_trailing():
    parser = ConditionParser()
    res = parser.parse(["focus it if discord is running"])
    assert len(res) == 1
    assert res[0]["condition"] == "discord is running"
    assert res[0]["action"] == "focus it"

def test_condition_once():
    parser = ConditionParser()
    res = parser.parse(["once chrome opens, maximize it"])
    assert len(res) == 1
    assert res[0]["condition"] == "chrome opens"
    assert res[0]["action"] == "maximize it"

def test_condition_after():
    parser = ConditionParser()
    res = parser.parse(["after whatsapp opens, focus it"])
    assert len(res) == 1
    assert res[0]["condition"] == "whatsapp opens"
    assert res[0]["action"] == "focus it"
