"""
Manages session state and customer data
"""

from typing import Optional, Dict, Any
from datetime import datetime

class SessionManager:
    """Manages session state across agent interactions"""
    
    def __init__(self):
        # Authentication state
        self.authenticated: bool = False
        self.customer_cpf: Optional[str] = None
        self.customer_data: Optional[Dict] = None
        self.auth_attempts: int = 0
        self.max_auth_attempts = 3

        # History
        self.messages: list = []

        # Agent routing
        self.current_agent: str = "triagem"
        self.agent_history = ["triagem"]

        # Session timing
        self.session_start = datetime.now()
        self.session_ended = False

        # Interview state
        self.interview_data: Dict = {}
        self.interview_step: int = 0

    def reset(self):
        """Reset session to initial state"""
        self.__init__()
    
    def set_customer_data(self, cpf: str, data: str) -> None:
        """Set authenticated customer data"""
        import json
        self.authenticated = True
        self.customer_cpf = cpf
        self.customer_data = json.loads(data)
        self.auth_attempts = 0
        print(f"[SessionManager] Authenticated Client: {self.customer_cpf}")
        print(f"[SessionManager] Data: {self.customer_data}")

    def increment_auth_attempts(self) -> None:
        """Increment authentication attempt counter"""
        self.auth_attempts += 1

    def get_remaining_attempts(self) -> int:
        """Return number of remaining authentication attempts"""
        return max(0, self.max_auth_attempts - self.auth_attempts)
    
    def reset_auth_attempts(self) -> None:
        """Reset authentication attempt counter"""
        self.auth_attempts = 0
        print("[SessionManager] Authentication attempts reset")

    def can_retry_auth(self) -> bool:
        """Check if customer can retry authentication"""
        return self.auth_attempts < self.max_auth_attempts
    
    def switch_agent(self, agent_name: str):
        """Switch to a different agent"""
        if self.current_agent != agent_name:
            print(f"[SessionManager] Transition: {self.current_agent} -> {agent_name}")
            self.current_agent = agent_name
            self.agent_history.append(agent_name)
    
    def get_customer_score(self) -> float:
        """Get customer's current credit score"""
        if self.customer_data:
            return float(self.customer_data["score"])
        return 0

    def get_customer_limit(self) -> float:
        """Get customer's current credit limit"""
        if self.customer_data:
            return float(self.customer_data["limite_credito"])
        return 0.0
    
    def update_customer_limit(self, new_limit: float) -> None:
        """Update customer's credit limit"""
        if self.customer_data:
            old_limit = float(self.customer_data["limite_credito"])
            self.customer_data["limite_credito"] = new_limit
            print(f"[SessionManager] Updated Limit: {old_limit} -> {new_limit}")
        else:
            print("[SessionManager] ⚠️ Update Limit Failed: No Customer Data")
    
    def update_customer_score(self, new_score: float) -> None:
        """Update customer's credit score"""
        if self.customer_data:
            old_score = float(self.customer_data["score"])
            self.customer_data["score"] = new_score
            print(f"[SessionManager] Updated Score: {old_score} -> {new_score}")
        else:
            print("[SessionManager] ⚠️ Update Score Failed: No Customer Data")
    
    def end_session(self) -> None:
        """End the session"""
        self.session_ended = True
        session_duration = datetime.now() - self.session_start
        print(f"[SessionManager] Session ended. Duration: {session_duration}")

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session history"""
        self.messages.append({"role": role, "content": content})

    def get_session_history(self) -> list:
        """Return the session history"""
        return self.messages
