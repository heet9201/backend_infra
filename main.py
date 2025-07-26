from fastapi import FastAPI
import uvicorn
from app.routes import user

app = FastAPI(title="Agentic Backend API")

app.include_router(user.router, prefix="/user")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
