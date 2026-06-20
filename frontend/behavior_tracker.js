class BehaviorTracker {
    constructor() {
        this.sessionId = this.getOrCreateSessionId();
        this.startTime = Date.now();
        this.mouseMovements = [];
        this.clicks = [];
        this.scrollEvents = [];
        this.keystrokes = [];
        this.lastMouseTime = 0;
        this.lastScrollTime = 0;
        this.isBlocked = false;

        // Check block status immediately on page load
        this.checkBlockStatus().then(() => {
            if (!this.isBlocked) {
                this.initializeTracking();
                this.startPeriodicSend();
            }
        });
    }

    // Use sessionStorage so session ID persists across page refreshes
    getOrCreateSessionId() {
        let id = sessionStorage.getItem('botDetectSessionId');
        if (!id) {
            id = 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
            sessionStorage.setItem('botDetectSessionId', id);
        }
        return id;
    }

    async checkBlockStatus() {
        try {
            const response = await fetch('http://localhost:5000/api/check_block?sessionId=' + this.sessionId);
            if (response.ok) {
                const result = await response.json();
                if (result.blocked) {
                    this.isBlocked = true;
                    this.lockPage(result.remaining);
                    document.getElementById('status').style.background = '#dc3545';
                    document.getElementById('status').textContent = 'BOT DETECTED - ACCESS BLOCKED';
                    document.getElementById('status').style.animation = 'blink 0.8s infinite';
                }
            }
        } catch (e) {
            // API not available
        }
    }

    initializeTracking() {
        document.addEventListener('mousemove', (e) => {
            if (this.isBlocked) return;
            const now = Date.now();
            if (now - this.lastMouseTime > 10) {
                this.mouseMovements.push({ x: e.clientX, y: e.clientY, timestamp: now, timeDiff: now - this.lastMouseTime });
                this.lastMouseTime = now;
            }
        });

        document.addEventListener('click', (e) => {
            if (this.isBlocked) { e.preventDefault(); e.stopImmediatePropagation(); return false; }
            this.clicks.push({ x: e.clientX, y: e.clientY, timestamp: Date.now(), target: e.target.tagName });
            this.sendBehaviorData();
        }, true);

        document.addEventListener('scroll', () => {
            if (this.isBlocked) { window.scrollTo(0, window.scrollY); return; }
            const now = Date.now();
            this.scrollEvents.push({ scrollY: window.scrollY, timestamp: now, timeDiff: now - this.lastScrollTime });
            this.lastScrollTime = now;
        });

        document.addEventListener('keydown', (e) => {
            if (this.isBlocked) { e.preventDefault(); e.stopImmediatePropagation(); return false; }
            this.keystrokes.push({ key: e.key, timestamp: Date.now() });
        }, true);

        document.addEventListener('keyup', (e) => {
            if (this.isBlocked) { e.preventDefault(); e.stopImmediatePropagation(); return false; }
        }, true);

        document.addEventListener('contextmenu', (e) => {
            if (this.isBlocked) { e.preventDefault(); return false; }
        });
    }

    calculateFeatures() {
        const now = Date.now();
        return {
            sessionId: this.sessionId,
            timeOnPage: (now - this.startTime) / 1000,
            totalMouseMovements: this.mouseMovements.length,
            totalClicks: this.clicks.length,
            totalScrollEvents: this.scrollEvents.length,
            totalKeystrokes: this.keystrokes.length,
            ...this.calculateMouseFeatures(),
            ...this.calculateClickFeatures(),
            ...this.calculateScrollFeatures(),
            timestamp: now
        };
    }

    calculateMouseFeatures() {
        if (this.mouseMovements.length < 2) return { avgMouseSpeed: 0, mouseSpeedVariance: 0, avgTimeBetweenMoves: 0, straightLineRatio: 0 };
        const speeds = [], timeDiffs = [];
        let totalDistance = 0;
        for (let i = 1; i < this.mouseMovements.length; i++) {
            const prev = this.mouseMovements[i - 1], curr = this.mouseMovements[i];
            const dist = Math.sqrt(Math.pow(curr.x - prev.x, 2) + Math.pow(curr.y - prev.y, 2));
            const td = curr.timestamp - prev.timestamp;
            if (td > 0) { speeds.push(dist / td); timeDiffs.push(td); totalDistance += dist; }
        }
        const first = this.mouseMovements[0], last = this.mouseMovements[this.mouseMovements.length - 1];
        const straightDist = Math.sqrt(Math.pow(last.x - first.x, 2) + Math.pow(last.y - first.y, 2));
        const avgSpeed = speeds.reduce((a, b) => a + b, 0) / speeds.length || 0;
        const variance = speeds.reduce((s, v) => s + Math.pow(v - avgSpeed, 2), 0) / speeds.length || 0;
        return {
            avgMouseSpeed: avgSpeed, mouseSpeedVariance: variance,
            avgTimeBetweenMoves: timeDiffs.reduce((a, b) => a + b, 0) / timeDiffs.length || 0,
            straightLineRatio: totalDistance > 0 ? straightDist / totalDistance : 0
        };
    }

    calculateClickFeatures() {
        if (this.clicks.length < 2) return { avgClickInterval: 0, clickIntervalVariance: 0, doubleClickCount: 0 };
        const intervals = [];
        let doubleClicks = 0;
        for (let i = 1; i < this.clicks.length; i++) {
            const interval = this.clicks[i].timestamp - this.clicks[i - 1].timestamp;
            intervals.push(interval);
            if (interval < 500) doubleClicks++;
        }
        const avg = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        const variance = intervals.reduce((s, v) => s + Math.pow(v - avg, 2), 0) / intervals.length;
        return { avgClickInterval: avg, clickIntervalVariance: variance, doubleClickCount: doubleClicks };
    }

    calculateScrollFeatures() {
        if (this.scrollEvents.length < 2) return { avgScrollSpeed: 0, scrollDirection: 0, scrollAcceleration: 0 };
        const speeds = [];
        let down = 0, up = 0;
        for (let i = 1; i < this.scrollEvents.length; i++) {
            const diff = this.scrollEvents[i].scrollY - this.scrollEvents[i - 1].scrollY;
            const td = this.scrollEvents[i].timestamp - this.scrollEvents[i - 1].timestamp;
            if (td > 0) { speeds.push(Math.abs(diff) / td); diff > 0 ? down++ : up++; }
        }
        const avg = speeds.reduce((a, b) => a + b, 0) / speeds.length || 0;
        return {
            avgScrollSpeed: avg,
            scrollDirection: (down - up) / (down + up || 1),
            scrollAcceleration: speeds.length > 1 ? Math.abs(speeds[speeds.length - 1] - speeds[0]) : 0
        };
    }

    async sendBehaviorData() {
        if (this.isBlocked) return;
        try {
            const response = await fetch('http://localhost:5000/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.calculateFeatures())
            });
            if (response.ok) {
                const result = await response.json();
                this.handleResult(result);
            }
        } catch (e) {
            console.log('Tracking service unavailable');
        }
    }

    handleResult(result) {
        const statusEl = document.getElementById('status');
        if (result.blocked || result.prediction === 'bot') {
            const seconds = result.blockRemaining || result.blockDuration || 35;
            this.lockPage(seconds);
            statusEl.style.background = '#dc3545';
            statusEl.textContent = 'BOT DETECTED - ACCESS BLOCKED';
            statusEl.style.animation = 'blink 0.8s infinite';
        } else {
            statusEl.style.background = '#28a745';
            statusEl.textContent = `Human Verified (${(result.confidence * 100).toFixed(1)}%)`;
            statusEl.style.animation = 'none';
        }
    }

    lockPage(seconds) {
        if (this.isBlocked) return;
        this.isBlocked = true;

        // Freeze scroll
        const scrollY = window.scrollY;
        window.onscroll = () => window.scrollTo(0, scrollY);

        // Disable all elements
        document.querySelectorAll('button, input, textarea, select, a').forEach(el => {
            el.disabled = true;
            el.style.pointerEvents = 'none';
            el.style.opacity = '0.4';
        });

        // Blur content
        const container = document.querySelector('.container');
        if (container) { container.style.filter = 'blur(5px)'; container.style.pointerEvents = 'none'; }

        // Show overlay
        this.showBlockOverlay(seconds);

        // Unlock after countdown
        setTimeout(() => this.unlockPage(), seconds * 1000);
    }

    unlockPage() {
        this.isBlocked = false;
        window.onscroll = null;

        document.querySelectorAll('button, input, textarea, select, a').forEach(el => {
            el.disabled = false;
            el.style.pointerEvents = 'auto';
            el.style.opacity = '1';
        });

        const container = document.querySelector('.container');
        if (container) { container.style.filter = 'none'; container.style.pointerEvents = 'auto'; }

        const overlay = document.getElementById('block-overlay');
        if (overlay) overlay.remove();

        const statusEl = document.getElementById('status');
        statusEl.style.background = '#fd7e14';
        statusEl.textContent = 'Block Lifted - Under Monitoring';
        statusEl.style.animation = 'none';
    }

    showBlockOverlay(seconds) {
        const existing = document.getElementById('block-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'block-overlay';
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(160,0,0,0.97); color: white;
            display: flex; align-items: center; justify-content: center;
            z-index: 999999; font-family: Arial, sans-serif; text-align: center;
            user-select: none; pointer-events: all;
        `;
        overlay.innerHTML = `
            <div style="padding:50px; max-width:580px;">
                <div style="font-size:90px; margin-bottom:10px;">&#128683;</div>
                <h1 style="font-size:44px; margin:0 0 10px 0; letter-spacing:3px;">BOT DETECTED</h1>
                <div style="width:60px; height:4px; background:#ffcc00; margin:0 auto 20px auto; border-radius:2px;"></div>
                <p style="font-size:18px; margin:8px 0;">Automated behavior detected. Access blocked for</p>
                <div style="font-size:72px; font-weight:bold; color:#ffcc00; margin:10px 0;" id="countdown">${seconds}</div>
                <p style="font-size:18px;">seconds</p>
                <div style="margin:25px auto; padding:15px 30px; background:rgba(0,0,0,0.5); border-radius:10px; display:inline-block; text-align:left;">
                    <p style="margin:5px 0; font-size:14px;">&#9888; Admin alert has been triggered</p>
                    <p style="margin:5px 0; font-size:14px;">&#128203; Session: <code style="color:#ffcc00;">${this.sessionId}</code></p>
                    <p style="margin:5px 0; font-size:14px;">&#128336; ${new Date().toLocaleString()}</p>
                </div>
                <p style="font-size:13px; opacity:0.6; margin-top:15px;">This incident has been logged and reported to the administrator.</p>
            </div>
        `;
        overlay.addEventListener('click', e => e.stopPropagation());
        document.body.appendChild(overlay);

        let remaining = seconds;
        const timer = setInterval(() => {
            remaining--;
            const el = document.getElementById('countdown');
            if (el) el.textContent = remaining;
            if (remaining <= 0) clearInterval(timer);
        }, 1000);
    }

    startPeriodicSend() {
        setInterval(() => {
            if (!this.isBlocked && (this.mouseMovements.length > 5 || this.clicks.length > 1)) {
                this.sendBehaviorData();
            }
        }, 5000);
    }
}

function handleClick(buttonId) {
    console.log('Button clicked: ' + buttonId);
}

function simulateBot() {
    fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sessionId: window.behaviorTracker.sessionId,
            timeOnPage: 3, totalMouseMovements: 5, totalClicks: 25,
            totalScrollEvents: 30, totalKeystrokes: 0,
            avgMouseSpeed: 1500, mouseSpeedVariance: 80,
            avgTimeBetweenMoves: 15, straightLineRatio: 0.99,
            avgClickInterval: 80, clickIntervalVariance: 30,
            avgScrollSpeed: 950, scrollDirection: 0.98, doubleClickCount: 0
        })
    })
    .then(r => r.json())
    .then(result => {
        console.log('Result:', result);
        window.behaviorTracker.handleResult(result);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    window.behaviorTracker = new BehaviorTracker();
    console.log('Bot Detection Active. Test with: simulateBot()');
});
