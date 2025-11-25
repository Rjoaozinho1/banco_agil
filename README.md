# 🏦 Banco Ágil - Sistema de Atendimento com Agentes de IA

Sistema de atendimento bancário inteligente utilizando múltiplos agentes especializados construído com LangChain, Groq API e Streamlit.

## 📋 Visão Geral

O Banco Ágil é um sistema de atendimento ao cliente que utiliza agentes de IA especializados para fornecer serviços bancários automatizados. Cada agente tem responsabilidades específicas e trabalha de forma coordenada para oferecer uma experiência fluida ao cliente.

## 🏗️ Arquitetura do Sistema

### Agentes Implementados

1. **Agente de Triagem** (`triage_agent.py`)
   - Porta de entrada do sistema
   - Realiza autenticação do cliente (CPF + data de nascimento)
   - Direciona para o agente apropriado
   - Permite até 3 tentativas de autenticação

2. **Agente de Crédito** (`credit_agent.py`)
   - Consulta limite de crédito disponível
   - Processa solicitações de aumento de limite
   - Valida aprovação com base no score do cliente
   - Oferece redirecionamento para entrevista em caso de reprovação

3. **Agente de Entrevista de Crédito** (`interview_agent.py`)
   - Conduz entrevista estruturada em 5 etapas
   - Coleta dados financeiros do cliente
   - Calcula novo score usando fórmula ponderada
   - Atualiza score na base de dados

4. **Agente de Câmbio** (`exchange_agent.py`)
   - Consulta cotações de moedas em tempo real
   - Utiliza API externa (Frankfurter API)
   - Apresenta cotações contra o Real (BRL)

### Orquestração

O sistema utiliza um **orquestrador simples** (`orchestrator.py`) que:
- Gerencia o fluxo entre agentes
- Mantém contexto da sessão
- Roteia mensagens para o agente ativo
- Detecta solicitações de encerramento

**Nota:** Não utiliza LangGraph - apenas um loop simples de roteamento.

### Gerenciamento de Estado

O `SessionManager` mantém:
- Estado de autenticação
- Dados do cliente autenticado
- Agente ativo atual
- Dados da entrevista em andamento
- Tentativas de autenticação

## 🎯 Funcionalidades Implementadas

### ✅ Autenticação
- Validação de CPF e data de nascimento
- Máximo de 3 tentativas
- Mensagens amigáveis de erro

### ✅ Consulta de Crédito
- Visualização de limite atual
- Exibição de score do cliente

### ✅ Aumento de Limite
- Solicitação de novo limite
- Validação automática baseada em score
- Registro em CSV com timestamp
- Atualização de limite se aprovado

### ✅ Entrevista de Crédito
- 5 perguntas estruturadas:
  1. Renda mensal
  2. Tipo de emprego (formal/autônomo/desempregado)
  3. Despesas fixas mensais
  4. Número de dependentes
  5. Existência de dívidas ativas
- Cálculo de score com fórmula ponderada
- Atualização automática na base de dados

### ✅ Cotação de Moedas
- Consulta em tempo real via API
- Suporte a principais moedas (USD, EUR, GBP, JPY, ARS)
- Apresentação formatada com data

### ✅ Tratamento de Erros
- Validação de entradas
- Tratamento de falhas de API
- Mensagens de erro amigáveis
- Fallbacks apropriados

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **LangChain** - Framework para agentes de IA
- **Groq API** - LLM inference (Llama 3.3 70B)
- **Streamlit** - Interface web interativa
- **Pandas** - Manipulação de dados CSV
- **Requests** - Chamadas para API de câmbio

## 📂 Estrutura do Projeto

```
banco-agil/
├── app.py                          # Aplicação Streamlit principal
├── config.py                       # Configurações e variáveis de ambiente
├── requirements.txt                # Dependências Python
├── .env.example                    # Exemplo de arquivo de ambiente
├── README.md                       # Esta documentação
│
├── agents/                         # Módulos dos agentes
│   ├── __init__.py
│   ├── orchestrator.py            # Orquestrador principal
│   ├── triage_agent.py            # Agente de triagem
│   ├── credit_agent.py            # Agente de crédito
│   ├── interview_agent.py         # Agente de entrevista
│   └── exchange_agent.py          # Agente de câmbio
│
├── tools/                          # Ferramentas LangChain
│   ├── __init__.py
│   ├── customer_tools.py          # Tools de cliente/autenticação
│   ├── credit_tools.py            # Tools de crédito
│   └── exchange_tools.py          # Tools de câmbio
│
├── utils/                          # Utilitários
│   ├── __init__.py
│   └── session_manager.py         # Gerenciador de sessão
│
└── data/                           # Dados CSV
    ├── clientes.csv               # Base de clientes
    ├── score_limite.csv           # Mapeamento score/limite
    └── solicitacoes_aumento_limite.csv  # Histórico de solicitações
```

## 🚀 Tutorial de Execução

### 1. Pré-requisitos

- Python 3.8 ou superior
- Conta Groq (para API key)

### 2. Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/banco-agil.git
cd banco-agil

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env e adicione sua GROQ_API_KEY
# Obtenha sua key em: https://console.groq.com/keys
```

### 4. Preparar Dados

Crie a pasta `data/` e os arquivos CSV:

```bash
mkdir data
```

Crie `data/clientes.csv`:
```csv
cpf,nome,data_nascimento,score,limite_credito
12345678901,João Silva,15/03/1985,650.0,5000.0
98765432100,Maria Santos,22/07/1990,720.0,8000.0
```

Crie `data/score_limite.csv`:
```csv
score_minimo,limite_maximo
0,1000
300,3000
500,5000
650,8000
750,12000
```

### 5. Executar

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

### 6. Testar

Use um dos CPFs de teste:
- CPF: `12345678901`
- Data: `15/03/1985`

Ou:
- CPF: `98765432100`
- Data: `22/07/1990`

## 🧪 Fluxos de Teste

### Teste 1: Consulta de Limite
1. Autenticar com CPF e data
2. Digitar: "quero consultar meu limite"
3. Sistema mostra limite atual

### Teste 2: Aumento de Limite Aprovado
1. Autenticar com CPF: 98765432100 (score 720)
2. Digitar: "quero aumentar meu limite"
3. Digitar: "10000"
4. Sistema aprova (score permite até 12000)

### Teste 3: Aumento Reprovado + Entrevista
1. Autenticar com CPF: 11122233344 (score 450)
2. Solicitar limite de 10000
3. Sistema reprova e oferece entrevista
4. Aceitar e responder perguntas
5. Novo score é calculado

### Teste 4: Cotação de Moeda
1. Autenticar
2. Digitar: "qual a cotação do dólar"
3. Sistema busca e mostra cotação atual

## 🎯 Desafios Enfrentados e Soluções

### 1. **Gerenciamento de Estado Entre Agentes**
**Desafio:** Manter contexto consistente ao transitar entre agentes.

**Solução:** Implementação do `SessionManager` centralizado que mantém:
- Estado de autenticação
- Dados do cliente
- Progresso da entrevista
- Agente ativo

### 2. **Extração de Dados Estruturados**
**Desafio:** Extrair CPF, datas e valores monetários de mensagens naturais.

**Solução:** Uso de regex patterns e validação explícita ao invés de depender apenas do LLM.

### 3. **Controle de Tokens e Custos**
**Desafio:** Minimizar uso de tokens mantendo boa UX.

**Solução:** 
- Respostas pré-escritas para fluxos comuns
- Lógica determinística quando possível
- LLM apenas para interpretação e decisões complexas

### 4. **Transições Suaves Entre Agentes**
**Desafio:** Fazer transições invisíveis ao usuário.

**Solução:** Mensagens de transição naturais que mantêm contexto e não mencionam "mudança de agente".

### 5. **Validação de Score vs Limite**
**Desafio:** Implementar lógica de aprovação baseada em tabela.

**Solução:** Tool dedicada que lê `score_limite.csv` e aplica regras de negócio.

## 💡 Escolhas Técnicas e Justificativas

### 1. **LangChain sem LangGraph**
- **Escolha:** Orquestração manual com loop simples
- **Justificativa:** 
  - Fluxo linear e previsível
  - Mais controle sobre transições
  - Menor complexidade
  - Mais fácil de debugar

### 2. **Groq API (Llama 3.3 70B)**
- **Escolha:** Groq com modelo Llama
- **Justificativa:**
  - Tier gratuito generoso
  - Latência muito baixa
  - Boa qualidade de resposta
  - API compatível com OpenAI

### 3. **Respostas Template + LLM Híbrido**
- **Escolha:** Mix de respostas prontas e geração
- **Justificativa:**
  - Reduz consumo de tokens
  - Respostas mais consistentes
  - Melhor controle de qualidade
  - LLM apenas quando necessário

### 4. **CSV ao Invés de Banco de Dados**
- **Escolha:** Pandas + CSV
- **Justificativa:**
  - Simplicidade para POC
  - Facilita testes e inspeção
  - Sem dependências extras
  - Suficiente para escala do desafio

### 5. **Validação Regex Para Dados Críticos**
- **Escolha:** Regex + validação determinística
- **Justificativa:**
  - CPF tem formato específico
  - Datas precisam ser válidas
  - Não confiar apenas no LLM
  - Evita erros de extração

## 🔒 Segurança e Boas Práticas

- ✅ API keys em variáveis de ambiente
- ✅ Validação de entrada em todas as tools
- ✅ Tratamento de exceções abrangente
- ✅ Limitação de tentativas de autenticação
- ✅ Dados sensíveis não expostos em logs

## 📈 Possíveis Melhorias Futuras

1. **Persistência:** Migrar para banco de dados real (PostgreSQL/MongoDB)
2. **Autenticação:** JWT tokens e sessões seguras
3. **Observabilidade:** Logging estruturado e métricas
4. **Testes:** Cobertura de testes unitários e integração
5. **Cache:** Redis para cotações e dados frequentes
6. **Async:** Processamento assíncrono para melhor performance
7. **Multi-modal:** Suporte a upload de documentos
8. **Analytics:** Dashboard para métricas de uso

## 📝 Licença

MIT License - veja LICENSE para detalhes

## 👤 Autor

Desenvolvido como parte do desafio técnico para Desenvolvedor de Agentes de IA.

## 🙏 Agradecimentos

- Groq pela API gratuita e rápida
- LangChain pela excelente framework
- Streamlit pela UI simples e eficaz