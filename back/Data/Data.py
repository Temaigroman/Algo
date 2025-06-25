import pandas as pd
from datetime import datetime, date
import time
import logging
import traceback
from typing import Optional, Union
from moexalgo import Ticker


class MoexAlgoHistory:
    def __init__(self):
        self.cache = {}
        self.last_request_time = None
        self.request_timeout = 3

    def _rate_limit(self):
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_timeout:
                time.sleep(self.request_timeout - elapsed)
        self.last_request_time = time.time()

    def _convert_interval(self, interval: str) -> str:
        """Конвертация интервалов в формат, поддерживаемый MOEX API"""
        interval_map = {
            '1d': 'D',
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '60m': '1h',
            '1h': '1h',
            '4h': '4h',
        }
        return interval_map.get(interval, 'D')

    def get_historical_data(
            self,
            ticker: str,
            start_date: Union[str, datetime, date],
            end_date: Union[str, datetime, date, None] = None,
            interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        try:
            self._rate_limit()

            cache_key = f"{ticker}_{start_date}_{end_date}_{interval}"
            if cache_key in self.cache:
                return self.cache[cache_key].copy()

            # Преобразование дат
            start_dt = pd.to_datetime(start_date).strftime('%Y-%m-%d')
            end_dt = pd.to_datetime(end_date).strftime('%Y-%m-%d') if end_date else datetime.now().strftime('%Y-%m-%d')

            moex_interval = self._convert_interval(interval)

            # Получение данных с правильными параметрами
            moex_ticker = Ticker(ticker)
            data = list(moex_ticker.candles(
                date=start_dt,
                till_date=end_dt,
                period=moex_interval
            ))

            if not data:
                return None

            df = pd.DataFrame(data)
            df = df.rename(columns={
                'begin': 'Datetime',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            df['Datetime'] = pd.to_datetime(df['Datetime'])
            df.set_index('Datetime', inplace=True)

            self.cache[cache_key] = df.copy()
            return df

        except Exception as e:
            logging.error(f"Error fetching MOEX data for {ticker}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def clear_cache(self):
        self.cache = {}