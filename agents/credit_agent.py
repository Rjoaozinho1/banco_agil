"""
Credit agent for credit limit queries and increase requests
"""

from utils.session_manager import SessionManager
from langchain_groq import ChatGroq
from tools.credit_tools import check_credit_limit, request_credit_increase
from config import GROQ_API_KEY, GROQ_MODEL

class CreditAgent:
    """Agent responsible for credit limit operations"""

    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0,
        )

        self.tools = [check_credit_limit, request_credit_increase]
        
        self.runnable = self.llm.bind_tools(self.tools)

        self.system_prompt = (
            "Você é um assistente de crédito do Banco Ágil. "
            "Identifique a intenção: consulta de limite ou solicitação de aumento. "
            "Para CONSULTA, use 'check_credit_limit'. Para AUMENTO, use 'request_credit_increase' quando o valor estiver informado; "
            "se não estiver, pergunte: 'Qual valor de limite você gostaria?'. "
            "Atualização de score NÃO é feita por aqui: se o cliente solicitar atualizar score, responda exatamente com "
            "'ROTA_ENTREVISTA|Para atualizar seu score, precisamos realizar uma entrevista rápida.' "
            "Se o aumento for NEGADO, responda exatamente com: 'ROTA_ENTREVISTA|Infelizmente não foi possível aprovar o aumento. Que tal responder algumas perguntas para reavaliarmos?'. "
            "Sempre use as ferramentas antes de responder e mantenha cordialidade e objetividade."
        )

    def _should_route_to_interview(self, response: str) -> tuple[bool, str]:
        """
        Check if the response should route to the interview agent.
        Returns: (should_route, cleaned_message)
        """
        if "ROTA_ENTREVISTA|" in response:
            parts = response.split("ROTA_ENTREVISTA|", 1)
            return True, parts[1] if len(parts) > 1 else "Vamos fazer uma entrevista?"
        return False, response

    def _build_context(self, session_manager: SessionManager) -> str:
        """Builds a structured context for the agent, including CPF, credit score, and current limit."""
        return f"""
        === CONTEXTO DO CLIENTE ===
        CPF: {session_manager.customer_cpf}
        Score de Crédito: {session_manager.get_customer_score()}
        Limite Atual: R$ {session_manager.get_customer_limit():.2f}
        ==========================
        """

    def process(self, message: str, session_manager: SessionManager) -> str:
        """Process message in credit agent"""

        print(f"[CreditAgent] Received message: {message}")

        if "entrevista" in message.lower():
            from agents.interview_agent import InterviewAgent
            print("[CreditAgent] Routing: handle_interview")
            session_manager.switch_agent("entrevista")
            agent = InterviewAgent()
            return agent.process(message, session_manager)

        try:
            context = self._build_context(session_manager)
            full_input = [("system", self.system_prompt), ("system", context)]

            try:
                history = session_manager.get_session_history()
                print(f"[CreditAgent] Session history: {history}")
                for msg in history:
                    full_input.append((msg.get("role"), msg.get("content")))
            except Exception as e:
                print(f"[CreditAgent] Error reading history: {e}")
            full_input.append(("user", message))

            print(f"[CreditAgent] Full input: {full_input}")

            result = self.runnable.invoke(full_input)

            print(f"[CreditAgent] LLM result: {result}")
            if result.content:
                should_route, clean_response = self._should_route_to_interview(result.content)
                if should_route:
                    print("[CreditAgent] Routing to InterviewAgent via marker")
                    session_manager.switch_agent("entrevista")
                    interview_agent = InterviewAgent()
                    return interview_agent.process(message, session_manager)
                return clean_response

            tool_calls = result.additional_kwargs.get("tool_calls")
            if tool_calls:
                import json
                tc = tool_calls[0]
                fn = tc.get("function", {})
                name = fn.get("name")
                args = json.loads(fn.get("arguments", "{}"))

                if name == "check_credit_limit":
                    out = check_credit_limit.invoke({"cpf": args.get("cpf", session_manager.customer_cpf)})
                    try:
                        data = json.loads(out)
                        if data.get("error"):
                            return f"Desculpe, não foi possível consultar: {data['error']}"
                        return (
                            f"Seu limite atual é R$ {data['limite_credito']:.2f} e seu score é {data['score']:.0f}. "
                            f"Posso ajudá-lo com solicitação de aumento?"
                        )
                    except Exception:
                        return str(out)

                if name == "request_credit_increase":
                    out = request_credit_increase.invoke({
                        "cpf": args.get("cpf", session_manager.customer_cpf),
                        "requested_limit": args.get("requested_limit")
                    })
                    try:
                        data = json.loads(out)
                        if data.get("error"):
                            return f"Não foi possível processar o aumento: {data['error']}"
                        if data.get("status") == "rejeitado":
                            print(f"[CreditAgent] Rejected increase request")
                            reject_response = self.llm.invoke([
                                ("system", 
                                "Você é um assistente de crédito do Banco Ágil. "
                                "O cliente requisitou um aumento no limite dele e o aumento de limite foi negado."
                                "Responde de uma forma amigavel sem saudacao, pois a conversa ja esta acontecendo, que o cliente entenda que o pedido dele foi negado (exemplifique), e que seja necessario fazer uma entrevista, AGORA, somente seguir o fluxo para reavaliar o status do seu pedido"
                                "Sem oferecer nada fora do escopo, que e uma entrevista"
                                "Exemplifique ao usuario que se ele deseja fazer a entrevista ele PRECISA digitar a palavra entrevista"
                                ),
                            ])
                            return reject_response.content
                        return (
                            f"Aumento aprovado! Seu novo limite é R$ {data['limite_atual']:.2f}. "
                            f"Deseja mais alguma ajuda?"
                        )
                    except Exception:
                        return str(out)

            return "Para prosseguir, você pode consultar seu limite ou solicitar um aumento informando o valor desejado."

        except ValueError as ve:
            print(f"Credit agent validation error: {ve}")
            return f"Desculpe, não consegui processar sua solicitação: {str(ve)}"
        
        except Exception as e:
            print(f"Credit agent unexpected error: {e}")
            return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
