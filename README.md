# 🏦 Banco Ágil - Sistema de Atendimento com Agentes de IA

Sistema de atendimento bancário inteligente utilizando múltiplos agentes especializados construído com LangChain, Groq API e Streamlit.

## 📋 Visão Geral

O Banco Ágil é um sistema de atendimento ao cliente que utiliza agentes de IA especializados para fornecer serviços bancários automatizados. Cada agente tem responsabilidades específicas e trabalha de forma coordenada para oferecer uma experiência fluida ao cliente.

Este repositório contempla uma prova de conceito completa com:
- Autenticação determinística de clientes por CPF e data de nascimento
- Operações de crédito (consulta de limite e aumento de limite)
- Entrevista estruturada para recalcular score de crédito
- Cotação de moedas em tempo real via API externa
- Orquestração simples entre agentes com manutenção de contexto de sessão

Objetivo da entrega: disponibilizar um projeto executável, com documentação clara e testes de uso que permitam validar todos os fluxos de ponta a ponta.

## 🏗️ Arquitetura do Sistema

### Agentes Implementados

1. **Agente de Triagem** (`agents/triage_agent.py`)
   - Porta de entrada do sistema
   - Realiza autenticação do cliente (CPF + data de nascimento)
   - Direciona para o agente apropriado (câmbio, crédito, entrevista)
   - Permite até 3 tentativas de autenticação
   - Referências: `agents/triage_agent.py:26` (prompt do sistema), `agents/triage_agent.py:99` (processamento e roteamento), `utils/session_manager.py:48` (contagem de tentativas)

2. **Agente de Crédito** (`agents/credit_agent.py`)
   - Consulta limite de crédito disponível
   - Processa solicitações de aumento de limite
   - Valida aprovação com base no score do cliente
   - Oferece redirecionamento para entrevista em caso de reprovação
   - Referências: `agents/credit_agent.py:80` (consulta limite), `agents/credit_agent.py:100` (processar aumento), `agents/credit_agent.py:198` (classificação de intenção)

3. **Agente de Entrevista de Crédito** (`agents/interview_agent.py`)
   - Conduz entrevista estruturada em 5 etapas
   - Coleta dados financeiros do cliente
   - Calcula novo score usando fórmula ponderada
   - Atualiza score na base de dados
   - Referências: `agents/interview_agent.py:49` (processo da entrevista), `agents/interview_agent.py:193` (finalização e atualização), `agents/interview_agent.py:253` (cálculo do score)

4. **Agente de Câmbio** (`agents/exchange_agent.py`)
   - Consulta cotações de moedas em tempo real
   - Utiliza API externa (Frankfurter API)
   - Apresenta cotações contra o Real (BRL)
   - Referências: `agents/exchange_agent.py:24` (prompt e tool), `tools/exchange_tools.py:53` (endpoint), `tools/exchange_tools.py:75` (tratamento de timeout)

### Orquestração

O sistema utiliza um **orquestrador simples** (`agents/orchestrator.py`) que:
- Gerencia o fluxo entre agentes
- Mantém contexto da sessão
- Roteia mensagens para o agente ativo
- Detecta solicitações de encerramento

Fluxo textual de alto nível:
- Usuário inicia → Triagem autentica → Classificação da intenção → Roteamento para Crédito/Entrevista/Câmbio → Resposta → Possível transição → Encerramento.

Referências: `agents/orchestrator.py:10` (instanciação de agentes), `agents/orchestrator.py:19` (processamento), `agents/orchestrator.py:54` (encerramento).

**Nota:** Não utiliza LangGraph - apenas um loop simples de roteamento.

### Gerenciamento de Estado

O `SessionManager` mantém:
- Estado de autenticação
- Dados do cliente autenticado
- Agente ativo atual
- Dados da entrevista em andamento
- Tentativas de autenticação
Referências: `utils/session_manager.py:10` (estado inicial), `utils/session_manager.py:41` (set_customer_data), `utils/session_manager.py:56` (switch_agent), `utils/session_manager.py:61` (score), `utils/session_manager.py:67` (limite).

## 🧩 Ferramentas (Tools) e Assinaturas

- `AuthenticateCustomerTool(cpf, birthdate) -> Dict`
  - Autentica cliente contra `data/clientes.csv`
  - Referências: `tools/customer_tools.py:10` (definição), `tools/customer_tools.py:20` (execução)

- `GetCustomerDataTool(cpf) -> Dict`
  - Obtém dados do cliente
  - Referências: `tools/customer_tools.py:58` (definição), `tools/customer_tools.py:68`

- `CheckCreditLimitTool(cpf) -> {limite_credito, score}`
  - Consulta limite e score
  - Referências: `tools/credit_tools.py:11` (definição), `tools/credit_tools.py:21`

- `RequestCreditIncreaseTool(cpf, current_limit, requested_limit, current_score) -> {status, ...}`
  - Processa aumento de limite; escreve em `data/solicitacoes_aumento_limite.csv` e atualiza `clientes.csv` se aprovado
  - Referências: `tools/credit_tools.py:51`, `tools/credit_tools.py:93`, `tools/credit_tools.py:105`

- `UpdateCustomerScoreTool(cpf, new_score) -> {old_score, new_score}`
  - Atualiza o score do cliente
  - Referências: `tools/credit_tools.py:129`, `tools/credit_tools.py:139`

- `GetExchangeRateTool(currency_code) -> string`
  - Consulta cotação via Frankfurter API `https://api.frankfurter.app/latest?from={CODE}&to=BRL`
  - Referências: `tools/exchange_tools.py:53` (endpoint), `tools/exchange_tools.py:75` (timeout), `tools/exchange_tools.py:78` (erros de rede)

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

## 🔐 Segurança e Boas Práticas

- API keys em variáveis de ambiente (`.env`)
- Validação de entradas e regex (CPF, datas, valores)
- Tratamento de exceções abrangente com mensagens amigáveis
- Limitação de tentativas de autenticação (`MAX_AUTH_ATTEMPTS`)
- Dados sensíveis não expostos em logs

Referências: `config.py:11` (GROQ), `agents/triage_agent.py:51` (CPF), `agents/triage_agent.py:58` (datas), `agents/credit_agent.py:173` (valores), `utils/session_manager.py:52` (retentativas).

## 👀 Observabilidade

- Logs via `print` nos agentes e tools para:
  - Classificação de intenção/ação
  - Parâmetros de entrada e resultados das tools
  - Transições de estado
- Sugestões de evolução: `logging` estruturado, níveis, IDs de correlação por sessão/CPF.

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

## 🗃️ Dados e Esquemas

- `data/clientes.csv`
  - Colunas: `cpf,data_nascimento,score,limite_credito`
  - Exemplo: `12345678901,15/03/1985,650.0,5000.0`
- `data/score_limite.csv`
  - Colunas: `score_minimo,limite_maximo`
  - Exemplo: `650,8000`
- `data/solicitacoes_aumento_limite.csv`
  - Colunas: `cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido`
  - Alimentado automaticamente ao solicitar aumento de limite

## 🚀 Tutorial de Execução

### 1. Pré-requisitos

- Python 3.8 ou superior
- Conta Groq (para API key)

### 2. Instalação

```bash
# Clone o repositório
git clone https://github.com/Rjoaozinho1/banco_agil.git
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

## 🐳 Execução com Docker

### 1) Docker Compose (Linux e Windows)

- Arquivo: `docker-compose.yml`
- Comandos:
  - Linux / macOS:
    ```bash
    docker compose up --build
    # Parar
    docker compose down
    ```
  - Windows (Docker Desktop):
    ```powershell
    docker compose up --build
    # Parar
    docker compose down
    ```
  - Alternativa (plugin legado):
    ```bash
    docker-compose up --build
    docker-compose down
    ```

- Observações:
  - O compose lê `.env` via `env_file` e monta `./data` em `/app/data` no container
  - Certifique-se que `data/` contém `clientes.csv` e `score_limite.csv`
  - Logs e erros aparecerão no terminal do container

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

Critérios de Aceitação:
- Mensagens claras e consistentes em cada etapa
- Persistência em CSV quando aplicável
- Atualização de score visível após entrevista
- Fallback amigável em falhas de API

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

## 🧯 Troubleshooting

- Erro `GROQ_API_KEY not found` ao iniciar
  - Verifique `.env` e variáveis de ambiente (`config.py:15`)

- Falta de arquivos em `data/`
  - Crie a pasta e CSVs conforme esquemas desta documentação

- Timeout/erro na Frankfurter API
  - Tente novamente; verifique conectividade (`tools/exchange_tools.py:75`)

- Erros ao ler/escrever CSV
  - Cheque permissões e caminhos relativos; feche arquivos abertos

## 📈 Possíveis Melhorias Futuras

1. **Persistência:** Migrar para banco de dados real (PostgreSQL/MongoDB)
2. **Autenticação:** JWT tokens e sessões seguras
3. **Observabilidade:** Logging estruturado e métricas
4. **Testes:** Cobertura de testes unitários e integração
5. **Cache:** Redis para cotações e dados frequentes
6. **Async:** Processamento assíncrono para melhor performance
7. **Multi-modal:** Suporte a upload de documentos
8. **Analytics:** Dashboard para métricas de uso

## ✅ Checklist de Aceite

- README completo, com instalação, execução e testes
- Multiagente funcional: triagem, crédito, entrevista e câmbio
- Autenticação robusta com até 3 tentativas
- Consulta de limite e persistência de solicitações de aumento
- Entrevista estruturada com recalculo e atualização de score
- Cotações reais via API com tratamento de erros
- Logs básicos para acompanhamento do fluxo
- Dados CSV prontos e esquemas documentados

## 📝 Licença

MIT License - veja LICENSE para detalhes

## 👤 Autor

Desenvolvido como parte do desafio técnico para Desenvolvedor de Agentes de IA.

## 🙏 Agradecimentos

- Groq pela API gratuita e rápida
- LangChain pela excelente framework
- Streamlit pela UI simples e eficaz
