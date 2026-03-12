function startTimer(duration, display, onComplete) {
    let timer = duration;
    let minutes, seconds;

    const interval = setInterval(() => {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        // Visual warning when time is low
        if (timer <= 60) {
            display.style.color = "#ef4444"; // Red color
            display.style.animation = "pulse 1s infinite";
        }

        if (--timer < 0) {
            clearInterval(interval);
            localStorage.removeItem('exam_time_left');
            if (onComplete) onComplete();
        } else {
            // Save current time to handle refreshes
            localStorage.setItem('exam_time_left', timer);
        }
    }, 1000);
}

// --- Anti-Cheating: Tab Switching Guard ---
let tabSwitches = 0;
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.location.pathname === '/exam') {
        tabSwitches++;
        localStorage.setItem('tab_switches', tabSwitches);
        
        // Notify student on return
        if (tabSwitches >= 3) {
            alert("⚠️ WARNING: Multiple tab switches detected. Exam may be auto-submitted.");
        } else {
            alert(`⚠️ Tab Switch Detected (${tabSwitches}/3). This incident has been logged.`);
        }
        
        // Sync with backend (optional: could be a stealth fetch)
        fetch('/log-incident', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({type: 'tab_switch', count: tabSwitches})
        });
    }
});

// Clear tab switches on form submission
document.addEventListener('submit', (e) => {
    if (e.target.id === 'exam-form') {
        const isLast = e.target.querySelector('button').textContent.includes('Complete');
        if (isLast) {
            localStorage.removeItem('exam_time_left');
            localStorage.removeItem('tab_switches');
        }
    }
});
