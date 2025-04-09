import unittest
import sys
from unittest.mock import patch
from javis.tools import python


class TestPython(unittest.TestCase):
    def test_run_python_code_success(self):
        # Test basic print statement
        result = python.run_python_code("print('Hello, World!')")
        self.assertEqual(result, "Hello, World!\n")
        
        # Test multiple print statements
        result = python.run_python_code("print('Line 1'); print('Line 2')")
        self.assertEqual(result, "Line 1\nLine 2\n")
        
        # Test variable assignment and printing
        result = python.run_python_code("x = 5; y = 10; print(x + y)")
        self.assertEqual(result, "15\n")
        
        # Test with a loop
        result = python.run_python_code("for i in range(3): print(i)")
        self.assertEqual(result, "0\n1\n2\n")
        
        # Test with no output
        result = python.run_python_code("x = 5")
        self.assertEqual(result, "")
        
        # Test with calculation
        result = python.run_python_code("print(sum([1, 2, 3, 4, 5]))")
        self.assertEqual(result, "15\n")
        
        # Test that stdout is properly restored
        original_stdout = sys.stdout
        python.run_python_code("print('test')")
        self.assertEqual(sys.stdout, original_stdout)
    
    def test_run_python_code_error(self):
        # Test syntax error
        result = python.run_python_code("print('Incomplete string")
        self.assertFalse(result.success)
        self.assertIn("Failed to execute Python code", result.message)
        
        # Test name error
        result = python.run_python_code("print(undefined_variable)")
        self.assertFalse(result.success)
        self.assertIn("Failed to execute Python code", result.message)
        
        # Test division by zero
        result = python.run_python_code("print(1/0)")
        self.assertFalse(result.success)
        self.assertIn("Failed to execute Python code", result.message)
    
    def test_run_shell_command_success(self):
        # Test simple echo command
        result = python.run_shell_command("echo 'Hello, World!'")
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Hello, World!", result.output)
        
        # Test command with multiple outputs
        result = python.run_shell_command("echo 'Line 1' && echo 'Line 2'")
        self.assertTrue(result.success)
        self.assertIn("Line 1", result.output)
        self.assertIn("Line 2", result.output)
    
    def test_run_shell_command_error(self):
        # Test command not found
        result = python.run_shell_command("nonexistentcommand")
        self.assertFalse(result.success)
        self.assertNotEqual(result.exit_code, 0)
        
        # Test command with error output
        result = python.run_shell_command("ls /nonexistentdirectory")
        self.assertFalse(result.success)
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.error)
    
    @patch('subprocess.run')
    def test_run_shell_command_exception(self, mock_run):
        # Test exception during command execution
        mock_run.side_effect = Exception("Command execution failed")
        result = python.run_shell_command("echo 'test'")
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, -1)
        self.assertIn("Failed to execute command", result.message)


if __name__ == "__main__":
    unittest.main()
