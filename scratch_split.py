import os

# 1. Read day8_part2
with open('tests/test_day8_part2.py', 'r') as f:
    part2 = f.read()

# 2. Extract folder parts
folder_part = """    def test_folder_navigation(self):
        # open reports folder
        self.engine.process_command("open reports folder")
        self.assertExecute("open_folder", {"folder_name": "reports"})
        self.executor_mock.reset_mock()
        
        # open reports folder in c drive kavi work degree
        self.engine.process_command("open reports folder in c drive kavi work degree")
        self.assertExecute("open_folder", {"folder_name": "reports", "base_path": "c drive kavi work degree"})
        self.executor_mock.reset_mock()
        
        # open folder reports
        self.engine.process_command("open folder reports")
        self.assertExecute("open_folder", {"folder_name": "reports"})
        self.executor_mock.reset_mock()
        
        # open folder reports in c drive kavi work degree
        self.engine.process_command("open folder reports in c drive kavi work degree")
        self.assertExecute("open_folder", {"folder_name": "reports", "base_path": "c drive kavi work degree"})
        self.executor_mock.reset_mock()

    def test_open_test_txt_in_desktop(self):
        self.engine.process_command("open test.txt in desktop")
        self.assertExecute("open_file", {"file_name": "test.txt", "path": "desktop"})
        self.executor_mock.reset_mock()"""

# 3. Append to router regressions
with open('tests/regression/test_day8_router_regressions.py', 'a') as f:
    f.write('\n' + folder_part)

# 4. Remove folder parts from part2
part2 = part2.replace(folder_part, '')

# 5. Append remaining part2 to search regressions
with open('tests/regression/test_day8_search_regressions.py', 'a') as f:
    f.write('\n' + part2.replace('class TestDay8Part2(unittest.TestCase):', 'class TestDay8SearchPart2(unittest.TestCase):').replace('if __name__ == "__main__":\n    unittest.main()', ''))

# 6. Delete part2
os.remove('tests/test_day8_part2.py')
