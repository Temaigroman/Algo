document.addEventListener('DOMContentLoaded', function() {
    const showFormBtn = document.getElementById('showFormBtn');
    const dataForm = document.getElementById('dataForm');
    const fetchDataBtn = document.getElementById('fetchDataBtn');
    const downloadJsonBtn = document.getElementById('downloadJsonBtn');
    const tickerInput = document.getElementById('ticker');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const timeframeSelect = document.getElementById('timeframe');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const dataTableContainer = document.getElementById('dataTableContainer');

    // Устанавливаем текущую дату по умолчанию
    const today = new Date().toISOString().split('T')[0];
    endDateInput.value = today;

    // Показываем форму
    showFormBtn.addEventListener('click', function() {
        dataForm.classList.toggle('hidden');
        if (!dataForm.classList.contains('hidden')) {
            tickerInput.focus();
        }
    });

    // Получаем данные
    fetchDataBtn.addEventListener('click', async function() {
        const ticker = tickerInput.value.trim().toUpperCase();
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const timeframe = timeframeSelect.value;

        if (!ticker || !startDate || !endDate) {
            showError('Пожалуйста, заполните все поля');
            return;
        }

        if (new Date(startDate) > new Date(endDate)) {
            showError('Начальная дата не может быть позже конечной даты');
            return;
        }

        try {
            const response = await fetch('/get-historical-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: ticker,
                    startDate: startDate,
                    endDate: endDate,
                    timeframe: timeframe
                })
            });

            const data = await response.json();

            if (data.error) {
                showError(data.error);
                return;
            }

            displayData(data);
        } catch (error) {
            showError('Ошибка при получении данных: ' + error.message);
        }
    });

    // Скачивание JSON
    downloadJsonBtn.addEventListener('click', async function() {
        if (!dataTableContainer.innerHTML) {
            showError('Нет данных для скачивания');
            return;
        }

        const ticker = tickerInput.value.trim().toUpperCase();
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const timeframe = timeframeSelect.value;

        try {
            const response = await fetch('/download-json', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: ticker,
                    startDate: startDate,
                    endDate: endDate,
                    timeframe: timeframe,
                    data: JSON.parse(dataTableContainer.dataset.rawData || '[]')
                })
            });

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${ticker}_${startDate}_to_${endDate}.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (error) {
            showError('Ошибка при скачивании: ' + error.message);
        }
    });

    function displayData(data) {
    errorDiv.classList.add('hidden');

    // Сохраняем сырые данные для скачивания
    dataTableContainer.dataset.rawData = JSON.stringify(data.data);

    let tableHTML = `
        <h3>${data.ticker} с ${data.startDate} по ${data.endDate} (${getTimeframeLabel(data.timeframe)})</h3>
        <table>
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
    `;

    data.data.forEach(item => {
        // Добавляем проверки на undefined/null и форматирование
        const formatValue = (value) => {
            if (value === null || value === undefined) return 'N/A';
            if (typeof value === 'number') {
                // Форматируем числа (цену и объем по-разному)
                if (item.hasOwnProperty('Volume') || item.hasOwnProperty('volume')) {
                    return value.toLocaleString();
                }
                return value.toFixed(2);
            }
            return value;
        };

        tableHTML += `
            <tr>
                <td>${item.Date || item.date || 'N/A'}</td>
                <td>${formatValue(item.Open || item.open)}</td>
                <td>${formatValue(item.High || item.high)}</td>
                <td>${formatValue(item.Low || item.low)}</td>
                <td>${formatValue(item.Close || item.close)}</td>
                <td>${formatValue(item.Volume || item.volume)}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    dataTableContainer.innerHTML = tableHTML;
    resultsDiv.classList.remove('hidden');
}
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
    }
    
    function getTimeframeLabel(timeframe) {
        const timeframes = {
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
        };
        
        return timeframes[timeframe] || timeframe;
    }
});