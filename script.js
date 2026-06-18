let logHistory = "";
let currentSessionData = [];

function updateSliderVal(val) {
    document.getElementById('thread-val').textContent = val;
}

function log(text) {
    const out = document.getElementById('console-out');
    const div = document.createElement('div');
    div.textContent = `> ${text}`;
    out.appendChild(div);
    out.scrollTop = out.scrollHeight;
}

function updateProgressBar(count) {
    const bar = document.getElementById('progress-bar');
    const total = 254;
    const percent = Math.min(Math.round((count / total) * 100), 100);
    bar.style.width = `${percent}%`;
}

function clearDatabase() {
    try {
        localStorage.removeItem('known_macs');
    } catch (e) {
        log("DATABASE_CLEAR_FAILED.");
    }
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
    let known = [];
    try {
        known = JSON.parse(localStorage.getItem('known_macs') || '[]');
    } catch (e) {
        known = [];
    }
    
    if (!known.includes(cleanMac)) {
        known.push(cleanMac);
        try {
            localStorage.setItem('known_macs', JSON.stringify(known));
        } catch (e) {
            log("STORAGE_WRITE_FAILED.");
        }
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
    let known = [];
    try {
        known = JSON.parse(localStorage.getItem('known_macs') || '[]');
    } catch (e) {
        known = [];
    }
    
    if (!known.includes(cleanMac)) {
        if (known.length > 0) {
            return true;
        }
        known.push(cleanMac);
        try {
            localStorage.setItem('known_macs', JSON.stringify(known));
        } catch (e) {
            log("STORAGE_WRITE_FAILED.");
        }
    }
    return false;
}

function startScan() {
    const btn = document.getElementById('scan-btn');
    const exportBtn = document.getElementById('export-btn');
    const grid = document.getElementById('device-grid');
    const count = document.getElementById('total-count');
    const bar = document.getElementById('progress-bar');
    const out = document.getElementById('console-out');
    const threads = document.getElementById('thread-slider').value;
    
    btn.disabled = true;
    exportBtn.disabled = true;
    grid.textContent = '';
    count.innerText = '0';
    bar.style.width = '0%';
    out.textContent = '';
    currentSessionData = [];
    
    const startTime = Date.now();
    log(`INITIALIZING_DEEP_SCAN WITH ${threads} THREADS...`);
    
    const source = new EventSource(`http://127.0.0.1:5005/scan?threads=${threads}`);
    let devices = 0;

    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    const macRegex = /^([0-9A-FA-F]{2}[:-]){5}([0-9A-FA-F]{2})$/;

    source.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.error) {
            log(`SECURITY_ABORT: ${data.message}`);
            source.close();
            btn.disabled = false;
            return;
        }

        if (data.progress) {
            updateProgressBar(data.count);
            return;
        }

        if (data.done) {
            const duration = ((Date.now() - startTime) / 1000).toFixed(2);
            log(`SCAN_COMPLETE IN ${duration} SECONDS.`);
            btn.disabled = false;
            if (currentSessionData.length > 0) {
                exportBtn.disabled = false;
            }
            source.close();
            return;
        }

        if (!ipRegex.test(data.ip) || !macRegex.test(data.mac)) {
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
        card.onclick = function() { toggleCard(this); };

        const innerContainer = document.createElement('div');

        const cardTop = document.createElement('div');
        cardTop.className = 'card-top';

        const vendorSpan = document.createElement('span');
        vendorSpan.textContent = data.vendor;

        const statusSpan = document.createElement('span');
        statusSpan.textContent = isNew ? 'WARNING_NODE' : 'ONLINE';
        statusSpan.style.color = isNew ? 'var(--red)' : 'var(--green)';

        cardTop.appendChild(vendorSpan);
        cardTop.appendChild(statusSpan);

        const ipHeader = document.createElement('h3');
        ipHeader.textContent = data.ip;

        const osDiv = document.createElement('div');
        osDiv.className = 'os';
        osDiv.textContent = data.name;

        const macDiv = document.createElement('div');
        macDiv.className = 'mac';
        macDiv.textContent = data.mac;

        const drawer = document.createElement('div');
        drawer.className = 'drawer';

        const portKeys = Object.keys(data.ports);
        if (portKeys.length > 0) {
            const drawerTitle = document.createElement('div');
            drawerTitle.className = 'drawer-title';
            drawerTitle.textContent = 'Active Services:';
            drawer.appendChild(drawerTitle);

            portKeys.forEach(port => {
                const bannerItem = document.createElement('div');
                bannerItem.className = 'banner-item';

                const strongText = document.createElement('strong');
                strongText.textContent = `Port ${port} (${data.ports[port].service}):`;
                
                const brNode = document.createElement('br');
                const textNode = document.createTextNode(data.ports[port].banner);

                bannerItem.appendChild(strongText);
                bannerItem.appendChild(brNode);
                bannerItem.appendChild(textNode);
                drawer.appendChild(bannerItem);
            });
        } else {
            const drawerTitle = document.createElement('div');
            drawerTitle.className = 'drawer-title';
            drawerTitle.textContent = 'No visible services active.';
            drawer.appendChild(drawerTitle);
        }

        innerContainer.appendChild(cardTop);
        innerContainer.appendChild(ipHeader);
        innerContainer.appendChild(osDiv);
        innerContainer.appendChild(macDiv);
        innerContainer.appendChild(drawer);

        const portTags = document.createElement('div');
        portTags.className = 'port-tags';

        const portTagSpan = document.createElement('span');
        portTagSpan.className = `port-tag ${isNew ? 'intruder-tag' : ''}`;
        portTagSpan.textContent = isNew ? 'INTRUDER_ALERT' : 'ONLINE';

        portTags.appendChild(portTagSpan);

        if (isNew) {
            const trustBtn = document.createElement('button');
            trustBtn.className = 'trust-btn';
            trustBtn.textContent = 'TRUST';
            trustBtn.onclick = function(event) {
                trustDevice(data.mac, cardId, event);
            };
            portTags.appendChild(trustBtn);
        }

        card.appendChild(innerContainer);
        card.appendChild(portTags);
        grid.appendChild(card);
    };

    source.onerror = () => {
        log("CONNECTION_LOST.");
        source.close();
        btn.disabled = false;
    };
}