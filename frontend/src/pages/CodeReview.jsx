import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function CodeReview({ data, apiBase }) {
    const navigate = useNavigate()
    const [selectedFile, setSelectedFile] = useState(null)
    const [reviewData, setReviewData] = useState(null)
    const [loading, setLoading] = useState(false)

    if (!data) {
        return (
            <div className="page" style={{ textAlign: 'center', paddingTop: '120px' }}>
                <h2>No Analysis Data</h2>
                <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Analyze a repository first.</p>
                <button className="btn btn-primary" style={{ marginTop: '20px' }} onClick={() => navigate('/')}>← Go Home</button>
            </div>
        )
    }

    const fileScores = data.health_scores?.file_scores || []

    const loadReview = async (filename) => {
        setSelectedFile(filename)
        setLoading(true)
        setReviewData(null)

        try {
            const res = await fetch(`${apiBase}/api/code-review/${data.owner}/${data.repo}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename }),
            })
            const result = await res.json()
            setReviewData(result)
        } catch (err) {
            setReviewData({ error: err.message })
        }
        setLoading(false)
    }

    const getStatusClass = (status) => {
        if (status === 'healthy') return 'badge-healthy'
        if (status === 'warning') return 'badge-warning'
        return 'badge-critical'
    }

    const renderDiff = (patch) => {
        if (!patch) return <span style={{ color: 'var(--text-muted)' }}>No diff available</span>
        const lines = patch.split('\n')
        return lines.map((line, i) => {
            let cls = 'diff-line context'
            if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-line addition'
            else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-line deletion'
            else if (line.startsWith('@@')) cls = 'diff-line context'
            return <span key={i} className={cls}>{line}{'\n'}</span>
        })
    }

    const renderAiReview = (text) => {
        if (!text) return null
        // Simple markdown-ish rendering
        const parts = text.split('\n')
        return parts.map((line, i) => {
            if (line.startsWith('**') && line.endsWith('**')) {
                return <h4 key={i} style={{ color: 'var(--accent-primary)', marginTop: '12px', marginBottom: '4px' }}>{line.replace(/\*\*/g, '')}</h4>
            }
            if (line.startsWith('- ') || line.startsWith('* ')) {
                return <li key={i} style={{ marginLeft: '16px', marginBottom: '2px' }}>{line.slice(2)}</li>
            }
            if (line.startsWith('#')) {
                const content = line.replace(/^#+\s*/, '')
                return <h4 key={i} style={{ color: 'var(--accent-primary)', marginTop: '12px', marginBottom: '4px' }}>{content}</h4>
            }
            if (line.trim() === '') return <br key={i} />
            // Handle inline bold
            const boldified = line.split(/\*\*(.*?)\*\*/g).map((part, j) =>
                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
            )
            return <p key={i} style={{ marginBottom: '4px' }}>{boldified}</p>
        })
    }

    const renderRiskTag = (tag) => {
        const tags = {
            'high-churn': '🔥 High churn',
            'single-maintainer': '🧍 Single maintainer risk',
            'low-test-coverage': '🧪 No test coverage signal',
            'bug-prone': '🐛 Bug-prone',
        }
        return tags[tag] || tag
    }

    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">🔍 Code Review</h1>
                <p className="page-subtitle">
                    Select a hotspot file to view its change history, diffs, and AI-powered analysis
                </p>
            </div>

            <div className="code-review-layout">
                {/* Sidebar - file list */}
                <div className="file-sidebar">
                    <div className="file-sidebar-title">Hotspot Files</div>
                    {fileScores.map((f, i) => (
                        <div
                            key={i}
                            className={`sidebar-file ${selectedFile === f.filename ? 'active' : ''}`}
                            onClick={() => loadReview(f.filename)}
                            title={f.filename}
                        >
                            <span className={`status-dot ${f.status}`}></span>
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                                {f.filename.split('/').pop()}
                            </span>
                            <span className={`card-badge ${getStatusClass(f.status)}`} style={{ fontSize: '10px', padding: '2px 6px' }}>
                                {Math.round(f.health_score)}
                            </span>
                        </div>
                    ))}
                </div>

                {/* Main content */}
                <div className="code-content">
                    {!selectedFile && (
                        <div className="card" style={{ textAlign: 'center', padding: '80px 40px' }}>
                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👈</div>
                            <h3>Select a file from the sidebar</h3>
                            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                Choose a hotspot file to view its change history, code diffs, and AI analysis
                            </p>
                        </div>
                    )}

                    {loading && (
                        <div className="card" style={{ textAlign: 'center', padding: '80px 40px' }}>
                            <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
                            <h3>Analyzing {selectedFile?.split('/').pop()}...</h3>
                            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                Fetching code, comparing versions, and generating AI review
                            </p>
                        </div>
                    )}

                    {reviewData && !loading && (
                        <>
                            {/* File info header */}
                            <div className="card">
                                <h3 style={{ marginBottom: '8px', wordBreak: 'break-all' }}>📄 {reviewData.filename}</h3>
                                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                    <span className="card-badge badge-warning" style={{ fontSize: '12px' }}>
                                        {reviewData.diffs?.length || 0} recent changes
                                    </span>
                                </div>
                            </div>

                            {reviewData.file_metrics && (
                                <div className="card">
                                    <div className="card-header">
                                        <h3 className="card-title">📐 Engineering Intelligence Metrics</h3>
                                    </div>
                                    <div className="grid-2" style={{ gap: '12px' }}>
                                        <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Churn Rate</div>
                                            <div style={{ fontSize: '20px', fontWeight: '700' }}>{reviewData.file_metrics.churn_rate || 0}%</div>
                                        </div>
                                        <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Contributor Count</div>
                                            <div style={{ fontSize: '20px', fontWeight: '700' }}>{reviewData.file_metrics.contributor_count || 0}</div>
                                        </div>
                                        <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Bug History (commits)</div>
                                            <div style={{ fontSize: '20px', fontWeight: '700' }}>{reviewData.file_metrics.bug_history_count || 0}</div>
                                        </div>
                                        <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Test Coverage Signal</div>
                                            <div style={{ fontSize: '20px', fontWeight: '700', color: reviewData.file_metrics.has_test_signal ? 'var(--color-healthy)' : 'var(--color-critical)' }}>
                                                {reviewData.file_metrics.has_test_signal ? 'Present' : 'Missing'}
                                            </div>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                                        {(reviewData.file_metrics.risk_tags || []).map((tag) => (
                                            <span key={tag} className="card-badge badge-warning" style={{ fontSize: '11px' }}>
                                                {renderRiskTag(tag)}
                                            </span>
                                        ))}
                                    </div>

                                    <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        {(reviewData.file_metrics.risk_drivers || []).map((driver) => (
                                            <div key={driver.driver} className="risk-driver-card">
                                                <strong style={{ fontSize: '12px' }}>{driver.driver}</strong>
                                                <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '8px' }}>
                                                    +{Math.round(driver.impact || 0)} risk
                                                </span>
                                                <p style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                    {driver.evidence}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* AI Review Panel */}
                            <div className="ai-review-panel">
                                <h3>🤖 AI Code Review</h3>
                                <div className="ai-review-content">
                                    {reviewData.error ? (
                                        <p style={{ color: 'var(--color-critical)' }}>Error: {reviewData.error}</p>
                                    ) : (
                                        renderAiReview(reviewData.ai_review)
                                    )}
                                </div>
                            </div>

                            {/* Diffs */}
                            {reviewData.diffs?.map((diff, i) => (
                                <div key={i} className="diff-viewer">
                                    <div className="diff-header">
                                        <div style={{ minWidth: 0, overflow: 'hidden' }}>
                                            <strong>Commit {diff.sha}</strong>
                                            <span style={{ marginLeft: '12px', color: 'var(--text-muted)', wordBreak: 'break-word' }}>
                                                {diff.message}
                                            </span>
                                        </div>
                                        <div style={{ display: 'flex', gap: '12px', fontSize: '12px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                            <span>by {diff.author}</span>
                                            <span>{diff.date?.slice(0, 10)}</span>
                                            <span style={{ color: 'var(--color-healthy)' }}>+{diff.additions}</span>
                                            <span style={{ color: 'var(--color-critical)' }}>-{diff.deletions}</span>
                                        </div>
                                    </div>
                                    <div className="diff-body">
                                        <pre>{renderDiff(diff.patch)}</pre>
                                    </div>
                                </div>
                            ))}

                            {/* Current file content */}
                            {reviewData.current_content && (
                                <div className="diff-viewer">
                                    <div className="diff-header">
                                        <strong>📝 Current File Content</strong>
                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                            {reviewData.current_content.split('\n').length} lines
                                        </span>
                                    </div>
                                    <div className="diff-body">
                                        <pre style={{ color: 'var(--text-secondary)' }}>
                                            {reviewData.current_content.slice(0, 5000)}
                                            {reviewData.current_content.length > 5000 && '\n\n... (truncated)'}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
