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

// Clear timer on submission
document.addEventListener('submit', (e) => {
    if (e.target.id === 'exam-form') {
        const isLast = e.target.querySelector('button').textContent.includes('Complete');
        if (isLast) {
            localStorage.removeItem('exam_time_left');
        }
    }
});
