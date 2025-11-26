"""
Exchange agent for currency quotation
"""

from langchain_groq import ChatGroq
from tools.exchange_tools import get_exchange_rate
from config import GROQ_API_KEY, GROQ_MODEL
from utils.session_manager import SessionManager

class ExchangeAgent:
    """Agent responsible for currency exchange rates"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0,
        )

        self.tools = [get_exchange_rate]
        
        self.runnable = self.llm.bind_tools(self.tools)
        
        self.system_prompt = (
            "Você é um assistente de câmbio do Banco Ágil. "
            "Identifique a moeda desejada e SEMPRE use a ferramenta 'get_exchange_rate' "
            "quando houver uma moeda válida. NUNCA chute; se a mensagem for ambígua, "
            "solicite o código ISO em maiúsculas (USD, EUR, GBP, JPY, ARS). "
            "Ao chamar a ferramenta, passe apenas o código da moeda. "
            "Se o cliente quiser falar sobre crédito (limite, aumento, score), responda APENAS com a palavra 'credito'."
        )

    def process(self, message: str, session_manager: SessionManager) -> str:
        """Process message in exchange agent"""
        
        try:
            print(f"Exchange agent received message: {message}")

            full_input = []
            if isinstance(session_manager, SessionManager) and len(session_manager.get_session_history()) >= 1:
                full_input = [("system", self.system_prompt), ("user", message)]
            else:
                for msg in session_manager.get_session_history():
                    full_input.append((msg["role"], msg["content"]))
                full_input.append(("system", self.system_prompt))
                full_input.append(("user", message))

            result = self.runnable.invoke(full_input)

            if result.content:
                intent = result.content.strip().lower()
                if intent == "credito":
                    print("Exchange agent intent redirect: credito")
                    from agents.credit_agent import CreditAgent
                    session_manager.switch_agent("credito")
                    agent = CreditAgent()
                    return agent.process(message, session_manager)

            if result.content == "" and result.additional_kwargs.get("tool_calls"):
                tool_call = result.additional_kwargs.get("tool_calls")[0]
                fn = tool_call.get("function", {})
                if fn.get("name") == "get_exchange_rate":
                    import json
                    args = json.loads(fn.get("arguments", "{}"))
                    code = args.get("currency_code")
                    rate_value = get_exchange_rate.invoke({"currency_code": code})
                    try:
                        val = float(rate_value)
                        prompt = [
                            ("system", "Você é um assistente do Banco Ágil."),
                            (
                                "system",
                                f"Com base na cotação informada, 1 {code} = {val:.4f} BRL. "
                                "Gere uma resposta curta, amigável e clara em PT-BR, "
                                "explicando a cotação e oferecendo ajuda para consultar outra moeda."
                            ),
                        ]
                        personalized = self.llm.invoke(prompt).content
                        return personalized + "\n\nDeseja consultar outra moeda ou posso ajudá-lo com algo mais?"
                    except Exception:
                        return str(rate_value)

            content = result.content or (
                "Para prosseguir, informe o código da moeda em maiúsculas (USD, EUR, GBP, JPY, ARS)."
            )
            return content

        except Exception as e:
            return (
                "Desculpe, não foi possível consultar a cotação no momento. "
                f"Erro: {str(e)}\n\nPor favor, tente novamente ou posso ajudá-lo com outro serviço?"
            )
