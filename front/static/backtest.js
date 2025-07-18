document.addEventListener('DOMContentLoaded', () => {
    // Элементы страницы
    const elements = {
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
        portfolioChart: document.getElementById('portfolioChart')
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
        renderIndicators();
        checkLocalStorage();
        updateRunButtonState();
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
                        type: indicator.name.toUpperCase(),
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

    // Обновление параметров индикатора
    window.updateIndicatorParam = function(input) {
        const indicatorId = input.dataset.indicator;
        const paramName = input.dataset.param;

        const indicator = selectedIndicators.find(i => i.id === indicatorId);
        if (indicator) {
            indicator.params[paramName] = parseFloat(input.value) || input.value;
        }
    };

    // Проверка localStorage на наличие данных
    function checkLocalStorage() {
        const savedData = localStorage.getItem('historicalData');
        if (savedData) {
            try {
                historicalData = JSON.parse(savedData);
                updateDataInfo();
                updateRunButtonState();
            } catch (e) {
                console.error('Error parsing saved data:', e);
            }
        }
    }

    // Обновление информации о данных
    function updateDataInfo() {
        if (historicalData) {
            elements.dataInfo.innerHTML = `
                <p><strong>Тикер:</strong> ${historicalData.ticker}</p>
                <p><strong>Период:</strong> ${formatDate(historicalData.startDate)} - ${formatDate(historicalData.endDate)}</p>
                <p><strong>Таймфрейм:</strong> ${historicalData.interval}</p>
                <p><strong>Записей:</strong> ${historicalData.data.length}</p>
            `;
        } else {
            elements.dataInfo.innerHTML = '<p>Загрузите данные через <a href="/">основную форму</a></p>';
        }
    }

    // Обновление состояния кнопки запуска
    function updateRunButtonState() {
        elements.runBacktestBtn.disabled = !(historicalData && selectedIndicators.length > 0);
    }

    // Обработчик кнопки запуска бэктеста
    elements.runBacktestBtn.addEventListener('click', async () => {
        if (!historicalData || selectedIndicators.length === 0) return;

        try {
            elements.loadingIndicator.style.display = 'flex';
            elements.resultsContainer.innerHTML = '<p>Выполняется бэктест...</p>';

            const params = {
                data: historicalData,
                strategy