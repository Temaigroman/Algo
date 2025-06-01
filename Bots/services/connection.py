# services/api_connector.py
import requests
from typing import Dict, Any

class APIConnector:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def get_market_data(self, ticker: str) -> Dict[str, Any]:
        """Получение рыночных данных (например, через MOEX ISS или брокерский API)"""
        response = self.session.get(f"{self.api_url}/marketdata/{ticker}")
        return response.json()

    def get_account_info(self) -> Dict[str, Any]:
        """Получение информации о счете"""
        response = self.session.get(f"{self.api_url}/account")
        return response.json()