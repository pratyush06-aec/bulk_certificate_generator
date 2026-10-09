from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from app.core.config import settings
from app.api.routes import jobs, certificates

app = FastAPI(
    title="Certificate Generator API",
    description="API for generating certificates.",
    version="1.0.0",
    docs_url=None,
)

app.include_router(jobs.router)
app.include_router(certificates.router)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_favicon_url="/favicon.png"
    )

@app.get("/favicon.png", include_in_schema=False)
async def favicon():
    return FileResponse("assets/fav_icon.png")

@app.get("/")
def read_root():
    return {"message": "Welcome to Certificate Generator API", "environment": settings.ENVIRONMENT}
