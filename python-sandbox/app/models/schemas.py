from pydantic import BaseModel

class CodeRequest(BaseModel):
    code: str
    timeout: int = 5 # seconds
    memory_limit_mb: int = 256

class CodeResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
