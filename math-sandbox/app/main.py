import os
import subprocess
import tempfile
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Math Sandbox API", description="A secure environment for executing Python code.")

class CodeRequest(BaseModel):
    code: str
    timeout: int = 5 # seconds
    memory_limit_mb: int = 256

class CodeResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int

@app.post("/execute", response_model=CodeResponse)
def execute_code(request: CodeRequest):
    code = request.code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as code_file:
        code_file.write(code)
        code_file_path = code_file.name

    # Inline runner script to enforce resource limits before executing the user code
    runner_script = f"""
import resource
import sys
import runpy

# Enforce resource limits
try:
    MAX_VIRTUAL_MEMORY = {request.memory_limit_mb} * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, MAX_VIRTUAL_MEMORY))

    MAX_CPU_TIME = {request.timeout}
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_TIME, MAX_CPU_TIME))

    # Prevent fork bombs
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
except Exception as e:
    print(f"Warning: Failed to set resource limits: {{e}}", file=sys.stderr)

# Execute user code
try:
    runpy.run_path({repr(code_file_path)}, run_name="__main__")
except SystemExit as e:
    sys.exit(e.code)
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as runner_file:
        runner_file.write(runner_script)
        runner_file_path = runner_file.name

    try:
        process = subprocess.Popen(
            ["python", runner_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            # Wall-clock timeout is slightly longer than CPU time limit
            stdout, stderr = process.communicate(timeout=request.timeout + 1)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            exit_code = 137 # Standard exit code for SIGKILL
            stderr += "\nExecution timed out (Wall-clock limit reached)."

    except Exception as e:
        return CodeResponse(stdout="", stderr=str(e), exit_code=-1)
    finally:
        if os.path.exists(code_file_path):
            os.remove(code_file_path)
        if os.path.exists(runner_file_path):
            os.remove(runner_file_path)

    return CodeResponse(stdout=stdout, stderr=stderr, exit_code=exit_code)

@app.get("/health")
def health_check():
    return {"status": "ok"}
