# services/money_manager.py

class MoneyManager:
    def __init__(self, api_connector, max_risk_per_trade: float = 0.02):
        self.api = api_connector
        self.max_risk_per_trade = max_risk_per_trade  # Максимальный риск на сделку (2%)

    def calculate_position_size(self, ticker: str, entry_price: float, stop_loss: float) -> int:
        """Расчет размера позиции на основе риска и стоп-лосса"""
        account_info = self.api.get_account_info()
        balance = account_info.get("balance", 0)
        risk_amount = balance * self.max_risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        if price_diff == 0:
            return 0
        position_size = int(risk_amount / price_diff)
        return min(position_size, account_info.get("available_lots", 0))