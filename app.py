"""
Banco Ágil - Sistema de Atendimento com Agentes de IA
"""

import streamlit as st
from datetime import datetime
from agents.orchestrator import AgentOrchestrator
from utils.session_manager import SessionManager

st.set_page_config(
    page_title="Banco Ágil - Atendimento",
    page_icon="🏦",
    layout="centered"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator()
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Banco Ágil")
st.subheader("Atendimento Virtual Inteligente")

with st.sidebar:
    st.header("ℹ️ Informações")

    if st.session_state.session_manager.authenticated:
        st.success(f"👤 Cliente autenticado")
    else:
        st.info("🔐 Aguardando autenticação")
        remaining = st.session_state.session_manager.get_remaining_attempts()
        if st.session_state.session_manager.auth_attempts > 0:
            st.warning(f"⚠️ Tentativas restantes: {remaining}")

    st.divider()
    st.write("**Agente Atual:**")
    st.write(st.session_state.session_manager.current_agent.replace("_", " ").title())

    st.divider()
    st.write("CPF: 11122233344\n\nDATA DE NASCIMENTO: 10/11/1978")
    st.divider()
    st.write("CPF: 12345678901\n\nDATA DE NASCIMENTO: 15/03/1985")
    
    st.divider()
    if st.button("🔄 Reiniciar Conversa"):
        st.session_state.messages = []
        st.session_state.orchestrator = AgentOrchestrator()
        st.session_state.session_manager = SessionManager()
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if st.session_state.session_manager.session_ended:
    st.warning("⚠️ **Sessão encerrada.** Por favor, clique em 'Reiniciar Conversa' para começar novamente.")
    st.stop()

if prompt := st.chat_input("Digite sua mensagem..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.session_manager.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            try:
                response = st.session_state.orchestrator.process_message(
                    prompt,
                    st.session_state.session_manager
                )

                if not isinstance(response, str):
                    response = str(response) if response else "Sem resposta"

                st.write(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                st.session_state.session_manager.messages.append({
                    "role": "assistant",
                    "content": response
                })


                if st.session_state.session_manager.session_ended:
                    st.rerun()

            except ValueError as ve:

                error_msg = str(ve)
                st.warning(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                st.session_state.session_manager.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
            except Exception as e:

                error_msg = "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou reinicie a conversa."
                st.error(error_msg)
                print(f"[APP] Erro inesperado: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                st.session_state.session_manager.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

st.divider()
st.caption("🔒 Banco Ágil - Todos os dados são fictícios para fins de demonstração")
