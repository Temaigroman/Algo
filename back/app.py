from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import json
from Backtest.Backtesting import Backtester
from Data.Data import YahooFinanceHistory

# Инициализация приложения
app = FastAPI()

# Получаем абсолютный путь к корневой директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Пути к статическим файлам и шаблонам
STATIC_DIR = BASE_DIR / "front" / "static"
TEMPLATES_DIR = BASE_DIR / "front" / "templates"

# Проверка существования путей (для отладки)
print(f"Static directory exists: {STATIC_DIR.exists()}")
print(f"Templates directory exists: {TEMPLATES_DIR.exists()}")

# Монтирование статических файлов
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

# Инициализация шаблонизатора
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/get_data")
async def get_data(
        ticker: str = Form(...),
        start_date: str = Form(...),
        end_date: str = Form(None),
        interval: str = Form("1d")
):
    """Получение исторических данных"""
    yf = YahooFinanceHistory()
    data = yf.get_historical_data(ticker, start_date, end_date, interval)
    if data is None:
        return JSONResponse({"error": "Не удалось загрузить данные"}, status_code=400)

    # Конвертация в JSON
    json_data = data.reset_index().to_json(orient="records", date_format="iso")
    return JSONResponse({"data": json_data})


@app.post("/run_backtest")
async def run_backtest(
        ticker: str = Form(...),
        strategy: str = Form(...),
        initial_capital: float = Form(10000),
        stop_loss: float = Form(0.05),
        take_profit: float = Form(0.10)
):
    """Запуск бэктеста"""
    try:
        # Получаем данные
        yf = YahooFinanceHistory()
        data = yf.get_historical_data(ticker, "2020-01-01")  # Можно изменить на параметры из формы

        # Запускаем бэктест
        backtester = Backtester()
        backtester.load_data(json.loads(data.reset_index().to_json(orient="records")))
        backtester.add_indicator(strategy)
        backtester.initial_capital = initial_capital
        backtester.stop_loss = stop_loss
        backtester.take_profit = take_profit

        # Получаем результаты
        portfolio_values = backtester.portfolio_values
        dates = [str(date) for date in backtester.data.index]

        return JSONResponse({
            "dates": dates,
            "portfolio_values": portfolio_values,
            "stats": {
                "return": f"{(portfolio_values[-1] / initial_capital - 1) * 100:.2f}",
                "max_drawdown": "5.25"  # Здесь должна быть ваша логика расчета
            }
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)