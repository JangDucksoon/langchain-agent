import subprocess
import requests
import time

def check_ollama_serving():
    response = subprocess.run(
        ["cmd", "/c", "tasklist | findstr ollama"],
        capture_output=True,
        text=True
    )

    if response.stdout:
        print("ollama is serving...")
    else:
        subprocess.Popen(
            ["ollama", "serve"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

    start = time.time()
    while time.time() - start < 15:
        try:
            resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=1)
            if resp.status_code == 200:
                print("ollama is running..")
                return True
        except requests.exceptions.RequestException:
            print("ollama is not running..")
            time.sleep(0.5)

    print("ollama serving time out")
    return False