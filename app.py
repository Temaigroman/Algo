import sys
import os
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import json
import logging
import traceback

# Настраиваем пути к шаблонам и статическим файлам
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'front', 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'front', 'static'))

# Добавляем путь к папке back/Data в Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'back', 'Data'))

# Импортируем после настройки пути
from Data import YahooFinanceHistory

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get-historical-data', methods=['POST'])
def get_historical_data():
    try:
        logger.debug("Received request data: %s", request.json)

        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        ticker = data.get('ticker', '').upper()
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        timeframe = data.get('timeframe', '1d')

        if not ticker or not start_date:
            return jsonify({"error": "Ticker and start date are required"}), 400

        logger.debug(f"Fetching data for {ticker} from {start_date} to {end_date} with {timeframe} interval")

        service = YahooFinanceHistory()
        df = service.get_historical_data(ticker, start_date, end_date, timeframe)

        if df is None or df.empty:
            error_msg = f"No data found for {ticker} with given parameters"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 404

        logger.debug("Successfully fetched %d rows of data", len(df))

        result = {
            "ticker": ticker,
            "startDate": start_date,
            "endDate": end_date if end_date else datetime.now().strftime('%Y-%m-%d'),
            "timeframe": timeframe,
            "data": json.loads(df.reset_index().to_json(orient='records', date_format='iso'))
        }

        return jsonify(result)

    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


if __name__ == '__main__':
    # Проверка путей
    print("Путь к шаблонам:", app.template_folder)
    print("Файлы в templates:", os.listdir(app.template_folder))
    print("Путь к static:", app.static_folder)
    print("Файлы в static:", os.listdir(app.static_folder))

    app.run(debug=True, host='0.0.0.0', port=5000)