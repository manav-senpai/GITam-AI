import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

export default function Home({ onAnalyze, analysisData }) {
    const [url, setUrl] = useState('https://github.com/pallets/flask')
    const navigate = useNavigate()

    const handleAnalyze = () => {
        if (url.trim()) onAnalyze(url.trim())
    }

    return (
        <div className="page">
            <div className="hero">
                <div className="hero-icon">🔬</div>
                <h1>Gitam AI</h1>
                <p>
                    Predict engineering failures before they happen. Analyze your codebase health,
                    spot risky components, and generate CEO-ready impact reports — powered by multi-agent intelligence.
                </p>
                <div className="input-group">
                    <input
                        className="input"
                        type="text"
                        placeholder="Paste a GitHub repo URL (e.g., https://github.com/pallets/flask)"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                        id="repo-url-input"
                    />
                    <button className="btn btn-primary" onClick={handleAnalyze} id="analyze-btn">
                        🚀 Analyze
                    </button>
                </div>

                {analysisData && (
                    <div style={{ marginTop: '36px', display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
                        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>📊 Dashboard</button>
                        <button className="btn btn-secondary" onClick={() => navigate('/code-review')}>🔍 Code Review</button>
                        <button className="btn btn-secondary" onClick={() => navigate('/report')}>📋 CEO Report</button>
                    </div>
                )}
            </div>

            <div className="grid-3" style={{ marginTop: '16px' }}>
                <div className="card" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '32px', marginBottom: '10px' }}>🧬</div>
                    <h3 style={{ marginBottom: '6px', fontSize: '15px' }}>Deep Code Analysis</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.6' }}>
                        Reads actual code diffs, identifies anti-patterns, and provides AI-powered review on hotspot files.
                    </p>
                </div>
                <div className="card" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '32px', marginBottom: '10px' }}>📈</div>
                    <h3 style={{ marginBottom: '6px', fontSize: '15px' }}>90-Day Predictions</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.6' }}>
                        Predicts failures using trend analysis on churn rates, bug correlations, and ownership diffusion.
                    </p>
                </div>
                <div className="card" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '32px', marginBottom: '10px' }}>💼</div>
                    <h3 style={{ marginBottom: '6px', fontSize: '15px' }}>CEO-Ready Reports</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.6' }}>
                        Translates technical risk into business impact — costs, time savings, and prioritized actions. Email it directly.
                    </p>
                </div>
            </div>
        </div>
    )
}
