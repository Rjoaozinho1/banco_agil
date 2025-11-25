"""
Tools for customer authentication and data access
"""

import pandas as pd
from langchain.tools import BaseTool
from typing import Optional, Dict
import os

class AuthenticateCustomerTool(BaseTool):
    """Tool to authenticate customer against database"""
    
    name: str = "authenticate_customer"
    description: str = """
    Authenticate a customer using CPF and birthdate.
    Input should be a dictionary with 'cpf' and 'birthdate' keys.
    Returns customer data if authenticated, or error message if not.
    """

    def _run(self, cpf: str, birthdate: str) -> Dict:
        """Authenticate customer"""
        try:
            # Load customers database
            df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
            
            # Clean CPF (remove any formatting)
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            
            # Find customer
            customer = df[df['cpf'] == cpf_clean]
            
            if customer.empty:
                return {"error": "CPF not found"}
            
            # Check birthdate
            customer_birthdate = customer.iloc[0]['data_nascimento']
            if customer_birthdate != birthdate:
                return {"error": "Birthdate mismatch"}
            
            # Return customer data
            return {
                "cpf": customer.iloc[0]['cpf'],
                "data_nascimento": customer.iloc[0]['data_nascimento'],
                "score": float(customer.iloc[0]['score']),
                "limite_credito": float(customer.iloc[0]['limite_credito'])
            }
            
        except FileNotFoundError:
            return {"error": "Database not found"}
        except Exception as e:
            return {"error": f"Authentication error: {str(e)}"}
    
    def _arun(self, *args, **kwargs):
        """Async version not implemented"""
        raise NotImplementedError("Async not supported")


class GetCustomerDataTool(BaseTool):
    """Tool to get customer data by CPF"""
    
    name: str = "get_customer_data"
    description: str = """
    Get customer data by CPF.
    Input should be the customer's CPF.
    Returns customer information.
    """
    
    def _run(self, cpf: str) -> Dict:
        """Get customer data"""
        try:
            df = pd.read_csv('data/clientes.csv', dtype={'cpf': str})
            
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            customer = df[df['cpf'] == cpf_clean]
            
            if customer.empty:
                return {"error": "Customer not found"}

            return {
                "cpf": customer.iloc[0]['cpf'],
                "score": float(customer.iloc[0]['score']),
                "limite_credito": float(customer.iloc[0]['limite_credito'])
            }

        except Exception as e:
            return {"error": str(e)}

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")