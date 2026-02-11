// Loki IDS Dashboard JavaScript
const API_BASE = '/api';
let currentPage = 1;
let pageSize = 25;  // Default page size
let currentSignaturePage = 1;
let signaturePageSize = 20;
let alertsChart = null;
let chartData = {};  // Store original chart data for filtering

// Input Modal System
let inputModalCallback = null;

function showInputModal(title, message, defaultValue, callback) {
    const modal = document.getElementById('inputModal');
    const titleEl = document.getElementById('inputModalTitle');
    const messageEl = document.getElementById('inputModalMessage');
    const inputEl = document.getElementById('inputModalInput');
    const confirmBtn = document.getElementById('inputModalConfirm');
    
    titleEl.textContent = title;
    messageEl.textContent = message;
    inputEl.value = defaultValue || '';
    inputModalCallback = callback;
    
    modal.style.display = 'block';
    
    // Focus input and select text
    setTimeout(() => {
        inputEl.focus();
        inputEl.select();
    }, 100);
    
    // Handle Enter key
    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            confirmInput();
        } else if (e.key === 'Escape') {
            closeInputModal();
        }
    };
    
    inputEl.onkeydown = handleKeyPress;
    confirmBtn.onclick = confirmInput;
}

function confirmInput() {
    const inputEl = document.getElementById('inputModalInput');
    const value = inputEl.value;
    closeInputModal();
    
    if (inputModalCallback) {
        inputModalCallback(value);
        inputModalCallback = null;
    }
}

function closeInputModal() {
    const modal = document.getElementById('inputModal');
    modal.style.display = 'none';
    inputModalCallback = null;
}

// Close input modal when clicking outside
document.addEventListener('click', function(event) {
    const inputModal = document.getElementById('inputModal');
    if (event.target == inputModal) {
        closeInputModal();
    }
});

// Toast Notification System
function showToast(title, message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Icon based on type
    let icon = 'ℹ';
    if (type === 'success') icon = '✓';
    else if (type === 'error') icon = '✗';
    else if (type === 'warning') icon = '⚠';
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-message">${message}</div>` : ''}
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }, duration);
    }
    
    return toast;
}

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
            
            // Stop auto-refresh when switching away from IoT tab
            stopIoTAutoRefresh();
            
            if (tab === 'alerts') loadAlerts();
            if (tab === 'signatures') loadSignatures();
            if (tab === 'iot') {
                loadIoTDevices();
                checkMQTTStatus();
                startIoTAutoRefresh(); // Start auto-refresh for IoT tab
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
        showToast('Error', 'Failed to load signature details', 'error');
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
        showToast('Error', 'Failed to save signature: ' + (error.message || 'Unknown error'), 'error');
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
        showToast('Error', 'Failed to toggle signature: ' + (error.message || 'Unknown error'), 'error');
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
        showToast('Invalid File', 'Please select a YAML file (.yaml or .yml)', 'warning');
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
let iotRefreshInterval = null;

async function loadIoTDevices() {
    try {
        const response = await fetch(`${API_BASE}/iot/devices`);
        const data = await response.json();
        displayIoTDevices(data.devices);
        
        // Also check MQTT status
        checkMQTTStatus();
    } catch (error) {
        console.error('Error loading IoT devices:', error);
        document.getElementById('iotDevicesList').innerHTML = 
            '<div class="alert-item">Error loading devices. Make sure MQTT broker is running.</div>';
    }
}

// Auto-refresh IoT devices every 3 seconds when on IoT tab
function startIoTAutoRefresh() {
    if (iotRefreshInterval) {
        clearInterval(iotRefreshInterval);
    }
    
    // Check if we're on the IoT tab
    const iotTab = document.getElementById('iot');
    if (iotTab && iotTab.classList.contains('active')) {
        iotRefreshInterval = setInterval(() => {
            loadIoTDevices();
        }, 3000); // Refresh every 3 seconds
    }
}

function stopIoTAutoRefresh() {
    if (iotRefreshInterval) {
        clearInterval(iotRefreshInterval);
        iotRefreshInterval = null;
    }
}

function displayIoTDevices(devices) {
    const container = document.getElementById('iotDevicesList');
    
    if (!devices || devices.length === 0) {
        container.innerHTML = '<div class="iot-device-card"><p style="text-align: center; color: #888;">No IoT devices registered. Devices will appear here when connected.</p></div>';
        return;
    }
    
    container.innerHTML = devices.map(device => {
        const deviceType = device.device_type;
        let controls = '';
        
        // Get device states
        const motionState = device.state?.motion_detected;
        const buzzerState = device.state?.buzzer_state;
        const alarmState = device.state?.alarm_enabled;
        const ledState = device.state?.led_state;
        
        const motionDetected = motionState === 'true' || motionState === true;
        const buzzerOn = buzzerState === 'on' || buzzerState === 'ON';
        const alarmEnabled = alarmState === 'true' || alarmState === true;
        const ledOn = ledState === 'on' || ledState === 'ON';
        const ledAuto = ledState === 'auto' || ledState === 'AUTO';
        
        // Parse bulb state if available
        const bulbState = device.state?.bulb_state;
        let bulbOn = false;
        let currentBrightness = 255;
        if (bulbState) {
            try {
                const bulb = typeof bulbState === 'string' ? JSON.parse(bulbState) : bulbState;
                bulbOn = (bulb.state === 'on' || bulb.state === 'ON');
                currentBrightness = bulb.brightness || 255;
            } catch (e) {
                console.error('Error parsing bulb state:', e);
            }
        }
        
        if (deviceType === 'rgb_controller' || device.device_id === 'esp32-2') {
            // Bulb Control (changed from RGB to regular bulb)
            controls = `
                <div class="iot-control-section">
                    <h4>Bulb Control</h4>
                    <div class="iot-status-display" style="margin-bottom: 15px;">
                        <div class="iot-status-indicator ${bulbOn ? 'active' : 'inactive'}"></div>
                        <span class="iot-status-text ${bulbOn ? 'active' : 'inactive'}">
                            Bulb: ${bulbOn ? 'ON' : 'OFF'}
                        </span>
                    </div>
                    <div class="iot-button-group" style="margin-bottom: 20px;">
                        <button onclick="controlBulb('${device.device_id}', 'on')" class="iot-btn iot-btn-success">Turn ON</button>
                        <button onclick="controlBulb('${device.device_id}', 'off')" class="iot-btn iot-btn-danger">Turn OFF</button>
                    </div>
                    <div class="iot-brightness-control" style="padding: 20px; background: #0f1419; border-radius: 8px; border: 1px solid #2a2f35;">
                        <label style="color: #888; font-size: 0.9em; display: block; margin-bottom: 10px;">Brightness:</label>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <input type="range" id="bulbBrightness_${device.device_id}" min="0" max="255" value="${currentBrightness}" 
                                   class="iot-brightness-slider"
                                   oninput="document.getElementById('bulbBrightnessValue_${device.device_id}').textContent = this.value">
                            <span class="iot-brightness-value" id="bulbBrightnessValue_${device.device_id}">${currentBrightness}</span>
                            <button onclick="controlBulbBrightness('${device.device_id}')" class="iot-btn iot-btn-primary" style="min-width: 100px;">Set Brightness</button>
                        </div>
                    </div>
                </div>
            `;
        } else if (deviceType === 'motion_sensor' || device.device_id === 'esp32-1') {
            // Motion Sensor, Alarm & Buzzer Control
            controls = `
                <div class="iot-control-section">
                    <h4>Motion Sensor Status</h4>
                    <div class="iot-status-display">
                        <div class="iot-status-indicator ${motionDetected ? 'detected' : 'inactive'}"></div>
                        <span class="iot-status-text ${motionDetected ? 'detected' : 'inactive'}">
                            Motion: ${motionDetected ? 'DETECTED' : 'No Motion'}
                        </span>
                    </div>
                    
                    <h4>Buzzer Control</h4>
                    <div class="iot-status-display" style="margin-bottom: 15px;">
                        <div class="iot-status-indicator ${buzzerOn ? 'active' : 'inactive'}"></div>
                        <span class="iot-status-text ${buzzerOn ? 'active' : 'inactive'}">
                            Buzzer: ${buzzerOn ? 'ON' : 'OFF'}
                        </span>
                    </div>
                    <div class="iot-button-group">
                        <button onclick="controlBuzzer('${device.device_id}', 'on')" class="iot-btn iot-btn-success">Buzzer ON</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'off')" class="iot-btn iot-btn-danger">Buzzer OFF</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'beep')" class="iot-btn iot-btn-secondary">Beep (1s)</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'beep', 2000)" class="iot-btn iot-btn-secondary">Beep (2s)</button>
                        <button onclick="controlBuzzer('${device.device_id}', 'beep', 500)" class="iot-btn iot-btn-secondary">Beep (0.5s)</button>
                    </div>
                    
                    <h4>Alarm System Control</h4>
                    <div class="iot-status-display" style="margin-bottom: 15px;">
                        <div class="iot-status-indicator ${alarmEnabled ? 'active' : 'inactive'}"></div>
                        <span class="iot-status-text ${alarmEnabled ? 'active' : 'inactive'}">
                            Alarm: ${alarmEnabled ? 'ENABLED' : 'DISABLED'}
                        </span>
                    </div>
                    <div class="iot-button-group">
                        <button onclick="controlAlarm('${device.device_id}', 'enable')" class="iot-btn iot-btn-success">Enable Alarm</button>
                        <button onclick="controlAlarm('${device.device_id}', 'disable')" class="iot-btn iot-btn-danger">Disable Alarm</button>
                        <button onclick="controlAlarm('${device.device_id}', 'test')" class="iot-btn iot-btn-primary">Test Alarm</button>
                    </div>
                    
                    <h4>LED Control</h4>
                    <div class="iot-status-display" style="margin-bottom: 15px;">
                        <div class="iot-status-indicator ${ledOn ? 'active' : (ledAuto ? 'detected' : 'inactive')}"></div>
                        <span class="iot-status-text ${ledOn ? 'active' : (ledAuto ? 'detected' : 'inactive')}">
                            LED: ${ledOn ? 'ON' : (ledAuto ? 'AUTO' : 'OFF')}
                        </span>
                    </div>
                    <div class="iot-button-group">
                        <button onclick="controlLED('${device.device_id}', 'on')" class="iot-btn iot-btn-success">LED ON</button>
                        <button onclick="controlLED('${device.device_id}', 'off')" class="iot-btn iot-btn-danger">LED OFF</button>
                        <button onclick="controlLED('${device.device_id}', 'auto')" class="iot-btn iot-btn-secondary">LED AUTO</button>
                    </div>
                </div>
            `;
        }
        
        // Use online status from API (tracked via MQTT heartbeats)
        const isOnline = device.online === true;
        const statusClass = isOnline ? 'online' : 'offline';
        const statusText = isOnline ? 'Online' : 'Offline';
        
        return `
            <div class="iot-device-card">
                <div class="iot-device-header">
                    <div>
                        <h3 class="iot-device-title">${device.name || device.device_id}</h3>
                        <p class="iot-device-info">Type: ${device.device_type}</p>
                        <p class="iot-device-info">Device ID: ${device.device_id}</p>
                        ${device.description ? `<p class="iot-device-info">${device.description}</p>` : ''}
                        ${device.last_seen ? `<p class="iot-device-info" style="font-size: 0.85em; color: #666;">Last seen: ${new Date(device.last_seen).toLocaleString()}</p>` : '<p class="iot-device-info" style="font-size: 0.85em; color: #666;">Last seen: Never (waiting for heartbeat)</p>'}
                    </div>
                    <div>
                        <span class="iot-status-badge ${device.enabled ? 'enabled' : 'disabled'}">
                            ${device.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                        <span class="iot-status-badge ${statusClass}" style="margin-top: 8px; display: block;">
                            ${statusText}
                        </span>
                    </div>
                </div>
                ${controls}
            </div>
        `;
    }).join('');
}

async function controlBulb(deviceId, state) {
    console.log(`[Bulb] Control called for device: ${deviceId}, state: ${state}`);
    
    try {
        // Get current brightness or use default
        const brightnessInput = document.getElementById(`bulbBrightness_${deviceId}`);
        const brightness = brightnessInput ? parseInt(brightnessInput.value) : 255;
        
        const url = `${API_BASE}/iot/devices/${deviceId}/bulb?state=${state}&brightness=${brightness}`;
        console.log(`[Bulb] API URL: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        console.log(`[Bulb] Response status: ${response.status}`);
        const data = await response.json();
        console.log(`[Bulb] Response data:`, data);
        
        if (data.success) {
            console.log(`[Bulb] ✓ Command sent successfully`);
            showToast('Bulb Command Sent', `Bulb turned ${state.toUpperCase()}`, 'success', 2000);
            loadIoTDevices(); // Refresh device states immediately
        } else {
            console.error(`[Bulb] ✗ Command failed:`, data);
            showToast('Bulb Command Failed', data.message || data.detail || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('[Bulb] Error controlling bulb:', error);
        showToast('Connection Error', `Failed to send bulb command. Check MQTT connection.`, 'error');
    }
}

async function controlBulbBrightness(deviceId) {
    console.log(`[Bulb] Brightness control called for device: ${deviceId}`);
    
    const brightnessInput = document.getElementById(`bulbBrightness_${deviceId}`);
    
    if (!brightnessInput) {
        console.error(`[Bulb] Missing brightness input for device ${deviceId}`);
        showToast('Error', 'Brightness control not found. Please refresh the page.', 'error');
        return;
    }
    
    const brightness = parseInt(brightnessInput.value);
    
    console.log(`[Bulb] Sending brightness command - Brightness: ${brightness}`);
    
    try {
        // When setting brightness, turn bulb ON if it's not already on
        const url = `${API_BASE}/iot/devices/${deviceId}/bulb?state=on&brightness=${brightness}`;
        console.log(`[Bulb] API URL: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        console.log(`[Bulb] Response status: ${response.status}`);
        const data = await response.json();
        console.log(`[Bulb] Response data:`, data);
        
        if (data.success) {
            console.log(`[Bulb] ✓ Brightness command sent successfully`);
            showToast('Brightness Set', `Brightness: ${brightness}%`, 'success', 2000);
            loadIoTDevices(); // Refresh device states immediately
        } else {
            console.error(`[Bulb] ✗ Command failed:`, data);
            showToast('Brightness Command Failed', data.message || data.detail || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('[Bulb] Error controlling bulb brightness:', error);
        showToast('Connection Error', `Failed to send brightness command. Check MQTT connection.`, 'error');
    }
}

async function controlAlarm(deviceId, action) {
    console.log(`[Alarm] Control called for device: ${deviceId}, action: ${action}`);
    
    try {
        const url = `${API_BASE}/iot/devices/${deviceId}/alarm?action=${action}`;
        console.log(`[Alarm] API URL: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        console.log(`[Alarm] Response status: ${response.status}`);
        const data = await response.json();
        console.log(`[Alarm] Response data:`, data);
        
        if (data.success) {
            console.log(`[Alarm] ✓ Command sent successfully`);
            const actionText = action.charAt(0).toUpperCase() + action.slice(1);
            showToast('Alarm Command Sent', `Alarm ${actionText}`, 'success', 2000);
            loadIoTDevices(); // Refresh device states immediately
        } else {
            console.error(`[Alarm] ✗ Command failed:`, data);
            showToast('Alarm Command Failed', data.message || data.detail || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('[Alarm] Error controlling alarm:', error);
        showToast('Connection Error', `Failed to send alarm command. Check MQTT connection.`, 'error');
    }
}

async function controlBuzzer(deviceId, action, duration = 1000) {
    console.log(`[Buzzer] Control called for device: ${deviceId}, action: ${action}, duration: ${duration}`);
    
    try {
        const url = `${API_BASE}/iot/devices/${deviceId}/buzzer?action=${action}&duration=${duration}`;
        console.log(`[Buzzer] API URL: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        console.log(`[Buzzer] Response status: ${response.status}`);
        const data = await response.json();
        console.log(`[Buzzer] Response data:`, data);
        
        if (data.success) {
            console.log(`[Buzzer] ✓ Command sent successfully`);
            const actionText = action === 'beep' ? `Beep (${duration}ms)` : action.toUpperCase();
            showToast('Buzzer Command Sent', actionText, 'success', 1500);
            loadIoTDevices(); // Refresh device states immediately
        } else {
            console.error(`[Buzzer] ✗ Command failed:`, data);
            showToast('Buzzer Command Failed', data.message || data.detail || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('[Buzzer] Error controlling buzzer:', error);
        showToast('Connection Error', `Failed to send buzzer command. Check MQTT connection.`, 'error');
    }
}

async function controlLED(deviceId, action) {
    console.log(`[LED] Control called for device: ${deviceId}, action: ${action}`);
    
    try {
        const url = `${API_BASE}/iot/devices/${deviceId}/led?action=${action}`;
        console.log(`[LED] API URL: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        console.log(`[LED] Response status: ${response.status}`);
        const data = await response.json();
        console.log(`[LED] Response data:`, data);
        
        if (data.success) {
            console.log(`[LED] ✓ Command sent successfully`);
            const actionText = action.charAt(0).toUpperCase() + action.slice(1);
            showToast('LED Command Sent', `LED ${actionText}`, 'success', 1500);
            loadIoTDevices(); // Refresh device states immediately
        } else {
            console.error(`[LED] ✗ Command failed:`, data);
            showToast('LED Command Failed', data.message || data.detail || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('[LED] Error controlling LED:', error);
        showToast('Connection Error', `Failed to send LED command. Check MQTT connection.`, 'error');
    }
}

async function checkMQTTStatus() {
    try {
        const response = await fetch(`${API_BASE}/iot/mqtt/status`);
        const data = await response.json();
        
        const statusEl = document.getElementById('mqttStatus');
        if (data.connected) {
            statusEl.textContent = 'MQTT: Connected';
            statusEl.className = 'iot-status-badge online';
        } else {
            statusEl.textContent = `MQTT: ${data.available ? 'Disconnected' : 'Not Available'}`;
            statusEl.className = 'iot-status-badge offline';
        }
    } catch (error) {
        console.error('Error checking MQTT status:', error);
        const statusEl = document.getElementById('mqttStatus');
        statusEl.textContent = 'MQTT: Error';
        statusEl.className = 'iot-status-badge offline';
    }
}

async function connectMQTT() {
    // Try the Raspberry Pi AP IP first, then localhost
    const hosts = ['10.0.0.1', '127.0.0.1', 'localhost'];
    let connected = false;
    let lastError = null;
    
    for (const host of hosts) {
        try {
            const response = await fetch(`${API_BASE}/iot/mqtt/connect?host=${host}&port=1883`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('MQTT Connected', `Successfully connected to broker at ${host}`, 'success');
                checkMQTTStatus();
                loadIoTDevices();
                connected = true;
                break;
            } else {
                lastError = data.detail || 'Connection failed';
            }
        } catch (error) {
            console.error(`Error connecting to ${host}:`, error);
            lastError = error.message;
            continue;
        }
    }
    
    if (!connected) {
        // Show custom input modal instead of prompt
        showInputModal(
            'Enter MQTT Broker IP',
            'Could not auto-connect. Enter Raspberry Pi IP address where the MQTT broker is running:',
            '10.0.0.1',
            async (rpiIp) => {
                if (rpiIp && rpiIp.trim()) {
                    try {
                        const response = await fetch(`${API_BASE}/iot/mqtt/connect?host=${rpiIp.trim()}&port=1883`, {
                            method: 'POST'
                        });
                        const data = await response.json();
                        if (data.success) {
                            showToast('MQTT Connected', `Successfully connected to broker at ${rpiIp}`, 'success');
                            checkMQTTStatus();
                            loadIoTDevices();
                        } else {
                            showToast('MQTT Connection Failed', `Failed to connect: ${data.detail || 'Unknown error'}\n\nMake sure:\n1. MQTT broker is running on Raspberry Pi\n2. IP address is correct\n3. Port 1883 is not blocked by firewall`, 'error', 6000);
                        }
                    } catch (error) {
                        showToast('Connection Error', `Connection error: ${error.message}\n\nMake sure the Raspberry Pi IP is correct and MQTT broker is running.`, 'error', 6000);
                    }
                } else {
                    showToast('Connection Cancelled', 'IP address is required', 'warning');
                }
            }
        );
    }
}

