"""
Tools for customer authentication and data access
"""

import json
from pydantic import Field, BaseModel
import pandas as pd
from langchain_core.tools import tool

class AuthSchema(BaseModel):
    cpf: str = Field(description="CPF do cliente")
    birthdate: str = Field(description="Data de nascimento do cliente no formato DD/MM/YYYY")

@tool("authenticate_customer", description="Authenticate customer by verifying CPF and birthdate.", args_schema=AuthSchema)
def authenticate_customer(cpf: str, birthdate: str) -> str:
    """Authenticate customer by verifying CPF and birthdate.
    Parameters:
    - cpf: string containing the CPF.
    - birthdate: birthdate in the format DD/MM/YYYY.
    """

    try:
        df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
        cpf_clean = ''.join(filter(str.isdigit, cpf))

        bd = birthdate.strip()
        if '-' in bd and '/' not in bd:
            parts = bd.split('-')
            if len(parts) == 3:
                bd = f"{parts[0]}/{parts[1]}/{parts[2]}"

        customer = df[df['cpf'] == cpf_clean]
        if customer.empty:
            return json.dumps({"error": "CPF não encontrado no sistema."})

        db_birthdate = str(customer.iloc[0]['data_nascimento'])
        db_birthdate_norm = db_birthdate.replace('-', '/')

        if db_birthdate != bd and db_birthdate_norm != bd:
            return json.dumps({"error": f"Data de nascimento incorreta. (Esperado formato similar a {db_birthdate})"})

        result = {
            "status": "success",
            "cpf": customer.iloc[0]['cpf'],
            "score": float(customer.iloc[0]['score']),
            "limite_credito": float(customer.iloc[0]['limite_credito'])
        }
        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": f"Erro técnico na validação: {str(e)}"})
