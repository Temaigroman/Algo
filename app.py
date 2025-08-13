import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify, send_file, make_response, render_template
from flask_cors import CORS

# --- Конфигурация приложения ---
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))  # Добавляем корень проекта в пути поиска

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'front' / 'templates'),
    static_folder=str(BASE_DIR / 'front' / 'static')
)

# Настройка CORS для всех маршрутов
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# --- Настройка логирования ---
def setup_logging():
    """Настройка системы логирования"""
    log_handler = RotatingFileHandler(
        'app.log',
        maxBytes=100000,
        backupCount=3
    )
    log_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.INFO)

setup_logging()

# --- Инициализация сервиса ---
try:
    from back.Data.Data import YahooFinanceHistory
    from back.Backtest.Backtesting import Backtester
    service = YahooFinanceHistory()
    app.logger.info("Services initialized successfully")
except ImportError as e:
    app.logger.critical(f"Failed to import modules: {str(e)}")
    raise
except Exception as e:
    app.logger.critical(f"Service initialization error: {str(e)}")
    raise

# --- Вспомогательные функции ---
def _build_cors_preflight_response() -> make_response:
    """Создает CORS response для предварительных запросов"""
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

def _validate_historical_request(data: Dict[str, Any]) -> Optional[tuple]:
    """Валидация входных параметров для исторических данных"""
    ticker = data.get('ticker', '').upper()
    start_date = data.get('startDate')

    if not ticker or not start_date:
        return None, ('Missing required parameters', 400)

    if not ticker.endswith('.ME') and ticker in ['SBER', 'GAZP', 'VTBR', 'MOEX', 'GMKN', 'LKOH', 'ROSN', 'TATN', 'NVTK', 'PLZL']:
        ticker += '.ME'

    return {
        'ticker': ticker,
        'start_date': start_date,
        'end_date': data.get('endDate', datetime.now().strftime('%Y-%m-%d')),
        'interval': data.get('interval', '1d')
    }, None

# --- Обработчики запросов ---
@app.route('/')
def index():
    """Главная страница приложения"""
    return render_template('index.html')

@app.route('/backtest')
def backtest_page():
    """Страница бэктестинга"""
    return render_template('backtest.html')

@app.route('/api/historical', methods=['POST', 'OPTIONS'])
def get_historical_data():
    """Получение исторических данных"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': 'Invalid request data'}), 400

        ticker = request_data.get('ticker', '').upper()
        start_date = request_data.get('startDate')
        end_date = request_data.get('endDate', datetime.now().strftime('%Y-%m-%d'))
        interval = request_data.get('interval', '1d')

        if not ticker or not start_date:
            return jsonify({'error': 'Missing required parameters'}), 400

        if not ticker.endswith('.ME') and ticker in ['SBER', 'GAZP', 'VTBR', 'MOEX', 'GMKN', 'LKOH', 'ROSN', 'TATN', 'NVTK', 'PLZL']:
            ticker += '.ME'

        app.logger.info(f"Request for {ticker} from {start_date} to {end_date}, interval {interval}")

        df = service.get_historical_data(ticker, start_date, end_date, interval)

        if df is None:
            return jsonify({
                'error': 'Failed to get data. Please check the ticker and date range.',
                'suggestions': [
                    'Try popular tickers: SBER.ME, GAZP.ME, VTBR.ME',
                    'Ensure dates are valid',
                    'Try different time intervals',
                    'For intraday data, maximum period is 60 days'
                ]
            }), 400

        result = {
            'ticker': ticker.replace('.ME', ''),
            'startDate': start_date,
            'endDate': end_date,
            'interval': interval,
            'data': json.loads(df.reset_index().to_json(orient='records', date_format='iso'))
        }

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/download', methods=['POST'])
def download_data():
    """Скачивание данных в формате JSON"""
    try:
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({'error': 'No data provided'}), 400

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            json.dump(data, tmp, indent=4)
            tmp_path = tmp.name

        response = make_response(send_file(
            tmp_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"moex_{data.get('ticker', 'data')}_{datetime.now().strftime('%Y%m%d')}.json"
        ))

        response.call_on_close(lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)
        return response

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST', 'OPTIONS'])
def run_backtest():
    """Запуск бэктеста"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    try:
        request_data = request.get_json()
        if not request_data or 'data' not in request_data:
            return jsonify({'error': 'No data provided'}), 400

        # Создаем экземпляр бэктестера
        backtester = Backtester()

        # Загружаем данные
        if not backtester.load_data_from_json(request_data['data']):
            return jsonify({'error': 'Failed to load data'}), 400

        # Устанавливаем параметры
        backtester.set_strategy_parameters(
            indicators=request_data.get('strategy_params', {}).get('indicators', []),
            logic=request_data.get('strategy_params', {}).get('logic', 'AND')
        )

        backtester.set_risk_parameters(
            initial_capital=float(request_data.get('initial_capital', 10000)),
            max_trade_amount=float(request_data.get('max_trade_amount', 1000)),
            stop_loss=float(request_data.get('stop_loss', 0.05)),
            take_profit=float(request_data.get('take_profit', 0.10))
        )

        # Запускаем бэктест
        results = backtester.run_backtest()

        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Backtest error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    )