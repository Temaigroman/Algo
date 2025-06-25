import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import traceback
from typing import Optional, Union


class YahooFinanceHistory:
    def __init__(self):
        self.cache = {}
        self.last_request_time = None
        self.request_timeout = 3  # seconds between requests

    def _rate_limit(self):
        """Ограничение частоты запросов"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_timeout:
                time.sleep(self.request_timeout - elapsed)
        self.last_request_time = time.time()

    def get_historical_data(
            self,
            ticker: str,
            start_date: Union[str, datetime],
            end_date: Union[str, datetime, None] = None,
            interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Получение исторических данных с улучшенной обработкой ошибок
        """
        try:
            self._rate_limit()

            # Проверка кэша
            cache_key = f"{ticker}_{start_date}_{end_date}_{interval}"
            if cache_key in self.cache:
                return self.cache[cache_key].copy()

            # Преобразование дат
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date) if end_date else datetime.now()

            # Для внутридневных данных ограничиваем период
            if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m']:
                max_days = 60
                if (end_dt - start_dt).days > max_days:
                    start_dt = end_dt - timedelta(days=max_days)

            # Получение данных
            data = yf.download(
                tickers=ticker,
                start=start_dt,
                end=end_dt,
                interval=interval,
                progress=False
            )

            if data.empty:
                raise ValueError(f"No data found for {ticker} with given parameters")

            # Кэширование данных
            self.cache[cache_key] = data.copy()
            return data

        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def clear_cache(self):
        """Очистка кэша данных"""
        self.cache = {}