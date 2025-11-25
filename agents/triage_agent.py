"""
Triage agent for authentication and routing
"""

import re
from datetime import datetime
from langchain.agents import create_agent
from langchain_groq import ChatGroq
# from langchain.agents import create_tool_calling_agent, AgentExecutor
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
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

        self.auth_tool = AuthenticateCustomerTool()

        prompt = """
        Você é um assistente especializado no triagem de clientes do Banco Ágil.

        Sua função é:
        1. Identificar se o cliente está autenticado com base no CPF e data de nascimento
        2. Se não autenticado, coletar o CPF e a data de nascimento
        3. Se autenticado, redirecionar para o serviço apropriado (consulta de saldo, aumento de limite, etc.)

        Seja objetivo e amigável. Sempre pergunte claramente as informações necessárias.
        """

        agent = create_agent(
            model=self.llm,
            tools=[self.auth_tool],
            system_prompt=prompt
        )
        self.agent_executor = agent

    def _run_agent(self, message: str, session_manager) -> str:
        """Run the agent with the given message"""
        result = self.agent_executor.invoke({
            "input": message
        })
        return result.get("output", "")

    def _extract_cpf(self, message: str):
        digits = re.findall(r"\d+", message)
        for d in digits:
            if len(d) == 11:
                return d
        return None

    def _normalize_birthdate(self, date_str: str):
        try:
            if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
                return date_str
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%d/%m/%Y")
            if re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                return dt.strftime("%d/%m/%Y")
        except Exception:
            pass
        return None

    def _extract_birthdate(self, message: str):
        patterns = [
            r"(\d{2}/\d{2}/\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}-\d{2}-\d{4})",
        ]
        for p in patterns:
            m = re.search(p, message)
            if m:
                return self._normalize_birthdate(m.group(1))
        return None

    def _llm_classify_intent(self, message: str):
        prompt = (
            "Classifique a intenção do usuário como exatamente uma destas opções: "
            "cambio, credito, outros. Responda apenas com a opção.\n\n" + message
        )
        try:
            res = self.llm.invoke(prompt)
            label = str(getattr(res, "content", str(res))).strip().lower()
            print(f"LLM intent classification: {label}")
            if label in {"cambio", "credito"}:
                return label
        except Exception:
            pass
        return "other"

    def process(self, message: str, session_manager) -> str:
        if not session_manager.authenticated:
            cpf = self._extract_cpf(message)
            birthdate = self._extract_birthdate(message)
            if cpf and birthdate:
                try:
                    _ = self.agent_executor.invoke({"input": f"cpf: {cpf}, data de nascimento: {birthdate}"})
                    result = self.auth_tool.run({"cpf": cpf, "birthdate": birthdate})
                    print(f"Auth tool result: {result}")

                    if "error" in result:
                        session_manager.increment_auth_attempts()
                        if not session_manager.can_retry_auth():
                            return "Desculpe, não foi possível autenticar. Por favor, reinicie a conversa."
                        return "Não consegui autenticar com os dados informados. Confirme seu CPF e data de nascimento no formato DD/MM/AAAA."
                    
                    session_manager.set_customer_data(result["cpf"], result)
                    return (
                        "Autenticação concluída com sucesso. Posso ajudar com câmbio de moedas ou operações de crédito."
                        "O que você deseja fazer?"
                    )
                except Exception:
                    session_manager.increment_auth_attempts()
                    if not session_manager.can_retry_auth():
                        return "Desculpe, houve um erro ao autenticar. Por favor, reinicie a conversa."
                    return "Ocorreu um erro ao autenticar. Por favor, informe novamente seu CPF e data de nascimento."
            else:
                response = self._run_agent(message, session_manager)
                if response:
                    return response + "\n\nPor favor, informe seu CPF e data de nascimento (DD/MM/AAAA)."
                return "Para continuar, preciso do seu CPF e da sua data de nascimento (DD/MM/AAAA)."

        label = self._llm_classify_intent(message)
        if label == "cambio":
            session_manager.switch_agent("cambio")
            return "Que bom, o que você deseja saber sobre câmbio de moedas?"
        if label == "credito":
            session_manager.switch_agent("credito")
            return "Que bom, o que você deseja fazer sobre operações de crédito?"

        return "Posso ajudar com câmbio de moedas ou operações de crédito (consultar limite, solicitar aumento). O que você deseja?"
