from fastapi import FastAPI
from app.routes import user
from app.routes import health
from app.routes import agent
from app.routes import session

app = FastAPI(title="Sahayak - AI Teaching Assistant API")

app.include_router(user.router, prefix="/user")
app.include_router(health.router, prefix="/health")
app.include_router(agent.router, prefix="/agent", tags=["AI Teaching Assistant"])
app.include_router(session.router, prefix="/session", tags=["User Sessions"])

# No need for uvicorn.run() in production, App Engine handles this.
