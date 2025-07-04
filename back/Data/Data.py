import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
import time
import logging
import traceback
from typing import Optional, Union


class YahooFinanceHistory:
    """
    Класс для получения исторических данных с Yahoo Finance через yfinance
    с кэшированием и ограничением частоты запросов
    """

    def __init__(self):
        self.cache = {}
        self.last_request_time = None
        self.request_timeout = 1  # Ограничение: 1 запрос в секунду
        logging.info("Инициализирован YahooFinanceHistory")

    def _rate_limit(self):
        """Ограничение частоты запросов к Yahoo Finance API"""
        if self.last_request_time and (time.time() - self.last_request_time) < self.request_timeout:
            sleep_time = self.request_timeout - (time.time() - self.last_request_time)
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _convert_interval(self, interval: str) -> str:
        """
        Конвертация интервалов из формата фронтенда в формат Yahoo Finance API
        """
        interval_map = {
            '1d': '1d',  # Дневные данные
            '1h': '1h',  # Часовые данные
            '4h': '4h',  # 4-часовые данные (не поддерживается Yahoo Finance)
            '1m': '1m',  # Минутные данные (только для последних 7 дней)
            '5m': '5m',  # 5-минутные данные
            '15m': '15m',  # 15-минутные данные
            '30m': '30m',  # 30-минутные данные
            '60m': '60m',  # 60-минутные данные
            '90m': '90m'  # 90-минутные данные
        }
        if interval not in interval_map:
            logging.warning(f"Неподдерживаемый интервал: {interval}. Используется '1d'")
        return interval_map.get(interval, '1d')

    def _validate_dates_for_interval(self, start_date: date, end_date: date, interval: str) -> tuple:
        """
        Проверка и корректировка дат в зависимости от интервала
        Возвращает корректные start_date и end_date
        """
        max_days = {
            '1m': 7,  # 1 минута - максимум 7 дней
            '5m': 60,  # 5 минут - максимум 60 дней
            '15m': 60,  # 15 минут - максимум 60 дней
            '30m': 60,  # 30 минут - максимум 60 дней
            '60m': 730,  # 60 минут - максимум 2 года
            '90m': 60,  # 90 минут - максимум 60 дней
            '1h': 730,  # 1 час - максимум 2 года
            '1d': None  # Дневные данные - без ограничений
        }.get(interval, None)

        if max_days and (end_date - start_date).days > max_days:
            new_start = end_date - timedelta(days=max_days)
            logging.warning(f"Для интервала {interval} период сокращен до {max_days} дней: {new_start} - {end_date}")
            return new_start, end_date

        return start_date, end_date

    def get_historical_data(
            self,
            ticker: str,
            start_date: Union[str, datetime, date],
            end_date: Union[str, datetime, date, None] = None,
            interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Основной метод для получения исторических данных

        Параметры:
        - ticker: тикер акции (например, 'SBER.ME' для MOEX)
        - start_date: начальная дата (строка или datetime/date)
        - end_date: конечная дата (по умолчанию текущая дата)
        - interval: интервал данных ('1d', '1h' и т.д.)

        Возвращает:
        - DataFrame с данными или None в случае ошибки
        """
        try:
            self._rate_limit()
            ticker = ticker.upper()

            # Проверка кэша
            cache_key = f"{ticker}_{start_date}_{end_date}_{interval}"
            if cache_key in self.cache:
                logging.debug(f"Используются кэшированные данные для {cache_key}")
                return self.cache[cache_key].copy()

            # Преобразование дат
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date() if end_date else date.today()

            if start_dt > end_dt:
                logging.error(f"Неверный диапазон дат: {start_dt} > {end_dt}")
                return None

            # Конвертация интервала
            yf_interval = self._convert_interval(interval)

            # Проверка и корректировка дат для выбранного интервала
            start_dt, end_dt = self._validate_dates_for_interval(start_dt, end_dt, yf_interval)

            # Получение данных
            logging.info(f"Запрос данных для {ticker} с {start_dt} по {end_dt}, интервал {yf_interval}")

            data = yf.download(
                tickers=ticker,
                start=start_dt,
                end=end_dt + timedelta(days=1),  # Yahoo Finance включает данные на дату start, но не включает end
                interval=yf_interval,
                progress=False,
                auto_adjust=True  # Автоматическая корректировка цен на дивиденды и сплиты
            )

            if data.empty:
                logging.warning(f"Нет данных для {ticker} за период {start_dt} - {end_dt}")
                return None

            # Переименовываем колонки для совместимости
            data = data.rename(columns={
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })

            # Сбрасываем индекс, чтобы Datetime стал колонкой
            data.reset_index(inplace=True)
            data.rename(columns={'Date': 'Datetime'}, inplace=True)

            # Кэшируем результат
            self.cache[cache_key] = data.copy()
            return data

        except Exception as e:
            logging.error(f"Ошибка при получении данных для {ticker}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def clear_cache(self):
        """Очистка кэша данных"""
        self.cache = {}
        logging.info("Кэш данных очищен")