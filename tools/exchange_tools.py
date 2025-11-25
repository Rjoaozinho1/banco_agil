"""
Tools for currency exchange operations
"""

from langchain.tools import BaseTool
from typing import Dict
import requests

class GetExchangeRateTool(BaseTool):
    """Tool to get real-time currency exchange rates"""
    
    name: str = "get_exchange_rate"
    description: str = """
    Get current exchange rate for a currency against BRL (Brazilian Real).
    Input should be the currency code (e.g., 'USD', 'EUR', 'GBP').
    Returns the current exchange rate and additional information.
    """
    
    def _run(self, currency_code: str) -> str:
        """Get exchange rate for specified currency"""
        try:
            # Normalize currency code
            currency_code = currency_code.upper().strip()
            
            # Map common names to codes
            currency_map = {
                "DOLAR": "USD",
                "DÓLAR": "USD",
                "EURO": "EUR",
                "LIBRA": "GBP",
                "IENE": "JPY",
                "YEN": "JPY",
                "PESO": "ARS",
                "PESO ARGENTINO": "ARS",
                "DOLAR AMERICANO": "USD",
                "USD": "USD",
                "EUR": "EUR",
                "GBP": "GBP",
                "JPY": "JPY",
                "ARS": "ARS"
            }
            
            if currency_code in currency_map:
                currency_code = currency_map[currency_code]
            
            supported = {"USD", "EUR", "GBP", "JPY", "ARS"}
            if currency_code not in supported:
                return (
                    "Moeda não suportada. Por favor informe um código ISO válido ou nome comum: "
                    "USD (Dólar), EUR (Euro), GBP (Libra), JPY (Iene/Yen), ARS (Peso Argentino)."
                )

            url = f"https://api.frankfurter.app/latest?from={currency_code}&to=BRL"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()

            try:
                rate = float(data.get("rates", {}).get("BRL"))
            except Exception:
                rate = None
            date = data.get("date")
            base = data.get("base", currency_code)

            if rate is None:
                return "Não foi possível obter a cotação no momento. Tente novamente mais tarde."

            return (
                f"1 {base} = {rate:.4f} BRL (data {date}). "
                "Você deseja consultar outra moeda?"
            )
            
        except requests.exceptions.Timeout:
            return "Desculpe, o serviço de cotação está demorando para responder. Por favor, tente novamente em alguns instantes."
        
        except requests.exceptions.RequestException as e:
            return f"Não foi possível consultar a cotação no momento. Por favor, tente novamente mais tarde."
        
        except Exception as e:
            return f"Erro ao consultar cotação: {str(e)}"
    
    def _arun(self, *args, **kwargs):
        """Async version not implemented"""
        raise NotImplementedError("Async not supported")
