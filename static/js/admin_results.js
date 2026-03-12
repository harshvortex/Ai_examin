const { useState, useEffect, useMemo, useRef } = React;

const ResultsDashboard = () => {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filterDifficulty, setFilterDifficulty] = useState('all');
    const [error, setError] = useState(null);
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        fetch('/api/admin/results')
            .then(res => res.json())
            .then(data => {
                setResults(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch results:", err);
                setError("Could not load exam data. Please try again.");
                setLoading(false);
            });
    }, []);

    // Derived stats
    const stats = useMemo(() => {
        if (results.length === 0) return { avgScore: 0, totalExams: 0, avgAccuracy: 0, compromisedCount: 0 };
        const totalExams = results.length;
        const avgScore = (results.reduce((acc, r) => acc + (r.score / r.total_questions), 0) / totalExams * 100).toFixed(1);
        const avgAccuracy = (results.reduce((acc, r) => acc + r.accuracy, 0) / totalExams).toFixed(1);
        const compromisedCount = results.filter(r => r.tab_switches >= 3).length;
        return { avgScore, totalExams, avgAccuracy, compromisedCount };
    }, [results]);

    // Filtered results
    const filteredResults = useMemo(() => {
        return results.filter(r => {
            const matchesSearch = r.student_name.toLowerCase().includes(search.toLowerCase()) || 
                                 r.student_email.toLowerCase().includes(search.toLowerCase());
            const matchesDiff = filterDifficulty === 'all' || r.difficulty === filterDifficulty;
            return matchesSearch && matchesDiff;
        });
    }, [results, search, filterDifficulty]);

    // Chart update
    useEffect(() => {
        if (loading || results.length === 0 || !chartRef.current) return;

        // Group results by date for the chart
        const groupedData = results.reduce((acc, r) => {
            const date = r.date_completed.split('T')[0];
            if (!acc[date]) acc[date] = { sum: 0, count: 0 };
            acc[date].sum += (r.score / r.total_questions) * 100;
            acc[date].count += 1;
            return acc;
        }, {});

        const labels = Object.keys(groupedData).sort();
        const chartData = labels.map(label => (groupedData[label].sum / groupedData[label].count).toFixed(1));

        const ctx = chartRef.current.getContext('2d');
        
        if (chartInstance.current) {
            chartInstance.current.destroy();
        }

        chartInstance.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.map(l => new Date(l).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})),
                datasets: [{
                    label: 'Avg Performance (%)',
                    data: chartData,
                    borderColor: '#818cf8',
                    backgroundColor: 'rgba(129, 140, 248, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                    y: { 
                        beginAtZero: true, 
                        max: 100, 
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8', callback: (v) => v + '%' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1
                    }
                }
            }
        });
    }, [loading, results]);

    if (loading) {
        return (
            <div style={{ padding: '4rem', textAlign: 'center' }}>
                <div className="loader"></div>
                <p style={{ marginTop: '1rem', color: '#94a3b8' }}>Aggregating Global Exam Data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ padding: '4rem', textAlign: 'center', color: '#ef4444' }}>
                <p>⚠️ {error}</p>
                <button onClick={() => window.location.reload()} className="btn btn-outline" style={{ marginTop: '1rem' }}>Retry</button>
            </div>
        );
    }

    return (
        <div style={{ animation: 'fadeIn 0.5s ease' }}>
            <div className="dashboard-header">
                <div>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>
                        <span style={{ background: 'linear-gradient(to right, #818cf8, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                            AI Performance Insights
                        </span>
                    </h1>
                    <p style={{ color: '#94a3b8' }}>Real-time monitoring of all examination clusters.</p>
                </div>
                
                <div className="search-nav">
                    <span>🔍</span>
                    <input 
                        type="text" 
                        placeholder="Search student or email..." 
                        className="search-input"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    <select 
                        style={{ background: 'rgba(255,255,255,0.05)', border: 'none', color: '#fff', padding: '0.5rem', borderRadius: '0.5rem' }}
                        value={filterDifficulty}
                        onChange={(e) => setFilterDifficulty(e.target.value)}
                    >
                        <option value="all">All Difficulty</option>
                        <option value="easy">Easy</option>
                        <option value="medium">Medium</option>
                        <option value="hard">Hard</option>
                    </select>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
                <div className="stat-card">
                    <span className="label">TOTAL EXAMS</span>
                    <span className="value">{stats.totalExams}</span>
                    <p style={{ fontSize: '0.7rem', color: '#10b981', marginTop: '0.5rem' }}>+12% vs last month</p>
                </div>
                <div className="stat-card">
                    <span className="label">AVG PERFORMANCE</span>
                    <span className="value">{stats.avgScore}%</span>
                    <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.5rem' }}>Global competency index</p>
                </div>
                <div className="stat-card">
                    <span className="label">ACCURACY</span>
                    <span className="value">{stats.avgAccuracy}%</span>
                    <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.5rem' }}>Precision rating</p>
                </div>
                <div className="stat-card" style={{borderColor: stats.compromisedCount > 0 ? 'rgba(239, 68, 68, 0.3)' : 'var(--glass-border)'}}>
                    <span className="label">SECURITY RISK</span>
                    <span className="value" style={{ color: stats.compromisedCount > 0 ? '#ef4444' : '#10b981' }}>{stats.compromisedCount}</span>
                    <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.5rem' }}>Compromised sessions</p>
                </div>
            </div>

            <div className="glass-card" style={{ height: '300px', marginBottom: '2.5rem', padding: '1.5rem' }}>
                <canvas ref={chartRef}></canvas>
            </div>

            <div className="results-table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Score</th>
                            <th>Difficulty</th>
                            <th>Time</th>
                            <th>Date</th>
                            <th>Alerts</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredResults.length > 0 ? filteredResults.map(r => (
                            <tr key={r.id}>
                                <td>
                                    <div style={{ fontWeight: 700 }}>{r.student_name}</div>
                                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{r.student_email}</div>
                                </td>
                                <td>
                                    <div style={{ fontWeight: 800, color: r.accuracy > 70 ? '#10b981' : (r.accuracy > 40 ? '#f59e0b' : '#ef4444') }}>
                                        {r.score}/{r.total_questions}
                                    </div>
                                    <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{r.accuracy}% Accuracy</div>
                                </td>
                                <td>
                                    <span className={`badge badge-${r.difficulty}`}>
                                        {r.difficulty.toUpperCase()}
                                    </span>
                                </td>
                                <td>{r.time_taken}s</td>
                                <td>{new Date(r.date_completed).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</td>
                                <td>
                                    {r.tab_switches > 0 && (
                                        <span style={{ 
                                            padding: '0.2rem 0.5rem', 
                                            borderRadius: '4px', 
                                            background: r.tab_switches >= 3 ? '#ef4444' : '#f59e0b', 
                                            color: '#fff', 
                                            fontSize: '0.65rem' ,
                                            fontWeight: 800
                                        }}>
                                            {r.tab_switches} SW
                                        </span>
                                    )}
                                </td>
                                <td>
                                    <a href={`/download-certificate/${r.id}`} target="_blank" className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }}>
                                        View Cert
                                    </a>
                                </td>
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan="7" style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>
                                    No records found matching your current parameters.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
            
            <style jsx>{`
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

// Render
const container = document.getElementById('admin-results-root');
const root = ReactDOM.createRoot(container);
root.render(<ResultsDashboard />);
