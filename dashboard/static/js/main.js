// Khởi tạo biến biểu đồ
let trafficChart = null;

function initChart() {
    const ctx = document.getElementById('trafficChart');
    if (!ctx) return;

    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Trục 1: Bắc - Nam (N1)',
                    data: [],
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Trục 2: Đông - Tây (N2)',
                    data: [],
                    borderColor: '#0284c7',
                    backgroundColor: 'rgba(2, 132, 199, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    beginAtZero: true,
                    suggestedMax: 8,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8', stepSize: 1 }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#f8fafc', font: { size: 13 } }
                }
            }
        }
    });
}

function updateStatus() {
    fetch('/api/status')
        .then(res => res.json())
        .then(data => {
            const n1Elem = document.getElementById('n1-val');
            const n2Elem = document.getElementById('n2-val');
            const green1Elem = document.getElementById('green1-val');
            const green2Elem = document.getElementById('green2-val');
            const badge = document.getElementById('mqtt-badge');

            if (n1Elem) n1Elem.innerText = data.n1 + " xe";
            if (n2Elem) n2Elem.innerText = data.n2 + " xe";
            if (green1Elem) green1Elem.innerText = data.green1 + " giây";
            if (green2Elem) green2Elem.innerText = data.green2 + " giây";

            if (badge) {
                if (data.mqtt_connected) {
                    badge.className = 'badge badge-online';
                    badge.innerText = 'MQTT: ONLINE';
                } else {
                    badge.className = 'badge badge-offline';
                    badge.innerText = 'MQTT: OFFLINE';
                }
            }
        })
        .catch(err => console.error("Lỗi cập nhật status:", err));
}

function updateHistoryAndStats() {
    fetch('/api/history')
        .then(res => res.json())
        .then(res => {
            const logs = res.history || [];
            const stats = res.stats || {};

            // 1. Cập nhật thống kê
            const totalElem = document.getElementById('total-logs');
            const avgN1Elem = document.getElementById('avg-n1');
            const avgN2Elem = document.getElementById('avg-n2');
            const maxElem = document.getElementById('max-vehicles');

            if (totalElem) totalElem.innerText = stats.total_records;
            if (avgN1Elem) avgN1Elem.innerText = stats.avg_n1 + " xe";
            if (avgN2Elem) avgN2Elem.innerText = stats.avg_n2 + " xe";
            if (maxElem) maxElem.innerText = Math.max(stats.max_n1, stats.max_n2) + " xe";

            // 2. Cập nhật biểu đồ Chart.js
            if (trafficChart && logs.length > 0) {
                trafficChart.data.labels = logs.map(l => l.time);
                trafficChart.data.datasets[0].data = logs.map(l => l.n1);
                trafficChart.data.datasets[1].data = logs.map(l => l.n2);
                trafficChart.update('none'); // Cập nhật mượt mà không giật
            }

            // 3. Cập nhật bảng dữ liệu lịch sử
            const tbody = document.getElementById('db-table-body');
            if (tbody && logs.length > 0) {
                const recentLogs = [...logs].reverse().slice(0, 10);
                tbody.innerHTML = recentLogs.map(l => `
                    <tr>
                        <td style="color: #94a3b8;">${l.full_time}</td>
                        <td class="val-orange" style="font-weight: bold;">${l.n1} xe</td>
                        <td class="val-blue" style="font-weight: bold;">${l.n2} xe</td>
                        <td>${l.green1}s</td>
                        <td>${l.green2}s</td>
                        <td><span class="mode-tag ${l.mode === 'AUTO' || l.mode === 'ADAPTIVE_AI' ? 'tag-auto' : 'tag-emergency'}">${l.mode}</span></td>
                    </tr>
                `).join('');
            }
        })
        .catch(err => console.error("Lỗi cập nhật history DB:", err));
}

function setMode(mode) {
    fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode })
    })
    .then(res => res.json())
    .then(() => {
        updateStatus();
        updateHistoryAndStats();
    })
    .catch(err => console.error("Lỗi gửi lệnh ghi đè:", err));
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    updateStatus();
    updateHistoryAndStats();

    // Lặp cập nhật
    setInterval(updateStatus, 1000);
    setInterval(updateHistoryAndStats, 2000);
});
