from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class ContextManager:
    """
    Manages rolling context buffer for voice sessions.
    Maintains recent conversation turns and truncates when exceeding limits.
    """
    
    def __init__(self, max_turns: int = 10, max_tokens: Optional[int] = None):
        """
        Initialize context manager.
        
        Args:
            max_turns: Maximum number of turns to keep in context
            max_tokens: Optional maximum token count (simplified estimation)
        """
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.turns: List[Dict[str, Any]] = []
    
    def add_turn(self, turn_type: str, content: str, speaker: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a turn to the context.
        
        Args:
            turn_type: Type of turn ("user" or "agent")
            content: Content of the turn
            speaker: Optional speaker identifier
            metadata: Optional additional metadata
        """
        turn = {
            "id": str(uuid.uuid4()),
            "type": turn_type,
            "content": content,
            "speaker": speaker or turn_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.turns.append(turn)
        self._enforce_limits()
    
    def add_user_utterance(self, text: str, confidence: float = 1.0, interrupted: bool = False) -> None:
        """Add a user utterance to context."""
        metadata = {
            "confidence": confidence,
            "interrupted": interrupted,
            "word_count": len(text.split())
        }
        self.add_turn("user", text, speaker="user", metadata=metadata)
    
    def add_agent_response(self, text: str, agent_name: str = "assistant", tools_used: Optional[List[str]] = None) -> None:
        """Add an agent response to context."""
        metadata = {
            "agent": agent_name,
            "tools_used": tools_used or [],
            "word_count": len(text.split())
        }
        self.add_turn("agent", text, speaker=agent_name, metadata=metadata)
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get current context information.
        
        Returns:
            Dictionary containing turns, counts, and truncation status
        """
        return {
            "turns": self.turns.copy(),
            "total_turns": len(self.turns),
            "truncated": len(self.turns) == self.max_turns and self.max_turns > 0,
            "estimated_tokens": self._estimate_tokens(),
            "last_updated": datetime.now().isoformat()
        }
    
    def get_recent_turns(self, count: int) -> List[Dict[str, Any]]:
        """Get the most recent N turns."""
        return self.turns[-count:] if count > 0 else []
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        user_turns = [t for t in self.turns if t["type"] == "user"]
        agent_turns = [t for t in self.turns if t["type"] == "agent"]
        
        return {
            "total_turns": len(self.turns),
            "user_turns": len(user_turns),
            "agent_turns": len(agent_turns),
            "duration_covered": self._calculate_duration(),
            "avg_confidence": self._calculate_avg_confidence(),
            "interruptions": len([t for t in self.turns if t.get("metadata", {}).get("interrupted")])
        }
    
    def clear_context(self) -> None:
        """Clear all context."""
        self.turns = []
    
    def _enforce_limits(self) -> None:
        """Enforce context limits by truncating oldest turns."""
        # Enforce turn limit
        if self.max_turns and len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
        
        # Enforce token limit (simplified)
        if self.max_tokens:
            while len(self.turns) > 1 and self._estimate_tokens() > self.max_tokens:
                self.turns.pop(0)  # Remove oldest turn
    
    def _estimate_tokens(self) -> int:
        """
        Estimate token count for all turns.
        Simple approximation: ~1.3 tokens per word.
        """
        total_words = sum(
            len(turn["content"].split()) 
            for turn in self.turns
        )
        return int(total_words * 1.3)
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate duration covered by current context."""
        if len(self.turns) < 2:
            return None
        
        try:
            first_time = datetime.fromisoformat(self.turns[0]["timestamp"])
            last_time = datetime.fromisoformat(self.turns[-1]["timestamp"])
            return (last_time - first_time).total_seconds()
        except (ValueError, KeyError):
            return None
    
    def _calculate_avg_confidence(self) -> Optional[float]:
        """Calculate average confidence for user turns."""
        user_confidences = [
            turn.get("metadata", {}).get("confidence")
            for turn in self.turns
            if turn["type"] == "user" and turn.get("metadata", {}).get("confidence") is not None
        ]
        
        if not user_confidences:
            return None
        
        return sum(user_confidences) / len(user_confidences)