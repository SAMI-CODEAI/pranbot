/**
 * Pran-Bot Terminal Interface
 * A Linux-style terminal UI for the gas detection robot
 */

// ===================== ELEMENTS =====================
const terminal = document.getElementById('terminal');
const output = document.getElementById('output');
const commandInput = document.getElementById('command-input');

// ===================== STATE =====================
let commandHistory = [];
let historyIndex = -1;
let sensorHistory = {
    smoke: [],
    methane: [],
    co: [],
    air: [],
    gpi: [],
    temperature: [],
    humidity: [],
    timestamps: []
};
const MAX_HISTORY = 60;
let updateInterval = null;
let activeCharts = {};

// ===================== SIMULATED SENSOR DATA =====================
const sensorReadings = {
    smoke: 802,
    methane: 119,
    co: 40,
    air: 90,
    temperature: 28.5,
    humidity: 55.2,
    battery: 3850,
    gpi: 78
};

// ===================== COMMANDS =====================
const commands = {
    help: () => {
        return `
<span class="highlight">Available Commands:</span>

  <span class="success">status</span>        - Show current sensor readings
  <span class="success">sensors</span>       - Display all MQ sensor values
  <span class="success">gpi</span>           - Show Gas Pollution Index
  <span class="success">env</span>           - Show temperature & humidity
  <span class="success">battery</span>       - Show battery level
  
  <span class="cyan">graph sensors</span> - Live sensor readings graph
  <span class="cyan">graph gpi</span>     - Live GPI trend graph
  <span class="cyan">graph env</span>     - Temperature & humidity graph
  <span class="cyan">graph all</span>     - Show all graphs
  <span class="cyan">graph stop</span>    - Stop live updates
  
  <span class="warning">forward</span>       - Move robot forward
  <span class="warning">back</span>          - Move robot backward
  <span class="warning">left</span>          - Turn robot left
  <span class="warning">right</span>         - Turn robot right
  <span class="warning">stop</span>          - Stop robot movement
  
  <span class="highlight">buzzer on</span>    - Activate buzzer
  <span class="highlight">buzzer off</span>   - Deactivate buzzer
  
  <span class="system-msg">clear</span>         - Clear terminal
  <span class="system-msg">history</span>       - Show command history
  <span class="system-msg">save</span>          - Save sensor data as CSV
  <span class="highlight">report</span>        - Generate AI PDF report (Gemma)
  <span class="system-msg">about</span>         - About Pran-Bot
  <span class="system-msg">help</span>          - Show this help message
`;
    },

    status: () => {
        updateSensorData();
        const gpiStatus = getGPIStatus(sensorReadings.gpi);
        return `
<span class="highlight">━━━ SYSTEM STATUS ━━━</span>

  GPI Level:    <span class="${gpiStatus.class}">${sensorReadings.gpi}</span> (${gpiStatus.label})
  Temperature:  ${sensorReadings.temperature.toFixed(1)} °C
  Humidity:     ${sensorReadings.humidity.toFixed(1)} %
  Battery:      ${getBatteryPercent(sensorReadings.battery)}%

  Status:       <span class="success">● OPERATIONAL</span>
`;
    },

    sensors: () => {
        updateSensorData();
        return `
<span class="highlight">━━━ MQ SENSOR ARRAY ━━━</span>

  ┌─────────┬──────────────┬─────────┐
  │ Sensor  │ Description  │ Level   │
  ├─────────┼──────────────┼─────────┤
  │ MQ-2    │ Smoke        │ ${padValue(sensorReadings.smoke)}   │
  │ MQ-3    │ Methane      │ ${padValue(sensorReadings.methane)}   │
  │ MQ-7    │ CO           │ ${padValue(sensorReadings.co)}   │
  │ MQ-135  │ Air Quality  │ ${padValue(sensorReadings.air)}   │
  └─────────┴──────────────┴─────────┘
`;
    },

    gpi: () => {
        updateSensorData();
        const gpi = sensorReadings.gpi;
        const status = getGPIStatus(gpi);
        const bar = createProgressBar(gpi, 500, 40);
        return `
<span class="highlight">━━━ GAS POLLUTION INDEX ━━━</span>

  Current GPI: <span class="${status.class}">${gpi}</span>
  Status:      <span class="${status.class}">${status.label}</span>

  ${bar}

  <span class="system-msg">0-50: Good | 51-100: Moderate | 101-200: Unhealthy</span>
  <span class="system-msg">201-300: Very Unhealthy | 301-500: Hazardous</span>
`;
    },

    env: () => {
        updateSensorData();
        return `
<span class="highlight">━━━ ENVIRONMENT ━━━</span>

  🌡️  Temperature:  ${sensorReadings.temperature.toFixed(1)} °C
  💧 Humidity:     ${sensorReadings.humidity.toFixed(1)} %
`;
    },

    battery: () => {
        const percent = getBatteryPercent(sensorReadings.battery);
        const bar = createProgressBar(percent, 100, 30);
        const statusClass = percent > 50 ? 'success' : percent > 20 ? 'warning' : 'error';
        return `
<span class="highlight">━━━ BATTERY STATUS ━━━</span>

  Level:  <span class="${statusClass}">${percent}%</span>
  ${bar}
`;
    },

    'graph sensors': () => createSensorGraph(),
    'graph gpi': () => createGPIGraph(),
    'graph env': () => createEnvGraph(),
    'graph all': () => {
        createSensorGraph();
        createGPIGraph();
        createEnvGraph();
        return null;
    },
    'graph stop': () => {
        stopLiveUpdates();
        return '<span class="warning">⏹ Live graph updates stopped.</span>';
    },

    forward: () => sendRobotCommand('f', 'Moving forward...'),
    back: () => sendRobotCommand('b', 'Moving backward...'),
    left: () => sendRobotCommand('l', 'Turning left...'),
    right: () => sendRobotCommand('r', 'Turning right...'),
    stop: () => sendRobotCommand('s', 'Stopping...'),

    'buzzer on': () => sendRobotCommand('bz', 'Buzzer activated!'),
    'buzzer off': () => sendRobotCommand('bo', 'Buzzer deactivated.'),

    clear: () => {
        output.innerHTML = '';
        return null;
    },

    history: () => {
        if (commandHistory.length === 0) {
            return '<span class="system-msg">No commands in history.</span>';
        }
        let result = '<span class="highlight">━━━ COMMAND HISTORY ━━━</span>\n\n';
        commandHistory.forEach((cmd, i) => {
            result += `  ${i + 1}. ${cmd}\n`;
        });
        return result;
    },

    save: () => {
        return saveDataAsCSV();
    },

    report: () => {
        return generateAIReport();
    },

    about: () => {
        return `
<span class="highlight">━━━ ABOUT PRAN-BOT ━━━</span>

  <span class="glow">Pran-Bot</span> - Environmental Guardian v1.0.0
  
  An autonomous IoT gas detection robot designed
  for industrial safety and environmental monitoring.
  
  Features:
  • Multi-gas sensing (MQ-2, MQ-3, MQ-7, MQ-135)
  • Autonomous obstacle avoidance
  • Real-time data streaming via WebSocket
  • Emergency stop on hazardous conditions
  
  <span class="system-msg">Developed for AIR Hackathon 2026</span>
`;
    }
};

// ===================== GRAPH FUNCTIONS =====================

function createSensorGraph() {
    const containerId = 'sensor-graph-' + Date.now();
    const graphHtml = `
<div class="graph-container" id="${containerId}">
    <div class="graph-header">
        <span class="highlight">━━━ LIVE SENSOR READINGS ━━━</span>
        <span class="graph-status success">● LIVE</span>
    </div>
    <canvas id="canvas-${containerId}" class="terminal-chart"></canvas>
</div>`;

    addOutput(graphHtml);

    setTimeout(() => {
        const ctx = document.getElementById(`canvas-${containerId}`);
        if (!ctx) return;

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sensorHistory.timestamps.slice(-30),
                datasets: [
                    {
                        label: 'MQ-2 (Smoke)',
                        data: sensorHistory.smoke.slice(-30),
                        borderColor: '#00ff00',
                        backgroundColor: 'rgba(0, 255, 0, 0.1)',
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: 'MQ-3 (Methane)',
                        data: sensorHistory.methane.slice(-30),
                        borderColor: '#00ffff',
                        backgroundColor: 'rgba(0, 255, 255, 0.1)',
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: 'MQ-7 (CO)',
                        data: sensorHistory.co.slice(-30),
                        borderColor: '#ffb000',
                        backgroundColor: 'rgba(255, 176, 0, 0.1)',
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: 'MQ-135 (Air)',
                        data: sensorHistory.air.slice(-30),
                        borderColor: '#ff00ff',
                        backgroundColor: 'rgba(255, 0, 255, 0.1)',
                        tension: 0.3,
                        borderWidth: 2
                    }
                ]
            },
            options: getChartOptions('ADC Value')
        });

        activeCharts[containerId] = chart;
        startLiveUpdates();
    }, 100);

    return null;
}

function createGPIGraph() {
    const containerId = 'gpi-graph-' + Date.now();
    const graphHtml = `
<div class="graph-container" id="${containerId}">
    <div class="graph-header">
        <span class="highlight">━━━ GPI TREND ━━━</span>
        <span class="graph-status success">● LIVE</span>
    </div>
    <canvas id="canvas-${containerId}" class="terminal-chart"></canvas>
</div>`;

    addOutput(graphHtml);

    setTimeout(() => {
        const ctx = document.getElementById(`canvas-${containerId}`);
        if (!ctx) return;

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sensorHistory.timestamps.slice(-30),
                datasets: [{
                    label: 'GPI',
                    data: sensorHistory.gpi.slice(-30),
                    borderColor: '#00ff00',
                    backgroundColor: createGradient(ctx, '#00ff00'),
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 0
                }]
            },
            options: {
                ...getChartOptions('GPI'),
                scales: {
                    ...getChartOptions('GPI').scales,
                    y: {
                        ...getChartOptions('GPI').scales.y,
                        min: 0,
                        max: 200
                    }
                }
            }
        });

        activeCharts[containerId] = chart;
        startLiveUpdates();
    }, 100);

    return null;
}

function createEnvGraph() {
    const containerId = 'env-graph-' + Date.now();
    const graphHtml = `
<div class="graph-container" id="${containerId}">
    <div class="graph-header">
        <span class="highlight">━━━ ENVIRONMENT ━━━</span>
        <span class="graph-status success">● LIVE</span>
    </div>
    <canvas id="canvas-${containerId}" class="terminal-chart"></canvas>
</div>`;

    addOutput(graphHtml);

    setTimeout(() => {
        const ctx = document.getElementById(`canvas-${containerId}`);
        if (!ctx) return;

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sensorHistory.timestamps.slice(-30),
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: sensorHistory.temperature.slice(-30),
                        borderColor: '#ff4444',
                        backgroundColor: 'rgba(255, 68, 68, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Humidity (%)',
                        data: sensorHistory.humidity.slice(-30),
                        borderColor: '#4444ff',
                        backgroundColor: 'rgba(68, 68, 255, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...getChartOptions('Value'),
                scales: {
                    x: getChartOptions('').scales.x,
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: 'rgba(0, 255, 0, 0.1)' },
                        ticks: { color: '#ff4444' },
                        title: { display: true, text: 'Temp (°C)', color: '#ff4444' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { color: '#4444ff' },
                        title: { display: true, text: 'Humidity (%)', color: '#4444ff' }
                    }
                }
            }
        });

        activeCharts[containerId] = chart;
        startLiveUpdates();
    }, 100);

    return null;
}

function getChartOptions(yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: {
                labels: {
                    color: '#00ff00',
                    font: { family: "'Ubuntu Mono', monospace" }
                }
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(0, 255, 0, 0.1)' },
                ticks: {
                    color: '#00cc00',
                    font: { family: "'Ubuntu Mono', monospace", size: 10 },
                    maxRotation: 0
                }
            },
            y: {
                grid: { color: 'rgba(0, 255, 0, 0.1)' },
                ticks: {
                    color: '#00cc00',
                    font: { family: "'Ubuntu Mono', monospace" }
                },
                title: {
                    display: true,
                    text: yLabel,
                    color: '#00ff00'
                }
            }
        }
    };
}

function createGradient(ctx, color) {
    const canvas = ctx.getContext ? ctx : ctx.canvas;
    const context = canvas.getContext('2d');
    const gradient = context.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, color.replace(')', ', 0.4)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    return gradient;
}

function startLiveUpdates() {
    if (updateInterval) return;

    updateInterval = setInterval(() => {
        updateSensorData();
        recordHistory();

        // Update all active charts
        Object.values(activeCharts).forEach(chart => {
            if (chart.data.datasets[0].label.includes('MQ') || chart.data.datasets[0].label.includes('Smoke')) {
                chart.data.labels = sensorHistory.timestamps.slice(-30);
                chart.data.datasets[0].data = sensorHistory.smoke.slice(-30);
                chart.data.datasets[1].data = sensorHistory.methane.slice(-30);
                chart.data.datasets[2].data = sensorHistory.co.slice(-30);
                chart.data.datasets[3].data = sensorHistory.air.slice(-30);
            } else if (chart.data.datasets[0].label === 'GPI') {
                chart.data.labels = sensorHistory.timestamps.slice(-30);
                chart.data.datasets[0].data = sensorHistory.gpi.slice(-30);
            } else if (chart.data.datasets[0].label.includes('Temperature')) {
                chart.data.labels = sensorHistory.timestamps.slice(-30);
                chart.data.datasets[0].data = sensorHistory.temperature.slice(-30);
                chart.data.datasets[1].data = sensorHistory.humidity.slice(-30);
            }
            chart.update('none');
        });
    }, 1000);
}

function stopLiveUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
    // Update status indicators
    document.querySelectorAll('.graph-status').forEach(el => {
        el.textContent = '⏹ PAUSED';
        el.classList.remove('success');
        el.classList.add('warning');
    });
}

function recordHistory() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    sensorHistory.timestamps.push(timeStr);
    sensorHistory.smoke.push(sensorReadings.smoke);
    sensorHistory.methane.push(sensorReadings.methane);
    sensorHistory.co.push(sensorReadings.co);
    sensorHistory.air.push(sensorReadings.air);
    sensorHistory.gpi.push(sensorReadings.gpi);
    sensorHistory.temperature.push(sensorReadings.temperature);
    sensorHistory.humidity.push(sensorReadings.humidity);

    // Trim to max history
    Object.keys(sensorHistory).forEach(key => {
        if (sensorHistory[key].length > MAX_HISTORY) {
            sensorHistory[key] = sensorHistory[key].slice(-MAX_HISTORY);
        }
    });
}

function saveDataAsCSV() {
    if (sensorHistory.timestamps.length === 0) {
        return '<span class="warning">⚠ No sensor data to save.</span>';
    }

    // Create CSV header
    const headers = ['Timestamp', 'Smoke (MQ-2)', 'Methane (MQ-3)', 'CO (MQ-7)', 'Air Quality (MQ-135)', 'GPI', 'Temperature (°C)', 'Humidity (%)'];
    let csvContent = headers.join(',') + '\n';

    // Add data rows
    for (let i = 0; i < sensorHistory.timestamps.length; i++) {
        const row = [
            sensorHistory.timestamps[i],
            sensorHistory.smoke[i],
            sensorHistory.methane[i],
            sensorHistory.co[i],
            sensorHistory.air[i],
            sensorHistory.gpi[i],
            sensorHistory.temperature[i].toFixed(1),
            sensorHistory.humidity[i].toFixed(1)
        ];
        csvContent += row.join(',') + '\n';
    }

    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const now = new Date();
    const filename = `pranbot_data_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}.csv`;

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    return `<span class="success">✓ Data saved to ${filename}</span>
<span class="system-msg">${sensorHistory.timestamps.length} records exported.</span>`;
}

// Report Server URL
const REPORT_SERVER_URL = 'http://localhost:5000';

async function generateAIReport() {
    if (sensorHistory.timestamps.length < 3) {
        addOutput('<span class="warning">⚠ Not enough data for report. Need at least 3 records.</span>');
        addOutput('<span class="system-msg">Let the system collect more data or run "graph sensors" first.</span>');
        return null;
    }

    // Show progress message
    addOutput(`
<div class="report-progress" id="report-progress">
    <span class="highlight">━━━ GENERATING AI REPORT ━━━</span>
    
    <span class="system-msg">📊 Preparing sensor data...</span>
    <span class="system-msg">🤖 Connecting to Gemma AI (gemma2:9b)...</span>
    <span class="warning">⏳ This may take 30-60 seconds...</span>
</div>`);

    try {
        // Check if server is running
        const healthCheck = await fetch(`${REPORT_SERVER_URL}/health`, {
            method: 'GET',
            timeout: 5000
        }).catch(() => null);

        if (!healthCheck || !healthCheck.ok) {
            addOutput('<span class="error">❌ Report server not running!</span>');
            addOutput('<span class="system-msg">Start the server with: python report_server.py</span>');
            return null;
        }

        const healthData = await healthCheck.json();
        if (healthData.ollama !== 'connected') {
            addOutput('<span class="error">❌ Ollama not connected!</span>');
            addOutput('<span class="system-msg">Make sure Ollama is running: ollama serve</span>');
            return null;
        }

        addOutput('<span class="success">✓ Server connected, generating report...</span>');

        // Send data to server
        const response = await fetch(`${REPORT_SERVER_URL}/generate-report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sensorData: sensorHistory
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            addOutput(`<span class="error">❌ Error: ${errorData.error}</span>`);
            return null;
        }

        // Download the PDF
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const now = new Date();
        const filename = `pranbot_report_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}.pdf`;

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        addOutput(`
<span class="success">━━━ REPORT GENERATED ━━━</span>

  <span class="success">✓ PDF Report: ${filename}</span>
  <span class="system-msg">✓ Data Points: ${sensorHistory.timestamps.length} records</span>
  <span class="system-msg">✓ AI Analysis: Gemma 2 9B</span>
  <span class="system-msg">✓ CSV data also saved</span>
  
  <span class="highlight">Report includes:</span>
  • Statistical summary table
  • Sensor readings graph
  • GPI trend analysis
  • Environmental conditions graph
  • Value distribution chart
  • AI-powered analysis & recommendations
`);

        return null;

    } catch (error) {
        console.error('Report generation error:', error);
        addOutput(`<span class="error">❌ Error: ${error.message}</span>`);
        addOutput('<span class="system-msg">Check console for details.</span>');
        return null;
    }
}

// ===================== HELPER FUNCTIONS =====================

function updateSensorData() {
    // Simulate slight variations in sensor readings
    sensorReadings.smoke = 790 + Math.floor(Math.random() * 30);
    sensorReadings.methane = 115 + Math.floor(Math.random() * 15);
    sensorReadings.co = 38 + Math.floor(Math.random() * 6);
    sensorReadings.air = 87 + Math.floor(Math.random() * 8);
    sensorReadings.temperature = 27 + Math.random() * 3;
    sensorReadings.humidity = 50 + Math.random() * 10;
    sensorReadings.battery = Math.max(3500, sensorReadings.battery - 1);

    // Calculate GPI
    const ratios = [
        sensorReadings.smoke / 800,
        sensorReadings.methane / 120,
        sensorReadings.co / 40,
        sensorReadings.air / 90
    ];
    const avgRatio = ratios.reduce((a, b) => a + b, 0) / ratios.length;
    sensorReadings.gpi = Math.min(500, Math.floor(100 * Math.log10(1 + avgRatio * 5)));
}

function getGPIStatus(gpi) {
    if (gpi <= 50) return { label: 'Good', class: 'success' };
    if (gpi <= 100) return { label: 'Moderate', class: 'warning' };
    if (gpi <= 200) return { label: 'Unhealthy', class: 'warning' };
    if (gpi <= 300) return { label: 'Very Unhealthy', class: 'error' };
    return { label: 'Hazardous', class: 'error' };
}

function getBatteryPercent(adc) {
    return Math.max(0, Math.min(100, Math.floor((adc - 3000) / 10.95)));
}

function padValue(val) {
    return String(val).padStart(4, ' ');
}

function createProgressBar(value, max, width) {
    const filled = Math.floor((value / max) * width);
    const empty = width - filled;
    const bar = '█'.repeat(filled) + '░'.repeat(empty);
    return `[${bar}]`;
}

function sendRobotCommand(cmd, message) {
    return `<span class="warning">⚙ ${message}</span>
<span class="system-msg">(Simulation mode: command '${cmd}' logged)</span>`;
}

function addOutput(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    output.appendChild(div);
    output.scrollTop = output.scrollHeight;
}

function processCommand(cmd) {
    const trimmedCmd = cmd.trim().toLowerCase();

    if (!trimmedCmd) return;

    // Add to history
    commandHistory.push(cmd);
    historyIndex = commandHistory.length;

    // Echo the command
    addOutput(`
        <div class="history-line">
            <span class="history-prompt">
                <span class="user">pranbot</span>@<span class="host">guardian</span>:<span class="path">~</span>$ 
            </span>
            <span class="command-echo">${escapeHtml(cmd)}</span>
        </div>
    `);

    // Process command
    let response;

    if (commands[trimmedCmd]) {
        response = commands[trimmedCmd]();
    } else if (trimmedCmd.startsWith('graph ')) {
        const subCmd = trimmedCmd;
        response = commands[subCmd] ? commands[subCmd]() : unknownCommand(cmd);
    } else if (trimmedCmd.startsWith('buzzer ')) {
        const subCmd = trimmedCmd;
        response = commands[subCmd] ? commands[subCmd]() : unknownCommand(cmd);
    } else {
        response = unknownCommand(cmd);
    }

    if (response) {
        addOutput(`<div class="response">${response}</div>`);
    }
}

function unknownCommand(cmd) {
    return `<span class="error">Command not found: ${escapeHtml(cmd)}</span>
<span class="system-msg">Type 'help' for available commands.</span>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===================== EVENT HANDLERS =====================

commandInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const cmd = commandInput.value;
        commandInput.value = '';
        processCommand(cmd);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (historyIndex > 0) {
            historyIndex--;
            commandInput.value = commandHistory[historyIndex];
        }
    } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (historyIndex < commandHistory.length - 1) {
            historyIndex++;
            commandInput.value = commandHistory[historyIndex];
        } else {
            historyIndex = commandHistory.length;
            commandInput.value = '';
        }
    } else if (e.key === 'Tab') {
        e.preventDefault();
        autocomplete();
    } else if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        commands.clear();
    }
});

// Keep focus on input
document.addEventListener('click', () => {
    commandInput.focus();
});

// Autocomplete
function autocomplete() {
    const input = commandInput.value.toLowerCase();
    if (!input) return;

    const matches = Object.keys(commands).filter(cmd => cmd.startsWith(input));
    if (matches.length === 1) {
        commandInput.value = matches[0];
    } else if (matches.length > 1) {
        addOutput(`<div class="system-msg">${matches.join('  ')}</div>`);
    }
}

// Initial focus and data
commandInput.focus();

// Pre-populate some history data
for (let i = 0; i < 10; i++) {
    updateSensorData();
    recordHistory();
}

// Startup animation
setTimeout(() => {
    addOutput('<span class="success">System initialized. Ready for commands.</span>');
    addOutput('<span class="system-msg">Try: <span class="cyan">graph sensors</span> | <span class="cyan">graph gpi</span> | <span class="cyan">graph all</span></span>');
}, 500);
