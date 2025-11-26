"""
Credit agent for credit limit queries and increase requests
"""

import re
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from tools.credit_tools import CheckCreditLimitTool, RequestCreditIncreaseTool
from agents.interview_agent import InterviewAgent
from config import GROQ_API_KEY, GROQ_MODEL

class CreditAgent:
    """Agent responsible for credit limit operations"""

    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )
        self.tools = [CheckCreditLimitTool(), RequestCreditIncreaseTool()]

        system_prompt = f"""Você é um assistente de crédito do Banco Ágil.

        Sua função é:
        1. Entender se o cliente quer consultar o limite atual ou solicitar aumento de limite
        2. Se for consulta de limite, use a ferramenta check_credit_limit
        3. Se o usuario informar um valor desejado use a ferramenta request_credit_increase, (ex: "aumentar o limite para 4000")
        4. Se for aumento, peça o valor desejado se não informado e processe o pedido com a ferramenta request_credit_increase
        5. Se o aumento for negado, sugira educadamente a entrevista retornando somente "entrevista".
        6. Explique o resultado de forma clara e amigável, respondendo de forma objetiva e cordial.

        Para realizar as ações, você DEVE usar as ferramentas disponíveis.
        Não refaca perguntas, sempre utilize as ferramentas disponiveis para gera uma resposta.
        """

        sp = SystemMessage(system_prompt)

        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=sp,
        )
        self.agent_executor = agent

    def process(self, message: str, session_manager) -> str:
        """Process message in credit agent"""

        print(f"Credit agent received message: {message}")

        if "entrevista" in message.lower():
            print("Credit agent routing: handle_interview")
            session_manager.switch_agent("entrevista")
            agent = InterviewAgent()
            return agent.process(message, session_manager)

        try:
            contexto_usuario = f"\n(Contexto do sistema: CPF {session_manager.customer_cpf}, Score Atual: {session_manager.get_customer_score()}, Limite Atual: {session_manager.get_customer_limit()})"
            
            full_input = contexto_usuario + "\n\n" + f"Mensagem do cliente: {message}"

            print(f"Credit agent full input: {full_input}")
            result = self.agent_executor.invoke(input={"input": full_input}, config={"max_iterations": 2})
            print(f"Credit agent result: {result}")
            return result["messages"][-1].content
        except Exception as e:
            print(f"Credit agent error: {e}")
            return f"Desculpe, ocorreu um erro. Detalhes: {str(e)}"
