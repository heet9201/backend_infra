import uuid
from app.models.user_model import UserRegisterRequest
from app.core.firestore import add_user_to_firestore

def register_user(user: UserRegisterRequest):
    user_id = str(uuid.uuid4())
    user_data = {
        "uid" : user.uid,
        "full_name": user.full_name,
        "email": user.email,
        "profile_image": user.profile_image,
        "uid": user_id,
    }
    return add_user_to_firestore(user_id, user_data)
