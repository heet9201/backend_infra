from pydantic import BaseModel, EmailStr

class UserRegisterRequest(BaseModel):
    uid : str
    full_name: str
    email: EmailStr
    profile_image: str

