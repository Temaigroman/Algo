import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import matplotlib
import tempfile
import os


class Backtester:
    def __init__(self):
        self.data = None
        self.initial_capital = 10000
        self.max_trade_amount = 1000
        self.stop_loss = 0.05  # 5%
        self.take_profit = 0.10  # 10%
        self.strategy_params = {
            'indicators': [],
            'logic': 'AND'
        }
        self.trades = []
        self.portfolio_values = []

    def load_data_from_json(self, data):
        """Загрузка исторических данных из JSON объекта"""
        try:
            if isinstance(data, str):
                # Если передана строка, пытаемся загрузить как JSON
                data = json.loads(data)

            self.data = pd.DataFrame(data['data'])
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data.set_index('Date', inplace=True)

            # Сохраняем метаданные если они есть
            self.ticker = data.get('ticker', 'UNKNOWN')
            self.start_date = data.get('startDate', self.data.index[0].date())
            self.end_date = data.get('endDate', self.data.index[-1].date())
            self.interval = data.get('interval', '1d')

            return True
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return False

    def add_indicator(self, indicator_type, params=None):
        """Добавление индикатора"""
        if params is None:
            params = {}

        if indicator_type == 'SMA':
            window = params.get('window', 20)
            self.data[f'sma_{window}'] = SMAIndicator(self.data['Close'], window).sma_indicator()
            self.strategy_params['indicators'].append({
                'type': 'SMA',
                'window': window,
                'column': 'Close'
            })

        elif indicator_type == 'EMA':
            window = params.get('window', 20)
            self.data[f'ema_{window}'] = EMAIndicator(self.data['Close'], window).ema_indicator()
            self.strategy_params['indicators'].append({
                'type': 'EMA',
                'window': window,
                'column': 'Close'
            })

        elif indicator_type == 'RSI':
            window = params.get('window', 14)
            overbought = params.get('overbought', 70)
            oversold = params.get('oversold', 30)
            self.data[f'rsi_{window}'] = RSIIndicator(self.data['Close'], window).rsi()
            self.strategy_params['indicators'].append({
                'type': 'RSI',
                'window': window,
                'overbought': overbought,
                'oversold': oversold,
                'column': 'Close'
            })

        elif indicator_type == 'Bollinger':
            window = params.get('window', 20)
            std_dev = params.get('std_dev', 2)
            bb = BollingerBands(self.data['Close'], window, std_dev)
            self.data[f'bb_upper_{window}'] = bb.bollinger_hband()
            self.data[f'bb_lower_{window}'] = bb.bollinger_lband()
            self.strategy_params['indicators'].append({
                'type': 'Bollinger',
                'window': window,
                'std_dev': std_dev,
                'column': 'Close'
            })

        elif indicator_type == 'MACD':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            macd = MACD(self.data['Close'], window_fast=fast, window_slow=slow, window_sign=signal)
            self.data['macd'] = macd.macd()
            self.data['macd_signal'] = macd.macd_signal()
            self.data['macd_hist'] = macd.macd_diff()
            self.strategy_params['indicators'].append({
                'type': 'MACD',
                'fast': fast,
                'slow': slow,
                'signal': signal,
                'column': 'Close'
            })

        else:
            print(f"Неизвестный тип индикатора: {indicator_type}")
            return False

        return True

    def set_strategy_parameters(self, indicators, logic='AND'):
        """Установка параметров стратегии"""
        self.strategy_params = {
            'indicators': indicators,
            'logic': logic
        }

        # Добавляем индикаторы в данные
        for indicator in indicators:
            self.add_indicator(indicator['type'], indicator)

    def set_risk_parameters(self, initial_capital=10000, max_trade_amount=1000,
                            stop_loss=0.05, take_profit=0.10):
        """Установка параметров риска"""
        self.initial_capital = float(initial_capital)
        self.max_trade_amount = float(max_trade_amount)
        self.stop_loss = float(stop_loss)
        self.take_profit = float(take_profit)

    def get_signal(self, i):
        """Генерация торгового сигнала"""
        if not self.strategy_params['indicators']:
            return None

        signals = []
        current_price = self.data.iloc[i]['Close']
        prev_price = self.data.iloc[i - 1]['Close']

        for indicator in self.strategy_params['indicators']:
            ind_type = indicator['type']

            if ind_type == 'SMA' or ind_type == 'EMA':
                col = f"{ind_type.lower()}_{indicator['window']}"
                if (prev_price < self.data.iloc[i - 1][col] and
                        current_price > self.data.iloc[i][col]):
                    signals.append('buy')
                elif (prev_price > self.data.iloc[i - 1][col] and
                      current_price < self.data.iloc[i][col]):
                    signals.append('sell')
                else:
                    signals.append(None)

            elif ind_type == 'RSI':
                col = f"rsi_{indicator['window']}"
                rsi = self.data.iloc[i - 1][col]
                if (rsi < indicator['oversold'] and
                        current_price > prev_price):
                    signals.append('buy')
                elif (rsi > indicator['overbought'] and
                      current_price < prev_price):
                    signals.append('sell')
                else:
                    signals.append(None)

            elif ind_type == 'Bollinger':
                upper = f"bb_upper_{indicator['window']}"
                lower = f"bb_lower_{indicator['window']}"
                if current_price < self.data.iloc[i][lower]:
                    signals.append('buy')
                elif current_price > self.data.iloc[i][upper]:
                    signals.append('sell')
                else:
                    signals.append(None)

            elif ind_type == 'MACD':
                macd = self.data.iloc[i]['macd']
                signal = self.data.iloc[i]['macd_signal']
                hist = self.data.iloc[i]['macd_hist']
                prev_hist = self.data.iloc[i - 1]['macd_hist']

                if macd > signal and hist > 0 and prev_hist <= 0:
                    signals.append('buy')
                elif macd < signal and hist < 0 and prev_hist >= 0:
                    signals.append('sell')
                else:
                    signals.append(None)

        valid_signals = [s for s in signals if s is not None]
        if not valid_signals:
            return None

        if self.strategy_params['logic'] == 'AND':
            if all(s == 'buy' for s in valid_signals):
                return 'buy'
            elif all(s == 'sell' for s in valid_signals):
                return 'sell'
        else:
            if 'buy' in valid_signals:
                return 'buy'
            elif 'sell' in valid_signals:
                return 'sell'

        return None

    def run_backtest(self):
        """Запуск бэктеста и возврат результатов"""
        if self.data is None:
            return {'error': 'Data not loaded'}

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
            signal = self.get_signal(i)
            current_price = self.data.iloc[i]['Close']

            if signal == 'buy' and position == 0 and capital > 0:
                trade_amount = min(capital, self.max_trade_amount)
                position = trade_amount / current_price
                entry_price = current_price
                capital -= trade_amount
                self.trades.append({
                    'date': self.data.index[i].isoformat(),
                    'type': 'buy',
                    'price': current_price,
                    'amount': trade_amount,
                    'profit': None
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
                    'date': self.data.index[i].isoformat(),
                    'type': 'sell',
                    'price': current_price,
                    'amount': trade_value,
                    'profit': profit
                })
                position = 0

            elif position > 0:
                current_profit_pct = (current_price - entry_price) / entry_price

                if current_profit_pct <= -self.stop_loss:
                    trade_value = position * current_price
                    capital += trade_value
                    losing_trades += 1

                    self.trades.append({
                        'date': self.data.index[i].isoformat(),
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
                        'date': self.data.index[i].isoformat(),
                        'type': 'take_profit',
                        'price': current_price,
                        'amount': trade_value,
                        'profit': trade_value - (position * entry_price)
                    })
                    position = 0

            portfolio_value = capital + (position * current_price if position > 0 else 0)
            self.portfolio_values.append(portfolio_value)

            if portfolio_value > peak:
                peak = portfolio_value
            drawdown = (peak - portfolio_value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        if position > 0:
            trade_value = position * current_price
            capital += trade_value
            profit = trade_value - (position * entry_price)

            if profit > 0:
                winning_trades += 1
            else:
                losing_trades += 1

            self.trades.append({
                'date': self.data.index[-1].isoformat(),
                'type': 'close',
                'price': current_price,
                'amount': trade_value,
                'profit': profit
            })

        total_return = (capital - self.initial_capital) / self.initial_capital * 100
        profit_factor = winning_trades / losing_trades if losing_trades > 0 else float('inf')

        return {
            'initial_capital': self.initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'max_drawdown': max_drawdown * 100,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'profit_factor': profit_factor,
            'trades': self.trades,
            'portfolio_values': self.portfolio_values,
            'equity_curve': [{'date': self.data.index[i].isoformat(), 'value': val}
                             for i, val in enumerate(self.portfolio_values[1:], 1)]
        }

    def plot_results(self, save_path=None):
        """Визуализация результатов (для использования в CLI)"""
        if not self.data or not self.trades:
            return False

        try:
            plt.figure(figsize=(14, 8))
            n_plots = 2 + len(self.strategy_params['indicators'])

            # График цены и сделок
            plt.subplot(n_plots, 1, 1)
            plt.plot(self.data.index, self.data['Close'], label='Цена закрытия')

            buy_dates = [pd.to_datetime(t['date']) for t in self.trades if t['type'] == 'buy']
            buy_prices = [t['price'] for t in self.trades if t['type'] == 'buy']
            plt.scatter(buy_dates, buy_prices, color='g', label='Покупка', marker='^')

            sell_dates = [pd.to_datetime(t['date']) for t in self.trades
                          if t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
            sell_prices = [t['price'] for t in self.trades
                           if t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
            colors = ['r' if t['profit'] < 0 else 'g' for t in self.trades
                      if t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
            plt.scatter(sell_dates, sell_prices, color=colors, label='Продажа', marker='v')

            plt.title('График цены и торговых сигналов')
            plt.legend()

            # График стоимости портфеля
            plt.subplot(n_plots, 1, 2)
            plt.plot(self.data.index[1:], self.portfolio_values[1:], label='Стоимость портфеля')
            plt.title('Динамика портфеля')
            plt.ylabel('Стоимость ($)')
            plt.legend()

            # Графики индикаторов
            for idx, indicator in enumerate(self.strategy_params['indicators'], 3):
                plt.subplot(n_plots, 1, idx)
                ind_type = indicator['type']

                if ind_type in ['SMA', 'EMA']:
                    col = f"{ind_type.lower()}_{indicator['window']}"
                    plt.plot(self.data.index, self.data[col],
                             label=f"{ind_type}({indicator['window']})")
                    plt.ylabel(f"{ind_type} Value")

                elif ind_type == 'RSI':
                    col = f"rsi_{indicator['window']}"
                    plt.plot(self.data.index, self.data[col], label='RSI')
                    plt.axhline(y=indicator['overbought'], color='r', linestyle='--')
                    plt.axhline(y=indicator['oversold'], color='g', linestyle='--')
                    plt.ylabel('RSI Value')

                elif ind_type == 'Bollinger':
                    upper = f"bb_upper_{indicator['window']}"
                    lower = f"bb_lower_{indicator['window']}"
                    plt.plot(self.data.index, self.data[upper], label='Верхняя полоса')
                    plt.plot(self.data.index, self.data[lower], label='Нижняя полоса')
                    plt.ylabel('Bollinger Bands')

                elif ind_type == 'MACD':
                    plt.plot(self.data.index, self.data['macd'], label='MACD')
                    plt.plot(self.data.index, self.data['macd_signal'], label='Signal')
                    plt.bar(self.data.index, self.data['macd_hist'],
                            label='Histogram', color='gray', alpha=0.5)
                    plt.ylabel('MACD')

                plt.legend()

            plt.xlabel('Дата')
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                plt.close()
                return save_path
            else:
                plt.show()
                return True

        except Exception as e:
            print(f"Ошибка при построении графиков: {e}")
            return False


def run_backtest_from_json(json_data, strategy_params, risk_params):
    """Функция для запуска бэктеста из JSON данных"""
    backtester = Backtester()

    if not backtester.load_data_from_json(json_data):
        return {'error': 'Failed to load data'}

    backtester.set_strategy_parameters(
        indicators=strategy_params.get('indicators', []),
        logic=strategy_params.get('logic', 'AND')
    )

    backtester.set_risk_parameters(
        initial_capital=risk_params.get('initial_capital', 10000),
        max_trade_amount=risk_params.get('max_trade_amount', 1000),
        stop_loss=risk_params.get('stop_loss', 0.05),
        take_profit=risk_params.get('take_profit', 0.10)
    )

    return backtester.run_backtest()


if __name__ == "__main__":
    # CLI интерфейс для тестирования
    matplotlib.use('TkAgg')

    print("Сервис бэктестинга торговых стратегий")
    print("=" * 50)

    backtester = Backtester()

    # Загрузка данных
    while True:
        filename = input("Введите путь к JSON файлу с историческими данными: ")
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            if backtester.load_data_from_json(data):
                break
        except Exception as e:
            print(f"Ошибка: {e}")

    # Выбор индикаторов
    indicators = []
    print("\nДоступные индикаторы:")
    print("1. SMA (Простая скользящая средняя)")
    print("2. EMA (Экспоненциальная скользящая средняя)")
    print("3. RSI (Индекс относительной силы)")
    print("4. Bollinger Bands (Полосы Боллинджера)")
    print("5. MACD (Moving Average Convergence Divergence)")

    while True:
        choice = input("Выберите индикатор (1-5) или 'готово' для завершения: ")
        if choice.lower() == 'готово':
            break

        if choice == '1':
            window = int(input("Введите период SMA (например, 20): "))
            indicators.append({'type': 'SMA', 'window': window, 'column': 'Close'})
        elif choice == '2':
            window = int(input("Введите период EMA (например, 20): "))
            indicators.append({'type': 'EMA', 'window': window, 'column': 'Close'})
        elif choice == '3':
            window = int(input("Введите период RSI (например, 14): "))
            overbought = int(input("Уровень перекупленности (например, 70): "))
            oversold = int(input("Уровень перепроданности (например, 30): "))
            indicators.append({'type': 'RSI', 'window': window, 'overbought': overbought,
                               'oversold': oversold, 'column': 'Close'})
        elif choice == '4':
            window = int(input("Введите период (например, 20): "))
            std_dev = int(input("Количество стандартных отклонений (например, 2): "))
            indicators.append({'type': 'Bollinger', 'window': window, 'std_dev': std_dev,
                               'column': 'Close'})
        elif choice == '5':
            fast = int(input("Быстрый период (по умолчанию 12): ") or 12)
            slow = int(input("Медленный период (по умолчанию 26): ") or 26)
            signal = int(input("Сигнальный период (по умолчанию 9): ") or 9)
            indicators.append({'type': 'MACD', 'fast': fast, 'slow': slow,
                               'signal': signal, 'column': 'Close'})
        else:
            print("Неверный выбор. Попробуйте снова.")

    logic = input("Логика объединения сигналов (AND/OR, по умолчанию AND): ").upper() or 'AND'
    backtester.set_strategy_parameters(indicators, logic)

    # Настройка параметров риска
    backtester.set_risk_parameters(
        initial_capital=float(input(f"Начальный капитал (по умолчанию 10000): ") or 10000),
        max_trade_amount=float(input(f"Макс. сумма сделки (по умолчанию 1000): ") or 1000),
        stop_loss=float(input(f"Стоп-лосс (% по умолчанию 5): ") or 5) / 100,
        take_profit=float(input(f"Тейк-профит (% по умолчанию 10): ") or 10) / 100
    )

    # Запуск бэктеста
    results = backtester.run_backtest()
    print("\nРезультаты бэктеста:")
    print("=" * 50)
    print(f"Начальный капитал: ${results['initial_capital']:.2f}")
    print(f"Конечный капитал: ${results['final_capital']:.2f}")
    print(f"Общая доходность: {results['total_return']:.2f}%")
    print(f"Прибыльные сделки: {results['winning_trades']}")
    print(f"Убыточные сделки: {results['losing_trades']}")
    print(f"Максимальная просадка: {results['max_drawdown']:.2f}%")
    print("=" * 50)

    # Построение графиков
    backtester.plot_results()