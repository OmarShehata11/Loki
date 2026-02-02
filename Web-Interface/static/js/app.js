// Loki IDS Dashboard JavaScript
const API_BASE = '/api';
let currentPage = 1;
let pageSize = 25;  // Default page size
let currentSignaturePage = 1;
let signaturePageSize = 20;
let alertsChart = null;
let chartData = {};  // Store original chart data for filtering

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadDashboard();
    setupWebSocket();
    setInterval(loadDashboard, 30000); // Refresh every 30 seconds
    
    // Set initial page size selector value
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) {
        pageSizeSelect.value = pageSize.toString();
    }
});

// Tab switching
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(tab).classList.add('active');
            
            if (tab === 'alerts') loadAlerts();
            if (tab === 'signatures') loadSignatures();
            if (tab === 'iot') {
                loadIoTDevices();
                checkMQTTStatus();
            }
        });
    });
}

// Dashboard
async function loadDashboard() {
    try {
        // Load stats
        const statsRes = await fetch(`${API_BASE}/stats`);
        const stats = await statsRes.json();
        
        document.getElementById('totalAlerts').textContent = stats.total_alerts.toLocaleString();
        document.getElementById('alerts24h').textContent = stats.alerts_last_24h.toLocaleString();
        
        // Load system status
        const statusRes = await fetch(`${API_BASE}/system/status`);
        const status = await statusRes.json();
        
        document.getElementById('idsStatus').textContent = status.ids_running ? 'Running' : 'Stopped';
        document.getElementById('idsStatus').style.color = status.ids_running ? '#4ade80' : '#f87171';
        
        // Update status indicator
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        if (status.ids_running) {
            statusDot.classList.add('online');
            statusDot.classList.remove('offline');
            statusText.textContent = 'IDS Online';
        } else {
            statusDot.classList.add('offline');
            statusDot.classList.remove('online');
            statusText.textContent = 'IDS Offline';
        }
        
        // Update charts
        updateAlertsByTypeChart(stats.alerts_by_type);
        updateTopIPsList(stats.top_attacking_ips);
        
        // Load recent alerts
        const alertsRes = await fetch(`${API_BASE}/alerts?page=1&page_size=10`);
        const alertsData = await alertsRes.json();
        displayRecentAlerts(alertsData.alerts);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function updateAlertsByTypeChart(data) {
    // Store original data for filtering
    chartData = { ...data };
    
    // Apply filters and update chart
    updateChartFilters();
}

function updateChartFilters() {
    const ctx = document.getElementById('alertsByTypeChart');
    if (!ctx) return;
    
    // Get checked filter types
    const checkboxes = document.querySelectorAll('.chart-filter-checkbox');
    const enabledTypes = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            enabledTypes.push(cb.dataset.type);
        }
    });
    
    // Filter data based on checkboxes
    const filteredLabels = [];
    const filteredValues = [];
    const colorMap = {
        'SIGNATURE': '#f87171',
        'BEHAVIOR': '#fbbf24',
        'SYSTEM': '#a78bfa'
    };
    const filteredColors = [];
    
    Object.keys(chartData).forEach(type => {
        if (enabledTypes.includes(type)) {
            filteredLabels.push(type);
            filteredValues.push(chartData[type]);
            filteredColors.push(colorMap[type] || '#888888');
        }
    });
    
    // Destroy existing chart if it exists
    if (alertsChart) {
        alertsChart.destroy();
    }
    
    // If no types selected, show empty chart
    if (filteredLabels.length === 0) {
        alertsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['No data'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#444444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e6e6e6'
                        }
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
        return;
    }
    
    // Create new chart with filtered data
    alertsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: filteredLabels,
            datasets: [{
                data: filteredValues,
                backgroundColor: filteredColors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e6e6e6'
                    }
                }
            }
        }
    });
}

function updateTopIPsList(ips) {
    const container = document.getElementById('topIPsList');
    if (!container) return;
    
    if (ips.length === 0) {
        container.innerHTML = '<p style="color: #888;">No attacking IPs in the last 24 hours</p>';
        return;
    }
    
    container.innerHTML = ips.map(ip => `
        <div class="ip-item">
            <span>${ip.ip}</span>
            <span style="color: #4a9eff; font-weight: bold;">${ip.count} alerts</span>
        </div>
    `).join('');
}

function displayRecentAlerts(alerts) {
    const container = document.getElementById('recentAlertsList');
    if (!container) return;
    
    if (alerts.length === 0) {
        container.innerHTML = '<p style="color: #888;">No recent alerts</p>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.type.toLowerCase()}">
            <div class="alert-info">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="alert-type">${alert.type}</span>
                    ${alert.subtype ? `<span class="badge subtype-badge">${alert.subtype.replace(/_/g, ' ')}</span>` : ''}
                    ${alert.pattern ? `<span class="badge pattern-badge">Pattern: ${alert.pattern}</span>` : ''}
                    ${alert.status ? `<span class="badge status-badge status-${alert.status.toLowerCase()}">${alert.status}</span>` : ''}
                </div>
                <strong>${alert.src_ip}:${alert.src_port || 'N/A'}</strong> → ${alert.dst_ip || 'N/A'}:${alert.dst_port || 'N/A'}
                <br>
                <small style="color: #888;">${alert.message}</small>
                ${alert.packet_count ? `<br><small style="color: #666;">Packets: ${alert.packet_count} | Duration: ${alert.duration_seconds ? alert.duration_seconds.toFixed(1) + 's' : 'N/A'}</small>` : ''}
                ${alert.total_packets ? `<br><small style="color: #666;">Total Packets: ${alert.total_packets} | Duration: ${alert.total_duration_seconds ? alert.total_duration_seconds.toFixed(1) + 's' : 'N/A'}</small>` : ''}
                <br>
                <small style="color: #666;">${new Date(alert.timestamp).toLocaleString()}</small>
            </div>
            <div class="item-actions">
                <button class="btn-delete" onclick="deleteAlert(${alert.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

// Alerts
function changePageSize() {
    const newPageSize = parseInt(document.getElementById('pageSizeSelect').value);
    pageSize = newPageSize;
    currentPage = 1;  // Reset to first page when changing page size
    loadAlerts();
}

// Debounce function to limit API calls when typing in filter inputs
let filterTimeout = null;
function debounceLoadAlerts() {
    if (filterTimeout) {
        clearTimeout(filterTimeout);
    }
    filterTimeout = setTimeout(() => {
        currentPage = 1;  // Reset to first page when filter changes
        loadAlerts();
    }, 300);  // Wait 300ms after user stops typing
}

async function loadAlerts() {
    try {
        const typeFilter = document.getElementById('alertTypeFilter')?.value || '';
        const subtypeFilter = document.getElementById('alertSubtypeFilter')?.value || '';
        const patternFilter = document.getElementById('alertPatternFilter')?.value || '';
        const statusFilter = document.getElementById('alertStatusFilter')?.value || '';
        const srcIpFilter = document.getElementById('srcIpFilter')?.value || '';
        const dstIpFilter = document.getElementById('dstIpFilter')?.value || '';
        
        // Update page size from selector if it exists
        const pageSizeSelect = document.getElementById('pageSizeSelect');
        if (pageSizeSelect) {
            pageSize = parseInt(pageSizeSelect.value);
        }
        
        let url = `${API_BASE}/alerts?page=${currentPage}&page_size=${pageSize}`;
        if (typeFilter) url += `&alert_type=${typeFilter}`;
        if (subtypeFilter) url += `&subtype=${subtypeFilter}`;
        if (patternFilter) url += `&pattern=${encodeURIComponent(patternFilter)}`;
        if (statusFilter) url += `&status=${statusFilter}`;
        if (srcIpFilter) url += `&src_ip=${encodeURIComponent(srcIpFilter)}`;
        if (dstIpFilter) url += `&dst_ip=${encodeURIComponent(dstIpFilter)}`;
        
        const res = await fetch(url);
        const data = await res.json();
        
        displayAlerts(data.alerts);
        updatePagination(data.total, data.page, data.page_size);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function displayAlerts(alerts) {
    const container = document.getElementById('alertsList');
    if (!container) return;
    
    if (alerts.length === 0) {
        container.innerHTML = '<p style="color: #888;">No alerts found</p>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.type.toLowerCase()}">
            <div class="alert-info">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="alert-type">${alert.type}</span>
                    ${alert.subtype ? `<span class="badge subtype-badge">${alert.subtype.replace(/_/g, ' ')}</span>` : ''}
                    ${alert.pattern ? `<span class="badge pattern-badge">Pattern: ${alert.pattern}</span>` : ''}
                    ${alert.status ? `<span class="badge status-badge status-${alert.status.toLowerCase()}">${alert.status}</span>` : ''}
                </div>
                <strong>${alert.src_ip}:${alert.src_port || 'N/A'}</strong> → ${alert.dst_ip || 'N/A'}:${alert.dst_port || 'N/A'}
                <br>
                <small style="color: #888;">${alert.message}</small>
                ${alert.packet_count ? `<br><small style="color: #666;">Packets: ${alert.packet_count} | Duration: ${alert.duration_seconds ? alert.duration_seconds.toFixed(1) + 's' : 'N/A'}</small>` : ''}
                ${alert.total_packets ? `<br><small style="color: #666;">Total Packets: ${alert.total_packets} | Duration: ${alert.total_duration_seconds ? alert.total_duration_seconds.toFixed(1) + 's' : 'N/A'}</small>` : ''}
                <br>
                <small style="color: #666;">${new Date(alert.timestamp).toLocaleString()}</small>
            </div>
            <div class="item-actions">
                <button class="btn-delete" onclick="deleteAlert(${alert.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function updatePagination(total, page, pageSize) {
    const pageInfo = document.getElementById('pageInfo');
    const totalPages = Math.ceil(total / pageSize);
    pageInfo.textContent = `Page ${page} of ${totalPages} (${total} total)`;
    
    document.getElementById('prevPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = page >= totalPages;
}

function changePage(delta) {
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    loadAlerts();
}

async function deleteAlert(id) {
    showConfirmModal(
        'Delete Alert',
        'Are you sure you want to delete this alert? This action cannot be undone.',
        async () => {
            try {
                await fetch(`${API_BASE}/alerts/${id}`, { method: 'DELETE' });
                loadAlerts();
                loadDashboard();
            } catch (error) {
                console.error('Error deleting alert:', error);
                showConfirmModal('Error', 'Failed to delete alert. Please try again.', null, 'OK');
            }
        }
    );
}

// Signatures
async function loadSignatures(showFeedback = false) {
    try {
        // Get filter values
        const search = document.getElementById('signatureSearch')?.value || '';
        const actionFilter = document.getElementById('signatureActionFilter')?.value || '';
        const enabledFilter = document.getElementById('signatureEnabledFilter')?.value || '';
        
        // Build URL with filters and pagination
        let url = `${API_BASE}/signatures?page=${currentSignaturePage}&page_size=${signaturePageSize}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (actionFilter) url += `&action=${actionFilter}`;
        if (enabledFilter) url += `&enabled=${enabledFilter === 'true'}`;
        
        const res = await fetch(url);
        const data = await res.json();
        const signatures = data.signatures || [];
        
        const container = document.getElementById('signaturesList');
        if (signatures.length === 0) {
            container.innerHTML = '<p style="color: #888;">No signatures found</p>';
            updateSignaturePagination(data.total || 0, data.page || 1, data.page_size || signaturePageSize);
            if (showFeedback) {
                showRefreshSuccess();
            }
            return;
        }
        
        container.innerHTML = signatures.map(sig => `
            <div class="signature-item signature-action-alert">
                <div class="item-info">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <strong>${sig.name}</strong>
                        <label class="toggle-switch">
                            <input type="checkbox" ${sig.enabled ? 'checked' : ''} 
                                   onchange="toggleSignature(${sig.id}, this.checked)"
                                   id="toggle-${sig.id}">
                            <span class="toggle-slider"></span>
                        </label>
                        <span class="badge ${sig.enabled ? 'badge-enabled' : 'badge-disabled'}">${sig.enabled ? 'Enabled' : 'Disabled'}</span>
                    </div>
                    <small style="color: #888;">Pattern: <code>${sig.pattern}</code></small>
                    <br>
                    <span class="badge action-badge action-alert">ALERT</span>
                    ${sig.description ? `<br><small style="color: #666;">${sig.description}</small>` : ''}
                </div>
                <div class="item-actions">
                    <button class="btn-edit" onclick="editSignature(${sig.id})">Edit</button>
                    <button class="btn-delete" onclick="deleteSignature(${sig.id})">Delete</button>
                </div>
            </div>
        `).join('');
        
        // Update pagination
        updateSignaturePagination(data.total || 0, data.page || 1, data.page_size || signaturePageSize);
        
        if (showFeedback) {
            showRefreshSuccess();
        }
    } catch (error) {
        console.error('Error loading signatures:', error);
        if (showFeedback) {
            showRefreshError();
        }
    }
}

function applySignatureFilters() {
    currentSignaturePage = 1; // Reset to first page when filtering
    loadSignatures();
}

function clearSignatureFilters() {
    document.getElementById('signatureSearch').value = '';
    document.getElementById('signatureActionFilter').value = '';
    document.getElementById('signatureEnabledFilter').value = '';
    currentSignaturePage = 1;
    loadSignatures();
}

function updateSignaturePagination(total, page, pageSize) {
    const pageInfo = document.getElementById('signaturePageInfo');
    const totalPages = Math.ceil(total / pageSize);
    pageInfo.textContent = `Page ${page} of ${totalPages} (${total} total)`;
    
    document.getElementById('prevSignaturePage').disabled = page <= 1;
    document.getElementById('nextSignaturePage').disabled = page >= totalPages;
}

function changeSignaturePage(delta) {
    currentSignaturePage += delta;
    if (currentSignaturePage < 1) currentSignaturePage = 1;
    loadSignatures();
}

async function refreshSignatures() {
    const btn = document.getElementById('refreshSignaturesBtn');
    const text = document.getElementById('refreshSignaturesText');
    const spinner = document.getElementById('refreshSignaturesSpinner');
    
    // Disable button and show loading
    btn.disabled = true;
    text.style.display = 'none';
    spinner.style.display = 'inline-block';
    
    // Load signatures with feedback
    await loadSignatures(true);
    
    // Re-enable button and hide spinner
    setTimeout(() => {
        btn.disabled = false;
        text.style.display = 'inline';
        spinner.style.display = 'none';
    }, 500);
}

function showRefreshSuccess() {
    const btn = document.getElementById('refreshSignaturesBtn');
    const text = document.getElementById('refreshSignaturesText');
    const spinner = document.getElementById('refreshSignaturesSpinner');
    
    // Hide spinner and show success text
    spinner.style.display = 'none';
    text.style.display = 'inline';
    text.textContent = '✓ Refreshed';
    btn.style.backgroundColor = '#4ade80';
    
    // Reset after 2 seconds
    setTimeout(() => {
        text.textContent = 'Refresh Signatures';
        btn.style.backgroundColor = '';
    }, 2000);
}

function showRefreshError() {
    const btn = document.getElementById('refreshSignaturesBtn');
    const text = document.getElementById('refreshSignaturesText');
    const spinner = document.getElementById('refreshSignaturesSpinner');
    
    // Hide spinner and show error text
    spinner.style.display = 'none';
    text.style.display = 'inline';
    text.textContent = '✗ Error';
    btn.style.backgroundColor = '#ef4444';
    
    // Reset after 2 seconds
    setTimeout(() => {
        text.textContent = 'Refresh Signatures';
        btn.style.backgroundColor = '';
    }, 2000);
}

let editingSignatureId = null;

function showAddSignatureModal() {
    editingSignatureId = null;
    document.getElementById('modalTitle').textContent = 'Add New Signature';
    document.getElementById('submitButton').textContent = 'Add Signature';
    document.getElementById('signatureForm').reset();
    document.getElementById('sigId').value = '';
    document.getElementById('sigEnabled').checked = true;
    document.getElementById('addSignatureModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('addSignatureModal').style.display = 'none';
    editingSignatureId = null;
    document.getElementById('signatureForm').reset();
    document.getElementById('sigId').value = '';
}

async function editSignature(id) {
    try {
        // Fetch signature details
        const res = await fetch(`${API_BASE}/signatures/${id}`);
        const sig = await res.json();
        
        // Populate form
        editingSignatureId = id;
        document.getElementById('sigId').value = sig.id;
        document.getElementById('sigName').value = sig.name;
        document.getElementById('sigPattern').value = sig.pattern;
        document.getElementById('sigDescription').value = sig.description || '';
        document.getElementById('sigEnabled').checked = sig.enabled;
        
        // Update modal title and button
        document.getElementById('modalTitle').textContent = 'Edit Signature';
        document.getElementById('submitButton').textContent = 'Update Signature';
        
        // Show modal
        document.getElementById('addSignatureModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading signature:', error);
        alert('Error loading signature details');
    }
}

document.getElementById('signatureForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const signature = {
        name: document.getElementById('sigName').value,
        pattern: document.getElementById('sigPattern').value,
        action: 'alert',  // Only alert action supported
        description: document.getElementById('sigDescription').value,
        enabled: document.getElementById('sigEnabled').checked
    };
    
    try {
        const sigId = document.getElementById('sigId').value;
        
        if (sigId && editingSignatureId) {
            // Update existing signature
            await fetch(`${API_BASE}/signatures/${sigId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(signature)
            });
        } else {
            // Create new signature
            await fetch(`${API_BASE}/signatures`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(signature)
            });
        }
        
        closeModal();
        loadSignatures();
    } catch (error) {
        console.error('Error saving signature:', error);
        alert('Error saving signature: ' + (error.message || 'Unknown error'));
    }
});

async function toggleSignature(id, enabled) {
    try {
        // Get current signature to preserve other fields
        const res = await fetch(`${API_BASE}/signatures/${id}`);
        const sig = await res.json();
        
        // Update only the enabled field
        await fetch(`${API_BASE}/signatures/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: sig.name,
                pattern: sig.pattern,
                action: sig.action,
                description: sig.description || '',
                enabled: enabled
            })
        });
        
        // Reload signatures to update the UI
        loadSignatures();
    } catch (error) {
        console.error('Error toggling signature:', error);
        alert('Error toggling signature: ' + (error.message || 'Unknown error'));
        // Reload to reset toggle state on error
        loadSignatures();
    }
}

async function deleteSignature(id) {
    showConfirmModal(
        'Delete Signature',
        'Are you sure you want to delete this signature? This action cannot be undone.',
        async () => {
            try {
                await fetch(`${API_BASE}/signatures/${id}`, { method: 'DELETE' });
                loadSignatures();
            } catch (error) {
                console.error('Error deleting signature:', error);
                showConfirmModal('Error', 'Failed to delete signature. Please try again.', null, 'OK');
            }
        }
    );
}

async function handleYamlFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.name.endsWith('.yaml') && !file.name.endsWith('.yml')) {
        alert('Please select a YAML file (.yaml or .yml)');
        event.target.value = ''; // Reset file input
        return;
    }
    
    // Show confirmation modal
    showConfirmModal(
        'Import Signatures',
        `Import signatures from ${file.name} to database? This will load YAML signatures into the database.`,
        async () => {
            try {
                // Create FormData and append file
                const formData = new FormData();
                formData.append('file', file);
                
                const res = await fetch(`${API_BASE}/signatures/reload`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.detail || 'Failed to import signatures');
                }
                
                const data = await res.json();
                showConfirmModal('Success', `Successfully imported ${data.count} signatures from ${data.filename || file.name} to database`, null, 'OK');
                loadSignatures();
            } catch (error) {
                console.error('Error importing signatures:', error);
                showConfirmModal('Error', `Error importing signatures: ${error.message}`, null, 'OK');
            } finally {
                // Reset file input
                event.target.value = '';
            }
        }
    );
}

async function reloadSignatures() {
    // This function is kept for backward compatibility but now triggers file input
    document.getElementById('yamlFileInput').click();
}

// Removed reloadIDSSignatures() - use loadSignatures() instead to refresh from database

// Confirmation Modal Functions
let confirmCallback = null;

function showConfirmModal(title, message, callback, confirmText = 'Confirm') {
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    const confirmBtn = document.getElementById('confirmButton');
    const cancelBtn = document.getElementById('cancelButton');
    const buttonsContainer = document.getElementById('confirmButtons');
    
    confirmCallback = callback;
    document.getElementById('confirmModal').style.display = 'block';
    
    // If no callback (info-only modal), show only OK button
    if (!callback) {
        confirmBtn.textContent = 'OK';
        confirmBtn.className = 'btn-secondary';
        cancelBtn.style.display = 'none';
        confirmBtn.onclick = () => closeConfirmModal();
    } else {
        confirmBtn.textContent = confirmText;
        confirmBtn.className = 'btn-delete';
        cancelBtn.style.display = 'inline-block';
        confirmBtn.onclick = () => {
            if (confirmCallback) {
                confirmCallback();
            }
            closeConfirmModal();
        };
    }
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
    confirmCallback = null;
}

// Close modals when clicking outside of them
document.addEventListener('click', function(event) {
    const signatureModal = document.getElementById('addSignatureModal');
    const confirmModal = document.getElementById('confirmModal');
    
    if (event.target == signatureModal) {
        closeModal();
    }
    if (event.target == confirmModal) {
        closeConfirmModal();
    }
});

// WebSocket for real-time updates
function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/alerts`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_alert') {
            // Refresh dashboard if on dashboard tab
            if (document.getElementById('dashboard').classList.contains('active')) {
                loadDashboard();
            }
            // Refresh alerts if on alerts tab
            if (document.getElementById('alerts').classList.contains('active')) {
                loadAlerts();
            }
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(setupWebSocket, 5000);
    };
}

// IoT Device Control Functions
async function loadIoTDevices() {
    try {
        const response = await fetch(`${API_BASE}/iot/devices`);
        const data = await response.json();
        displayIoTDevices(data.devices);
    } catch (error) {
        console.error('Error loading IoT devices:', error);
        document.getElementById('iotDevicesList').innerHTML = 
            '<div class="alert-item">Error loading devices. Make sure MQTT broker is running.</div>';
    }
}

function displayIoTDevices(devices) {
    const container = document.getElementById('iotDevicesList');
    
    if (!devices || devices.length === 0) {
        container.innerHTML = '<div class="alert-item">No IoT devices registered. Devices will appear here when connected.</div>';
        return;
    }
    
    container.innerHTML = devices.map(device => {
        const deviceType = device.device_type;
        let controls = '';
        
        if (deviceType === 'rgb_controller' || device.device_id === 'esp32-2') {
            // RGB LED Control
            controls = `
                <div style="margin-top: 15px;">
                    <h4>RGB LED Control</h4>
                    <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                        <input type="color" id="rgbColor_${device.device_id}" value="#FF0000" style="width: 60px; height: 40px;">
                        <input type="range" id="rgbBrightness_${device.device_id}" min="0" max="255" value="255" 
                               oninput="document.getElementById('brightnessValue_${device.device_id}').textContent = this.value">
                        <span>Brightness: <span id="brightnessValue_${device.device_id}">255</span></span>
                        <select id="rgbEffect_${device.device_id}">
                            <option value="solid">Solid</option>
                            <option value="fade">Fade</option>
                            <option value="rainbow">Rainbow</option>
                            <option value="blink">Blink</option>
                        </select>
                        <button onclick="controlRGB('${device.device_id}')" class="btn-primary">Apply</button>
                    </div>
                </div>
            `;
        } else if (deviceType === 'motion_sensor' || device.device_id === 'esp32-1') {
            // Motion Sensor, Alarm & Buzzer Control
            const motionDetected = device.state?.motion_detected === 'true' || device.state?.motion_detected === true;
            controls = `
                <div style="margin-top: 15px;">
                    <h4>Motion Sensor Status</h4>
                    <p style="margin-bottom: 15px;">Motion Detected: <strong style="color: ${motionDetected ? '#ff4444' : '#44ff44'}; font-size: 1.1em;">${motionDetected ? 'YES' : 'NO'}</strong></p>
                    
                    <h4>Buzzer Control</h4>
                    <div style="display: flex; gap: 10px; margin-top: 10px; margin-bottom: 15px; flex-wrap: wrap; align-items: center;">
                        <button onclick="controlBuzzer('${device.device_id}', 'on')" class="btn-primary">Buzzer ON</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'off')" class="btn-secondary">Buzzer OFF</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'beep')" class="btn-secondary">Beep (1s)</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'beep', 2000)" class="btn-secondary">Beep (2s)</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'beep', 500)" class="btn-secondary">Beep (0.5s)</button>
                    </div>
                    
                    <h4>Alarm System Control</h4>
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <button onclick="controlAlarm('${device.device_id}', 'enable')" class="btn-primary">Enable Alarm</button>
                        <button onclick="controlAlarm('${device.device_id}', 'disable')" class="btn-secondary">Disable Alarm</button>
                        <button onclick="controlAlarm('${device.device_id}', 'test')" class="btn-secondary">Test Alarm</button>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="alert-item" style="padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                    <div>
                        <h3 style="margin: 0 0 10px 0;">${device.name || device.device_id}</h3>
                        <p style="color: #888; margin: 5px 0;">Type: ${device.device_type}</p>
                        <p style="color: #888; margin: 5px 0;">Device ID: ${device.device_id}</p>
                        ${device.description ? `<p style="color: #aaa; margin: 5px 0;">${device.description}</p>` : ''}
                        ${device.last_seen ? `<p style="color: #666; margin: 5px 0; font-size: 0.9em;">Last seen: ${new Date(device.last_seen).toLocaleString()}</p>` : ''}
                    </div>
                    <span class="badge" style="background: ${device.enabled ? '#44ff44' : '#888'}">
                        ${device.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </div>
                ${controls}
            </div>
        `;
    }).join('');
}

async function controlRGB(deviceId) {
    const color = document.getElementById(`rgbColor_${deviceId}`).value;
    const brightness = parseInt(document.getElementById(`rgbBrightness_${deviceId}`).value);
    const effect = document.getElementById(`rgbEffect_${deviceId}`).value;
    
    try {
        const response = await fetch(`${API_BASE}/iot/devices/${deviceId}/rgb?color=${encodeURIComponent(color)}&brightness=${brightness}&effect=${effect}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`RGB command sent successfully to ${deviceId}`);
            loadIoTDevices(); // Refresh device states
        } else {
            alert(`Failed to send RGB command: ${data.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error controlling RGB:', error);
        alert('Error sending RGB command. Check MQTT connection.');
    }
}

async function controlAlarm(deviceId, action) {
    try {
        const response = await fetch(`${API_BASE}/iot/devices/${deviceId}/alarm?action=${action}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Alarm ${action} command sent successfully to ${deviceId}`);
            loadIoTDevices(); // Refresh device states
        } else {
            alert(`Failed to send alarm command: ${data.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error controlling alarm:', error);
        alert('Error sending alarm command. Check MQTT connection.');
    }
}

async function controlBuzzer(deviceId, action, duration = 1000) {
    try {
        const response = await fetch(`${API_BASE}/iot/devices/${deviceId}/buzzer?action=${action}&duration=${duration}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const message = duration ? `Buzzer ${action} (${duration}ms) command sent successfully` : `Buzzer ${action} command sent successfully`;
            // Don't show alert for quick beeps, just log
            if (action === 'beep' && duration <= 1000) {
                console.log(message);
            } else {
                alert(message);
            }
            loadIoTDevices(); // Refresh device states
        } else {
            alert(`Failed to send buzzer command: ${data.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error controlling buzzer:', error);
        alert('Error sending buzzer command. Check MQTT connection.');
    }
}

async function checkMQTTStatus() {
    try {
        const response = await fetch(`${API_BASE}/iot/mqtt/status`);
        const data = await response.json();
        
        const statusEl = document.getElementById('mqttStatus');
        if (data.connected) {
            statusEl.textContent = 'MQTT: Connected';
            statusEl.style.background = '#44ff44';
            statusEl.style.color = '#000';
        } else {
            statusEl.textContent = `MQTT: ${data.available ? 'Disconnected' : 'Not Available'}`;
            statusEl.style.background = data.available ? '#ffaa00' : '#ff4444';
            statusEl.style.color = '#fff';
        }
    } catch (error) {
        console.error('Error checking MQTT status:', error);
        const statusEl = document.getElementById('mqttStatus');
        statusEl.textContent = 'MQTT: Error';
        statusEl.style.background = '#ff4444';
        statusEl.style.color = '#fff';
    }
}

async function connectMQTT() {
    // Try localhost first (since RPi is the AP), then fallback to common AP IPs
    const hosts = ['127.0.0.1', 'localhost', '10.0.0.1'];
    let connected = false;
    
    for (const host of hosts) {
        try {
            const response = await fetch(`${API_BASE}/iot/mqtt/connect?host=${host}&port=1883`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`Successfully connected to MQTT broker at ${host}!`);
                checkMQTTStatus();
                loadIoTDevices();
                connected = true;
                break;
            }
        } catch (error) {
            console.error(`Error connecting to ${host}:`, error);
            continue;
        }
    }
    
    if (!connected) {
        alert('Error connecting to MQTT broker. Make sure the broker is running on the Raspberry Pi.');
    }
}

