import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


class Backtester:
    def __init__(self):
        self.data = None
        self.initial_capital = 10000
        self.max_trade_amount = 1000
        self.stop_loss = 0.05  # 5%
        self.take_profit = 0.10  # 10%
        self.strategy_params = {}
        self.trades = []
        self.portfolio_values = []

    def load_data_from_json(self, filename):
        """Загрузка исторических данных из JSON файла"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.data = pd.DataFrame(data)
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data.set_index('Date', inplace=True)
            print(f"Данные успешно загружены. Период: {self.data.index[0].date()} - {self.data.index[-1].date()}")
            return True
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return False

    def select_indicator(self):
        """Выбор технического индикатора"""
        print("\nДоступные индикаторы:")
        print("1. SMA (Простая скользящая средняя)")
        print("2. EMA (Экспоненциальная скользящая средняя)")
        print("3. RSI (Индекс относительной силы)")
        print("4. Bollinger Bands (Полосы Боллинджера)")

        choice = input("Выберите индикатор (1-4): ")

        if choice == '1':
            window = int(input("Введите период SMA (например, 20): "))
            self.strategy_params = {
                'indicator': 'SMA',
                'window': window,
                'column': 'Close'
            }
            self.data['indicator'] = SMAIndicator(self.data['Close'], window).sma_indicator()

        elif choice == '2':
            window = int(input("Введите период EMA (например, 20): "))
            self.strategy_params = {
                'indicator': 'EMA',
                'window': window,
                'column': 'Close'
            }
            self.data['indicator'] = EMAIndicator(self.data['Close'], window).ema_indicator()

        elif choice == '3':
            window = int(input("Введите период RSI (например, 14): "))
            overbought = int(input("Уровень перекупленности (например, 70): "))
            oversold = int(input("Уровень перепроданности (например, 30): "))
            self.strategy_params = {
                'indicator': 'RSI',
                'window': window,
                'overbought': overbought,
                'oversold': oversold,
                'column': 'Close'
            }
            self.data['indicator'] = RSIIndicator(self.data['Close'], window).rsi()

        elif choice == '4':
            window = int(input("Введите период (например, 20): "))
            std_dev = int(input("Количество стандартных отклонений (например, 2): "))
            self.strategy_params = {
                'indicator': 'Bollinger',
                'window': window,
                'std_dev': std_dev,
                'column': 'Close'
            }
            bb = BollingerBands(self.data['Close'], window, std_dev)
            self.data['indicator_upper'] = bb.bollinger_hband()
            self.data['indicator_lower'] = bb.bollinger_lband()

        else:
            print("Неверный выбор индикатора")
            return False

        return True

    def set_risk_parameters(self):
        """Установка параметров риска"""
        self.initial_capital = float(
            input(f"Начальный капитал (по умолчанию {self.initial_capital}): ") or self.initial_capital)
        self.max_trade_amount = float(
            input(f"Максимальная сумма сделки (по умолчанию {self.max_trade_amount}): ") or self.max_trade_amount)
        self.stop_loss = float(
            input(f"Стоп-лосс (% от цены входа, по умолчанию {self.stop_loss * 100}%): ") or self.stop_loss) / 100
        self.take_profit = float(
            input(f"Тейк-профит (% от цены входа, по умолчанию {self.take_profit * 100}%): ") or self.take_profit) / 100

    def run_backtest(self):
        """Запуск бэктеста"""
        if self.data is None:
            print("Данные не загружены")
            return

        capital = self.initial_capital
        position = 0
        entry_price = 0
        max_drawdown = 0
        peak = capital
        winning_trades = 0
        losing_trades = 0

        self.portfolio_values = [capital]
        self.trades = []

        for i in range(1, len(self.data)):
            current_price = self.data.iloc[i]['Close']
            prev_price = self.data.iloc[i - 1]['Close']

            # Сигналы для разных индикаторов
            signal = None
            if self.strategy_params['indicator'] == 'SMA' or self.strategy_params['indicator'] == 'EMA':
                if self.data.iloc[i - 1]['Close'] < self.data.iloc[i - 1]['indicator'] and current_price > \
                        self.data.iloc[i]['indicator']:
                    signal = 'buy'
                elif self.data.iloc[i - 1]['Close'] > self.data.iloc[i - 1]['indicator'] and current_price < \
                        self.data.iloc[i]['indicator']:
                    signal = 'sell'

            elif self.strategy_params['indicator'] == 'RSI':
                if self.data.iloc[i - 1]['indicator'] < self.strategy_params['oversold'] and current_price > prev_price:
                    signal = 'buy'
                elif self.data.iloc[i - 1]['indicator'] > self.strategy_params[
                    'overbought'] and current_price < prev_price:
                    signal = 'sell'

            elif self.strategy_params['indicator'] == 'Bollinger':
                if current_price < self.data.iloc[i]['indicator_lower']:
                    signal = 'buy'
                elif current_price > self.data.iloc[i]['indicator_upper']:
                    signal = 'sell'

            # Логика торговли
            if signal == 'buy' and position == 0 and capital > 0:
                trade_amount = min(capital, self.max_trade_amount)
                position = trade_amount / current_price
                entry_price = current_price
                capital -= trade_amount
                self.trades.append({
                    'date': self.data.index[i],
                    'type': 'buy',
                    'price': current_price,
                    'amount': trade_amount
                })

            elif signal == 'sell' and position > 0:
                trade_value = position * current_price
                capital += trade_value
                profit = trade_value - (position * entry_price)

                if profit > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1

                self.trades.append({
                    'date': self.data.index[i],
                    'type': 'sell',
                    'price': current_price,
                    'amount': trade_value,
                    'profit': profit
                })
                position = 0

            # Проверка стоп-лосса и тейк-профита
            elif position > 0:
                current_profit_pct = (current_price - entry_price) / entry_price

                if current_profit_pct <= -self.stop_loss:
                    trade_value = position * current_price
                    capital += trade_value
                    losing_trades += 1

                    self.trades.append({
                        'date': self.data.index[i],
                        'type': 'stop_loss',
                        'price': current_price,
                        'amount': trade_value,
                        'profit': trade_value - (position * entry_price)
                    })
                    position = 0

                elif current_profit_pct >= self.take_profit:
                    trade_value = position * current_price
                    capital += trade_value
                    winning_trades += 1

                    self.trades.append({
                        'date': self.data.index[i],
                        'type': 'take_profit',
                        'price': current_price,
                        'amount': trade_value,
                        'profit': trade_value - (position * entry_price)
                    })
                    position = 0

            # Расчет текущей стоимости портфеля
            portfolio_value = capital + (position * current_price if position > 0 else 0)
            self.portfolio_values.append(portfolio_value)

            # Расчет максимальной просадки
            if portfolio_value > peak:
                peak = portfolio_value
            drawdown = (peak - portfolio_value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Закрываем открытую позицию в конце периода
        if position > 0:
            trade_value = position * current_price
            capital += trade_value
            profit = trade_value - (position * entry_price)

            if profit > 0:
                winning_trades += 1
            else:
                losing_trades += 1

            self.trades.append({
                'date': self.data.index[-1],
                'type': 'close',
                'price': current_price,
                'amount': trade_value,
                'profit': profit
            })

        # Результаты
        total_return = (capital - self.initial_capital) / self.initial_capital * 100
        profit_factor = winning_trades / losing_trades if losing_trades > 0 else float('inf')

        print("\nРезультаты бэктеста:")
        print("=" * 50)
        print(f"Начальный капитал: ${self.initial_capital:.2f}")
        print(f"Конечный капитал: ${capital:.2f}")
        print(f"Общая доходность: {total_return:.2f}%")
        print(f"Прибыльные сделки: {winning_trades}")
        print(f"Убыточные сделки: {losing_trades}")
        print(f"Процент прибыльных сделок: {winning_trades / (winning_trades + losing_trades) * 100:.2f}%")
        print(f"Фактор прибыли: {profit_factor:.2f}")
        print(f"Максимальная просадка: {max_drawdown * 100:.2f}%")
        print("=" * 50)

        self.plot_results()

    def plot_results(self):
        """Визуализация результатов"""
        plt.figure(figsize=(12, 6))

        # График цены и индикатора
        plt.subplot(2, 1, 1)
        plt.plot(self.data.index, self.data['Close'], label='Цена закрытия')

        if self.strategy_params['indicator'] == 'SMA' or self.strategy_params['indicator'] == 'EMA':
            plt.plot(self.data.index, self.data['indicator'],
                     label=f"{self.strategy_params['indicator']}({self.strategy_params['window']})")
        elif self.strategy_params['indicator'] == 'RSI':
            plt.plot(self.data.index, self.data['indicator'], label='RSI')
            plt.axhline(y=self.strategy_params['overbought'], color='r', linestyle='--')
            plt.axhline(y=self.strategy_params['oversold'], color='g', linestyle='--')
        elif self.strategy_params['indicator'] == 'Bollinger':
            plt.plot(self.data.index, self.data['indicator_upper'], label='Верхняя полоса')
            plt.plot(self.data.index, self.data['indicator_lower'], label='Нижняя полоса')

        # Отметки сделок
        buy_dates = [t['date'] for t in self.trades if t['type'] == 'buy']
        buy_prices = [t['price'] for t in self.trades if t['type'] == 'buy']
        plt.scatter(buy_dates, buy_prices, color='g', label='Покупка', marker='^')

        sell_dates = [t['date'] for t in self.trades if t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
        sell_prices = [t['price'] for t in self.trades if t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
        colors = ['r' if t['profit'] < 0 else 'g' for t in self.trades if
                  t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
        plt.scatter(sell_dates, sell_prices, color=colors, label='Продажа', marker='v')

        plt.title('График цены и торговых сигналов')
        plt.legend()

        # График стоимости портфеля
        plt.subplot(2, 1, 2)
        plt.plot(self.data.index, self.portfolio_values[1:], label='Стоимость портфеля')
        plt.title('Динамика портфеля')
        plt.xlabel('Дата')
        plt.ylabel('Стоимость ($)')
        plt.legend()

        plt.tight_layout()
        plt.show()


def main():
    print("Сервис бэктестинга торговых стратегий")
    print("=" * 50)

    backtester = Backtester()

    # Загрузка данных
    while True:
        filename = input("Введите путь к JSON файлу с историческими данными: ")
        if backtester.load_data_from_json(filename):
            break

    # Выбор стратегии
    while True:
        if backtester.select_indicator():
            break

    # Настройка параметров
    backtester.set_risk_parameters()

    # Запуск бэктеста
    backtester.run_backtest()


if __name__ == "__main__":
    main()