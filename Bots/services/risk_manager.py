# services/risk_manager.py
from typing import Dict, Optional

class RiskManager:
    def __init__(self, order_manager):
        self.order_manager = order_manager

    def check_stop_loss(self, current_price: float, stop_loss: float) -> bool:
        """Проверка на срабатывание стоп-лосса"""
        return current_price <= stop_loss

    def check_take_profit(self, current_price: float, take_profit: float) -> bool:
        """Проверка на срабатывание тейк-профита"""
        return current_price >= take_profit

    def close_position(self, ticker: str, position_type: str, quantity: int, price: float) -> Optional[Dict]:
        """Закрытие позиции по рынку или лимитной цене"""
        side = "sell" if position_type == "long" else "buy"
        return self.order_manager.place_order(ticker, side, quantity, price)