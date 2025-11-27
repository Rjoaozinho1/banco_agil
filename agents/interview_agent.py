"""
Interview agent for credit score recalculation
"""

import re
import json
from langchain_groq import ChatGroq
from tools.credit_tools import update_customer_score
from utils.session_manager import SessionManager
from config import GROQ_API_KEY, GROQ_MODEL

class InterviewAgent:
    """Agent responsible for conducting credit score interview"""

    def __init__(self):
        self.llm = ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0)
        self.tools = [update_customer_score]
        self.runnable = self.llm.bind_tools(self.tools)

        self.system_prompt = (
            "Você é um assistente de entrevista de crédito do Banco Ágil. "
            "Siga estas regras de estilo: não cumprimente repetidamente, não repita que é uma entrevista, "
            "mantenha respostas curtas (1–2 linhas) e objetivas. "
            "Colete: renda_mensal (número), tipo_emprego (Formal/Autônomo/Desempregado), despesas_fixas (número), "
            "num_dependentes (0, 1, 2, 3+), tem_dividas (sim/não). "
            "Se a resposta estiver inválida, explique brevemente o motivo e peça novamente apenas o campo necessário. "
            "NÃO chame ferramentas até concluir a entrevista e calcular o novo score. "
            "Ao concluir, SOMENTE chame 'update_customer_score' se o novo score for MAIOR que o atual; nunca diminua o score."
        )
    
    def process(self, message: str, session_manager: SessionManager) -> str:
        """Process message in interview agent"""

        print(f"[InterviewAgent] Received message: {message}")
        print(f"[InterviewAgent] Current step: {session_manager.interview_step}")

        current_step = session_manager.interview_step

        if session_manager.interview_attempts == None:
            session_manager.interview_attempts = {}

        if current_step == 0:
            num_check = self._extract_number(message)
            print(f"[InterviewAgent] num_check: {num_check}")

        required_fields = [
            "renda_mensal",
            "tipo_emprego",
            "despesas_fixas",
            "num_dependentes",
            "tem_dividas",
        ]

        if current_step < len(required_fields):

            question_type = required_fields[current_step]
            print(f"[InterviewAgent] question_type: {question_type}")
            
            answer = self._extract_answer(message, question_type)
            print(f"[InterviewAgent] extracted answer: {answer}")
            
            if answer is None:
                session_manager.interview_attempts[question_type] = session_manager.interview_attempts.get(question_type, 0) + 1
                print(f"[InterviewAgent] invalid attempts for {question_type}: {session_manager.interview_attempts[question_type]}")
                
                if session_manager.interview_attempts[question_type] >= 3:
                    session_manager.end_session()
                    print("[InterviewAgent] Ending due to repeated invalid answers")
                    return "Entrevista encerrada por respostas inválidas repetidas. Obrigado!"

                context = self._build_interview_context(session_manager, reason=f"Resposta inválida para {question_type}")
                agent_msg = self._llm_ask_next(message, session_manager, context, force_field=question_type)
                print(f"[InterviewAgent] llm retry msg: {agent_msg}")

                return agent_msg

            session_manager.interview_data[question_type] = answer
            print(f"[InterviewAgent] stored: {session_manager.interview_data}")

            session_manager.interview_step += 1
            print(f"[InterviewAgent] advanced to step: {session_manager.interview_step}")
            
            if session_manager.interview_step >= len(required_fields):
                print("[InterviewAgent] Completing interview")
                return self._finalize_interview(session_manager)
            
            context = self._build_interview_context(session_manager)
            next_msg = self._llm_ask_next(message, session_manager, context)
            print(f"[InterviewAgent] next llm msg: {next_msg}")
            
            return next_msg
        
        return "Entrevista já finalizada."
    
    def _extract_answer(self, message: str, question_type: str):
        """Extract answer based on question type"""
        
        print(f"[InterviewAgent] extracting answer for {question_type} from message: {message}")
        message_lower = message.lower()
        
        if question_type == "renda_mensal":
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
            print(f"[InterviewAgent] despesas_fixas parsed: {amount}")
            return amount if amount and amount >= 0 else None
        
        elif question_type == "num_dependentes":
            num = self._extract_number(message)
            print(f"[InterviewAgent] num_dependentes parsed: {num}")
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

        print(f"[InterviewAgent] _extract_number raw message: {message}")
        clean_message = message.replace('R$', '').replace('r$', '').replace('.', '').replace(',', '.')
        
        pattern = r'(\d+\.?\d*)'
        match = re.search(pattern, clean_message)
        
        if match:
            try:
                value = float(match.group(1))
                print(f"[InterviewAgent] _extract_number parsed value: {value}")
                return value
            except ValueError:
                print("[InterviewAgent] _extract_number ValueError")
                return None
        return None
    
    def _build_interview_context(self, session_manager: SessionManager, reason: str | None = None) -> str:
        data = session_manager.interview_data
        required_fields = [
            "renda_mensal",
            "tipo_emprego",
            "despesas_fixas",
            "num_dependentes",
            "tem_dividas",
        ]
        missing = [f for f in required_fields if f not in data or data.get(f) in (None, "")]
        attempts = session_manager.interview_attempts or {}
        rules = (
            "Regras: renda/despesas como números (R$ permitido), tipo_emprego em {Formal, Autônomo, Desempregado}, "
            "num_dependentes inteiro (usar '3+' para três ou mais), tem_dividas em {sim, não}."
        )
        ctx = (
            f"CPF: {session_manager.customer_cpf or 'N/A'}\n"
            f"Score Atual: {session_manager.get_customer_score() or 0:.0f}\n"
            f"Dados coletados: {data}\n"
            f"Faltantes: {missing}\n"
            f"Tentativas: {attempts}\n"
            f"{rules}\n"
        )
        if reason:
            ctx += f"Motivo: {reason}\n"
        print(f"[InterviewAgent] context: {ctx}")
        return ctx

    def _llm_ask_next(self, message: str, session_manager: SessionManager, context: str, force_field: str | None = None) -> str:
        try:
            instructions = (
                "Gere uma única mensagem em PT-BR, clara e amigável, sem cumprimentos e sem repetir informações já ditas."
                " Pergunte APENAS o próximo campo faltante com orientação mínima."
                " Se 'force_field' estiver presente, pergunte especificamente por ele."
            )
            full_input = [("system", self.system_prompt), ("system", context)]
            try:
                examples_shown = session_manager.interview_examples_shown or {}
                current_field = force_field
                if not current_field:
                    required_fields = [
                        "renda_mensal",
                        "tipo_emprego",
                        "despesas_fixas",
                        "num_dependentes",
                        "tem_dividas",
                    ]
                    data = session_manager.interview_data
                    for f in required_fields:
                        if f not in data or data.get(f) in (None, ""):
                            current_field = f
                            break
                if current_field and not examples_shown.get(current_field, False):
                    example = ""
                    if current_field == "renda_mensal":
                        example = "Exemplo: 3500"
                    elif current_field == "tipo_emprego":
                        example = "Escolha: Formal, Autônomo ou Desempregado"
                    elif current_field == "despesas_fixas":
                        example = "Exemplo: 1200"
                    elif current_field == "num_dependentes":
                        example = "Responda: 0, 1, 2 ou 3+"
                    elif current_field == "tem_dividas":
                        example = "Responda: sim ou não"
                    if example:
                        full_input.append(("system", f"Inclua um único exemplo curto apenas desta vez: {example}"))
                        try:
                            examples_shown[current_field] = True
                            print(f"[InterviewAgent] examples_shown updated: {examples_shown}")
                        except Exception as e:
                            print(f"[InterviewAgent] examples_shown update error: {e}")
            except Exception as e:
                print(f"[InterviewAgent] examples_shown handling error: {e}")
            
            try:
                history = session_manager.get_session_history()
                for msg in history:
                    full_input.append((msg.get("role"), msg.get("content")))
            except Exception as e:
                print(f"[InterviewAgent] Error reading history: {e}")

            full_input.append(("system", instructions))

            if force_field:
                full_input.append(("system", f"Pergunte especificamente sobre: {force_field}"))

            full_input.append(("user", message))
            print(f"[InterviewAgent] ask_next full_input: {full_input}")

            result = self.llm.invoke(full_input)
            print(f"[InterviewAgent] ask_next result: {result}")

            return result.content or "Por favor, informe o dado solicitado."
        except Exception:
            return "Por favor, informe o dado solicitado."
    
    def _finalize_interview(self, session_manager: SessionManager) -> str:
        """Calculate new score and finalize interview"""
        
        data = session_manager.interview_data
        print(f"[InterviewAgent] finalize with data: {data}")
        
        # Calculate new score using the formula
        new_score = self._calculate_score(data)
        print(f"[InterviewAgent] calculated new_score: {new_score}")

        current_score = session_manager.get_customer_score()
        
        print(f"[InterviewAgent] current_score={current_score}")

        if new_score <= current_score:
            print("[InterviewAgent] new_score not higher; skipping tool invocation")
            session_manager.interview_data = {}
            session_manager.interview_step = 0
            session_manager.interview_attempts = {}
            session_manager.switch_agent("credito")
            response = (
                f"Entrevista concluída. Seu score atual permanece {current_score:.0f}. "
                f"Para melhorar seu score, podemos revisar suas informações e hábitos financeiros."
            )

            return response
        
        print(f"[InterviewAgent] invoking update_customer_score with cpf={session_manager.customer_cpf}, new_score={new_score}")

        out = update_customer_score.invoke({"cpf": session_manager.customer_cpf, "new_score": new_score})
        print(f"[InterviewAgent] update_customer_score raw result: {out}")
        
        try:
            data_out = json.loads(out)
        except Exception:
            data_out = {"error": "Retorno inválido da ferramenta"}
        
        if data_out.get("error"):
            print("[InterviewAgent] error updating score via tool")
            return "Desculpe, ocorreu um erro ao atualizar seu score. Por favor, tente novamente."
        
        session_manager.update_customer_score(new_score)
        print("[InterviewAgent] session score updated")
        
        session_manager.interview_data = {}
        session_manager.interview_step = 0
        session_manager.interview_attempts = {}
        print("[InterviewAgent] reset interview state")
        
        session_manager.switch_agent("credito")
        print("[InterviewAgent] switched to credit agent")
        
        old_score = data_out.get('old_score', current_score)
        score_change = new_score - old_score
        change_indicator = "📈" if score_change > 0 else "📉" if score_change < 0 else "➡️"
        summary = (
            f"{{\"old_score\": {old_score:.0f}, \"new_score\": {new_score:.0f}, \"delta\": {score_change:+.0f}}}"
        )
        print(f"[InterviewAgent] summary: {summary}")

        response = (
            f"✅ Entrevista concluída com sucesso!\n\n" +
            f"Seu score foi atualizado:\n\nScore anterior: {old_score:.0f}\n\nNovo score: {new_score:.0f}\n\nVariação: {change_indicator} {score_change:+.0f} pontos\n\n"
        )

        return response
    
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

        {'renda_mensal': 6000.0, 'tipo_emprego': 'autônomo', 'despesas_fixas': 3500.0, 'num_dependentes': 0, 'tem_dividas': 'não'}
        
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
