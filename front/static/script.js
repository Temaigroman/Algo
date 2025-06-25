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

    // Установка дат по умолчанию (MOEX хранит данные с 2020 года)
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
        errorDiv.classList.add('hidden');

        const ticker = tickerInput.value.trim().toUpperCase();
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const timeframe = timeframeSelect.value;

        if (!ticker || !startDate || !endDate) {
            showError('Пожалуйста, заполните все обязательные поля');
            return;
        }

        // Валидация дат
        const minDate = new Date('2020-01-01');
        const selectedStartDate = new Date(startDate);
        if (selectedStartDate < minDate) {
            showError('MOEX предоставляет данные только с 2020 года');
            return;
        }

        const response = await fetch('/api/historical', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                ticker: ticker,
                startDate: startDate,
                endDate: endDate,
                interval: timeframe
            })
        });

        if (response.status === 404) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Данные не найдены для указанного тикера или периода');
        }

        if (!response.ok) {
            throw new Error(`Ошибка сервера: ${response.status}`);
        }

        const data = await response.json();
        displayData(data);

    } catch (err) {
        showError(err.message);
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
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: dataTableContainer.dataset.rawData
            });

            if (!response.ok) {
                throw new Error('Ошибка при скачивании');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'moex_data.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            showError(err.message);
            console.error('Download error:', err);
        }
    });

    // Отображение данных
    function displayData(data) {
        errorDiv.classList.add('hidden');
        dataTableContainer.dataset.rawData = JSON.stringify(data);

        const tableHTML = `
            <h3>${data.ticker} (${data.startDate} - ${data.endDate}, ${data.interval})</h3>
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
                        ${data.data.map(item => `
                            <tr>
                                <td>${formatDate(item.Datetime || item.Date)}</td>
                                <td>${formatNumber(item.Open)}</td>
                                <td>${formatNumber(item.High)}</td>
                                <td>${formatNumber(item.Low)}</td>
                                <td>${formatNumber(item.Close)}</td>
                                <td>${formatVolume(item.Volume)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        dataTableContainer.innerHTML = tableHTML;
        resultsDiv.classList.remove('hidden');
    }

    // Вспомогательные функции
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU') +
                (date.getHours() ? ' ' + date.toLocaleTimeString('ru-RU') : '');
        } catch {
            return dateString;
        }
    }

    function formatNumber(value) {
        if (value === null || value === undefined) return 'N/A';
        return Number(value).toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function formatVolume(value) {
        if (value === null || value === undefined) return 'N/A';
        return parseInt(value).toLocaleString('ru-RU');
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
    }
});