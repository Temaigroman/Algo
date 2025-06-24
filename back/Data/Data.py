import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import time
import logging
import traceback
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

        # Установка пользовательского заголовка (альтернатива set_user_agent)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _rate_limit(self):
        """Ограничение частоты запросов (3 секунды между запросами)"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < 3:
                time.sleep(3 - elapsed)
        self.last_request_time = time.time()

    def get_historical_data(
            self,
            ticker: str,
            start_date: Union[str, datetime],
            end_date: Union[str, datetime, None] = None,
            interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Улучшенный метод получения исторических данных
        """
        try:
            self._rate_limit()

            # Преобразование дат
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(datetime.now())

            # Для внутридневных данных ограничиваем период 60 днями
            if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m']:
                max_days = 60
                if (end_dt - start_dt).days > max_days:
                    start_dt = end_dt - timedelta(days=max_days)
                    logger.warning(f"Для интервала {interval} период сокращен до {max_days} дней")

            logger.info(f"Запрос данных: {ticker} ({start_dt.date()} - {end_dt.date()}, {interval})")

            # Получение данных с обработкой ошибок
            data = yf.download(
                tickers=ticker,
                start=start_dt,
                end=end_dt,
                interval=interval,
                progress=False,
                threads=False,
                group_by='ticker'
            )

            if data.empty:
                logger.error(f"Данные не получены. Возможные причины:")
                logger.error("- Рынок был закрыт в этот период")
                logger.error("- Неправильный тикер")
                logger.error("- Слишком узкий диапазон дат")
                return None

            self.data = data
            logger.info(f"Успешно получено {len(data)} строк данных")
            return data

        except Exception as e:
            logger.error(f"Ошибка при получении данных: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    # Остальные методы класса остаются без изменений
    # ...