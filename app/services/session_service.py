import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from app.models.session_model import UserSession, UserMessage, SessionResponse, SessionHistoryResponse, SessionDetailsResponse
from app.core.firestore import db
from app.utils.logger import logger

class SessionService:
    """Service for managing user sessions"""
    
    def __init__(self):
        """Initialize the session service"""
        self.sessions_collection = db.collection("sessions")
        self.users_collection = db.collection("users")
        self.active_sessions: Dict[str, UserSession] = {}  # In-memory cache for active sessions
        
    def user_exists(self, user_id: str) -> bool:
        """
        Check if a user exists in the database
        
        Args:
            user_id: The ID of the user to check
            
        Returns:
            bool: True if the user exists, False otherwise
        """
        if not user_id:
            return False
            
        try:
            user_doc = self.users_collection.document(user_id).get()
            return user_doc.exists
        except Exception as e:
            logger.error(f"Error checking if user {user_id} exists: {e}")
            return False
    
    def get_session(self, user_id: str) -> UserSession:
        """
        Get a session for a user. If no session exists, create one.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            UserSession: The user's session
        """
        if not user_id:
            raise ValueError("User ID cannot be empty")
            
        # Skip user validation for anonymous users
        if user_id != "anonymous" and not self.user_exists(user_id):
            raise ValueError(f"User with ID {user_id} does not exist")
            
        try:
            # Check if session exists in memory cache
            for session in self.active_sessions.values():
                if session.user_id == user_id:
                    return session
            
            # Check if session exists in Firestore
            sessions_ref = self.sessions_collection.where("user_id", "==", user_id).limit(1).stream()
            
            session_docs = list(sessions_ref)
            if session_docs:
                # Session exists in Firestore, retrieve it
                session_data = session_docs[0].to_dict()
                session_id = session_docs[0].id
                
                # Convert message timestamps
                messages = []
                for msg in session_data.get("messages", []):
                    if isinstance(msg.get("timestamp"), str):
                        msg["timestamp"] = datetime.fromisoformat(msg.get("timestamp"))
                    messages.append(UserMessage(**msg))
                
                # Create session object
                session = UserSession(
                    session_id=session_id,
                    user_id=session_data.get("user_id"),
                    created_at=datetime.fromisoformat(session_data.get("created_at")) if isinstance(session_data.get("created_at"), str) else session_data.get("created_at"),
                    last_active=datetime.fromisoformat(session_data.get("last_active")) if isinstance(session_data.get("last_active"), str) else session_data.get("last_active"),
                    messages=messages,
                    language_preference=session_data.get("language_preference", "english"),
                    context=session_data.get("context", {})
                )
                
                # Cache the session
                self.active_sessions[session_id] = session
                return session
            else:
                # No session exists, create a new one
                return self.create_session(user_id)
                
        except Exception as e:
            logger.error(f"Error getting session for user {user_id}: {e}")
            # If there's an error, create a new session as fallback
            return self.create_session(user_id)
    
    def create_session(self, user_id: str) -> UserSession:
        """
        Create a new session for a user
        
        Args:
            user_id: The ID of the user
            
        Returns:
            UserSession: The newly created session
        """
        try:
            now = datetime.now()
            session_id = str(uuid.uuid4())
            
            # Create session object
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                created_at=now,
                last_active=now,
                messages=[],
                language_preference="english",
                context={}
            )
            
            # Store in Firestore
            session_dict = session.dict()
            # Convert datetime objects to strings for Firestore
            session_dict["created_at"] = session_dict["created_at"].isoformat()
            session_dict["last_active"] = session_dict["last_active"].isoformat()
            
            self.sessions_collection.document(session_id).set(session_dict)
            
            # Cache the session
            self.active_sessions[session_id] = session
            
            logger.info(f"Created new session {session_id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            # Create a memory-only session as fallback
            now = datetime.now()
            session_id = str(uuid.uuid4())
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                created_at=now,
                last_active=now,
                messages=[],
                language_preference="english",
                context={}
            )
            
            self.active_sessions[session_id] = session
            return session
    
    def update_session_context(self, session_id: str, context_update: Dict[str, Any]) -> Optional[UserSession]:
        """
        Update the context data of a session
        
        Args:
            session_id: The ID of the session
            context_update: Dictionary with context data to update
            
        Returns:
            Optional[UserSession]: The updated session, or None if the session doesn't exist
        """
        try:
            # Get the session
            if session_id not in self.active_sessions:
                # Try to get from Firestore
                session_doc = self.sessions_collection.document(session_id).get()
                if not session_doc.exists:
                    logger.warning(f"Session {session_id} not found for context update")
                    return None
                
                # Session exists in Firestore but not in memory, need to load it first
                self.get_session(session_doc.to_dict().get("user_id"))
                
            # Get the session from memory
            session = self.active_sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found in memory for context update")
                return None
            
            # Update the context
            if not session.context:
                session.context = {}
                
            # Merge the update into the existing context
            session.context.update(context_update)
            
            # Update last_active
            session.last_active = datetime.now()
            
            # Update in Firestore
            updates = {
                "context": session.context,
                "last_active": session.last_active.isoformat()
            }
            
            self.sessions_collection.document(session_id).update(updates)
            
            logger.info(f"Updated context for session {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error updating session context for {session_id}: {e}")
            return None
            
    def add_message(self, session_id: str, message: UserMessage) -> Optional[UserSession]:
        """
        Add a message to a session
        
        Args:
            session_id: The ID of the session
            message: The message to add
            
        Returns:
            Optional[UserSession]: The updated session, or None if the session doesn't exist
        """
        if not user_id:
            logger.error("Cannot add message: User ID is required")
            return ""
            
        try:
            # Get or create session
            session = self.get_session(user_id)
            
            # Create message
            message = UserMessage(
                timestamp=datetime.now(),
                content=content,
                agent_type=agent_type,
                metadata=metadata or {}
            )
            
            # Add to session
            session.messages.append(message)
            session.last_active = datetime.now()
            
            # Update Firestore
            try:
                session_dict = session.dict()
                
                # Convert datetime objects to strings for Firestore
                session_dict["last_active"] = session_dict["last_active"].isoformat()
                
                # Convert message timestamps
                for msg in session_dict["messages"]:
                    msg["timestamp"] = msg["timestamp"].isoformat()
                
                self.sessions_collection.document(session.session_id).set(session_dict)
                logger.info(f"Added message to session {session.session_id}")
            except Exception as e:
                logger.error(f"Error updating session in Firestore: {e}")
                # Continue with in-memory session even if Firestore update fails
            
            return session.session_id
            
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return ""
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[UserMessage]:
        """
        Get the message history for a user
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of messages to return (most recent first)
            
        Returns:
            List[UserMessage]: List of user messages
        """
        try:
            session = self.get_session(user_id)
            
            # Return most recent messages first, up to the limit
            return session.messages[-limit:] if len(session.messages) > limit else session.messages
            
        except Exception as e:
            logger.error(f"Error getting message history for user {user_id}: {e}")
            return []
    
    def get_session_by_id(self, session_id: str, user_id: str) -> Optional[UserSession]:
        """
        Get a session by its ID and validate that it belongs to the specified user.
        
        Args:
            session_id: The ID of the session to retrieve
            user_id: The ID of the user who should own the session
            
        Returns:
            Optional[UserSession]: The user's session if found, None otherwise
        """
        if not session_id or not user_id:
            logger.error("Session ID and User ID cannot be empty")
            return None
            
        try:
            # Check if session exists in memory cache
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                # Validate that the session belongs to the user
                if session.user_id == user_id:
                    return session
                else:
                    logger.warning(f"Session {session_id} does not belong to user {user_id}")
                    return None
            
            # Check if session exists in Firestore
            session_doc = self.sessions_collection.document(session_id).get()
            
            if session_doc.exists:
                session_data = session_doc.to_dict()
                
                # Validate that the session belongs to the user
                if session_data.get("user_id") != user_id:
                    logger.warning(f"Session {session_id} does not belong to user {user_id}")
                    return None
                
                # Convert message timestamps
                messages = []
                for msg in session_data.get("messages", []):
                    if isinstance(msg.get("timestamp"), str):
                        msg["timestamp"] = datetime.fromisoformat(msg.get("timestamp"))
                    messages.append(UserMessage(**msg))
                
                # Create session object
                session = UserSession(
                    session_id=session_id,
                    user_id=session_data.get("user_id"),
                    created_at=datetime.fromisoformat(session_data.get("created_at")) if isinstance(session_data.get("created_at"), str) else session_data.get("created_at"),
                    last_active=datetime.fromisoformat(session_data.get("last_active")) if isinstance(session_data.get("last_active"), str) else session_data.get("last_active"),
                    messages=messages,
                    language_preference=session_data.get("language_preference", "english"),
                    context=session_data.get("context", {})
                )
                
                # Cache the session
                self.active_sessions[session_id] = session
                return session
            else:
                logger.warning(f"Session {session_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting session by ID {session_id}: {e}")
            return None
    
    def clear_session(self, user_id: str) -> SessionResponse:
        """
        Clear a user's session history
        
        Args:
            user_id: The ID of the user
            
        Returns:
            SessionResponse: Response indicating success or failure
        """
        if not user_id:
            return SessionResponse(
                status="error",
                session_id="",
                message="User ID is required"
            )
            
        try:
            # Get session
            session = self.get_session(user_id)
            
            # Clear messages
            session.messages = []
            
            # Update Firestore
            try:
                session_dict = session.dict()
                # Convert datetime objects to strings for Firestore
                session_dict["created_at"] = session_dict["created_at"].isoformat()
                session_dict["last_active"] = datetime.now().isoformat()
                
                self.sessions_collection.document(session.session_id).set(session_dict)
            except Exception as e:
                logger.error(f"Error clearing session in Firestore: {e}")
            
            return SessionResponse(
                status="success",
                session_id=session.session_id,
                message="Session history cleared successfully"
            )
            
        except Exception as e:
            logger.error(f"Error clearing session for user {user_id}: {e}")
            return SessionResponse(
                status="error",
                session_id="",
                message=f"Error clearing session: {str(e)}"
            )

    def get_session_history(self, session_id: str, user_id: str, limit: int = 50) -> Optional[SessionHistoryResponse]:
        """
        Get the full session history by session ID and user ID
        
        Args:
            session_id: The ID of the session
            user_id: The ID of the user who owns the session
            limit: Maximum number of messages to return
            
        Returns:
            Optional[SessionHistoryResponse]: The session history, or None if not found
        """
        try:
            # Get the session
            session = self.get_session_by_id(session_id, user_id)
            
            if not session:
                logger.warning(f"Session {session_id} not found or does not belong to user {user_id}")
                return None
                
            # Create the response
            messages = session.messages[-limit:] if len(session.messages) > limit else session.messages
            
            return SessionHistoryResponse(
                status="success",
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at.isoformat() if isinstance(session.created_at, datetime) else str(session.created_at),
                last_active=session.last_active.isoformat() if isinstance(session.last_active, datetime) else str(session.last_active),
                language_preference=session.language_preference,
                message_count=len(session.messages),
                messages=messages,
                context_keys=list(session.context.keys()) if session.context else []
            )
            
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return None
            
    def get_all_sessions_for_user(self, user_id: str) -> List[str]:
        """
        Get all session IDs for a user
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List[str]: List of session IDs
        """
        if not user_id:
            return []
            
        try:
            # Check if the user exists (except for anonymous users)
            if user_id != "anonymous" and not self.user_exists(user_id):
                logger.warning(f"User {user_id} does not exist")
                return []
                
            # Query Firestore for all sessions for the user
            sessions_ref = self.sessions_collection.where("user_id", "==", user_id).stream()
            return [session.id for session in sessions_ref]
            
        except Exception as e:
            logger.error(f"Error getting all sessions for user {user_id}: {e}")
            return []
    
    def get_session_details(self, user_id: str) -> SessionDetailsResponse:
        """
        Get session details without messages
        
        Args:
            user_id: The ID of the user
            
        Returns:
            SessionDetailsResponse: Session details
        """
        try:
            session = self.get_session(user_id)
            
            return SessionDetailsResponse(
                status="success",
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at.isoformat() if isinstance(session.created_at, datetime) else str(session.created_at),
                last_active=session.last_active.isoformat() if isinstance(session.last_active, datetime) else str(session.last_active),
                language_preference=session.language_preference,
                message_count=len(session.messages),
                context_keys=list(session.context.keys()) if session.context else []
            )
            
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            return SessionDetailsResponse(
                status="error",
                session_id="",
                user_id=user_id,
                message_count=0
            )

# Create a global instance of the SessionService
session_service = SessionService()
