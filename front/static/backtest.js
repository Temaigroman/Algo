document.addEventListener('DOMContentLoaded', () => {
            // Элементы страницы
            const elements = {
                dataUploadArea: document.getElementById('dataUploadArea'),
                fileInput: document.getElementById('fileInput'),
                indicatorsContainer: document.getElementById('indicatorsContainer'),
                logicSelect: document.getElementById('logicSelect'),
                initialCapital: document.getElementById('initialCapital'),
                maxTradeAmount: document.getElementById('maxTradeAmount'),
                stopLoss: document.getElementById('stopLoss'),
                takeProfit: document.getElementById('takeProfit'),
                runBacktestBtn: document.getElementById('runBacktestBtn'),
                resultsContainer: document.getElementById('resultsContainer'),
                dataInfo: document.getElementById('dataInfo'),
                loadingIndicator: document.getElementById('loadingIndicator'),
                tradesTable: document.querySelector('#tradesTable tbody'),
                priceChart: document.getElementById('priceChart'),
                portfolioChart: document.getElementById('portfolioChart'),
                resultsDiv: document.getElementById('resultsDiv')
            };

            // Доступные индикаторы
            const availableIndicators = [
                {
                    id: 'sma',
                    name: 'SMA',
                    description: 'Простая скользящая средняя',
                    params: [
                        { name: 'window', label: 'Период', type: 'number', default: 20, min: 5, max: 200 }
                    ]
                },
                {
                    id: 'ema',
                    name: 'EMA',
                    description: 'Экспоненциальная скользящая средняя',
                    params: [
                        { name: 'window', label: 'Период', type: 'number', default: 20, min: 5, max: 200 }
                    ]
                },
                {
                    id: 'rsi',
                    name: 'RSI',
                    description: 'Индекс относительной силы',
                    params: [
                        { name: 'window', label: 'Период', type: 'number', default: 14, min: 5, max: 50 },
                        { name: 'overbought', label: 'Перекупленность', type: 'number', default: 70, min: 50, max: 90 },
                        { name: 'oversold', label: 'Перепроданность', type: 'number', default: 30, min: 10, max: 50 }
                    ]
                },
                {
                    id: 'bollinger',
                    name: 'Bollinger Bands',
                    description: 'Полосы Боллинджера',
                    params: [
                        { name: 'window', label: 'Период', type: 'number', default: 20, min: 5, max: 50 },
                        { name: 'std_dev', label: 'Станд. отклонения', type: 'number', default: 2, min: 1, max: 3, step: 0.1 }
                    ]
                },
                {
                    id: 'macd',
                    name: 'MACD',
                    description: 'Moving Average Convergence Divergence',
                    params: [
                        { name: 'fast', label: 'Быстрый период', type: 'number', default: 12, min: 5, max: 26 },
                        { name: 'slow', label: 'Медленный период', type: 'number', default: 26, min: 10, max: 50 },
                        { name: 'signal', label: 'Сигнальный период', type: 'number', default: 9, min: 5, max: 20 }
                    ]
                }
            ];

            // Выбранные индикаторы
            let selectedIndicators = [];
            let historicalData = null;
            let priceChart = null;
            let portfolioChart = null;

            // Инициализация страницы
            function initPage() {
                setupEventListeners();
                renderIndicators();
            }

            // Настройка обработчиков событий
            function setupEventListeners() {
                // Обработчики для загрузки данных
                elements.dataUploadArea.addEventListener('click', () => elements.fileInput.click());

                elements.fileInput.addEventListener('change', handleFileSelect);

                elements.dataUploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    elements.dataUploadArea.classList.add('dragover');
                });

                elements.dataUploadArea.addEventListener('dragleave', () => {
                    elements.dataUploadArea.classList.remove('dragover');
                });

                elements.dataUploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    elements.dataUploadArea.classList.remove('dragover');
                    if (e.dataTransfer.files.length) {
                        elements.fileInput.files = e.dataTransfer.files;
                        handleFileSelect({ target: elements.fileInput });
                    }
                });

                elements.runBacktestBtn.addEventListener('click', runBacktest);
            }

            // Обработка выбора файла
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const parsedData = JSON.parse(e.target.result);

                        // Проверяем обязательные поля
                        if (!parsedData.data || !Array.isArray(parsedData.data)) {
                            throw new Error('Неверный формат данных. Ожидается объект с полем data (массив)');
                        }

                        historicalData = parsedData;
                        updateDataInfo();
                        updateRunButtonState();
                        showSuccess('Данные успешно загружены!');
                    } catch (error) {
                        showError('Ошибка при загрузке файла: ' + error.message);
                    }
                };
                reader.onerror = () => showError('Ошибка при чтении файла');
                reader.readAsText(file);
            }

            // Обновление информации о данных
            function updateDataInfo() {
                if (historicalData) {
                    elements.dataInfo.innerHTML = `
                        <div class="alert alert-success">
                            <p><strong>Данные успешно загружены</strong></p>
                            ${historicalData.ticker ? `<p><strong>Тикер:</strong> ${historicalData.ticker}</p>` : ''}
                            ${historicalData.startDate ? `<p><strong>Начальная дата:</strong> ${formatDate(historicalData.startDate)}</p>` : ''}
                            ${historicalData.endDate ? `<p><strong>Конечная дата:</strong> ${formatDate(historicalData.endDate)}</p>` : ''}
                            <p><strong>Количество записей:</strong> ${historicalData.data.length}</p>
                        </div>
                    `;
                } else {
                    elements.dataInfo.innerHTML = '<div class="alert alert-warning">Данные не загружены</div>';
                }
            }

            // Обновление состояния кнопки запуска
            function updateRunButtonState() {
                elements.runBacktestBtn.disabled = !(historicalData && selectedIndicators.length > 0);
            }

            // Запуск бэктеста
            async function runBacktest() {
                if (!historicalData || selectedIndicators.length === 0) return;

                try {
                    elements.runBacktestBtn.disabled = true;
                    elements.loadingIndicator.style.display = 'flex';
                    elements.resultsContainer.classList.add('hidden');

                    const params = {
                        data: historicalData,
                        strategy_params: {
                            indicators: selectedIndicators.map(ind => ({
                                type: ind.name.toUpperCase(),
                                ...ind.params
                            })),
                            logic: elements.logicSelect.value
                        },
                        initial_capital: parseFloat(elements.initialCapital.value),
                        max_trade_amount: parseFloat(elements.maxTradeAmount.value),
                        stop_loss: parseFloat(elements.stopLoss.value) / 100,
                        take_profit: parseFloat(elements.takeProfit.value) / 100
                    };

                    const response = await fetch('/api/backtest', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(params)
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.error || 'Ошибка сервера');
                    }

                    const data = await response.json();
                    displayResults(data);

                } catch (error) {
                    showError(error.message);
                    console.error('Backtest error:', error);
                } finally {
                    elements.runBacktestBtn.disabled = false;
                    elements.loadingIndicator.style.display = 'none';
                }
            }

            // Отображение результатов
            function displayResults(data) {
                try {
                    // Основные результаты
                    elements.resultsDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h4>Результаты бэктеста</h4>
                            <p>Начальный капитал: ${formatCurrency(data.initial_capital)}</p>
                            <p>Конечный капитал: ${formatCurrency(data.final_capital)}</p>
                            <p>Общая доходность: ${data.total_return.toFixed(2)}%</p>
                            <p>Максимальная просадка: ${data.max_drawdown.toFixed(2)}%</p>
                            <p>Прибыльные сделки: ${data.winning_trades}</p>
                            <p>Убыточные сделки: ${data.losing_trades}</p>
                            <p>Фактор прибыли: ${data.profit_factor.toFixed(2)}</p>
                        </div>
                    `;

                    // Сделки
                    elements.tradesTable.innerHTML = data.trades.map(trade => `
                        <tr class="${trade.profit < 0 ? 'table-danger' : 'table-success'}">
                            <td>${formatDateTime(trade.date)}</td>
                            <td>${trade.type}</td>
                            <td>${formatCurrency(trade.price)}</td>
                            <td>${formatCurrency(trade.amount)}</td>
                            <td>${trade.profit !== null ? formatCurrency(trade.profit) : 'N/A'}</td>
                        </tr>
                    `).join('');

                    // Графики
                    renderCharts(data);

                    // Показываем результаты
                    elements.resultsContainer.classList.remove('hidden');

                } catch (error) {
                    showError('Ошибка при отображении результатов');
                    console.error('Results display error:', error);
                }
            }

            // Построение графиков
            function renderCharts(data) {
                // Очистка предыдущих графиков
                if (priceChart) priceChart.destroy();
                if (portfolioChart) portfolioChart.destroy();

                // График цены
                const priceLabels = historicalData.data.map(item => formatDate(item.Date));
                const priceData = historicalData.data.map(item => parseFloat(item.Close));

                priceChart = new Chart(elements.priceChart, {
                    type: 'line',
                    data: {
                        labels: priceLabels,
                        datasets: [{
                            label: 'Цена закрытия',
                            data: priceData,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });

                // График портфеля
                const portfolioLabels = data.equity_curve.map(item => formatDate(item.date));
                const portfolioData = data.equity_curve.map(item => item.value);

                portfolioChart = new Chart(elements.portfolioChart, {
                    type: 'line',
                    data: {
                        labels: portfolioLabels,
                        datasets: [{
                            label: 'Стоимость портфеля',
                            data: portfolioData,
                            borderColor: 'rgb(54, 162, 235)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }

            // Рендер доступных индикаторов
            function renderIndicators() {
                elements.indicatorsContainer.innerHTML = '';

                availableIndicators.forEach(indicator => {
                    const isSelected = selectedIndicators.some(i => i.id === indicator.id);

                    const card = document.createElement('div');
                    card.className = `col-md-6 indicator-card ${isSelected ? 'selected' : ''}`;
                    card.innerHTML = `
                        <div class="card h-100">
                            <div class="card-body">
                                <h6 class="card-title">${indicator.name}</h6>
                                <p class="card-text small text-muted">${indicator.description}</p>
                                ${isSelected ? renderIndicatorParams(indicator) : ''}
                            </div>
                        </div>
                    `;

                    card.addEventListener('click', (e) => {
                        if (e.target.tagName === 'INPUT') return;

                        if (isSelected) {
                            selectedIndicators = selectedIndicators.filter(i => i.id !== indicator.id);
                        } else {
                            selectedIndicators.push({
                                id: indicator.id,
                                name: indicator.name,
                                params: indicator.params.reduce((acc, param) => {
                                    acc[param.name] = param.default;
                                    return acc;
                                }, {})
                            });
                        }

                        renderIndicators();
                        updateRunButtonState();
                    });

                    elements.indicatorsContainer.appendChild(card);
                });
            }

            // Рендер параметров индикатора
            function renderIndicatorParams(indicator) {
                const selected = selectedIndicators.find(i => i.id === indicator.id);
                if (!selected) return '';

                return indicator.params.map(param => `
                    <div class="mb-2">
                        <label class="form-label small">${param.label}:</label>
                        <input type="${param.type}"
                               class="form-control form-control-sm"
                               value="${selected.params[param.name]}"
                               min="${param.min || ''}"
                               max="${param.max || ''}"
                               step="${param.step || '1'}"
                               data-indicator="${indicator.id}"
                               data-param="${param.name}"
                               oninput="updateIndicatorParam(this)">
                    </div>
                `).join('');
            }

            // Функции форматирования
            function formatDate(dateStr) {
                if (!dateStr) return 'нет данных';
                try {
                    const date = new Date(dateStr);
                    return date.toLocaleDateString('ru-RU');
                } catch {
                    return dateStr;
                }
            }

            function formatDateTime(dateStr) {
                if (!dateStr) return 'нет данных';
                try {
                    const date = new Date(dateStr);
                    return date.toLocaleString('ru-RU');
                } catch {
                    return dateStr;
                }
            }

            function formatCurrency(value) {
                if (value === null || value === undefined || isNaN(value)) {
                    return 'нет данных';
                }
                return Number(value).toLocaleString('ru-RU', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }

            // Вспомогательные функции
            function showError(message) {
                alert(message); // В реальном приложении можно заменить на более красивый вывод
            }

            function showSuccess(message) {
                alert(message); // В реальном приложении можно заменить на более красивый вывод
            }

            // Глобальная функция для обновления параметров индикатора
            window.updateIndicatorParam = function(input) {
                const indicatorId = input.dataset.indicator;
                const paramName = input.dataset.param;

                const indicator = selectedIndicators.find(i => i.id === indicatorId);
                if (indicator) {
                    indicator.params[paramName] = parseFloat(input.value) || input.value;
                }
            };

            // Инициализация страницы
            initPage();
        });