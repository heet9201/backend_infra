from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.get("/")
async def health_check():
    try:
        return {"status": "success", "user_id": "Jai Shree Krishna"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
