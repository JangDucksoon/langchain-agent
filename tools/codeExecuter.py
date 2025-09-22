import tempfile
import subprocess
import os
from langchain.tools import tool

@tool
def execute_python_code(code: str) -> str:
    """
        Execute {code} for only python with external module and Return the output
        <Critical!!!> Never use this tool unless explicitly instructed to run Python code!!!!

        Args:
            code(str) : python code for execution in python file

        Return:
            str: output of code execution

        Examples:
          - "print('Hello World')" → "Hello World"
          - "2 + 2" → "4"
    """
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_file = f.name

        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        os.unlink(temp_file)

        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error : time out"
    except Exception as e:
        return f"Error : {e}"

@tool
def execute_python_docker(code: str, install_script: str | None) -> str:
    """
        Execute {code} for only python with external module in docker container and Return the output
        <Critical!!!> Never use this tool unless explicitly instructed to run Python code!!!!

        Args:
            code(str) : python code for execution in python file
            install_script(str or None) : external module install script (pip install ...)

        Return:
            str: output of code execution

        Examples:
            - code: "import numpy as np; print(np.array([1,2,3]))", install_script: "pip install numpy" → "[1 2 3]"
            - code: "import requests; r = requests.get('https://api.github.com'); print(r.status_code)", install_script: "pip install requests" → "200"
    """

    image_name = "python:3.12-slim"
    try:
        image_exist = check_docker_image_exists(image_name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_file = f.name

        if install_script:
            bash_command = f"{install_script} && python /app/code.py"
        else:
            bash_command = "python /app/code.py"

        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{temp_file}:/app/code.py",
            image_name,
            "bash", "-c", bash_command
        ], capture_output=True, text=True, timeout=60, encoding="utf-8")

        os.unlink(temp_file)

        if not image_exist:
            try:
                subprocess.run(["docker", "rmi", image_name], capture_output=True, check=False)
            except Exception as e:
                pass

        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

def check_docker_image_exists(image_name):
    try:
        result = subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True)
        return bool(result.stdout.strip())
    except:
        return False