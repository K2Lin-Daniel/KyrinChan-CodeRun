from fastapi import FastAPI
from api.execute import router as execute_router
from api.health import router as health_router

app = FastAPI(
    title="Python Calculation Sandbox API",
    description="A secure environment for executing general Python and scientific calculation code."
)

app.include_router(execute_router)
app.include_router(health_router)
