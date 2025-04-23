import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os
import subprocess
import sys


class YahooFinanceHistory:
    def __init__(self):
        self.data = None
        self.available_intervals = {
            '1m': '1 минута',
            '2m': '2 минуты',
            '5m': '5 минут',
            '15m': '15 минут',
            '30m': '30 минут',
            '60m': '60 минут',
            '90m': '90 минут',
            '1h': '1 час',
            '1d': '1 день',
            '5d': '5 дней',
            '1wk': '1 неделя',
            '1mo': '1 месяц',
            '3mo': '3 месяца'
        }

    def get_historical_data(self, ticker, start_date, end_date=None, interval='1d'):
        """
        Получает исторические данные для указанного тикера за заданный период

        :param ticker: Символ акции (например, 'AAPL')
        :param start_date: Начальная дата в формате 'YYYY-MM-DD' или datetime
        :param end_date: Конечная дата (по умолчанию текущая дата)
        :param interval: Таймфрейм данных (по умолчанию '1d' - дневные данные)
        :return: DataFrame с историческими данными
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if interval not in self.available_intervals:
            print(f"Неподдерживаемый интервал. Доступные интервалы: {', '.join(self.available_intervals.keys())}")
            return None

        try:
            # Загружаем данные
            stock = yf.Ticker(ticker)
            self.data = stock.history(start=start_date, end=end_date, interval=interval)

            if self.data.empty:
                print(f"Не удалось получить данные для {ticker}. Проверьте тикер и даты.")
                return None

            return self.data

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return None

    def display_data(self, num_rows=10):
        """
        Отображает данные в консоли

        :param num_rows: Количество строк для отображения
        """
        if self.data is None:
            print("Нет данных для отображения. Сначала получите данные.")
            return

        print("\n" + "=" * 50)
        print(f"Исторические данные (первые {num_rows} строк):")
        print("=" * 50)
        print(self.data.head(num_rows))

        print("\n" + "=" * 50)
        print("Основная статистика:")
        print("=" * 50)
        print(self.data.describe())

    def save_to_csv(self, filename):
        """
        Сохраняет данные в CSV файл

        :param filename: Имя файла для сохранения
        """
        if self.data is None:
            print("Нет данных для сохранения.")
            return

        try:
            self.data.to_csv(filename)
            print(f"Данные успешно сохранены в {filename}")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def save_to_json(self, filename="stock_data.json"):
        """Сохраняет данные в JSON-файл."""
        if self.data is None:
            print("Нет данных для сохранения.")
            return False

        try:
            # Конвертируем DataFrame в JSON (ориентируясь на записи)
            json_data = self.data.reset_index().to_json(
                filename,
                orient='records',
                date_format='iso'
            )
            print(f"Данные сохранены в {os.path.abspath(filename)}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")
            return False

    def get_data_as_json_str(self):
        """Возвращает данные в виде JSON-строки (для передачи)."""
        if self.data is None:
            return None
        return self.data.reset_index().to_json(orient='records', date_format='iso')


def main():
    print("Yahoo Finance Historical Data Service")
    print("=" * 50)

    service = YahooFinanceHistory()

    while True:
        print("\nМеню:")
        print("1. Получить исторические данные")
        print("2. Просмотреть данные")
        print("3. Сохранить данные в CSV")
        print("4. Сохранить данные в JSON")
        print("5. Передать данные в другой скрипт")
        print("6. Выход")

        choice = input("Выберите действие (1-6): ")

        if choice == '1':
            ticker = input("Введите тикер (например, AAPL): ").upper()
            start_date = input("Введите начальную дату (YYYY-MM-DD): ")
            end_date = input("Введите конечную дату (YYYY-MM-DD, оставьте пустым для текущей даты): ") or None

            print("\nДоступные таймфреймы:")
            for key, value in service.available_intervals.items():
                print(f"{key}: {value}")

            interval = input("Введите таймфрейм (по умолчанию '1d'): ") or '1d'

            data = service.get_historical_data(ticker, start_date, end_date, interval)
            if data is not None:
                print(f"\nУспешно получены данные для {ticker} с интервалом {interval}")

        elif choice == '2':
            if service.data is not None:
                num_rows = input("Сколько строк отобразить (по умолчанию 10): ") or 10
                try:
                    service.display_data(int(num_rows))
                except ValueError:
                    print("Некорректное число. Используется значение по умолчанию.")
                    service.display_data()
            else:
                print("Сначала получите данные.")

        elif choice == '3':
            if service.data is not None:
                filename = input("Введите имя файла для сохранения (например, data.csv): ") or "data.csv"
                service.save_to_csv(filename)
            else:
                print("Нет данных для сохранения.")

        elif choice == '4':
            if service.data is not None:
                filename = input("Введите имя JSON-файла (например, data.json): ") or "data.json"
                service.save_to_json(filename)
            else:
                print("Нет данных для сохранения.")

        elif choice == '5':
            if service.data is not None:
                json_str = service.get_data_as_json_str()
                if json_str:
                    try:
                        subprocess.run(
                            ["python", "analyzer.py", json_str],
                            check=True
                        )
                        print("Данные успешно переданы в analyzer.py")
                    except Exception as e:
                        print(f"Ошибка при передаче данных: {e}")
                else:
                    print("Не удалось преобразовать данные в JSON")
            else:
                print("Нет данных для передачи.")

        elif choice == '6':
            print("Выход из программы.")
            break

        else:
            print("Некорректный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()