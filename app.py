"""
Banco Ágil - Sistema de Atendimento com Agentes de IA
"""

import streamlit as st
from datetime import datetime
from agents.orchestrator import AgentOrchestrator
from utils.session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="Banco Ágil - Atendimento",
    page_icon="🏦",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator()
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

# Custom CSS
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

# Header
st.title("🏦 Banco Ágil")
st.subheader("Atendimento Virtual Inteligente")

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ Informações")
    st.write("**Status do Sistema:** ✅ Online")
    
    if st.session_state.session_manager.authenticated:
        st.success(f"👤 Cliente autenticado")
        st.write(f"**CPF:** {st.session_state.session_manager.customer_cpf[:3]}.***.***-{st.session_state.session_manager.customer_cpf[-2:]}")
    else:
        st.info("🔐 Aguardando autenticação")
    
    st.divider()
    st.write("**Agente Atual:**")
    st.write(st.session_state.session_manager.current_agent.replace("_", " ").title())

    st.divider()
    st.write("**CPF:** 12345678901")
    st.write("**DATA DE NASCIMENTO:** 15/03/1985")
    
    st.divider()
    if st.button("🔄 Reiniciar Conversa"):
        st.session_state.messages = []
        st.session_state.orchestrator = AgentOrchestrator()
        st.session_state.session_manager = SessionManager()
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Initial greeting
if len(st.session_state.messages) == 0:
    initial_message = """Olá! Bem-vindo ao Banco Ágil! 👋

Sou seu assistente virtual e estou aqui para ajudá-lo com:
- 💳 Consulta e aumento de limite de crédito
- 💱 Cotação de moedas
- 📋 Entrevista para atualização de score
"""
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": initial_message
    })
    with st.chat_message("assistant"):
        st.write(initial_message)

# Chat input
if prompt := st.chat_input("Digite sua mensagem..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            try:
                response = st.session_state.orchestrator.process_message(
                    prompt,
                    st.session_state.session_manager
                )
                
                st.write(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                
            except Exception as e:
                error_msg = f"Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente. (Erro: {str(e)})"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer
st.divider()
st.caption("🔒 Banco Ágil - Todos os dados são fictícios para fins de demonstração")