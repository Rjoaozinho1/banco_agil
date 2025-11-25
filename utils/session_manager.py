"""
Manages session state and customer data
"""

from typing import Optional, Dict

class SessionManager:
    """Manages session state across agent interactions"""
    
    def __init__(self):
        # Authentication state
        self.authenticated: bool = False
        self.customer_cpf: Optional[str] = None
        self.customer_data: Optional[Dict] = None
        self.auth_attempts: int = 0

        # Agent routing
        self.current_agent: str = "triage"

        # Triage state
        self.cpf_collected: bool = False
        self.birthdate_collected: bool = False
        self.temp_cpf: Optional[str] = None

        # Interview state
        self.interview_data: Dict = {}
        self.interview_step: int = 0

        # Credit state
        self.pending_credit_request: bool = False
        self.requested_limit: Optional[float] = None

        # Conversation state
        self.should_end: bool = False
        self.last_agent: Optional[str] = None

    def reset(self):
        """Reset session to initial state"""
        self.__init__()
    
    def set_customer_data(self, cpf: str, data: Dict):
        """Set authenticated customer data"""
        self.authenticated = True
        self.customer_cpf = cpf
        self.customer_data = data
        self.auth_attempts = 0
    
    def increment_auth_attempts(self):
        """Increment authentication attempt counter"""
        self.auth_attempts += 1
    
    def can_retry_auth(self) -> bool:
        """Check if customer can retry authentication"""
        return self.auth_attempts < 3
    
    def switch_agent(self, agent_name: str):
        """Switch to a different agent"""
        self.last_agent = self.current_agent
        self.current_agent = agent_name
    
    def get_customer_score(self) -> float:
        """Get customer's current credit score"""
        if self.customer_data:
            return float(self.customer_data.get('score', 0))
        return 0.0
    
    def get_customer_limit(self) -> float:
        """Get customer's current credit limit"""
        if self.customer_data:
            return float(self.customer_data.get('limite_credito', 0))
        return 0.0
    
    def update_customer_score(self, new_score: float):
        """Update customer's credit score"""
        if self.customer_data:
            self.customer_data['score'] = new_score