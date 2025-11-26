"""
Exchange agent for currency quotation
"""

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from tools.exchange_tools import GetExchangeRateTool
from config import GROQ_API_KEY, GROQ_MODEL

class ExchangeAgent:
    """Agent responsible for currency exchange rates"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )
        
        self.exchange_tool = GetExchangeRateTool()

        prompt = f"""Você é um assistente especializado em cotações de moedas do Banco Ágil.

        Sua função é:
        1. Identificar qual moeda o cliente quer consultar
        2. Quando for consultar, chame a ferramenta get_exchange_rate passando APENAS o código da moeda em MAIÚSCULAS (ex: USD, EUR, GBP, JPY, ARS)
        3. Apresentar a cotação de forma clara e amigável

        {input}"""
        
        agent = create_agent(model=self.llm, tools=[self.exchange_tool], system_prompt=prompt)
        self.agent_executor = agent

    def process(self, message: str, session_manager) -> str:
        """Process message in exchange agent"""
        
        try:
            print(f"Exchange agent received message: {message}")

            result = self.agent_executor.invoke({
                "input": message
            })

            print(f"Exchange agent result: {result}")
            
            response = result.get("output", "")

            if response:
                response += "\n\nDeseja consultar outra moeda ou posso ajudá-lo com algo mais?"

            if not response:
                code = self._extract_currency_code(message)
                if code:
                    try:
                        formatted = self.exchange_tool.run(code)
                        return (formatted if isinstance(formatted, str) else str(formatted))
                    except Exception:
                        pass

            print(f"Exchange agent response: {response}")
            return response
            
        except Exception as e:
            return f"""Desculpe, não foi possível consultar a cotação no momento.

            Erro: {str(e)}

            Por favor, tente novamente ou posso ajudá-lo com outro serviço?"""

    def _extract_currency_code(self, message: str):
        m = message.lower()
        if any(k in m for k in ["usd", "dolar", "dólar", "dolar americano"]):
            return "USD"
        if any(k in m for k in ["eur", "euro"]):
            return "EUR"
        if any(k in m for k in ["gbp", "libra"]):
            return "GBP"
        if any(k in m for k in ["jpy", "iene", "yen"]):
            return "JPY"
        if any(k in m for k in ["ars", "peso", "peso argentino"]):
            return "ARS"
        return None
