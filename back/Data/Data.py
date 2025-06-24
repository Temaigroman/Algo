import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import subprocess
import sys
import time
import logging
from typing import Optional, Union

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YahooFinanceHistory:
    def __init__(self):
        self.data = None
        self.last_request_time = None
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

        # Настройка yfinance


    def _rate_limit(self):
        """Ограничение частоты запросов"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < 2:  # 2 секунды между запросами
                time.sleep(2 - elapsed)
        self.last_request_time = time.time()

    def get_historical_data(
            self,
            ticker: str,
            start_date: Union[str, datetime],
            end_date: Union[str, datetime, None] = None,
            interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Улучшенный метод получения исторических данных с защитой от лимитов

        :param ticker: Тикер акции (например 'AAPL')
        :param start_date: Начальная дата (YYYY-MM-DD или datetime)
        :param end_date: Конечная дата (по умолчанию текущая дата)
        :param interval: Таймфрейм данных
        :return: DataFrame с данными или None при ошибке
        """
        try:
            self._rate_limit()

            # Преобразование дат
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(datetime.now())

            # Корректировка для однодневных запросов
            if start_dt == end_dt:
                start_dt = start_dt - timedelta(days=1)
                logger.info(f"Adjusted date range: {start_dt} to {end_dt}")

            # Проверка интервала
            if interval not in self.available_intervals:
                raise ValueError(
                    f"Неподдерживаемый интервал. Доступные: {', '.join(self.available_intervals.keys())}"
                )

            logger.info(f"Requesting data for {ticker} ({start_dt.date()} to {end_dt.date()}, {interval})")

            # Получение данных
            data = yf.download(
                tickers=ticker,
                start=start_dt,
                end=end_dt,
                interval=interval,
                progress=False,
                threads=False,  # Отключаем многопоточность
                auto_adjust=True
            )

            if data.empty:
                logger.warning(f"No data returned for {ticker}. Possible reasons:")
                logger.warning("- Market was closed in this period")
                logger.warning("- Invalid ticker symbol")
                logger.warning("- Too narrow date range")
                return None

            self.data = data
            logger.info(f"Successfully retrieved {len(data)} rows")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def display_data(self, num_rows: int = 10) -> None:
        """Отображение данных с улучшенным форматированием"""
        if self.data is None:
            logger.warning("No data to display")
            return

        print("\n" + "=" * 80)
        print(f"Исторические данные (первые {num_rows} строк):".center(80))
        print("=" * 80)
        print(self.data.head(num_rows).to_string())

        print("\n" + "=" * 80)
        print("Статистика:".center(80))
        print("=" * 80)
        print(self.data.describe().to_string())

    def save_to_csv(self, filename: str) -> bool:
        """Улучшенное сохранение в CSV"""
        try:
            if self.data is None:
                raise ValueError("Нет данных для сохранения")

            self.data.to_csv(filename)
            logger.info(f"Данные сохранены в {os.path.abspath(filename)}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении CSV: {str(e)}")
            return False

    def save_to_json(self, filename: str = "stock_data.json") -> bool:
        """Улучшенное сохранение в JSON"""
        try:
            if self.data is None:
                raise ValueError("Нет данных для сохранения")

            json_data = self.data.reset_index().to_json(
                filename,
                orient='records',
                date_format='iso',
                indent=2
            )
            logger.info(f"Данные сохранены в {os.path.abspath(filename)}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении JSON: {str(e)}")
            return False

    def get_data_as_json_str(self) -> Optional[str]:
        """Получение данных в виде JSON строки"""
        if self.data is None:
            return None
        return self.data.reset_index().to_json(orient='records', date_format='iso')

