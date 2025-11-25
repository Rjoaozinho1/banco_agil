"""
Interview agent for credit score recalculation
"""

import re
from langchain_groq import ChatGroq
from tools.credit_tools import UpdateCustomerScoreTool
from config import GROQ_API_KEY, GROQ_MODEL

class InterviewAgent:
    """Agent responsible for conducting credit score interview"""
    
    INTERVIEW_QUESTIONS = [
        "renda_mensal",
        "tipo_emprego",
        "despesas_fixas",
        "num_dependentes",
        "tem_dividas"
    ]
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )
        self.update_score_tool = UpdateCustomerScoreTool()
    
    def process(self, message: str, session_manager) -> str:
        """Process message in interview agent"""
        
        current_step = session_manager.interview_step
        
        # Process answer for current question
        if current_step < len(self.INTERVIEW_QUESTIONS):
            question_type = self.INTERVIEW_QUESTIONS[current_step]
            answer = self._extract_answer(message, question_type)
            
            if answer is None:
                return self._get_retry_message(question_type)
            
            # Store answer
            session_manager.interview_data[question_type] = answer
            session_manager.interview_step += 1
            
            # Check if interview is complete
            if session_manager.interview_step >= len(self.INTERVIEW_QUESTIONS):
                return self._finalize_interview(session_manager)
            
            # Ask next question
            return self._get_next_question(session_manager.interview_step)
        
        return "Entrevista já finalizada."
    
    def _extract_answer(self, message: str, question_type: str):
        """Extract answer based on question type"""
        
        message_lower = message.lower()
        
        if question_type == "renda_mensal":
            # Extract number
            amount = self._extract_number(message)
            return amount if amount and amount > 0 else None
        
        elif question_type == "tipo_emprego":
            if any(word in message_lower for word in ["formal", "carteira", "clt", "registrado"]):
                return "formal"
            elif any(word in message_lower for word in ["autônomo", "autonomo", "freelancer", "pj", "próprio", "proprio"]):
                return "autônomo"
            elif any(word in message_lower for word in ["desempregado", "desempregada", "sem emprego", "não trabalho", "nao trabalho"]):
                return "desempregado"
            return None
        
        elif question_type == "despesas_fixas":
            amount = self._extract_number(message)
            return amount if amount and amount >= 0 else None
        
        elif question_type == "num_dependentes":
            num = self._extract_number(message)
            if num is not None and num >= 0:
                if num >= 3:
                    return "3+"
                return int(num)
            return None
        
        elif question_type == "tem_dividas":
            if any(word in message_lower for word in ["sim", "tenho", "possuo", "há", "existe"]):
                return "sim"
            elif any(word in message_lower for word in ["não", "nao", "sem", "nenhuma", "zero"]):
                return "não"
            return None
        
        return None
    
    def _extract_number(self, message: str) -> float:
        """Extract number from message"""
        clean_message = message.replace('R$', '').replace('r$', '').replace('.', '').replace(',', '.')
        
        pattern = r'(\d+\.?\d*)'
        match = re.search(pattern, clean_message)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def _get_next_question(self, step: int) -> str:
        """Get next interview question"""
        
        questions = {
            0: "Para começar, qual é sua renda mensal? (informe o valor em reais)",
            1: """Qual é seu tipo de emprego?
- Formal (CLT/Carteira assinada)
- Autônomo (Freelancer/PJ)
- Desempregado""",
            2: "Quais são suas despesas fixas mensais? (aluguel, contas, etc. - informe o valor total em reais)",
            3: "Quantos dependentes você tem? (filhos ou outras pessoas que dependem de você financeiramente)",
            4: "Você possui dívidas ativas no momento? (responda sim ou não)"
        }
        
        return questions.get(step, "")
    
    def _get_retry_message(self, question_type: str) -> str:
        """Get retry message for invalid answer"""
        
        messages = {
            "renda_mensal": "Por favor, informe um valor válido para sua renda mensal (apenas números):",
            "tipo_emprego": "Por favor, escolha uma das opções: Formal, Autônomo ou Desempregado:",
            "despesas_fixas": "Por favor, informe um valor válido para suas despesas fixas mensais:",
            "num_dependentes": "Por favor, informe o número de dependentes (0, 1, 2, 3 ou mais):",
            "tem_dividas": "Por favor, responda 'sim' ou 'não' sobre a existência de dívidas:"
        }
        
        return messages.get(question_type, "Resposta inválida. Por favor, tente novamente:")
    
    def _finalize_interview(self, session_manager) -> str:
        """Calculate new score and finalize interview"""
        
        data = session_manager.interview_data
        
        # Calculate new score using the formula
        new_score = self._calculate_score(data)
        
        # Update customer score
        result = self.update_score_tool.run({
            "cpf": session_manager.customer_cpf,
            "new_score": new_score
        })
        
        if "error" in result:
            return "Desculpe, ocorreu um erro ao atualizar seu score. Por favor, tente novamente."
        
        # Update session
        session_manager.update_customer_score(new_score)
        
        # Reset interview state
        session_manager.interview_data = {}
        session_manager.interview_step = 0
        
        # Switch back to credit agent
        session_manager.switch_agent("credit")
        
        old_score = result.get('old_score', 0)
        score_change = new_score - old_score
        change_indicator = "📈" if score_change > 0 else "📉" if score_change < 0 else "➡️"
        
        return f"""✅ Entrevista concluída com sucesso!

Seu score foi atualizado:
Score anterior: {old_score:.0f}
Novo score: {new_score:.0f}
Variação: {change_indicator} {score_change:+.0f} pontos

Agora você pode solicitar novamente o aumento de limite com seu novo score!

Gostaria de fazer uma nova solicitação de aumento de limite?"""
    
    def _calculate_score(self, data: dict) -> float:
        """Calculate credit score based on interview data"""
        
        # Weights
        peso_renda = 30
        peso_emprego = {
            "formal": 300,
            "autônomo": 200,
            "desempregado": 0
        }
        peso_dependentes = {
            0: 100,
            1: 80,
            2: 60,
            "3+": 30
        }
        peso_dividas = {
            "sim": -100,
            "não": 100
        }
        
        # Extract data
        renda = data.get("renda_mensal", 0)
        despesas = data.get("despesas_fixas", 0)
        tipo_emprego = data.get("tipo_emprego", "desempregado")
        num_dependentes = data.get("num_dependentes", 0)
        tem_dividas = data.get("tem_dividas", "sim")
        
        # Calculate score
        score = (
            (renda / (despesas + 1)) * peso_renda +
            peso_emprego.get(tipo_emprego, 0) +
            peso_dependentes.get(num_dependentes, 0) +
            peso_dividas.get(tem_dividas, 0)
        )
        
        # Ensure score is between 0 and 1000
        score = max(0, min(1000, score))
        
        return round(score, 2)