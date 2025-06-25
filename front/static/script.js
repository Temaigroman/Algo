document.addEventListener('DOMContentLoaded', () => {
    // DOM элементы
    const showFormBtn = document.getElementById('showFormBtn');
    const dataForm = document.getElementById('dataForm');
    const tickerInput = document.getElementById('ticker');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const timeframeSelect = document.getElementById('timeframe');
    const fetchDataBtn = document.getElementById('fetchDataBtn');
    const downloadJsonBtn = document.getElementById('downloadJsonBtn');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const dataTableContainer = document.getElementById('dataTableContainer');

    // Установка дат по умолчанию
    endDateInput.value = new Date().toISOString().split('T')[0];
    startDateInput.value = new Date(new Date().setFullYear(new Date().getFullYear() - 1))
        .toISOString().split('T')[0];

    // Показ/скрытие формы
    showFormBtn.addEventListener('click', () => {
        dataForm.classList.toggle('hidden');
    });

    // Получение данных
    fetchDataBtn.addEventListener('click', async () => {
        try {
            const ticker = tickerInput.value.trim().toUpperCase();
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;
            const timeframe = timeframeSelect.value;

            if (!ticker || !startDate || !endDate) {
                showError('Пожалуйста, заполните все обязательные поля');
                return;
            }

            const response = await fetch('/api/historical', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker,
                    startDate,
                    endDate,
                    interval: timeframe
                })
            });

            const data = await response.json();

            if (!response.ok) {
                showError(data.error || 'Ошибка при получении данных');
                return;
            }

            displayData(data);
        } catch (err) {
            showError('Ошибка соединения: ' + err.message);
            console.error('Fetch error:', err);
        }
    });

    // Скачивание данных
    downloadJsonBtn.addEventListener('click', async () => {
        if (!dataTableContainer.dataset.rawData) {
            showError('Нет данных для скачивания');
            return;
        }

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: dataTableContainer.dataset.rawData
            });

            if (!response.ok) {
                throw new Error('Ошибка при скачивании');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `stock_data_${new Date().toISOString()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            showError('Ошибка при скачивании: ' + err.message);
            console.error('Download error:', err);
        }
    });

    // Отображение данных
    function displayData(data) {
    errorDiv.classList.add('hidden');
    dataTableContainer.dataset.rawData = JSON.stringify(data);

    const tableHTML = `
        <h3>${data.ticker} (${data.startDate} - ${data.endDate})</h3>
        <div class="table-responsive">
            <table class="table">
                <thead>
                    <tr>
                        <th>Дата</th>
                        <th>Открытие</th>
                        <th>Максимум</th>
                        <th>Минимум</th>
                        <th>Закрытие</th>
                        <th>Объем</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.data.map(item => {
                        // Преобразуем ключи из формата ('Close', 'AAPL') в простые значения
                        const transformedItem = {
                            Date: item["('Date', '')"],
                            Open: item["('Open', 'AAPL')"],
                            High: item["('High', 'AAPL')"],
                            Low: item["('Low', 'AAPL')"],
                            Close: item["('Close', 'AAPL')"],
                            Volume: item["('Volume', 'AAPL')"]
                        };

                        return `
                            <tr>
                                <td>${formatDate(transformedItem.Date)}</td>
                                <td>${formatNumber(transformedItem.Open)}</td>
                                <td>${formatNumber(transformedItem.High)}</td>
                                <td>${formatNumber(transformedItem.Low)}</td>
                                <td>${formatNumber(transformedItem.Close)}</td>
                                <td>${formatVolume(transformedItem.Volume)}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    dataTableContainer.innerHTML = tableHTML;
    resultsDiv.classList.remove('hidden');
}

// Добавляем новую функцию для форматирования даты
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
        return dateString; // Возвращаем как есть, если не удалось распарсить
    }
}

// Обновляем formatNumber и formatVolume
function formatNumber(value) {
    if (value === null || value === undefined) return 'N/A';
    return Number(value).toFixed(2);
}

function formatVolume(value) {
    if (value === null || value === undefined) return 'N/A';
    return parseInt(value).toLocaleString();
}

    // Вспомогательные функции
    function formatNumber(value) {
        return value?.toFixed?.(2) ?? 'N/A';
    }

    function formatVolume(value) {
        return value?.toLocaleString?.() ?? 'N/A';
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
    }
});