from app.core.firebase import db

def add_user_to_firestore(user_id: str, user_data: dict):
    users_ref = db.collection("users").document(user_id)
    users_ref.set(user_data, merge=True)
    return user_id
