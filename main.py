from fastapi import FastAPI
from app.routes import user
from app.routes import health

app = FastAPI(title="Agentic Backend API")

app.include_router(user.router, prefix="/user")
app.include_router(health.router, prefix="/health")

# No need for uvicorn.run() in production, App Engine handles this.
