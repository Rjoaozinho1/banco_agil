"""
Tools for currency exchange operations
"""

from pydantic import BaseModel, Field
from langchain_core.tools import tool
import requests

class ExchangeRateSchema(BaseModel):
    currency_code: str = Field(description="Código ISO da moeda (e.g., USD, EUR, GBP, JPY, ARS)")

@tool("get_exchange_rate", description="Obter a cotação atual da moeda contra BRL", args_schema=ExchangeRateSchema)
def get_exchange_rate(currency_code: str) -> str:
    try:
        code = currency_code.upper().strip()

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

        if code in currency_map:
            code = currency_map[code]

        supported = {"USD", "EUR", "GBP", "JPY", "ARS"}
        if code not in supported:
            return "Moeda não suportada. Informe um código válido: USD, EUR, GBP, JPY, ARS."

        url = f"https://api.frankfurter.app/latest?from={code}&to=BRL"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        rate_raw = data.get("rates", {}).get("BRL")
        try:
            rate = float(rate_raw) if rate_raw is not None else None
        except Exception:
            rate = None

        if rate is None:
            return "Não foi possível obter a cotação no momento. Tente novamente mais tarde."

        return f"{rate:.4f}"

    except requests.exceptions.Timeout:
        return "Desculpe, o serviço de cotação está demorando para responder. Tente novamente em alguns instantes."
    except requests.exceptions.RequestException:
        return "Não foi possível consultar a cotação no momento. Por favor, tente novamente mais tarde."
    except Exception as e:
        return f"Erro ao consultar cotação: {str(e)}"
