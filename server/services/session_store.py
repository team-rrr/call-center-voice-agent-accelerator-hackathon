from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
import uuid

from models.session import Session
from services.redaction import comprehensive_redaction


logger = logging.getLogger(__name__)


class SessionStore:
    """
    In-memory session store for managing active voice sessions.
    
    This class provides thread-safe operations for creating, retrieving, updating,
    and managing voice interaction sessions. In production deployments, this would
    typically be backed by a distributed cache (Redis) or database for persistence
    and scalability across multiple service instances.
    
    The store handles:
    - Session lifecycle management (create, retrieve, update, delete)
    - Concurrent access protection via async locks
    - Automatic session cleanup and expiration
    - Session statistics and metadata tracking
    
    Attributes:
        _sessions: Internal dictionary mapping session IDs to Session objects
        _lock: Async lock for thread-safe operations
        
    Thread Safety:
        All public methods are async and use internal locking to ensure
        thread-safe operations in concurrent environments.
        
    Example:
        >>> store = SessionStore()
        >>> session = await store.create_session()
        >>> retrieved = await store.get_session(session.id)
        >>> await store.end_session(session.id)
    """
    
    def __init__(self) -> None:
        """
        Initialize the session store with empty session dictionary and lock.
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        logger.info("SessionStore initialized")
    
    async def create_session(self, session_id: Optional[str] = None) -> Session:
        """
        Create a new voice interaction session.
        
        Creates a new session with a unique identifier and initializes it in
        'active' status. If no session_id is provided, a UUID4 will be generated.
        
        Args:
            session_id: Optional session identifier. If None, a UUID4 is generated.
            
        Returns:
            Session: The newly created session object with 'active' status
            
        Raises:
            ValueError: If the provided session_id already exists
            
        Example:
            >>> session = await store.create_session()
            >>> print(session.id)  # UUID4 string
            >>> print(session.status)  # "active"
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
            logger.info(
                "Created new session",
                extra={
                    "session_id": session_id,
                    "start_time": session.start_time.isoformat(),
                    "total_sessions": len(self._sessions)
                }
            )
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