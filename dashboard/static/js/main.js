function updateDashboard() {
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
        .catch(err => console.error("Lỗi cập nhật dashboard:", err));
}

function setMode(mode) {
    fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode })
    })
    .then(res => res.json())
    .then(() => updateDashboard())
    .catch(err => console.error("Lỗi gửi lệnh điều khiển:", err));
}

// Cập nhật ngay khi tải trang và lặp lại mỗi 1 giây
document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();
    setInterval(updateDashboard, 1000);
});
