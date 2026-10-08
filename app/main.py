from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import jobs, certificates

app = FastAPI(
    title="Certificate Generator API",
    description="API for generating certificates.",
    version="1.0.0"
)

app.include_router(jobs.router)
app.include_router(certificates.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Certificate Generator API", "environment": settings.ENVIRONMENT}
