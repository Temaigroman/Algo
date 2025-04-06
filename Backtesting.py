import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Callable, Dict, List, Optional


class Backtester:
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        """
        Инициализация бэктестера

        :param initial_capital: Начальный капитал
        :param commission: Комиссия за сделку (в долях от суммы сделки)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()

    def reset(self):
        """Сброс состояния бэктестера"""
        self.capital = self.initial_capital
        self.positions = {}  # {symbol: shares}
        self.portfolio_value = []
        self.trades = []
        self.data = None

    def download_data(
            self,
            symbols: List[str],
            start_date: str,
            end_date: str,
            progress: bool = False
    ) -> None:
        """
        Загрузка данных из Yahoo Finance

        :param symbols: Список тикеров
        :param start_date: Дата начала в формате 'YYYY-MM-DD'
        :param end_date: Дата окончания в формате 'YYYY-MM-DD'
        :param progress: Показывать прогресс загрузки
        """
        print(f"Загрузка данных с {start_date} по {end_date} для {symbols}...")
        data = yf.download(
            symbols,
            start=start_date,
            end=end_date,
            group_by='ticker',
            progress=progress
        )

        # Преобразуем мультииндекс в плоскую структуру
        if len(symbols) > 1:
            self.data = {}
            for symbol in symbols:
                self.data[symbol] = data[symbol].copy()
        else:
            self.data = {symbols[0]: data.copy()}

        print("Данные успешно загружены.")

    def add_signal(
            self,
            symbol: str,
            signal_func: Callable[[pd.DataFrame], pd.Series],
            signal_name: str = "signal"
    ) -> None:
        """
        Добавление торгового сигнала к данным

        :param symbol: Тикер
        :param signal_func: Функция, принимающая DataFrame и возвращающая Series с сигналами
        :param signal_name: Название колонки с сигналом
        """
        if symbol not in self.data:
            raise ValueError(f"Данные для {symbol} не найдены")

        signals = signal_func(self.data[symbol])
        if not isinstance(signals, pd.Series):
            raise ValueError("Функция сигнала должна возвращать pd.Series")

        self.data[symbol][signal_name] = signals

    def backtest(
            self,
            symbol: str,
            signal_name: str = "signal",
            buy_limit_pct: float = -0.01,  # -1% от текущей цены
            sell_limit_pct: float = 0.01,  # +1% от текущей цены
            max_position: float = 0.5  # Макс. доля капитала в одной позиции
    ) -> None:
        """
        Запуск бэктеста для указанного символа и сигнала

        :param symbol: Тикер
        :param signal_name: Название колонки с сигналом
        :param buy_limit_pct: Процент для лимитной покупки
        :param sell_limit_pct: Процент для лимитной продажи
        :param max_position: Максимальная доля капитала для одной позиции
        """
        if symbol not in self.data:
            raise ValueError(f"Данные для {symbol} не найдены")

        if signal_name not in self.data[symbol]:
            raise ValueError(f"Сигнал {signal_name} не найден в данных")

        df = self.data[symbol].copy()
        df['date'] = df.index
        df['next_open'] = df['Open'].shift(-1)
        df['next_close'] = df['Close'].shift(-1)

        # Инициализация колонок для бэктеста
        df['position'] = 0
        df['trade_price'] = 0.0
        df['shares'] = 0
        df['cash'] = self.initial_capital
        df['portfolio_value'] = self.initial_capital

        current_shares = 0
        current_cash = self.initial_capital

        for i, row in df.iterrows():
            if pd.isna(row['next_open']) or pd.isna(row[signal_name]):
                continue

            signal = row[signal_name]
            price = row['Close']
            next_open = row['next_open']

            # Лимитные цены
            buy_limit_price = price * (1 + buy_limit_pct)
            sell_limit_price = price * (1 + sell_limit_pct)

            # Проверяем, исполнятся ли наши лимитные заявки на следующий день
            buy_executed = (signal > 0) and (next_open <= buy_limit_price)
            sell_executed = (signal < 0) and (next_open >= sell_limit_price)

            if buy_executed and current_shares == 0:
                # Вычисляем сколько акций можем купить (не более max_position капитала)
                max_pos_value = current_cash * max_position
                shares_to_buy = max_pos_value // buy_limit_price

                if shares_to_buy > 0:
                    cost = shares_to_buy * buy_limit_price
                    commission = cost * self.commission
                    total_cost = cost + commission

                    if total_cost <= current_cash:
                        current_shares += shares_to_buy
                        current_cash -= total_cost

                        # Записываем сделку
                        trade = {
                            'date': i,
                            'symbol': symbol,
                            'type': 'buy',
                            'shares': shares_to_buy,
                            'price': buy_limit_price,
                            'commission': commission,
                            'value': cost
                        }
                        self.trades.append(trade)

            elif sell_executed and current_shares > 0:
                # Продаем все акции
                value = current_shares * sell_limit_price
                commission = value * self.commission
                total_value = value - commission

                current_cash += total_value

                # Записываем сделку
                trade = {
                    'date': i,
                    'symbol': symbol,
                    'type': 'sell',
                    'shares': current_shares,
                    'price': sell_limit_price,
                    'commission': commission,
                    'value': value
                }
                self.trades.append(trade)

                current_shares = 0

            # Обновляем состояние портфеля
            position_value = current_shares * row['Close']
            portfolio_value = current_cash + position_value

            df.at[i, 'position'] = current_shares
            df.at[i, 'shares'] = current_shares
            df.at[i, 'cash'] = current_cash
            df.at[i, 'portfolio_value'] = portfolio_value

        self.data[symbol] = df
        self.positions[symbol] = current_shares
        self.capital = current_cash

    def get_results(self, symbol: str) -> pd.DataFrame:
        """Получить результаты бэктеста для символа"""
        if symbol not in self.data:
            raise ValueError(f"Данные для {symbol} не найдены")
        return self.data[symbol]

    def get_trades(self) -> pd.DataFrame:
        """Получить список всех сделок"""
        return pd.DataFrame(self.trades)

    def get_summary(self) -> Dict:
        """Получить сводку по результатам бэктеста"""
        if not self.trades:
            return {}

        trades_df = self.get_trades()
        start_date = trades_df['date'].min()
        end_date = trades_df['date'].max()

        # Вычисляем прибыль
        initial_value = self.initial_capital
        final_value = self.capital + sum(
            shares * self.data[symbol]['Close'].iloc[-1]
            for symbol, shares in self.positions.items()
        )
        profit_pct = (final_value - initial_value) / initial_value * 100

        # Статистика по сделкам
        num_trades = len(trades_df)
        num_buys = len(trades_df[trades_df['type'] == 'buy'])
        num_sells = len(trades_df[trades_df['type'] == 'sell'])
        avg_profit_per_trade = profit_pct / num_trades if num_trades > 0 else 0

        return {
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_value,
            'final_value': final_value,
            'profit_pct': profit_pct,
            'num_trades': num_trades,
            'num_buys': num_buys,
            'num_sells': num_sells,
            'avg_profit_per_trade': avg_profit_per_trade,
            'commission_paid': trades_df['commission'].sum()
        }


# Пример использования
if __name__ == "__main__":
    # Инициализация бэктестера
    backtester = Backtester(initial_capital=10000.0, commission=0.001)

    # Загрузка данных
    backtester.download_data(
        symbols=['AAPL'],
        start_date='2020-01-01',
        end_date='2021-12-31'
    )


    # Определение торгового сигнала (простая скользящая средняя)
    def moving_average_signal(data: pd.DataFrame, short_window=20, long_window=50) -> pd.Series:
        """Генерирует сигналы на основе пересечения скользящих средних"""
        data['short_ma'] = data['Close'].rolling(short_window).mean()
        data['long_ma'] = data['Close'].rolling(long_window).mean()
        signal = pd.Series(0, index=data.index)
        signal[data['short_ma'] > data['long_ma']] = 1  # Сигнал на покупку
        signal[data['short_ma'] < data['long_ma']] = -1  # Сигнал на продажу
        return signal