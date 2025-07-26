from fastapi import APIRouter, HTTPException
from app.models.user_model import UserRegisterRequest
from app.services.user_service import register_user

router = APIRouter()

@router.post("/register")
async def register_user_route(user: UserRegisterRequest):
    try:
        result = register_user(user)
        return {"status": "success", "user_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
