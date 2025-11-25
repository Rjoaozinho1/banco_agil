"""
Interview agent for credit score recalculation
"""

import re
from langchain_groq import ChatGroq
from langchain.agents import create_agent
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

        prompt = f"""Você é um assistente de entrevista de crédito do Banco Ágil.

Conduza a entrevista passo a passo para coletar:
- renda_mensal (número em reais)
- tipo_emprego (Formal/Autônomo/Desempregado)
- despesas_fixas (número em reais)
- num_dependentes (0, 1, 2, 3+)
- tem_dividas (sim/não)

Se a resposta estiver inválida, explique brevemente e peça novamente de forma objetiva.
Não chame ferramentas até que a entrevista esteja completa e o novo score tenha sido calculado.
Respostas devem ser claras e amigáveis.

{input}
"""

        agent = create_agent(model=self.llm, tools=[self.update_score_tool], system_prompt=prompt)
        self.agent_executor = agent
    
    def process(self, message: str, session_manager) -> str:
        """Process message in interview agent"""
        print(f"Interview agent received message: {message}")
        print(f"Interview agent current_step: {session_manager.interview_step}")
        current_step = session_manager.interview_step
        if not hasattr(session_manager, "interview_attempts"):
            session_manager.interview_attempts = {}

        if current_step == 0:
            num_check = self._extract_number(message)
            print(f"Interview agent num_check: {num_check}")
            if num_check is None:
                return self._get_next_question(0)

        # Process answer for current question
        if current_step < len(self.INTERVIEW_QUESTIONS):
            question_type = self.INTERVIEW_QUESTIONS[current_step]
            print(f"Interview agent question_type: {question_type}")
            answer = self._extract_answer(message, question_type)
            print(f"Interview agent extracted answer: {answer}")
            
            if answer is None:
                session_manager.interview_attempts[question_type] = session_manager.interview_attempts.get(question_type, 0) + 1
                print(f"Interview agent invalid answer attempts for {question_type}: {session_manager.interview_attempts[question_type]}")
                if session_manager.interview_attempts[question_type] >= 3:
                    session_manager.should_end = True
                    print("Interview agent ending due to repeated invalid answers")
                    return "Entrevista encerrada por respostas inválidas repetidas. Obrigado!"
                retry_msg = self._get_retry_message(question_type)
                print(f"Interview agent retry message: {retry_msg}")
                agent_msg = self._run_agent(retry_msg)
                print(f"Interview agent agent_msg: {agent_msg}")
                return agent_msg
            
            # Store answer
            session_manager.interview_data[question_type] = answer
            print(f"Interview agent stored: {session_manager.interview_data}")
            session_manager.interview_step += 1
            print(f"Interview agent advanced to step: {session_manager.interview_step}")
            
            # Check if interview is complete
            if session_manager.interview_step >= len(self.INTERVIEW_QUESTIONS):
                print("Interview agent completing interview")
                return self._finalize_interview(session_manager)
            
            # Ask next question
            next_q = self._get_next_question(session_manager.interview_step)
            print(f"Interview agent next question: {next_q}")
            return next_q
        
        return "Entrevista já finalizada."
    
    def _extract_answer(self, message: str, question_type: str):
        """Extract answer based on question type"""
        
        print(f"Interview agent extracting answer for {question_type} from message: {message}")
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
            print(f"Interview agent despesas_fixas parsed: {amount}")
            return amount if amount and amount >= 0 else None
        
        elif question_type == "num_dependentes":
            num = self._extract_number(message)
            print(f"Interview agent num_dependentes parsed: {num}")
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
        print(f"Interview agent _extract_number raw message: {message}")
        clean_message = message.replace('R$', '').replace('r$', '').replace('.', '').replace(',', '.')
        
        pattern = r'(\d+\.?\d*)'
        match = re.search(pattern, clean_message)
        
        if match:
            try:
                value = float(match.group(1))
                print(f"Interview agent _extract_number parsed value: {value}")
                return value
            except ValueError:
                print("Interview agent _extract_number ValueError")
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
        
        next_q = questions.get(step, "")
        print(f"Interview agent _get_next_question step={step} next_q={next_q}")
        return next_q
    
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
        print(f"Interview agent finalize with data: {data}")
        
        # Calculate new score using the formula
        new_score = self._calculate_score(data)
        print(f"Interview agent calculated new_score: {new_score}")
        
        # Update customer score
        print(f"Interview agent calling update_score_tool with cpf={session_manager.customer_cpf}, new_score={new_score}")
        result = self.update_score_tool.run({
            "cpf": session_manager.customer_cpf,
            "new_score": new_score
        })
        print(f"Interview agent update_score_tool result: {result}")
        
        if "error" in result:
            print("Interview agent error updating score")
            return "Desculpe, ocorreu um erro ao atualizar seu score. Por favor, tente novamente."
        
        # Update session
        session_manager.update_customer_score(new_score)
        print("Interview agent session score updated")
        
        # Reset interview state
        session_manager.interview_data = {}
        session_manager.interview_step = 0
        if hasattr(session_manager, "interview_attempts"):
            session_manager.interview_attempts = {}
        print("Interview agent reset interview state")
        
        # Switch back to credit agent
        session_manager.switch_agent("credit")
        print("Interview agent switched to credit agent")
        
        old_score = result.get('old_score', 0)
        score_change = new_score - old_score
        change_indicator = "📈" if score_change > 0 else "📉" if score_change < 0 else "➡️"
        summary = (
            f"{{\"old_score\": {old_score:.0f}, \"new_score\": {new_score:.0f}, \"delta\": {score_change:+.0f}}}"
        )
        print(f"Interview agent summary: {summary}")

        return (
            f"✅ Entrevista concluída com sucesso!\n\n" +
            f"Seu score foi atualizado:\nScore anterior: {old_score:.0f}\nNovo score: {new_score:.0f}\nVariação: {change_indicator} {score_change:+.0f} pontos\n\n"
        )

    def _run_agent(self, message: str) -> str:
        try:
            print(f"Interview agent invoking agent with message: {message}")
            result = self.agent_executor.invoke({"input": message})
            print(f"Interview agent agent result: {result}")
            return result.get("output", "")
        except Exception:
            print("Interview agent agent invocation failed; returning original message")
            return message
    
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
