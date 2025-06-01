# bot.py
from services.api_connector import APIConnector
from services.order_manager import OrderManager
from services.risk_manager import RiskManager
from services.money_manager import MoneyManager

class TradingBot:
    def __init__(self, api_url: str, api_key: str):
        self.api = APIConnector(api_url, api_key)
        self.order_manager = OrderManager(self.api)
        self.risk_manager = RiskManager(self.order_manager)
        self.money_manager = MoneyManager(self.api)

    def run_strategy(self, ticker: str, strategy_config: Dict):
        """Основная логика торгового алгоритма"""
        data = self.api.get_market_data(ticker)
        current_price = data["last_price"]

        # Пример стратегии: покупка при пробитии SMA50
        if self._check_buy_condition(data, strategy_config):
            entry_price = current_price
            stop_loss = entry_price * 0.95  # Стоп-лосс 5%
            take_profit = entry_price * 1.10  # Тейк-профит 10%

            # Расчет позиции с учетом риска
            quantity = self.money_manager.calculate_position_size(ticker, entry_price, stop_loss)
            if quantity > 0:
                self.order_manager.place_order(ticker, "buy", quantity, entry_price)

                # Мониторинг позиции
                while True:
                    data = self.api.get_market_data(ticker)
                    current_price = data["last_price"]

                    if self.risk_manager.check_stop_loss(current_price, stop_loss) or \
                       self.risk_manager.check_take_profit(current_price, take_profit):
                        self.risk_manager.close_position(ticker, "long", quantity, current_price)
                        break

    def _check_buy_condition(self, data: Dict, config: Dict) -> bool:
        """Логика входа в сделку (пример: SMA50 > SMA200)"""
        sma_50 = data["sma_50"]
        sma_200 = data["sma_200"]
        return sma_50 > sma_200

# Пример использования
if __name__ == "__main__":
    bot = TradingBot(api_url="https://moex-api.example.com", api_key="your_api_key")
    bot.run_strategy("GAZP", {"sma_period": 50})