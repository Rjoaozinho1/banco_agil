"""
Triage agent for authentication and routing
"""

import json
from langchain_groq import ChatGroq
from tools.customer_tools import authenticate_customer
from utils.session_manager import SessionManager
from config import GROQ_API_KEY, GROQ_MODEL


class TriageAgent:
    """Agent responsible for customer authentication and initial routing"""


    def __init__(self):

        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )

        self.tools = [authenticate_customer]
        self.auth_tool = authenticate_customer

        self.system_prompt = """Você é o Agente de Triagem do Banco Ágil.

        OBJETIVO: Autenticar o cliente usando a ferramenta 'authenticate_customer' com os dados presentes na mensagem do usuário.

        REGRAS CRÍTICAS:
        - SEMPRE use a ferramenta 'authenticate_customer' quando ambos os dados estiverem na mensagem.
        - NUNCA invente, infira ou reutilize dados sem o usuário informar novamente.
        """

        self.auth_prompt = """
        Você é o Agente de Triagem do Banco Ágil.
        - Após o usuário estar autenticado, pergunte: "Como posso ajudá-lo hoje? Posso auxiliar com Crédito ou Câmbio?"
        """

        self.classification_prompt = """Analise a mensagem do cliente e identifique a intenção.

        Mensagem: "{message}"

        Responda APENAS com uma destas palavras:
        - credito: se o cliente quer consultar limite, pedir aumento de crédito
        - cambio: se o cliente quer consultar cotação de moedas, dólar, câmbio
        - entrevista: se o cliente quer fazer entrevista de crédito, atualizar score
        - outros: se não se enquadra nas opções acima

        Resposta (apenas uma palavra):"""

        self.runnable = self.llm.bind_tools(self.tools)


    def process(self, message: str, session_manager: SessionManager) -> str:
        """Main process loop with authentication control"""

        print(f"""[TriageAgent] Status - Auth: {session_manager.authenticated}, Attempts: {session_manager.auth_attempts}""")

        if session_manager.authenticated:
            return self._handle_routing(message, session_manager)

        if session_manager.auth_attempts >= 3:
            return self._handle_max_attempts_exceeded(session_manager)

        try:
            print(f"[TriageAgent] Input context: {session_manager.get_session_history()}")

            full_input = []

            if len(session_manager.get_session_history()) >= 1:
                full_input = [
                    ("system", self.system_prompt), 
                    ("user", message),
                ]
            else:
                for msg in session_manager.get_session_history():
                    full_input.append((msg["role"], msg["content"]))
                full_input.append(("user", message))

            print(f"[TriageAgent] Full input: {full_input}")

            result = self.runnable.invoke(full_input)
            
            print(f"[TriageAgent] Triage agent result: {result}")

            auth_success = False            
            if result.content == "" and result.additional_kwargs.get("tool_calls")[0].get("function").get("name") == "authenticate_customer":
                auth_success = self._process_auth_result(
                    result.additional_kwargs.get("tool_calls")[0].get("function").get("arguments"),
                    session_manager,
                )

                if auth_success:
                    client_data = session_manager.customer_data
                    result = self.llm.invoke([
                        ("system", self.auth_prompt),
                        ("system", f"✅ Autenticação bem-sucedida! O cliente {client_data} foi autenticado."),
                    ])
                    return result.content

            if not auth_success:
                session_manager.increment_auth_attempts()
                print(f"[TriageAgent] Incrementing auth attempts: {session_manager.auth_attempts}")

            return result.content

        except Exception as e:
            print(f"[TriageAgent] Error: {e}")
            return "Desculpe, ocorreu um erro técnico. Por favor, tente novamente."


    def _process_auth_result(self, tool_message: dict, session_manager: SessionManager) -> bool:
        """
        Process authentication result from tool invocation
        """

        try:
            session_manager.increment_auth_attempts()
            print(f"[TriageAgent] Processing auth result: {tool_message}")

            result_data = json.loads(tool_message)
            print(f"[TriageAgent] Parsed result data: {result_data}")

            if result_data.get("cpf"):

                result = self.auth_tool.invoke({
                    "cpf": result_data.get("cpf"),
                    "birthdate": result_data.get("birthdate"),
                })
                print(f"[TriageAgent] Auth tool result: {result}")

                session_manager.set_customer_data(
                    cpf=result_data.get("cpf"),
                    data=result
                )
                session_manager.reset_auth_attempts()
                print("[TriageAgent] ✅ Auth successful")
                return True
            else:
                print(f"[TriageAgent] ❌ Auth failed: {result_data.get('message')}")
                return False
                
        except Exception as e:
            print(f"[TriageAgent] Error processing auth result: {e}")
            return False


    def _handle_max_attempts_exceeded(self, session_manager: SessionManager) -> str:
        """Handle max authentication attempts exceeded"""

        print("[TriageAgent] Max Auth Attempts Exceeded")
        session_manager.end_session()
        return (
            "Lamento, mas não foi possível autenticar seus dados após 3 tentativas. "
            "Por favor, verifique suas informações e tente novamente mais tarde. "
            "Se precisar de ajuda, entre em contato com nossa central de atendimento. "
            "Tenha um ótimo dia! 👋"
        )


    def _handle_routing(self, message: str, session_manager: SessionManager) -> str:
        """
        Route to appropriate agent after authentication
        """
        print(f"[TriageAgent] Routing authenticated customer: {message}")

        prompt_classification = self.classification_prompt.format(message=message)

        try:
            intent = self.llm.invoke(prompt_classification).content.strip().lower()
            print(f"[TriageAgent] Identified intent: {intent}")

            if "credito" in intent:
                from agents.credit_agent import CreditAgent
                session_manager.switch_agent("credito")
                agent = CreditAgent()
                return agent.process(message, session_manager)
            
            elif "cambio" in intent:
                from agents.exchange_agent import ExchangeAgent
                session_manager.switch_agent("cambio")
                agent = ExchangeAgent()
                return agent.process(message, session_manager)
            
            elif "entrevista" in intent:
                from agents.interview_agent import InterviewAgent
                session_manager.switch_agent("entrevista")
                agent = InterviewAgent()
                return agent.process(message, session_manager)
            
            else:
                return (
                    f"Olá! Estou aqui para ajudar. "
                    f"Posso auxiliá-lo com:\n"
                    f"• 💳 Crédito (consulta de limite e solicitação de aumento)\n"
                    f"• 💱 Câmbio (cotação de moedas)\n\n"
                    f"Como posso ajudá-lo?"
                )

        except Exception as e:
            print(f"[TriageAgent] Error routing intent: {e}")
            return "Posso ajudá-lo com Crédito ou Câmbio. O que prefere?"
