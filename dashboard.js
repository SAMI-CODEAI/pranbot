// Emergency Dashboard Logic

document.addEventListener('DOMContentLoaded', () => {
    const stats = {
        total: document.getElementById('stat-total'),
        injured: document.getElementById('stat-injured'),
        trapped: document.getElementById('stat-trapped'),
        evacuation: document.getElementById('stat-evacuation')
    };

    const feed = document.getElementById('message-feed');
    const canvas = document.getElementById('hotspot-map');
    const ctx = canvas.getContext('2d');
    const clock = document.getElementById('clock');

    let processedMsgIds = new Set();

    // Resize canvas
    function resizeCanvas() {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Clock
    setInterval(() => {
        clock.innerText = new Date().toLocaleTimeString();
    }, 1000);

    // Fetch Stats
    async function updateStats() {
        try {
            const resp = await fetch('/api/emergency/stats');
            const data = await resp.json();

            stats.total.innerText = data.total;
            stats.injured.innerText = data.injured;
            stats.trapped.innerText = data.trapped;
            stats.evacuation.innerText = data.need_evacuation;

            drawHotspots(data.hotspots);
        } catch (e) {
            console.error("Failed to fetch stats", e);
        }
    }

    // Fetch Messages
    async function updateFeed() {
        try {
            const resp = await fetch('/api/emergency/list');
            const data = await resp.json();

            if (data.length > 0) {
                const placeholder = document.querySelector('.feed-placeholder');
                if (placeholder) placeholder.remove();
            }

            data.reverse().forEach(msg => {
                if (!processedMsgIds.has(msg.id)) {
                    addMessageToFeed(msg);
                    processedMsgIds.add(msg.id);
                }
            });
        } catch (e) {
            console.error("Failed to fetch feed", e);
        }
    }

    function addMessageToFeed(msg) {
        const div = document.createElement('div');
        div.className = `msg-card ${msg.severity}`;
        div.innerHTML = `
            <div class="msg-header">
                <span class="tag ${msg.category}">${msg.category}</span>
                <span class="msg-time">${new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
            <p class="msg-text">${msg.raw}</p>
            <div class="msg-need">AI Insight: ${msg.need}</div>
        `;
        feed.prepend(div);

        // Keep feed manageable
        if (feed.children.length > 50) {
            feed.lastElementChild.remove();
        }
    }

    function drawHotspots(hotspots) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw grid lines
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 1;
        for (let i = 0; i < canvas.width; i += 40) {
            ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, canvas.height); ctx.stroke();
        }
        for (let i = 0; i < canvas.height; i += 40) {
            ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(canvas.width, i); ctx.stroke();
        }

        hotspots.forEach(loc => {
            const x = (loc.x / 100) * canvas.width;
            const y = (loc.y / 100) * canvas.height;

            // Outer glow
            const grad = ctx.createRadialGradient(x, y, 0, x, y, 40);
            grad.addColorStop(0, 'rgba(239, 68, 68, 0.4)');
            grad.addColorStop(1, 'transparent');

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(x, y, 40, 0, Math.PI * 2);
            ctx.fill();

            // Core dot
            ctx.fillStyle = '#ef4444';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    // Initial load and intervals
    updateStats();
    updateFeed();
    setInterval(updateStats, 3000);
    setInterval(updateFeed, 2000);
});
