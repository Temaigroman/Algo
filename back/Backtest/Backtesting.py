import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import matplotlib


class Backtester:
    def __init__(self):
        self.data = None
        self.initial_capital = 10000
        self.max_trade_amount = 1000
        self.stop_loss = 0.05  # 5%
        self.take_profit = 0.10  # 10%
        self.strategy_params = {
            'indicators': [],  # Теперь храним список индикаторов
            'logic': 'AND'  # Логика объединения сигналов (AND/OR)
        }
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

    def select_indicators(self):
        """Выбор нескольких индикаторов"""
        print("\nДоступные индикаторы:")
        print("1. SMA (Простая скользящая средняя)")
        print("2. EMA (Экспоненциальная скользящая средняя)")
        print("3. RSI (Индекс относительной силы)")
        print("4. Bollinger Bands (Полосы Боллинджера)")
        print("5. MACD (Moving Average Convergence Divergence)")

        selected = []
        while True:
            choice = input("Выберите индикатор (1-5) или 'готово' для завершения: ")
            if choice.lower() == 'готово':
                break

            if choice == '1':
                window = int(input("Введите период SMA (например, 20): "))
                self.add_indicator('SMA', {'window': window})
                selected.append(f"SMA({window})")

            elif choice == '2':
                window = int(input("Введите период EMA (например, 20): "))
                self.add_indicator('EMA', {'window': window})
                selected.append(f"EMA({window})")

            elif choice == '3':
                window = int(input("Введите период RSI (например, 14): "))
                overbought = int(input("Уровень перекупленности (например, 70): "))
                oversold = int(input("Уровень перепроданности (например, 30): "))
                self.add_indicator('RSI', {'window': window, 'overbought': overbought, 'oversold': oversold})
                selected.append(f"RSI({window})")

            elif choice == '4':
                window = int(input("Введите период (например, 20): "))
                std_dev = int(input("Количество стандартных отклонений (например, 2): "))
                self.add_indicator('Bollinger', {'window': window, 'std_dev': std_dev})
                selected.append(f"BB({window},{std_dev})")

            elif choice == '5':
                fast = int(input("Быстрый период (по умолчанию 12): ") or 12)
                slow = int(input("Медленный период (по умолчанию 26): ") or 26)
                signal = int(input("Сигнальный период (по умолчанию 9): ") or 9)
                self.add_indicator('MACD', {'fast': fast, 'slow': slow, 'signal': signal})
                selected.append(f"MACD({fast},{slow},{signal})")

            else:
                print("Неверный выбор. Попробуйте снова.")

        if not selected:
            print("Не выбрано ни одного индикатора")
            return False

        # Выбор логики объединения сигналов
        logic = input("Логика объединения сигналов (AND/OR, по умолчанию AND): ").upper() or 'AND'
        if logic not in ['AND', 'OR']:
            print("Неверный выбор логики. Используется AND")
            logic = 'AND'

        self.strategy_params['logic'] = logic
        print(f"\nВыбранные индикаторы ({logic}): {', '.join(selected)}")
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

    def get_signal(self, i):
        """Генерация торгового сигнала на основе выбранных индикаторов"""
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

        # Фильтрация None значений
        valid_signals = [s for s in signals if s is not None]
        if not valid_signals:
            return None

        # Применяем логику объединения
        if self.strategy_params['logic'] == 'AND':
            if all(s == 'buy' for s in valid_signals):
                return 'buy'
            elif all(s == 'sell' for s in valid_signals):
                return 'sell'
        else:  # OR логика
            if 'buy' in valid_signals:
                return 'buy'
            elif 'sell' in valid_signals:
                return 'sell'

        return None

    def run_backtest(self):
        """Запуск бэктеста с комбинированными индикаторами"""
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
            signal = self.get_signal(i)
            current_price = self.data.iloc[i]['Close']

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
        """Визуализация результатов с несколькими индикаторами"""
        try:
            plt.figure(figsize=(14, 8))
            n_plots = 2 + len(self.strategy_params['indicators'])

            # График цены и сделок
            plt.subplot(n_plots, 1, 1)
            plt.plot(self.data.index, self.data['Close'], label='Цена закрытия')

            # Отметки сделок
            buy_dates = [t['date'] for t in self.trades if t['type'] == 'buy']
            buy_prices = [t['price'] for t in self.trades if t['type'] == 'buy']
            plt.scatter(buy_dates, buy_prices, color='g', label='Покупка', marker='^')

            sell_dates = [t['date'] for t in self.trades if t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
            sell_prices = [t['price'] for t in self.trades if
                           t['type'] in ['sell', 'stop_loss', 'take_profit', 'close']]
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

            # Проверка доступности GUI
            if matplotlib.get_backend().lower() in ['agg', 'pdf', 'svg', 'ps']:
                plt.savefig('backtest_results.png')
                print("\nГрафик сохранен в backtest_results.png")
            else:
                plt.show()

        except Exception as e:
            print(f"\nОшибка при построении графиков: {e}")
            plt.savefig('backtest_results.png')
            print("График сохранен в backtest_results.png")


def main():
    print("Сервис бэктестинга торговых стратегий")
    print("=" * 50)

    backtester = Backtester()

    # Загрузка данных
    while True:
        filename = input("Введите путь к JSON файлу с историческими данными: ")
        if backtester.load_data_from_json(filename):
            break

    # Выбор индикаторов
    while True:
        if backtester.select_indicators():
            break

    # Настройка параметров
    backtester.set_risk_parameters()

    # Запуск бэктеста
    backtester.run_backtest()


if __name__ == "__main__":
    # Явно устанавливаем бэкенд для отображения графиков
    matplotlib.use('TkAgg')  # Можно также использовать 'Qt5Agg'
    main()