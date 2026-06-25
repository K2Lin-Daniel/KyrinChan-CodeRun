from pydantic import BaseModel

class CodeRequest(BaseModel):
    code: str
    timeout: int = 5 # seconds
    memory_limit_mb: int = 256
    files: dict[str, str] = {} # filename -> base64-encoded file content

class CodeResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    images: dict[str, str] = {} # filename -> base64-encoded image data URL

