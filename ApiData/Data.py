import yfinance as yf
import pandas as pd
from datetime import datetime


class YahooFinanceHistory:
    def __init__(self):
        self.data = None

    def get_historical_data(self, ticker, start_date, end_date=None):
        """
        Получает исторические данные для указанного тикера за заданный период

        :param ticker: Символ акции (например, 'AAPL')
        :param start_date: Начальная дата в формате 'YYYY-MM-DD' или datetime
        :param end_date: Конечная дата (по умолчанию текущая дата)
        :return: DataFrame с историческими данными
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            # Загружаем данные
            stock = yf.Ticker(ticker)
            self.data = stock.history(start=start_date, end=end_date)

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


def main():
    print("Yahoo Finance Historical Data Service")
    print("=" * 50)

    service = YahooFinanceHistory()

    while True:
        print("\nМеню:")
        print("1. Получить исторические данные")
        print("2. Просмотреть данные")
        print("3. Сохранить данные в CSV")
        print("4. Выход")

        choice = input("Выберите действие (1-4): ")

        if choice == '1':
            ticker = input("Введите тикер (например, AAPL): ").upper()
            start_date = input("Введите начальную дату (YYYY-MM-DD): ")
            end_date = input("Введите конечную дату (YYYY-MM-DD, оставьте пустым для текущей даты): ") or None

            data = service.get_historical_data(ticker, start_date, end_date)
            if data is not None:
                print(f"\nУспешно получены данные для {ticker}")

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
            print("Выход из программы.")
            break

        else:
            print("Некорректный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()