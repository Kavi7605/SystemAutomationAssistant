import pytest
import os
import json
import shutil
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.context.persistence_manager import PersistenceManager

class TestPersistenceManager:
    def setup_method(self):
        self.test_dir = "tests/data_tmp"
        self.context_file = os.path.join(self.test_dir, "context.json")
        self.state_file = os.path.join(self.test_dir, "state.json")
        self.pm = PersistenceManager(context_file=self.context_file, state_file=self.state_file)

    def teardown_method(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_context(self):
        mock_context = {
            "current_active_app": "discord",
            "opened_apps_history": ["steam", "discord"]
        }
        
        self.pm.save_context(mock_context)
        
        loaded = self.pm.load_context()
        assert loaded["current_active_app"] == "discord"
        assert loaded["opened_apps_history"] == ["steam", "discord"]

    def test_save_and_load_state(self):
        mock_state = {
            "states": {
                "steam": {"running": True}
            },
            "current_active_app": "steam"
        }
        
        self.pm.save_state(mock_state)
        
        loaded = self.pm.load_state()
        assert loaded["states"]["steam"]["running"] == True
        assert loaded["current_active_app"] == "steam"

    def test_missing_files_return_empty_dicts(self):
        # Don't save anything
        assert self.pm.load_context() == {}
        assert self.pm.load_state() == {}

    def test_corrupted_json_handled_gracefully(self):
        # Write corrupted JSON
        with open(self.context_file, "w") as f:
            f.write("{invalid json format...")
            
        with open(self.state_file, "w") as f:
            f.write("not even json")
            
        assert self.pm.load_context() == {}
        assert self.pm.load_state() == {}
