import os
import sys
import json
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file, make_response, render_template
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'back', 'Data'))

# Инициализация приложения
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'front', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'front', 'static'))
CORS(app)  # Разрешаем все CORS-запросы

# Настройка логирования
log_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
log_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

# Импорт после настройки путей
from Data import MoexAlgoHistory

service = MoexAlgoHistory()


# CORS предварительные запросы
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/')
def index():
    """Главная страница приложения"""
    return render_template('index.html')


@app.route('/api/historical', methods=['POST', 'OPTIONS'])
def get_historical_data():
    try:
        if request.method == 'OPTIONS':
            return _build_cors_preflight_response()

        data = request.get_json()
        app.logger.info(f"Request data: {data}")

        # Валидация параметров
        ticker = data.get('ticker', '').upper()
        start_date = data.get('startDate')
        end_date = data.get('endDate', datetime.now().strftime('%Y-%m-%d'))
        interval = data.get('interval', '1d')

        if not ticker or not start_date:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Получение данных
        df = service.get_historical_data(ticker, start_date, end_date, interval)

        if df is None:
            return jsonify({'error': 'No data available for the specified period'}), 404

        if df.empty:
            return jsonify({'error': 'Empty data received from MOEX'}), 404

        # Подготовка результата
        result = {
            'ticker': ticker,
            'startDate': start_date,
            'endDate': end_date,
            'interval': interval,
            'data': json.loads(df.reset_index().to_json(orient='records', date_format='iso'))
        }

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/download', methods=['POST'])
def download_data():
    try:
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({'error': 'No data provided'}), 400

        # Создание временного файла
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            json.dump(data, tmp, indent=4)
            tmp_path = tmp.name

        # Подготовка ответа
        response = make_response(send_file(
            tmp_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"moex_{data.get('ticker', 'data')}_{datetime.now().strftime('%Y%m%d')}.json"
        ))

        # Удаление файла после отправки
        response.call_on_close(lambda: os.unlink(tmp_path))
        return response

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)