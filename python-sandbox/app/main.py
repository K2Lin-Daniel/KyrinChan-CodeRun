import os
import shutil
from fastapi import FastAPI
from api.execute import router as execute_router
from api.health import router as health_router

app = FastAPI(
    title="Stellarator Engine - Python Calculation Sandbox API",
    description="A secure environment for executing general Python and scientific calculation code."
)

@app.on_event("startup")
def startup_event():
    # Copy prebuilt matplotlib config and font cache to a shared writable location in tmpfs once on startup
    src = "/home/sandboxuser/.matplotlib"
    dst = "/tmp/.matplotlib"
    if os.path.isdir(src) and not os.path.exists(dst):
        try:
            shutil.copytree(src, dst, copy_function=shutil.copy)
        except Exception:
            pass

app.include_router(execute_router)
app.include_router(health_router)
