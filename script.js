let logHistory = "";
let currentSessionData = [];

function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function log(text) {
    const out = document.getElementById('console-out');
    const sanitized = escapeHTML(text);
    logHistory += `&gt; ${sanitized}\n`;
    out.innerHTML = logHistory;
    out.scrollTop = out.scrollHeight;
}

function updateProgressBar(count) {
    const bar = document.getElementById('progress-bar');
    const total = 254;
    const percent = Math.min(Math.round((count / total) * 100), 100);
    bar.style.width = `${percent}%`;
}

function clearDatabase() {
    localStorage.removeItem('known_macs');
    log("DATABASE_CLEARED. ALL NODES RESET TO UNTRUSTED.");
}

function exportJSON() {
    if (currentSessionData.length === 0) return;
    const sanitizedJSON = JSON.stringify(currentSessionData, null, 4);
    const blob = new Blob([sanitizedJSON], { type: 'application/json' });
    const downloadAnchor = document.createElement('a');
    downloadAnchor.href = URL.createObjectURL(blob);
    downloadAnchor.setAttribute("download", `netvision_report_${Math.round(Date.now()/1000)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    log("REPORT_EXPORTED_SUCCESSFULLY.");
}

function toggleCard(cardElement) {
    cardElement.classList.toggle('expanded');
}

function trustDevice(mac, elementId, event) {
    event.stopPropagation();
    const cleanMac = mac.replace(/[^\w\:]/g, '');
    const cleanElementId = elementId.replace(/[^\w\-]/g, '');
    let known = JSON.parse(localStorage.getItem('known_macs') || '[]');
    if (!known.includes(cleanMac)) {
        known.push(cleanMac);
        localStorage.setItem('known_macs', JSON.stringify(known));
    }
    
    const card = document.getElementById(cleanElementId);
    if (card) {
        card.classList.remove('intruder');
        const statusSpan = card.querySelector('.card-top span:last-child');
        const tagSpan = card.querySelector('.port-tag');
        const trustBtn = card.querySelector('.trust-btn');
        
        if (statusSpan) {
            statusSpan.innerText = 'ONLINE';
            statusSpan.style.color = 'var(--green)';
        }
        if (tagSpan) {
            tagSpan.innerText = 'ONLINE';
            tagSpan.className = 'port-tag';
            tagSpan.style.borderColor = 'var(--green)';
            tagSpan.style.color = 'var(--green)';
        }
        if (trustBtn) {
            trustBtn.remove();
        }
        log(`NODE_TRUSTED: ${cleanMac}`);
    }
}

function checkIsNew(mac) {
    const cleanMac = mac.replace(/[^\w\:]/g, '');
    if (cleanMac === "00:00:00:00:00:00") return false;
    let known = JSON.parse(localStorage.getItem('known_macs') || '[]');
    if (!known.includes(cleanMac)) {
        if (known.length > 0) {
            return true;
        }
        known.push(cleanMac);
        localStorage.setItem('known_macs', JSON.stringify(known));
    }
    return false;
}

function startScan() {
    const btn = document.getElementById('scan-btn');
    const exportBtn = document.getElementById('export-btn');
    const grid = document.getElementById('device-grid');
    const count = document.getElementById('total-count');
    const bar = document.getElementById('progress-bar');
    
    btn.disabled = true;
    exportBtn.disabled = true;
    grid.innerHTML = '';
    count.innerText = '0';
    bar.style.width = '0%';
    logHistory = "";
    currentSessionData = [];
    
    log("INITIALIZING_DEEP_SCAN...");
    
    const source = new EventSource('http://127.0.0.1:5005/scan');
    let devices = 0;

    source.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.progress) {
            updateProgressBar(data.count);
            return;
        }

        if (data.done) {
            log("SCAN_COMPLETE.");
            btn.disabled = false;
            if (currentSessionData.length > 0) {
                exportBtn.disabled = false;
            }
            source.close();
            return;
        }

        devices++;
        count.innerText = devices;
        currentSessionData.push(data);

        const isNew = checkIsNew(data.mac);
        if (isNew) {
            log(`ALERT: NEW DEVICE -> ${data.ip}`);
        } else {
            log(`RESOLVED: ${data.ip}`);
        }
        
        const cleanMacId = data.mac.replace(/:/g, '').replace(/[^\w]/g, '');
        const cardId = `dev-${cleanMacId}`;
        const card = document.createElement('div');
        card.className = `card ${isNew ? 'intruder' : ''}`;
        card.id = cardId;
        card.setAttribute('onclick', 'toggleCard(this)');
        
        let bannersHtml = "";
        const portKeys = Object.keys(data.ports);
        if (portKeys.length > 0) {
            bannersHtml += `<div class="drawer-title">Active Services:</div>`;
            portKeys.forEach(port => {
                const cleanPort = escapeHTML(port);
                const cleanService = escapeHTML(data.ports[port].service);
                const cleanBanner = escapeHTML(data.ports[port].banner);
                bannersHtml += `
                    <div class="banner-item">
                        <strong>Port ${cleanPort} (${cleanService}):</strong><br>
                        ${cleanBanner}
                    </div>`;
            });
        } else {
            bannersHtml += `<div class="drawer-title">No visible services active.</div>`;
        }

        const cleanVendor = escapeHTML(data.vendor);
        const cleanIp = escapeHTML(data.ip);
        const cleanName = escapeHTML(data.name);
        const cleanMac = escapeHTML(data.mac);

        card.innerHTML = `
            <div>
                <div class="card-top">
                    <span>${cleanVendor}</span>
                    <span style="color: ${isNew ? 'var(--red)' : 'var(--green)'}">
                        ${isNew ? 'WARNING_NODE' : 'ONLINE'}
                    </span>
                </div>
                <h3>${cleanIp}</h3>
                <div class="os">${cleanName}</div>
                <div class="mac">${cleanMac}</div>
                <div class="drawer">
                    ${bannersHtml}
                </div>
            </div>
            <div class="port-tags">
                <span class="port-tag ${isNew ? 'intruder-tag' : ''}">
                    ${isNew ? 'INTRUDER_ALERT' : 'ONLINE'}
                </span>
                ${isNew ? `<button class="trust-btn" onclick="trustDevice('${cleanMac}', '${cardId}', event)">TRUST</button>` : ''}
            </div>
        `;
        grid.appendChild(card);
    };

    source.onerror = () => {
        log("CONNECTION_LOST.");
        source.close();
        btn.disabled = false;
    };
}