# services/order_manager.py
from typing import Dict, Optional

class OrderManager:
    def __init__(self, api_connector):
        self.api = api_connector

    def place_order(self, ticker: str, side: str, quantity: int, price: float) -> Optional[Dict]:
        """Отправка ордера (покупка/продажа)"""
        order = {
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "price": price
        }
        response = self.api.session.post(f"{self.api.api_url}/orders", json=order)
        return response.json() if response.status_code == 200 else None

    def cancel_order(self, order_id: str) -> bool:
        """Отмена ордера"""
        response = self.api.session.delete(f"{self.api.api_url}/orders/{order_id}")
        return response.status_code == 200