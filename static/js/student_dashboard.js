const { useState, useEffect, useMemo, useRef } = React;

const StudentRecords = () => {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        fetch('/api/student/results')
            .then(res => res.json())
            .then(data => {
                setResults(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Achievement sync failed:", err);
                setLoading(false);
            });
    }, []);

    const filtered = useMemo(() => {
        if (filter === 'all') return results;
        return results.filter(r => r.difficulty === filter);
    }, [results, filter]);

    // Trend Chart
    useEffect(() => {
        if (loading || results.length === 0 || !chartRef.current) return;

        const ctx = chartRef.current.getContext('2d');
        const sorted = [...results].reverse();
        const labels = sorted.map(r => new Date(r.date_completed).toLocaleDateString(undefined, {month: 'short', day: 'numeric'}));
        const scores = sorted.map(r => r.accuracy);

        if (chartInstance.current) chartInstance.current.destroy();

        chartInstance.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Competency Trend (%)',
                    data: scores,
                    borderColor: '#818cf8',
                    backgroundColor: 'rgba(129, 140, 248, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: false },
                    y: { 
                        beginAtZero: true, 
                        max: 100, 
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }, [loading, results]);

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '2rem' }}><div className="loader"></div></div>;
    }

    return (
        <div style={{ animation: 'fadeIn 0.6s ease' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 250px', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div className="glass-card" style={{ padding: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Achievement Ledger</h3>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            {['all', 'easy', 'medium', 'hard'].map(d => (
                                <button 
                                    key={d}
                                    onClick={() => setFilter(d)}
                                    style={{
                                        padding: '0.2rem 0.6rem',
                                        fontSize: '0.7rem',
                                        fontWeight: 800,
                                        borderRadius: '0.5rem',
                                        border: '1px solid var(--glass-border)',
                                        background: filter === d ? 'var(--primary)' : 'transparent',
                                        color: filter === d ? '#fff' : 'var(--text-muted)',
                                        cursor: 'pointer',
                                        textTransform: 'uppercase'
                                    }}
                                >
                                    {d}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--text-muted)' }}>
                                    <th style={{ padding: '1rem 0.5rem', textAlign: 'left' }}>Session Date</th>
                                    <th style={{ padding: '1rem 0.5rem', textAlign: 'left' }}>Grade</th>
                                    <th style={{ padding: '1rem 0.5rem', textAlign: 'left' }}>Accuracy</th>
                                    <th style={{ padding: '1rem 0.5rem', textAlign: 'right' }}>Log</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.length > 0 ? filtered.map(r => (
                                    <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                        <td style={{ padding: '1rem 0.5rem' }}>
                                            <div style={{ fontWeight: 600 }}>{new Date(r.date_completed).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}</div>
                                            <span style={{ fontSize: '0.65rem', color: `var(--${r.difficulty})`, fontWeight: 800, textTransform: 'uppercase' }}>{r.difficulty}</span>
                                        </td>
                                        <td style={{ padding: '1rem 0.5rem', fontWeight: 700 }}>{r.score}/{r.total_questions}</td>
                                        <td style={{ padding: '1rem 0.5rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <div style={{ width: '40px', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px' }}>
                                                    <div style={{ width: `${r.accuracy}%`, height: '100%', background: r.accuracy > 70 ? 'var(--accent)' : (r.accuracy > 40 ? 'var(--warning)' : 'var(--danger)'), borderRadius: '2px' }}></div>
                                                </div>
                                                <span style={{ fontSize: '0.75rem' }}>{r.accuracy}%</span>
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem 0.5rem', textAlign: 'right' }}>
                                            <a href={r.certificate_url} target="_blank" style={{ fontSize: '1rem', textDecoration: 'none' }}>📜</a>
                                        </td>
                                    </tr>
                                )) : (
                                    <tr>
                                        <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>No session logs found in database.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-muted)', marginBottom: '1.5rem', textTransform: 'uppercase' }}>Learning Momentum</h3>
                    <div style={{ flex: 1, minHeight: '150px' }}>
                        <canvas ref={chartRef}></canvas>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Render
const container = document.getElementById('dashboard-results-root');
if (container) {
    const root = ReactDOM.createRoot(container);
    root.render(<StudentRecords />);
}
