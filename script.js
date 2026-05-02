function log(text) {
    const out = document.getElementById('console-out');
    out.innerHTML += `<div>> ${text}</div>`;
    out.scrollTop = out.scrollHeight;
}

async function startScan() {
    const btn = document.getElementById('scan-btn');
    const grid = document.getElementById('device-grid');
    
    btn.disabled = true;
    grid.innerHTML = '';
    log("INITIALIZING_DEEP_SCAN...");
    
    try {
        const response = await fetch('http://127.0.0.1:5005/scan');
        const data = await response.json();
        
        log(`DISCOVERY_COMPLETE: ${data.length} NODES FOUND.`);
        renderDevices(data);
    } catch (e) {
        log("FATAL_ERROR: SERVER_UNREACHABLE");
    } finally {
        btn.disabled = false;
        log("SYSTEM_IDLE.");
    }
}

function renderDevices(devices) {
    const grid = document.getElementById('device-grid');
    document.getElementById('total-count').innerText = devices.length;

    devices.forEach((dev, i) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.animationDelay = `${i * 0.1}s`;
        
        const ports = dev.ports.map(p => `<span class="port-tag">${p}</span>`).join('');
        
        card.innerHTML = `
            <div class="card-top">
                <span>${dev.vendor}</span>
                <span>${dev.latency}</span>
            </div>
            <h3>${dev.ip}</h3>
            <div class="os">OS_HINT: ${dev.os}</div>
            <div class="mac">${dev.mac}</div>
            <div class="port-tags">${ports || '<span style="color:#333">SECURE_NODE</span>'}</div>
        `;
        grid.appendChild(card);
        log(`MAPPED: ${dev.ip} [${dev.os}]`);
    });
}