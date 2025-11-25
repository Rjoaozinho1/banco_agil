"""
Tools for credit operations
"""

import pandas as pd
from langchain.tools import BaseTool
from typing import Dict
from datetime import datetime
import os

class CheckCreditLimitTool(BaseTool):
    """Tool to check customer's current credit limit"""
    
    name: str = "check_credit_limit"
    description: str = """
    Check a customer's current credit limit and score.
    Input should be a dictionary with 'cpf' key.
    Returns credit limit and score information.
    """
    
    def _run(self, cpf: str) -> Dict:
        """Check credit limit"""
        try:
            df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
            
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            customer = df[df['cpf'] == cpf_clean]
            
            if customer.empty:
                return {"error": "Customer not found"}
            
            return {
                "cpf": cpf_clean,
                "limite_credito": float(customer.iloc[0]['limite_credito']),
                "score": float(customer.iloc[0]['score'])
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")


class RequestCreditIncreaseTool(BaseTool):
    """Tool to request credit limit increase"""
    
    name: str = "request_credit_increase"
    description: str = """
    Process a credit limit increase request.
    Input should be a dictionary with: cpf, current_limit, requested_limit, current_score.
    Returns approval status based on score requirements.
    """
    
    def _run(self, cpf: str, current_limit: float, requested_limit: float, current_score: float) -> Dict:
        """Process credit increase request"""
        try:
            # Load score-limit mapping
            score_df = pd.read_csv('data/score_limite.csv')
            
            # Check if requested limit is allowed for current score
            approved = False
            for _, row in score_df.iterrows():
                if current_score >= row['score_minimo'] and requested_limit <= row['limite_maximo']:
                    approved = True
                    break
            
            # Prepare request data
            timestamp = datetime.now().isoformat()
            status = "aprovado" if approved else "rejeitado"
            
            request_data = {
                "cpf_cliente": cpf,
                "data_hora_solicitacao": timestamp,
                "limite_atual": current_limit,
                "novo_limite_solicitado": requested_limit,
                "status_pedido": status
            }

            # Save to CSV
            requests_file = 'data/solicitacoes_aumento_limite.csv'
            
            if os.path.exists(requests_file):
                requests_df = pd.read_csv(requests_file)
                requests_df = pd.concat([requests_df, pd.DataFrame([request_data])], ignore_index=True)
            else:
                requests_df = pd.DataFrame([request_data])
            
            requests_df.to_csv(requests_file, index=False)
            
            # If approved, update customer's limit in clientes.csv
            if approved:
                customers_df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
                customers_df.loc[customers_df['cpf'] == cpf, 'limite_credito'] = requested_limit
                customers_df.to_csv('data/clientes.csv', index=False)
            
            return {
                "status": status,
                "cpf": cpf,
                "limite_atual": current_limit,
                "limite_solicitado": requested_limit,
                "timestamp": timestamp
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")


class UpdateCustomerScoreTool(BaseTool):
    """Tool to update customer's credit score"""
    
    name: str = "update_customer_score"
    description: str = """
    Update a customer's credit score after interview.
    Input should be a dictionary with 'cpf' and 'new_score' keys.
    Returns confirmation of update.
    """
    
    def _run(self, cpf: str, new_score: float) -> Dict:
        """Update customer score"""
        try:
            df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
            
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            
            # Get old score
            old_score = float(df[df['cpf'] == cpf_clean]['score'].iloc[0])
            
            # Update score
            df.loc[df['cpf'] == cpf_clean, 'score'] = new_score
            df.to_csv('data/clientes.csv', index=False)
            
            return {
                "cpf": cpf_clean,
                "old_score": old_score,
                "new_score": new_score,
                "updated": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")