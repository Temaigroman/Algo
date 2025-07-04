import pandas as pd
from datetime import datetime, date
import time
import logging
from typing import Optional, Union
from moexalgo import Ticker, Market


class MoexAlgoHistory:
    def __init__(self):
        self.cache = {}
        self.last_request_time = None
        self.request_timeout = 1
        self._api_params = self._detect_api_version()
        logging.info(f"Using API parameters: {self._api_params}")

    def _detect_api_version(self):
        """Определяем параметры для текущей версии moexalgo"""
        test_ticker = Ticker('SBER')
        test_cases = [
            {'period': 'D', 'from': '2024-01-01', 'till': '2024-01-02'},
            {'interval': 'D', 'from': '2024-01-01', 'till': '2024-01-02'},
            {'period': 'D', 'start': '2024-01-01', 'end': '2024-01-02'}
        ]

        for params in test_cases:
            try:
                list(test_ticker.candles(**params))
                logging.info(f"Detected API version with params: {params}")
                return params
            except Exception as e:
                logging.debug(f"API test failed with params {params}: {str(e)}")
                continue

        logging.warning("Using default API parameters")
        return {'period': 'D', 'from': None, 'till': None}

    def _rate_limit(self):
        if self.last_request_time and (time.time() - self.last_request_time) < self.request_timeout:
            time.sleep(self.request_timeout - (time.time() - self.last_request_time))
        self.last_request_time = time.time()

    def get_historical_data(
            self,
            ticker: str,
            start_date: Union[str, datetime, date],
            end_date: Union[str, datetime, date, None] = None,
            interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        try:
            self._rate_limit()
            ticker = ticker.upper()
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date() if end_date else date.today()

            if start_dt > end_dt:
                logging.error("Invalid date range")
                return None

            moex_ticker = Ticker(ticker)
            moex_interval = self._convert_interval(interval)

            # Формируем параметры запроса
            params = {}
            for k, v in self._api_params.items():
                if k in ['period', 'interval']:
                    params[k] = moex_interval
                elif k in ['from', 'start']:
                    params[k] = start_dt.strftime('%Y-%m-%d')
                elif k in ['till', 'end']:
                    params[k] = end_dt.strftime('%Y-%m-%d')

            logging.info(f"Requesting data for {ticker} with params: {params}")
            data = list(moex_ticker.candles(**params))

            if not data:
                logging.warning(f"No data for {ticker} in {start_dt} - {end_dt}")
                return None

            df = pd.DataFrame(data).rename(columns={
                'begin': 'Datetime',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            return df.set_index('Datetime')

        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {str(e)}", exc_info=True)
            return None

    def _convert_interval(self, interval: str) -> str:
        """Конвертация интервалов с обработкой ошибок"""
        interval_map = {
            '1d': '24h',
            '1h': '60min',
            '4h': '4h',
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min'
        }
        if interval not in interval_map:
            logging.warning(f"Unsupported interval: {interval}. Using '24h'")
        return interval_map.get(interval, '24h')