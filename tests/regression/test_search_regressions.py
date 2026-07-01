import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSearchRegressions:

    def assertExecute(self, expected_action, expected_params=None, cmd_idx=0):
        self.executor_mock.execute.assert_called()
        cmd = self.executor_mock.execute.call_args[0][0]
        print(f"DEBUG: execute called with cmd: {cmd}")
        if isinstance(cmd, list):
            cmd = cmd[cmd_idx]
        print(f"DEBUG: asserting cmd action {cmd['action']} == {expected_action}")
        assert cmd["action"] == expected_action
        if expected_params:
            for k, v in expected_params.items():
                assert cmd["parameters"][k] == v

    def test_priority1_search_intent_bypass_planner(self):
        commands = [
            ("open github and search kavi7605 user", "github.com", "kavi7605"),
            ("open github and search python repositories", "github.com", "python"),
            ("open youtube and search avengers", "youtube.com", "avengers"),
            ("open reddit and search python", "reddit", "python"),
        ]
        
        if True:
            for cmd, domain_hint, query_hint in commands:
                self.engine.process_command(cmd)
                self.task_planner_mock.plan_tasks.assert_not_called()
                self.assertExecute("open_url")
                url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
                assert domain_hint in url
                assert query_hint in url
                self.executor_mock.reset_mock()
        if False:
            pass
    def test_priority2_natural_website_search_grammar(self):
        commands = [
            ("open youtube website avengers", "avengers"),
            ("open youtube website shorts", "shorts"),
            ("open github website kavi7605", "kavi7605"),
            ("open github website kavi7605 user", "kavi7605"),
            ("open github website kavi7605 users", "kavi7605"),
            ("open github website python repositories", "python")
        ]
        
        for cmd, query_hint in commands:
            self.engine.process_command(cmd)
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
            url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
            assert query_hint in url
            self.executor_mock.reset_mock()

    def test_priority3_close_application_classification(self):
        
        if True:
            commands = [
                ("close lively wallpaper", "lively wallpaper"),
                ("close steam", "steam"),
                ("close whatsapp", "whatsapp")
            ]
            
            for cmd, app_name in commands:
                self.engine.process_command(cmd)
                self.task_planner_mock.plan_tasks.assert_not_called()
                self.assertExecute("close_application", {"application_name": app_name})
                self.executor_mock.reset_mock()
        if False:
            pass


import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestApplicationClassification:

    def assertExecute(self, expected_action, expected_params=None, cmd_idx=0):
        self.executor_mock.execute.assert_called()
        cmd = self.executor_mock.execute.call_args[0][0]
        print(f"DEBUG: execute called with cmd: {cmd}")
        if isinstance(cmd, list):
            cmd = cmd[cmd_idx]
        print(f"DEBUG: asserting cmd action {cmd['action']} == {expected_action}")
        assert cmd["action"] == expected_action
        if expected_params:
            for k, v in expected_params.items():
                assert cmd["parameters"][k] == v

    def test_baseline_github(self):
        # open github -> AppFinder says it's installed -> Application
        
        if True:
            self.engine.process_command("open github")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_application", {"application_name": "github"})
            self.executor_mock.reset_mock()
            
            # open github website -> Website
            self.engine.process_command("open github website")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
        if False:
            pass
    def test_baseline_youtube(self):
        
        if True:
            # open youtube -> not installed, but in registry -> Website
            self.engine.process_command("open youtube")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
            self.executor_mock.reset_mock()
            
            # open youtube website -> Website
            self.engine.process_command("open youtube website")
            self.task_planner_mock.plan_tasks.assert_not_called()
            self.assertExecute("open_url")
        if False:
            pass
    def test_multi_action_combinations(self):
        
        if True:
            # open github and github website -> App + Website
            self.engine.process_command("open github and github website")
            cmds = self.executor_mock.execute.call_args[0][0]
            assert len(cmds) == 2
            assert cmds[0]["action"] == "open_application"
            assert cmds[1]["action"] == "open_url"
            self.executor_mock.reset_mock()
            
            # open github and youtube -> App + Website
            self.engine.process_command("open github and youtube")
            cmds = self.executor_mock.execute.call_args[0][0]
            assert len(cmds) == 2
            assert cmds[0]["action"] == "open_application"
            assert cmds[1]["action"] == "open_url"
            self.executor_mock.reset_mock()
            
            # open youtube and github -> Website + App
            self.engine.process_command("open youtube and github")
            cmds = self.executor_mock.execute.call_args[0][0]
            assert len(cmds) == 2
            assert cmds[0]["action"] == "open_url"
            assert cmds[1]["action"] == "open_application"
            self.executor_mock.reset_mock()
            
            # open vscode and steam -> App + App
            self.engine.process_command("open vscode and steam")
            cmds = self.executor_mock.execute.call_args[0][0]
            assert len(cmds) == 2
            assert cmds[0]["action"] == "open_application"
            assert cmds[1]["action"] == "open_application"
            self.executor_mock.reset_mock()
            
            # open vscode and github website -> App + Website
            self.engine.process_command("open vscode and github website")
            cmds = self.executor_mock.execute.call_args[0][0]
            assert len(cmds) == 2
            assert cmds[0]["action"] == "open_application"
            assert cmds[1]["action"] == "open_url"
        if False:
            pass
    def test_search_normalization(self):
        # open github website kavi7605 user
        self.engine.process_command("open github website kavi7605 user")
        self.assertExecute("open_url")
        url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
        assert "kavi7605" in url
        assert "users" in url
        self.executor_mock.reset_mock()
        
        # open github website and search kavi7605 user
        self.engine.process_command("open github website and search kavi7605 user")
        self.assertExecute("open_url")
        url2 = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
        assert url == url2
        self.executor_mock.reset_mock()
        
        # open youtube website shorts
        self.engine.process_command("open youtube website shorts")
        self.assertExecute("open_url")
        url = self.executor_mock.execute.call_args[0][0]["parameters"]["url"]
        assert "shorts" in url

    def test_search_validation_modes(self):
        invalid_queries = ["user", "repository", "issue"]
        for query in invalid_queries:
            self.engine.process_command(f"open github website {query}")
            cmd = self.executor_mock.execute.call_args[0][0]
            if isinstance(cmd, list): cmd = cmd[0]
            assert cmd["action"] == "unsupported"
            assert "Validation error" in cmd["parameters"]["message"]
            assert f"before search mode '{query}'" in cmd["parameters"]["message"]
            self.executor_mock.reset_mock()

    def test_folder_navigation(self):
        # open reports folder
        self.engine.process_command("open reports folder")
        self.assertExecute("open_item", {"item_name": "reports"})
        self.executor_mock.reset_mock()
        
        # open reports folder in c drive kavi work degree
        self.engine.process_command("open reports folder in c drive kavi work degree")
        self.assertExecute("open_item", {"item_name": "reports", "target_folder": "c drive kavi work degree"})
        self.executor_mock.reset_mock()
        
        # open folder reports
        self.engine.process_command("open folder reports")
        self.assertExecute("open_item", {"item_name": "reports"})
        self.executor_mock.reset_mock()
        
        # open folder reports in c drive kavi work degree
        self.engine.process_command("open folder reports in c drive kavi work degree")
        self.assertExecute("open_item", {"item_name": "reports", "target_folder": "c drive kavi work degree"})
        self.executor_mock.reset_mock()

    def test_unknown_target_search_fallback(self):
        
        if True:
            self.engine.process_command("open quantum computing")
            self.assertExecute("search_web", {"query": "quantum computing"})
            self.executor_mock.reset_mock()
            
            self.engine.process_command("open kavi7605")
            self.assertExecute("search_web", {"query": "kavi7605"})
        if False:
            pass
    def test_open_test_txt_in_desktop(self):
        self.engine.process_command("open test.txt in desktop")
        self.assertExecute("open_item", {"item_name": "test.txt", "target_folder": "desktop"})
        self.executor_mock.reset_mock()

    def test_open_vscode_and_close_steam(self):
        self.task_planner_mock.plan_tasks.return_value = ["open vscode", "close steam"]
        self.parser_mock.parse_command.side_effect = [
            {"action": "open_application", "parameters": {"application_name": "vscode"}},
            {"action": "close_application", "parameters": {"application_name": "steam"}}
        ]
        self.engine.process_command("open vscode and close steam")
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.executor_mock.execute.assert_called()


