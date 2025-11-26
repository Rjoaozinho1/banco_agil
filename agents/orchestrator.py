"""
Main orchestrator for routing messages to appropriate agents
"""

from agents.triage_agent import TriageAgent
from agents.credit_agent import CreditAgent
from agents.interview_agent import InterviewAgent
from agents.exchange_agent import ExchangeAgent
from utils.session_manager import SessionManager


class AgentOrchestrator:
    """Simple orchestrator that routes messages to the appropriate agent"""
    
    def __init__(self):
        self.triage_agent: TriageAgent = TriageAgent()
        self.credit_agent: CreditAgent = CreditAgent()
        self.interview_agent: InterviewAgent = InterviewAgent()
        self.exchange_agent: ExchangeAgent = ExchangeAgent()
        
    def process_message(self, message: str, session_manager: SessionManager) -> str:
        """
        Process user message and route to appropriate agent
        
        Args:
            message: User's message
            session_manager: Session state manager
            
        Returns:
            Agent's response
        """

        current_agent = session_manager.current_agent
        print(f"Current agent: {current_agent}")

        if self._is_goodbye_message(message):
            return self._handle_goodbye(session_manager)

        if current_agent == "triagem":
            print(f"Triagem message: {message}")
            return self.triage_agent.process(message, session_manager)

        elif current_agent == "credito":
            print(f"Crédito message: {message}")
            return self.credit_agent.process(message, session_manager)

        elif current_agent == "entrevista":
            print(f"Entrevista message: {message}")
            return self.interview_agent.process(message, session_manager)

        elif current_agent == "cambio":
            print(f"Câmbio message: {message}")
            return self.exchange_agent.process(message, session_manager)

        else:
            return "Desculpe, não entendi. Por favor, tente novamente."

    def _is_goodbye_message(self, message: str) -> bool:
        """Check if user wants to end conversation"""
        goodbye_keywords = [
            "obrigado", "tchau", "adeus", "até logo", "finalizar", "encerrar",
            "sair", "desligar", "terminar", "acabar", "bye"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in goodbye_keywords)
    
    def _handle_goodbye(self, session_manager: SessionManager) -> str:
        """Handle conversation end"""
        session_manager.end_session()
        return """Obrigado por utilizar os serviços do Banco Ágil! 

        Foi um prazer atendê-lo. Tenha um ótimo dia! 👋

        (Para iniciar uma nova conversa, clique em "Reiniciar Conversa" na barra lateral)"""
