from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
import uuid

from ..models.session import Session
from ..services.redaction import comprehensive_redaction


logger = logging.getLogger(__name__)


class SessionStore:
    """
    In-memory session store for managing active voice sessions.
    In production, this would likely be backed by a database or cache.
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(self, session_id: Optional[str] = None) -> Session:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID, will generate if not provided
            
        Returns:
            Created session object
        """
        async with self._lock:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            if session_id in self._sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            session = Session(
                id=session_id,
                status="active",
                start_time=datetime.now(),
                version="1.0.0"
            )
            
            self._sessions[session_id] = session
            logger.info(f"Created session {session_id}")
            return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object if found, None otherwise
        """
        async with self._lock:
            return self._sessions.get(session_id)
    
    async def update_session(self, session: Session) -> None:
        """
        Update an existing session.
        
        Args:
            session: Session object to update
        """
        async with self._lock:
            if session.id not in self._sessions:
                raise ValueError(f"Session {session.id} not found")
            
            self._sessions[session.id] = session
            logger.debug(f"Updated session {session.id}")
    
    async def end_session(self, session_id: str) -> Optional[Session]:
        """
        End a session and mark it as ended.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated session object if found, None otherwise
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.end_session()
                logger.info(f"Ended session {session_id}")
                return session
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the store.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            return False
    
    async def list_active_sessions(self) -> List[Session]:
        """
        Get list of all active sessions.
        
        Returns:
            List of active session objects
        """
        async with self._lock:
            return [
                session for session in self._sessions.values() 
                if session.is_active()
            ]
    
    async def cleanup_ended_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up ended sessions older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for ended sessions
            
        Returns:
            Number of sessions cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        async with self._lock:
            sessions_to_remove = []
            
            for session_id, session in self._sessions.items():
                if (session.status == "ended" and 
                    session.end_time and 
                    session.end_time < cutoff_time):
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._sessions[session_id]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old sessions")
        
        return cleaned_count
    
    async def get_session_count(self) -> Dict[str, int]:
        """
        Get count of sessions by status.
        
        Returns:
            Dictionary with session counts by status
        """
        async with self._lock:
            counts = {"active": 0, "ended": 0, "total": len(self._sessions)}
            
            for session in self._sessions.values():
                counts[session.status] = counts.get(session.status, 0) + 1
            
            return counts