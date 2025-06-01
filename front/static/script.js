// Загрузка данных
document.getElementById("dataForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch("/get_data", {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        alert("Ошибка при загрузке данных!");
        return;
    }

    const data = await response.json();
    console.log("Данные загружены:", data);
    alert("Данные успешно загружены!");
});

// Запуск бэктеста
document.getElementById("backtestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch("/run_backtest", {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        alert("Ошибка при запуске бэктеста!");
        return;
    }

    const results = await response.json();
    renderResults(results);
});

// Отрисовка результатов
function renderResults(data) {
    const ctx = document.getElementById('chart').getContext('2d');

    // Удаляем старый график, если есть
    if (window.myChart) {
        window.myChart.destroy();
    }

    // Создаем новый график
    window.myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Стоимость портфеля ($)',
                data: data.portfolio_values,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Дата'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Стоимость ($)'
                    }
                }
            }
        }
    });

    // Выводим статистику
    document.getElementById("stats").innerHTML = `
        <h3>📊 Результаты бэктеста</h3>
        <p>Доходность: <strong>${data.stats.return}%</strong></p>
        <p>Максимальная просадка: <strong>${data.stats.max_drawdown}%</strong></p>
    `;
}