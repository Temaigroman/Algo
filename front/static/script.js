document.addEventListener('DOMContentLoaded', () => {
    // Получаем элементы
    const elements = {
        showFormBtn: document.getElementById('showFormBtn'),
        dataForm: document.getElementById('dataForm'),
        tickerInput: document.getElementById('ticker'),
        startDateInput: document.getElementById('startDate'),
        endDateInput: document.getElementById('endDate'),
        timeframeSelect: document.getElementById('timeframe'),
        fetchDataBtn: document.getElementById('fetchDataBtn'),
        downloadJsonBtn: document.getElementById('downloadJsonBtn'),
        resultsDiv: document.getElementById('results'),
        errorDiv: document.getElementById('error'),
        dataTableContainer: document.getElementById('dataTableContainer'),
        loadingIndicator: document.getElementById('loadingIndicator')
    };

    // Устанавливаем даты по умолчанию
    const today = new Date();
    elements.endDateInput.value = today.toISOString().split('T')[0];
    elements.startDateInput.value = new Date(today.setFullYear(today.getFullYear() - 1))
        .toISOString().split('T')[0];

    // Обработчик для кнопки "Показать форму"
    elements.showFormBtn.addEventListener('click', (e) => {
        e.preventDefault();
        elements.dataForm.classList.toggle('hidden');
        elements.showFormBtn.textContent = elements.dataForm.classList.contains('hidden')
            ? 'Показать форму'
            : 'Скрыть форму';
    });

    // Обработчик для кнопки "Получить данные"
    elements.fetchDataBtn.addEventListener('click', async () => {
        try {
            elements.errorDiv.classList.add('hidden');
            elements.fetchDataBtn.disabled = true;
            elements.loadingIndicator.style.display = 'flex';
            elements.resultsDiv.classList.add('hidden');

            const ticker = elements.tickerInput.value.trim().toUpperCase();
            const startDate = elements.startDateInput.value;
            const endDate = elements.endDateInput.value;
            const timeframe = elements.timeframeSelect.value;

            if (!ticker || !startDate || !endDate) {
                throw new Error('Пожалуйста, заполните все поля');
            }

            // Добавляем .ME для российских акций, если не указано
            const fullTicker = ticker.endsWith('.ME') || !['SBER', 'GAZP', 'VTBR', 'MOEX', 'GMKN'].includes(ticker)
                ? ticker
                : `${ticker}.ME`;

            const response = await fetch('http://127.0.0.1:5000/api/historical', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                credentials: 'include',
                body: JSON.stringify({
                    ticker: fullTicker,
                    startDate: startDate,
                    endDate: endDate,
                    interval: timeframe
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({
                    error: 'Ошибка сервера'
                }));
                throw new Error(errorData.error || `Ошибка: ${response.status}`);
            }

            const data = await response.json();
            console.log('Полученные данные:', data); // Для отладки

            if (!data?.data?.length) {
                throw new Error('Данные не найдены. Проверьте параметры запроса.');
            }

            displayData(data);

        } catch (error) {
            showError(error.message);
            console.error('Fetch error:', error);
        } finally {
            elements.fetchDataBtn.disabled = false;
            elements.loadingIndicator.style.display = 'none';
        }
    });

    function showError(message) {
        elements.errorDiv.textContent = message;
        elements.errorDiv.classList.remove('hidden');
    }

    function displayData(data) {
        try {
            elements.dataTableContainer.dataset.rawData = JSON.stringify(data);

            let tableHtml = `
                <h3>${data.ticker} (${formatDate(data.startDate)} - ${formatDate(data.endDate)})</h3>
                <div class="table-responsive">
                    <table class="table table-striped">
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
                // Динамически определяем ключи полей
                const keys = Object.keys(item);
                const dateKey = keys.find(k => k.toLowerCase().includes('datetime') ||
                                      k.toLowerCase().includes('date')) || keys[0];

                const getValue = (field) => {
                    const fieldKey = keys.find(k =>
                        k.toLowerCase().includes(field.toLowerCase()) &&
                        (k.includes(data.ticker) || !k.includes(')'))
                    );
                    return fieldKey ? item[fieldKey] : null;
                };

                const dateValue = item[dateKey];
                const open = getValue('open');
                const high = getValue('high');
                const low = getValue('low');
                const close = getValue('close');
                const volume = getValue('volume');

                tableHtml += `
                    <tr>
                        <td>${formatDateTime(dateValue)}</td>
                        <td>${formatCurrency(open)}</td>
                        <td>${formatCurrency(high)}</td>
                        <td>${formatCurrency(low)}</td>
                        <td>${formatCurrency(close)}</td>
                        <td>${formatNumber(volume)}</td>
                    </tr>
                `;
            });

            tableHtml += `
                        </tbody>
                    </table>
                </div>
            `;

            elements.dataTableContainer.innerHTML = tableHtml;
            elements.resultsDiv.classList.remove('hidden');

        } catch (error) {
            showError('Ошибка при отображении данных');
            console.error('Display error:', error);
            console.log('Полученные данные:', data);
        }
    }

    elements.downloadJsonBtn.addEventListener('click', () => {
        try {
            if (!elements.dataTableContainer.dataset.rawData) {
                throw new Error('Нет данных для скачивания');
            }

            const dataStr = elements.dataTableContainer.dataset.rawData;
            const data = JSON.parse(dataStr);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `stock_${data.ticker}_${data.startDate}_${data.endDate}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            showError(error.message);
        }
    });

    // Функции форматирования
    function formatDate(dateStr) {
        try {
            return new Date(dateStr).toLocaleDateString('ru-RU');
        } catch {
            return dateStr;
        }
    }

    function formatDateTime(dateStr) {
        if (!dateStr) return 'нет данных';
        try {
            const cleanDateStr = String(dateStr).replace(/[()']/g, '');
            const date = new Date(cleanDateStr);
            return date.toLocaleDateString('ru-RU');
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

    function formatNumber(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return 'нет данных';
        }
        return Number(value).toLocaleString('ru-RU');
    }
});