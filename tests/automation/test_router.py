import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSemanticRouting:
    def test_1_open_github_bypasses_parser_and_planner(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_application"
        assert call_args["parameters"]["application_name"] == "github"

    def test_2_open_github_website_routes_to_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github website")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_url"
        assert call_args["parameters"]["url"] == "https://github.com"

    def test_3_open_github_website_python_projects_single_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github website python projects")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_url"
        assert call_args["parameters"]["url"] == "https://github.com/search?q=python+projects&type=repositories"

    def test_4_open_youtube_website_ghost_of_yotei_single_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open youtube website ghost of yotei")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_url"
        assert call_args["parameters"]["url"] == "https://www.youtube.com/results?search_query=ghost+of+yotei"

    def test_5_open_domain_name_routes_to_url(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("open github.com")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "open_url"
        assert call_args["parameters"]["url"] == "https://github.com"

    def test_6_create_test_txt_routes_to_create_file(self):
        self.executor_mock.execute.return_value = {"status": "success", "message": "Success"}
        self.engine.process_command("create test.txt")
        
        self.task_planner_mock.plan_tasks.assert_not_called()
        self.parser_mock.parse_command.assert_not_called()
        
        call_args = self.executor_mock.execute.call_args[0][0]
        assert call_args["action"] == "create_file"
        assert call_args["parameters"]["file_name"] == "test.txt"


