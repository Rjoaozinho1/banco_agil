"""
Tools for credit operations
"""

import os
import json
import pandas as pd
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CheckCreditLimitArgsSchema(BaseModel):
    cpf: str = Field(description="CPF do cliente")

class RequestCreditIncreaseArgsSchema(BaseModel):
    cpf: str = Field(description="CPF do cliente")
    requested_limit: float = Field(description="Novo limite desejado pelo cliente")

class UpdateCustomerScoreArgsSchema(BaseModel):
    cpf: str = Field(description="CPF do cliente")
    new_score: float = Field(description="Novo score calculado")


@tool("check_credit_limit", description="Verifica limite e score. Use para consultas de saldo ou situação atual.", args_schema=CheckCreditLimitArgsSchema)
def check_credit_limit(cpf: str) -> str:
    try:
        print(f"[CreditTool] check_credit_limit start cpf={cpf}")
        
        df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        print(f"[CreditTool] cpf_clean={cpf_clean}")
        
        customer = df[df['cpf'] == cpf_clean]
        if customer.empty:
            print("[CreditTool] customer not found")
            return json.dumps({"error": "Cliente não encontrado"})
       
        result = {
            "cpf": cpf_clean,
            "limite_credito": float(customer.iloc[0]['limite_credito']),
            "score": float(customer.iloc[0]['score'])
        }
        
        print(f"[CreditTool] check_credit_limit result={result}")
        
        return json.dumps(result)
    
    except Exception as e:
        print(f"[CreditTool] check_credit_limit error={e}")
        return json.dumps({"error": str(e)})


@tool("request_credit_increase", description="Solicita aumento de limite. Requer CPF e o valor desejado.", args_schema=RequestCreditIncreaseArgsSchema)
def request_credit_increase(cpf: str, requested_limit: float) -> str:
    try:
        print(f"[CreditTool] request_credit_increase start cpf={cpf} requested_limit={requested_limit}")
     
        df_clientes = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        print(f"[CreditTool] cpf_clean={cpf_clean}")
     
        customer = df_clientes[df_clientes['cpf'] == cpf_clean]
        if customer.empty:
            print("[CreditTool] customer not found for increase")
            return json.dumps({"error": "Cliente não encontrado para processar aumento"})
     
        current_limit = float(customer.iloc[0]['limite_credito'])
        current_score = float(customer.iloc[0]['score'])
        print(f"[CreditTool] current_limit={current_limit} current_score={current_score}")
     
        score_df = pd.read_csv('data/score_limite.csv')
        approved = False
        for _, row in score_df.iterrows():
            if current_score >= row['score_minimo'] and requested_limit <= row['limite_maximo']:
                approved = True
                break
     
        status = "aprovado" if approved else "rejeitado"
        print(f"[CreditTool] increase status={status}")
     
        request_data = {
            "cpf_cliente": cpf_clean,
            "data_hora_solicitacao": datetime.now().isoformat(),
            "limite_atual": current_limit,
            "novo_limite_solicitado": requested_limit,
            "status_pedido": status
        }
     
        file_path = 'data/solicitacoes_aumento_limite.csv'
        new_row = pd.DataFrame([request_data])
     
        if os.path.exists(file_path):
            pd.concat([pd.read_csv(file_path), new_row], ignore_index=True).to_csv(file_path, index=False)
        else:
            new_row.to_csv(file_path, index=False)
     
        print("[CreditTool] increase request recorded")
        if approved:
            df_clientes.loc[df_clientes['cpf'] == cpf_clean, 'limite_credito'] = requested_limit
            df_clientes.to_csv('data/clientes.csv', index=False)
            print("[CreditTool] limit updated in clientes.csv")
     
        result = {
            "status": status,
            "limite_atual": current_limit if not approved else requested_limit,
            "mensagem": "Aprovado com sucesso" if approved else "Negado por score insuficiente"
        }
        print(f"[CreditTool] request_credit_increase result={result}")
     
        return json.dumps(result)
    
    except Exception as e:
        print(f"[CreditTool] request_credit_increase error={e}")
        return json.dumps({"error": str(e)})


@tool("update_customer_score", description="Atualiza o score de crédito do cliente.", args_schema=UpdateCustomerScoreArgsSchema)
def update_customer_score(cpf: str, new_score: float) -> str:
    try:
        print(f"[CreditTool] update_customer_score start cpf={cpf} new_score={new_score}")
        df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
        
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        print(f"[CreditTool] cpf_clean={cpf_clean}")
        
        old_score = float(df[df['cpf'] == cpf_clean]['score'].iloc[0])
        print(f"[CreditTool] old_score={old_score}")
        
        df.loc[df['cpf'] == cpf_clean, 'score'] = new_score
        df.to_csv('data/clientes.csv', index=False)
        print("[CreditTool] score updated in clientes.csv")
        
        result = {
            "cpf": cpf_clean,
            "old_score": old_score,
            "new_score": new_score,
            "updated": True
        }
        print(f"[CreditTool] update_customer_score result={result}")
        
        return json.dumps(result)
    except Exception as e:
        print(f"[CreditTool] update_customer_score error={e}")
        return json.dumps({"error": str(e)})
