import io
import sys
import subprocess
from typing import Union

from pydantic import BaseModel

__all__ = [
    "run_python_code",
    "run_shell_command",
]


class CommandResult(BaseModel):
    success: bool
    output: str
    error: str
    exit_code: int
    message: str
    

def run_python_code(code: str) -> Union[str, CommandResult]:
    """Run Python code and return its output.

    Args:
        code (str): The Python code to execute.

    Returns:
        Union[str, CommandResult]: The output of the executed code as a string if successful,
            or a CommandResult with error details if the operation failed.
    """
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    try:
        exec(code)
        output = new_stdout.getvalue()
        return output
    except Exception as e:
        return CommandResult(
            success=False,
            output="",
            error=str(e),
            exit_code=-1,
            message=f"Failed to execute Python code: {str(e)}"
        )
    finally:
        sys.stdout = old_stdout


def run_shell_command(command: str) -> CommandResult:
    """Run a shell command and return the result.

    Args:
        command (str): The shell command to execute.

    Returns:
        CommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if command executed successfully
            - output: Standard output from the command
            - error: Standard error from the command
            - exit_code: Exit code returned by the command
            - message: Description of the operation result
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            text=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        return CommandResult(
            success=result.returncode == 0,
            output=result.stdout,
            error=result.stderr,
            exit_code=result.returncode,
            message=f"Command executed with exit code {result.returncode}"
        )
    except Exception as e:
        return CommandResult(
            success=False,
            output="",
            error=str(e),
            exit_code=-1,
            message=f"Failed to execute command: {str(e)}"
        )
