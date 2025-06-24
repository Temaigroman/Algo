from flask import Flask, render_template, request, jsonify, send_file
from Data import YahooFinanceHistory
from datetime import datetime
import json
import os
import logging
import traceback

app = Flask(__name__)

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
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)