import { useNavigate } from 'react-router-dom'

export default function Dashboard({ data, costConfig }) {
    const navigate = useNavigate()

    if (!data) {
        return (
            <div className="page" style={{ textAlign: 'center', paddingTop: '120px' }}>
                <h2>No Analysis Data</h2>
                <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                    Go to Home and analyze a repository first.
                </p>
                <button className="btn btn-primary" style={{ marginTop: '20px' }} onClick={() => navigate('/')}>
                    ← Go Home
                </button>
            </div>
        )
    }

    const { repo_info, health_scores, predictions, code_analysis, bug_analysis } = data
    const overall = health_scores?.overall_score || {}
    const breakdown = overall.breakdown || {}
    const weights = overall.weights || {}
    const grade = health_scores?.grade || 'N/A'
    const fileScores = health_scores?.file_scores || []
    const timeline = predictions?.timeline || []
    const predictionList = predictions?.predictions || []
    const simulationScenarios = predictions?.failure_simulation?.scenarios || []
    const commitFreq = code_analysis?.commit_frequency?.monthly || {}
    const totalIssues = bug_analysis?.total_issues || 0
    const totalBugs = bug_analysis?.total_bugs || 0
    const bugSignalSource = bug_analysis?.bug_signal_source || 'issues'

    const componentLabels = {
        code_quality: 'Code Quality',
        bug_density: 'Bug Density',
        test_coverage: 'Test Coverage',
        commit_stability: 'Commit Stability',
        ownership_risk: 'Ownership Risk',
    }

    const getScoreColor = (score) => {
        if (score >= 70) return 'var(--color-healthy)'
        if (score >= 40) return 'var(--color-warning)'
        return 'var(--color-critical)'
    }

    const formatTag = (tag) => {
        const map = {
            'high-churn': '🔥 High churn',
            'single-maintainer': '🧍 Single maintainer risk',
            'low-test-coverage': '🧪 No test coverage signal',
            'bug-prone': '🐛 Bug-prone pattern',
        }
        return map[tag] || tag
    }

    const monthlyEntries = buildMonthlySeries(commitFreq, 8)
    const maxCommits = Math.max(...monthlyEntries.map(([, v]) => v), 1)

    function buildMonthlySeries(monthlyMap, slotCount = 8) {
        const now = new Date()
        const keys = []

        for (let i = slotCount - 1; i >= 0; i -= 1) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
            const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
            keys.push(key)
        }

        return keys.map((k) => [k, Number(monthlyMap[k] || 0)])
    }

    return (
        <div className="page">
            <div className="page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <h1 className="page-title">📊 Dashboard</h1>
                    <span className="card-badge badge-healthy" style={{ fontSize: '13px' }}>
                        {repo_info?.name}
                    </span>
                </div>
                <p className="page-subtitle">{repo_info?.description}</p>
                {costConfig?.appliedCost !== null && (
                    <div style={{ marginTop: '10px' }}>
                        <span className="card-badge badge-warning" style={{ fontSize: '12px' }}>
                            Applied Risk Cost (90d): ${Number(costConfig.appliedCost).toLocaleString()}
                        </span>
                    </div>
                )}
            </div>

            <div className="grid-4" style={{ marginBottom: '24px' }}>
                <div className="card stat-card">
                    <div className="score-circle">
                        <span className="score-value" style={{ color: getScoreColor(overall.score) }}>
                            {Math.round(overall.score || 0)}
                        </span>
                        <span className="score-label">/ 100</span>
                        <span className="score-grade" style={{ color: getScoreColor(overall.score) }}>{grade}</span>
                    </div>
                    <div className="stat-label">Overall Health</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-value status-critical">{health_scores?.critical_count || 0}</div>
                    <div className="stat-label">Critical Files</div>
                    <div className="stat-change status-critical">Needs immediate attention</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-value status-warning">{health_scores?.warning_count || 0}</div>
                    <div className="stat-label">Warning Files</div>
                    <div className="stat-change status-warning">Monitor closely</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-value status-healthy">{health_scores?.healthy_count || 0}</div>
                    <div className="stat-label">Healthy Files</div>
                    <div className="stat-change status-healthy">Good condition</div>
                </div>
            </div>

            <div className="grid-2" style={{ marginBottom: '24px' }}>
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🏥 Health Score Formula</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {Object.entries(componentLabels).map(([key, label]) => {
                            const value = breakdown[key] || 0
                            const weight = weights[key] || 0
                            return (
                                <div key={key}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                                            {label} ({weight}%)
                                        </span>
                                        <span style={{ fontSize: '13px', fontWeight: '600', color: getScoreColor(value) }}>
                                            {Math.round(value)}
                                        </span>
                                    </div>
                                    <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                                        <div style={{
                                            height: '100%',
                                            width: `${value}%`,
                                            background: getScoreColor(value),
                                            borderRadius: '3px',
                                            transition: 'width 0.5s ease',
                                        }}></div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                    <p style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {overall.formula || 'Weighted model is used for transparent scoring.'}
                    </p>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🐛 Bug Summary</h3>
                    </div>
                    <div className="grid-2" style={{ gap: '12px' }}>
                        <div style={{ textAlign: 'center', padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                            <div style={{ fontSize: '24px', fontWeight: '700' }}>{bug_analysis?.total_bugs || 0}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Bugs</div>
                        </div>
                        <div style={{ textAlign: 'center', padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                            <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--color-critical)' }}>{bug_analysis?.open_bugs || 0}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Open Bugs</div>
                        </div>
                        <div style={{ textAlign: 'center', padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                            <div style={{ fontSize: '24px', fontWeight: '700' }}>{bug_analysis?.avg_resolution_days || '—'}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Avg Resolution (days)</div>
                        </div>
                        <div style={{ textAlign: 'center', padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                            <div style={{ fontSize: '24px', fontWeight: '700' }}>{code_analysis?.total_commits || 0}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Commits</div>
                        </div>
                    </div>
                    <p style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {totalIssues === 0
                            ? bugSignalSource === 'activity-inference'
                                ? `No issue tracker data found; showing a conservative inferred bug signal from recent activity.`
                                : bugSignalSource === 'commit-signals'
                                    ? `No issue labels found; bug signal inferred from bug-fix commit patterns.`
                                    : 'No GitHub issues were found for this repository in the fetched window.'
                            : totalBugs === 0
                                ? `Fetched ${totalIssues} issues, but none matched bug signals.`
                                : `Detected ${totalBugs} bug-like issues from ${totalIssues} total issues.`}
                    </p>
                </div>
            </div>

            <div className="grid-2" style={{ marginBottom: '24px' }}>
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📈 Commit Frequency</h3>
                    </div>
                    <div className="bar-chart">
                        {monthlyEntries.map(([month, count]) => (
                            <div
                                key={month}
                                className="bar"
                                style={{ height: `${(count / maxCommits) * 100}%` }}
                                title={`${month}: ${count} commits`}
                            ></div>
                        ))}
                    </div>
                    <div className="bar-labels">
                        {monthlyEntries.map(([month]) => (
                            <span key={month} className="bar-label">{month.slice(5)}</span>
                        ))}
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">⚠️ Explainable Risk Forecast</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {timeline.map((t, i) => (
                            <div key={i} style={{
                                display: 'flex', alignItems: 'center', gap: '16px',
                                padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)'
                            }}>
                                <span style={{ fontSize: '14px', fontWeight: '600', width: '40px' }}>{t.period}</span>
                                <div style={{ flex: 1, display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                                    <span className="card-badge badge-critical" style={{ fontSize: '11px' }}>
                                        🔴 {t.high_risk} high
                                    </span>
                                    <span className="card-badge badge-warning" style={{ fontSize: '11px' }}>
                                        🟡 {t.medium_risk} med
                                    </span>
                                    <span className="card-badge badge-healthy" style={{ fontSize: '11px' }}>
                                        🟢 {t.low_risk} low
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {predictionList.slice(0, 3).map((p) => (
                            <div key={p.filename} className="risk-driver-card">
                                <strong style={{ fontSize: '12px' }}>{p.filename}</strong>
                                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>{p.explanation}</p>
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
                                    {(p.risk_drivers || []).slice(0, 4).map((driver) => (
                                        <span key={driver.driver} className="card-badge badge-warning" style={{ fontSize: '10px' }}>
                                            {driver.driver} (+{Math.round(driver.impact)})
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginBottom: '24px' }}>
                <div className="card-header">
                    <h3 className="card-title">🧠 Failure Simulation (If This File Breaks)</h3>
                </div>
                <div className="simulation-grid">
                    {simulationScenarios.slice(0, 4).map((scenario) => (
                        <div key={scenario.trigger_file} className="simulation-card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                                <strong style={{ fontSize: '12px' }}>{scenario.trigger_file}</strong>
                                <span className={`card-badge ${scenario.risk_level === 'high' ? 'badge-critical' : scenario.risk_level === 'medium' ? 'badge-warning' : 'badge-healthy'}`} style={{ fontSize: '10px' }}>
                                    {scenario.risk_level}
                                </span>
                            </div>
                            <p style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                                Estimated downtime: <strong>{scenario.estimated_downtime_hours}h</strong> · Cascading failures: <strong>{scenario.cascading_failures}</strong>
                            </p>
                            <p style={{ marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                                Impacted modules: {(scenario.impacted_modules || []).slice(0, 3).join(', ') || 'No direct neighbors detected'}
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">🔥 Hotspot Files (Highest Risk)</h3>
                    <button className="btn btn-secondary" onClick={() => navigate('/code-review')} style={{ fontSize: '12px', padding: '6px 14px' }}>
                        Open Code Review →
                    </button>
                </div>
                <ul className="file-list">
                    {fileScores.slice(0, 12).map((f, i) => (
                        <li key={i} className="file-item" onClick={() => navigate('/code-review')}>
                            <div className="file-info">
                                <span className={`status-dot ${f.status}`}></span>
                                <span className="file-name" title={f.filename}>
                                    {f.filename}
                                </span>
                            </div>
                            <div className="file-meta" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <span>🔄 {f.change_count} changes</span>
                                <span>+{f.additions} / -{f.deletions}</span>
                                <span>👥 {f.unique_authors}</span>
                                {(f.risk_tags || []).slice(0, 2).map((tag) => (
                                    <span key={tag} className="card-badge badge-warning" style={{ fontSize: '10px' }}>
                                        {formatTag(tag)}
                                    </span>
                                ))}
                                <span className={`file-score ${f.status === 'healthy' ? 'status-healthy' : f.status === 'warning' ? 'status-warning' : 'status-critical'}`}>
                                    {Math.round(f.health_score)}
                                </span>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    )
}
