const { useState, useEffect, useMemo, useRef } = React;

const ResultPage = () => {
    const dataElement = document.getElementById('result-data');
    if (!dataElement) return null;
    
    const data = JSON.parse(dataElement.textContent);
    const [animatedScore, setAnimatedScore] = useState(0);
    const chartRef = useRef(null);

    // Score animation
    useEffect(() => {
        let start = 0;
        const end = data.score;
        if (start === end) {
            setAnimatedScore(end);
            return;
        }
        
        const duration = 1000; // 1 second
        const stepTime = Math.abs(Math.floor(duration / end));
        
        let timer = setInterval(() => {
            start += 1;
            setAnimatedScore(start);
            if (start >= end) clearInterval(timer);
        }, stepTime);
        return () => clearInterval(timer);
    }, [data.score]);

    // Chart initialization
    useEffect(() => {
        if (!chartRef.current) return;
        const ctx = chartRef.current.getContext('2d');
        
        const categories = Object.keys(data.analytics);
        const scores = categories.map(cat => (data.analytics[cat].correct / data.analytics[cat].total) * 100);

        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: categories,
                datasets: [{
                    label: 'Skill Proficiency (%)',
                    data: scores,
                    fill: true,
                    backgroundColor: 'rgba(129, 140, 248, 0.2)',
                    borderColor: 'rgb(129, 140, 248)',
                    pointBackgroundColor: 'rgb(129, 140, 248)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(129, 140, 248)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#94a3b8', font: { size: 10 } },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }, []);

    const securityStatus = data.tab_switches === 0 ? "Clean" : (data.tab_switches < 3 ? "Minor Infraction" : "Compromised");
    const securityColor = data.tab_switches === 0 ? "#10b981" : (data.tab_switches < 3 ? "#f59e0b" : "#ef4444");

    return (
        <div style={{ maxWidth: '900px', margin: '2rem auto', padding: '0 1rem' }}>
            <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🚀</div>
                <h1 style={{ marginBottom: '0.5rem', fontSize: '2.5rem', fontWeight: 800 }}>Performance Briefing</h1>
                <p style={{ color: '#94a3b8', marginBottom: '3rem' }}>Analysis complete. Your metrics have been logged to the neural network.</p>

                <div className="performance-container" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '3rem', alignItems: 'center', marginBottom: '3rem' }}>
                    <div style={{ textAlign: 'left' }}>
                        <p style={{ fontSize: '0.8rem', color: '#818cf8', textTransform: 'uppercase', letterSpacing: '2px', fontWeight: 800, marginBottom: '0.5rem' }}>Aptitude Score</p>
                        <div style={{ fontSize: '5rem', fontWeight: 900, lineHeight: 1, margin: '1rem 0', color: '#fff', display: 'flex', alignItems: 'baseline' }}>
                            {animatedScore}
                            <span style={{ fontSize: '1.5rem', color: '#94a3b8', fontWeight: 400, marginLeft: '0.5rem' }}>/{data.total}</span>
                        </div>
                        
                        {data.penalty_applied > 0 && (
                            <div style={{ marginBottom: '1.5rem', padding: '0.75rem', borderRadius: '0.8rem', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                                <p style={{ color: '#ef4444', fontSize: '0.8rem', fontWeight: 800 }}>⚠️ -{data.penalty_applied} Penalty Points Applied</p>
                                <p style={{ color: '#94a3b8', fontSize: '0.7rem' }}>Cheating deduction from base score: {data.real_score}/{data.total}</p>
                            </div>
                        )}

                        <div style={{ padding: '1.5rem', borderRadius: '1.25rem', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                <span style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>Integrity Status</span>
                                <span style={{ color: securityColor, fontWeight: 800, fontSize: '0.8rem' }}>{securityStatus.toUpperCase()}</span>
                            </div>
                            <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{ 
                                    width: `${Math.max(5, 100 - (data.tab_switches * 25))}%`, 
                                    height: '100%', 
                                    background: securityColor,
                                    transition: 'width 1.5s cubic-bezier(0.4, 0, 0.2, 1)'
                                }}></div>
                            </div>
                            <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.75rem' }}>
                                Trace: {data.tab_switches} tab deviations | {data.snapshots.length} active captures.
                            </p>
                        </div>
                    </div>

                    <div style={{ background: 'rgba(129, 140, 248, 0.03)', borderRadius: '2rem', padding: '1.5rem', border: '1px solid rgba(255,255,255,0.08)', position: 'relative' }}>
                         <div style={{ height: '300px' }}>
                            <canvas ref={chartRef}></canvas>
                         </div>
                    </div>
                </div>

                <div className="glass-card" style={{ textAlign: 'left', marginBottom: '2.5rem', borderLeft: '4px solid #818cf8', background: 'rgba(129, 140, 248, 0.05)', padding: '1.5rem' }}>
                    <p style={{ color: '#818cf8', fontSize: '0.7rem', fontWeight: 900, textTransform: 'uppercase', marginBottom: '0.5rem', letterSpacing: '1px' }}>🤖 Neural Feedback</p>
                    <p style={{ fontSize: '1.1rem', lineHeight: 1.6, color: '#f1f5f9', fontStyle: 'italic', fontWeight: 500 }}>
                        "{data.tutor_feedback}"
                    </p>
                </div>

                {data.snapshots.length > 0 && (
                    <div style={{ textAlign: 'left', marginBottom: '3rem' }}>
                        <p style={{ color: '#94a3b8', fontSize: '0.7rem', fontWeight: 900, textTransform: 'uppercase', marginBottom: '1.5rem', letterSpacing: '1px' }}>📸 Forensic Evidence</p>
                        <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '1rem' }}>
                            {data.snapshots.map((snap, idx) => (
                                <img key={idx} src={snap} style={{ height: '90px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 16px rgba(0,0,0,0.3)', flex: '0 0 auto' }} />
                            ))}
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <a href={data.dashboard_url} className="btn btn-outline" style={{ padding: '0.75rem 2rem', fontSize: '0.9rem' }}>
                        🏠 Dashboard
                    </a>
                    <a href={data.certificate_url} className="btn btn-primary" style={{ padding: '0.75rem 2.5rem', fontSize: '0.9rem' }} target="_blank">
                        🎓 Claim Certificate
                    </a>
                </div>
            </div>
        </div>
    );
};

// Render
const container = document.getElementById('result-page-root');
if (container) {
    const root = ReactDOM.createRoot(container);
    root.render(<ResultPage />);
}
