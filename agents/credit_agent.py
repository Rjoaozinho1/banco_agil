"""
Credit agent for credit limit queries and increase requests
"""

import re
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from tools.credit_tools import CheckCreditLimitTool, RequestCreditIncreaseTool
from config import GROQ_API_KEY, GROQ_MODEL

class CreditAgent:
    """Agent responsible for credit limit operations"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )
        self.check_limit_tool = CheckCreditLimitTool()
        self.request_increase_tool = RequestCreditIncreaseTool()

        prompt = """Você é um assistente de crédito do Banco Ágil.

Sua função é:
1. Entender se o cliente quer consultar o limite atual ou solicitar aumento de limite
2. Se for consulta de limite, use a ferramenta para obter limite e score
3. Se for aumento, peça o valor desejado se não informado e processe o pedido
4. Explique o resultado de forma clara e amigável e ofereça próximos passos

Responda de forma objetiva e cordial."""

        agent = create_agent(model=self.llm, tools=[self.check_limit_tool, self.request_increase_tool], system_prompt=prompt)
        self.agent_executor = agent
    
    def process(self, message: str, session_manager) -> str:
        """Process message in credit agent"""
        try:
            action = self._llm_classify_action(message)
        except Exception:
            action = "other"

        if action == "check_limit":
            return self._check_current_limit(session_manager)

        if action == "request_increase":
            return self._handle_increase_request(message, session_manager)

        try:
            result = self.agent_executor.invoke({"input": message})
            response = result.get("output", "")
            if response:
                response += f"\n\nSeu limite atual é de R$ {session_manager.get_customer_limit():.2f}. Posso consultar seu limite ou solicitar um aumento. O que você prefere?"
            return response or (
                f"Seu limite atual é de R$ {session_manager.get_customer_limit():.2f}. "
                "Deseja consultar detalhes do limite ou solicitar um aumento?"
            )
        except Exception as e:
            return f"Desculpe, ocorreu um erro ao processar sua solicitação. Erro: {str(e)}"
    
    def _check_current_limit(self, session_manager) -> str:
        """Check customer's current credit limit"""
        
        result = self.check_limit_tool.run({
            "cpf": session_manager.customer_cpf
        })
        
        if "error" in result:
            return "Desculpe, não foi possível consultar seu limite no momento. Por favor, tente novamente."
        
        return f"""📊 Informações do seu crédito:

💳 Limite disponível: R$ {result['limite_credito']:.2f}
⭐ Score atual: {result['score']:.0f}

Gostaria de solicitar um aumento de limite?"""
    
    def _handle_increase_request(self, message: str, session_manager) -> str:
        """Handle credit limit increase request"""
        
        # Extract requested amount
        requested_amount = self._extract_amount(message)
        
        if not requested_amount:
            try:
                result = self.agent_executor.invoke({
                    "input": "Para solicitar aumento de limite, informe o novo limite desejado (ex: 5000 ou 5.000,00)."
                })
                response = result.get("output", "")
                return response or (
                    "Para solicitar um aumento de limite, por favor informe o novo limite desejado. "
                    "Exemplo: 'Gostaria de aumentar meu limite para R$ 5000' ou apenas '5000'."
                )
            except Exception:
                return (
                    "Para solicitar um aumento de limite, por favor informe o novo limite desejado. "
                    "Exemplo: 'Gostaria de aumentar meu limite para R$ 5000' ou apenas '5000'."
                )
        
        # Process the request
        result = self.request_increase_tool.run({
            "cpf": session_manager.customer_cpf,
            "current_limit": session_manager.get_customer_limit(),
            "requested_limit": requested_amount,
            "current_score": session_manager.get_customer_score()
        })
        
        if "error" in result:
            return f"Desculpe, ocorreu um erro ao processar sua solicitação: {result['error']}"
        
        # Check if approved or rejected
        if result["status"] == "aprovado":
            # Update session with new limit
            session_manager.customer_data['limite_credito'] = requested_amount
            
            return f"""✅ Parabéns! Sua solicitação de aumento de limite foi APROVADA!

Novo limite aprovado: R$ {requested_amount:.2f}
Limite anterior: R$ {result['limite_atual']:.2f}

Seu novo limite já está disponível para uso!

Posso ajudá-lo com mais alguma coisa?"""
        
        else:  # rejected
            return f"""❌ Infelizmente sua solicitação de aumento de limite foi REPROVADA.

Limite solicitado: R$ {requested_amount:.2f}
Limite atual: R$ {result['limite_atual']:.2f}
Seu score atual: {session_manager.get_customer_score():.0f}

O limite solicitado requer um score mais alto para aprovação.

💡 Você pode melhorar seu score através de uma entrevista de reavaliação de crédito, onde atualizaremos suas informações financeiras.

Gostaria de fazer a entrevista para tentar aumentar seu score?"""

    def _extract_amount(self, message: str) -> float:
        """Extract monetary amount from message"""
        
        # Remove currency symbols and normalize
        clean_message = message.replace('R$', '').replace('r$', '')
        
        # Look for numbers (with optional decimal point and comma)
        patterns = [
            r'(\d+\.?\d*)',  # 5000 or 5000.00
            r'(\d+,\d+)',    # 5000,00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_message)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    amount = float(amount_str)
                    if amount > 0:
                        return amount
                except ValueError:
                    continue
        
        return None

    def _llm_classify_action(self, message: str) -> str:
        prompt = (
            "Classifique a intenção do usuário como exatamente uma destas opções: "
            "check_limit, request_increase, other. Responda apenas com a opção.\n\n" + message
        )
        try:
            res = self.llm.invoke(prompt)
            label = str(getattr(res, "content", str(res))).strip().lower()
            if label in {"check_limit", "request_increase", "other"}:
                return label
        except Exception:
            pass
        return "other"
