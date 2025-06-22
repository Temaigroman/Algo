document.addEventListener('DOMContentLoaded', function() {
    const showFormBtn = document.getElementById('showFormBtn');
    const dataForm = document.getElementById('dataForm');
    const fetchDataBtn = document.getElementById('fetchDataBtn');
    const tickerInput = document.getElementById('ticker');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const timeframeSelect = document.getElementById('timeframe');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const dataTableContainer = document.getElementById('dataTableContainer');
    
    // Устанавливаем текущую дату по умолчанию для конечной даты
    const today = new Date().toISOString().split('T')[0];
    endDateInput.value = today;
    
    // Показываем форму при нажатии на кнопку
    showFormBtn.addEventListener('click', function() {
        dataForm.classList.toggle('hidden');
        if (!dataForm.classList.contains('hidden')) {
            tickerInput.focus();
        }
    });
    
    // Получаем данные при нажатии на кнопку
    fetchDataBtn.addEventListener('click', function() {
        const ticker = tickerInput.value.trim().toUpperCase();
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const timeframe = timeframeSelect.value;
        
        // Валидация
        if (!ticker || !startDate || !endDate) {
            showError('Пожалуйста, заполните все поля');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            showError('Начальная дата не может быть позже конечной даты');
            return;
        }
        
        // Здесь должен быть запрос к API для получения данных
        // Для демонстрации используем моковые данные
        fetchHistoricalData(ticker, startDate, endDate, timeframe);
    });
    
    function fetchHistoricalData(ticker, startDate, endDate, timeframe) {
        // В реальном приложении здесь должен быть fetch или axios запрос к API
        // Например:
        /*
        fetch(`https://api.marketdata.com/v3/historical?ticker=${ticker}&start=${startDate}&end=${endDate}&timeframe=${timeframe}`)
            .then(response => response.json())
            .then(data => displayData(data))
            .catch(error => showError('Ошибка при получении данных: ' + error.message));
        */
        
        // Для демонстрации используем моковые данные
        console.log(`Запрос данных для: ${ticker}, с ${startDate} по ${endDate}, таймфрейм: ${timeframe}`);
        
        // Имитация задержки запроса
        setTimeout(() => {
            // Моковые данные
            const mockData = generateMockData(ticker, startDate, endDate, timeframe);
            displayData(mockData);
        }, 1000);
    }
    
    function generateMockData(ticker, startDate, endDate, timeframe) {
        const data = [];
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        // Генерируем случайные данные для каждого дня в диапазоне
        for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
            const open = (100 + Math.random() * 50).toFixed(2);
            const high = (parseFloat(open) + Math.random() * 10).toFixed(2);
            const low = (parseFloat(open) - Math.random() * 10).toFixed(2);
            const close = (parseFloat(low) + Math.random() * (parseFloat(high) - parseFloat(low))).toFixed(2);
            const volume = Math.floor(Math.random() * 10000000);
            
            data.push({
                date: date.toISOString().split('T')[0],
                open,
                high,
                low,
                close,
                volume
            });
        }
        
        return {
            ticker,
            startDate,
            endDate,
            timeframe,
            data
        };
    }
    
    function displayData(data) {
        errorDiv.classList.add('hidden');
        
        // Создаем таблицу с данными
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
            tableHTML += `
                <tr>
                    <td>${item.date}</td>
                    <td>${item.open}</td>
                    <td>${item.high}</td>
                    <td>${item.low}</td>
                    <td>${item.close}</td>
                    <td>${item.volume.toLocaleString()}</td>
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