// Oslo Commute Time Optimizer - Frontend JavaScript

let chart = null;

// Tab Navigation
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    if (tabName === 'analyze') {
        document.getElementById('analyzeTab').classList.add('active');
        document.querySelector('[onclick="showTab(\'analyze\')"]').classList.add('active');
    } else if (tabName === 'settings') {
        document.getElementById('settingsTab').classList.add('active');
        document.querySelector('[onclick="showTab(\'settings\')"]').classList.add('active');
        loadSettingsData();
    }
}

// Analyze Form Submission
document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        home: formData.get('home'),
        work: formData.get('work'),
        day: formData.get('day'),
        mode: formData.get('mode')
    };

    // Show loading, hide results
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.error || error.detail || 'Analysis failed');
        }

        const result = await response.json();
        displayResults(result);

    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

// Display Results
function displayResults(data) {
    document.getElementById('results').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';

    if (data.error) {
        showError(data.error, data.help);
        return;
    }

    // Update summary cards
    document.getElementById('bestTime').textContent = data.best.time;
    document.getElementById('bestDuration').textContent = `${data.best.duration_minutes} min`;

    document.getElementById('worstTime').textContent = data.worst.time;
    document.getElementById('worstDuration').textContent = `${data.worst.duration_minutes} min`;

    document.getElementById('differenceValue').textContent = `${data.difference_minutes} min`;

    // Update metadata
    const metadataHtml = `
        <strong>Day:</strong> ${data.metadata.day} |
        <strong>Data Source:</strong> ${data.metadata.data_source || 'Google Maps'} |
        ${data.metadata.analysis_date ? `<strong>Analysis Date:</strong> ${data.metadata.analysis_date}` : ''}
        ${data.metadata.origin ? `<br><strong>Route:</strong> ${data.metadata.origin} → ${data.metadata.destination}` : ''}
    `;
    document.getElementById('metadata').innerHTML = metadataHtml;

    // Create chart
    createChart(data.all);
}

// Show Error Message
function showError(message, helpText = '') {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.innerHTML = `
        <strong>Error:</strong> ${message}
        ${helpText ? `<br><small>${helpText}</small>` : ''}
    `;
    errorDiv.style.display = 'block';
    document.getElementById('summaryCards').style.display = 'none';
    document.querySelector('.chart-container').style.display = 'none';
}

// Create Travel Time Chart
function createChart(data) {
    const ctx = document.getElementById('travelTimeChart').getContext('2d');

    // Destroy existing chart if any
    if (chart) {
        chart.destroy();
    }

    const labels = data.map(d => d.time);
    const durations = data.map(d => d.duration_minutes);

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Travel Time (minutes)',
                data: durations,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} minutes`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Travel Time (minutes)',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Departure Time',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });

    document.getElementById('summaryCards').style.display = 'grid';
    document.querySelector('.chart-container').style.display = 'block';
}

// Settings Tab Functions
async function loadSettingsData() {
    await Promise.all([
        refreshStatus(),
        loadSegments(),
        loadDataQuality()
    ]);
}

async function refreshStatus() {
    try {
        const response = await fetch('/api/datex/status');
        const data = await response.json();

        const statusHtml = `
            <div class="status-item">
                <span class="status-label">Collection Status:</span>
                <span class="status-badge ${data.is_collecting ? 'active' : 'inactive'}">
                    ${data.is_collecting ? 'Running' : 'Stopped'}
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Last Poll:</span>
                <span class="status-value">${data.last_poll || 'Never'}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Days of Data:</span>
                <span class="status-value">${data.days_collected}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Analysis Ready:</span>
                <span class="status-badge ${data.readiness.ready ? 'active' : 'inactive'}">
                    ${data.readiness.ready ? 'Yes' : 'No'}
                </span>
            </div>
            ${!data.readiness.ready ? `
                <div class="info-message" style="margin-top: 15px;">
                    <strong>${data.readiness.reason}</strong><br>
                    ${data.readiness.recommendation}
                </div>
            ` : ''}
        `;

        document.getElementById('collectionStatus').innerHTML = statusHtml;

    } catch (error) {
        document.getElementById('collectionStatus').innerHTML = `
            <p class="error-message">Failed to load status: ${error.message}</p>
        `;
    }
}

async function startCollection() {
    try {
        const response = await fetch('/api/datex/collection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'start' })
        });

        if (response.ok) {
            alert('Data collection started successfully!');
            await refreshStatus();
        } else {
            throw new Error('Failed to start collection');
        }
    } catch (error) {
        alert('Error starting collection: ' + error.message);
    }
}

async function stopCollection() {
    try {
        const response = await fetch('/api/datex/collection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'stop' })
        });

        if (response.ok) {
            alert('Data collection stopped successfully!');
            await refreshStatus();
        } else {
            throw new Error('Failed to stop collection');
        }
    } catch (error) {
        alert('Error stopping collection: ' + error.message);
    }
}

async function initializeSegments() {
    const btn = event.target;
    const msgDiv = document.getElementById('initMessage');

    btn.disabled = true;
    btn.textContent = 'Initializing...';
    msgDiv.innerHTML = '<p class="info-message">Fetching segments from DATEX API...</p>';

    try {
        const response = await fetch('/api/datex/initialize-segments', {
            method: 'POST'
        });

        if (response.ok) {
            const data = await response.json();
            msgDiv.innerHTML = `<p class="success-message">Successfully initialized ${data.segment_count} segments!</p>`;
            await loadSegments();
        } else {
            const error = await response.json();
            throw new Error(error.detail);
        }
    } catch (error) {
        msgDiv.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Initialize Segments';
    }
}

async function loadSegments() {
    try {
        const response = await fetch('/api/datex/segments/available');
        const data = await response.json();

        if (data.segments.length === 0) {
            document.getElementById('segmentList').innerHTML = `
                <p class="info-message">No segments available. Click "Initialize Segments" above to fetch them.</p>
            `;
            return;
        }

        const segmentsHtml = data.segments.map(seg => `
            <div class="segment-item">
                <label>
                    <input type="checkbox"
                           value="${seg.segment_id}"
                           ${seg.is_selected ? 'checked' : ''}>
                    <div>
                        <div class="segment-name">${seg.name}</div>
                        <div class="segment-description">${seg.description || seg.segment_id}</div>
                    </div>
                </label>
            </div>
        `).join('');

        document.getElementById('segmentList').innerHTML = segmentsHtml;

    } catch (error) {
        document.getElementById('segmentList').innerHTML = `
            <p class="error-message">Failed to load segments: ${error.message}</p>
        `;
    }
}

async function saveSegments() {
    const checkboxes = document.querySelectorAll('#segmentList input[type="checkbox"]:checked');
    const selectedIds = Array.from(checkboxes).map(cb => cb.value);

    if (selectedIds.length === 0) {
        alert('Please select at least one segment');
        return;
    }

    try {
        const response = await fetch('/api/datex/segments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ segment_ids: selectedIds })
        });

        if (response.ok) {
            const data = await response.json();
            alert(`Successfully saved ${data.selected_count} segments!`);
            await refreshStatus();
        } else {
            throw new Error('Failed to save segments');
        }
    } catch (error) {
        alert('Error saving segments: ' + error.message);
    }
}

async function loadDataQuality() {
    try {
        const response = await fetch('/api/datex/quality');
        const data = await response.json();

        const qualityHtml = `
            <div class="status-item">
                <span class="status-label">Total Samples:</span>
                <span class="status-value">${data.total_samples.toLocaleString()}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Selected Segments:</span>
                <span class="status-value">${data.selected_segments}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Data Quality:</span>
                <span class="status-value">${data.quality}</span>
            </div>
        `;

        document.getElementById('dataQuality').innerHTML = qualityHtml;

    } catch (error) {
        document.getElementById('dataQuality').innerHTML = `
            <p class="error-message">Failed to load quality stats: ${error.message}</p>
        `;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Oslo Commute Time Optimizer loaded');
});
