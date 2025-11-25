"""
Triage agent for authentication and routing
"""

import re
from datetime import datetime
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from agents.interview_agent import InterviewAgent
from agents.credit_agent import CreditAgent
from agents.exchange_agent import ExchangeAgent
from tools.customer_tools import AuthenticateCustomerTool
from config import GROQ_API_KEY, GROQ_MODEL

class TriageAgent:
    """Agent responsible for customer authentication and initial routing"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )

        self.tools = [AuthenticateCustomerTool()]

        self.auth_tool = AuthenticateCustomerTool()

        system_prompt = """"
        Você é o Assistente de Triagem do Banco Ágil.

        Seu objetivo principal é AUTENTICAR o usuário.

        Regras:
        1. Para autenticar, você PRECISA do CPF e da Data de Nascimento.
        2. Se o usuário não fornecer um dos dois, PEÇA educadamente.
        3. Assim que tiver os dois dados, USE IMEDIATAMENTE a ferramenta 'authenticate_customer'.
        4. Se a ferramenta retornar erro, explique o erro ao usuário e peça os dados corretos.
        5. Se a ferramenta retornar sucesso, dê as boas vindas.
        6. Quando o usuario ja estiver autenticado, indentifique-o e redirecione para o próximo passo.

        Não tente adivinhar dados. Não invente CPFs. Somente use a ferramenta quando obtiver os dois dados necessários.
        """

        sp = SystemMessage(system_prompt)

        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=sp
        )
        self.agent_executor = agent

    def process(self, message: str, session_manager) -> str:
        """Main process loop"""

        if session_manager.authenticated:
            return self._handle_routing(message, session_manager)

        try:
            print(f"Triagem Agent input: {message}")

            response = self.agent_executor.invoke({"input": message})

            print(f"Triagem Agent response: {response}")

            agent_output_text = response["messages"][-1].content

            print(f"Triagem Agent output: {agent_output_text}")

            return agent_output_text

        except Exception as e:
            print(f"Erro no TriageAgent: {e}")
            return "Desculpe, tive um problema técnico. Poderia repetir?"
        
    def _handle_routing(self, message: str, session_manager) -> str:
        """Handle routing based on user intent"""

        prompt_classification = (
            f"O usuário disse: '{message}'. Classifique a intenção em APENAS uma destas palavras: "
            "cambio, credito, entrevista, outros. Responda apenas com a palavra."
        )

        try:
            intent = self.llm.invoke(prompt_classification).content.strip().lower()
            print(f"🔀 Intent Routing: {intent}")

            if "cambio" in intent:
                session_manager.switch_agent("cambio")
                agent = ExchangeAgent()
                return agent.process(message, session_manager)
            
            elif "credito" in intent:
                session_manager.switch_agent("credito")
                agent = CreditAgent()
                return agent.process(message, session_manager)
            
            elif "entrevista" in intent:
                session_manager.switch_agent("entrevista")
                agent = InterviewAgent()
                return agent.process(message, session_manager)

            else:
                return "Entendi. Posso ajudar especificamente com Câmbio ou Crédito. Qual prefere?"
        except Exception:
            print(f"Erro no TriageAgent: {e}")
            return "Não entendi. Você quer falar sobre Câmbio ou Crédito?"