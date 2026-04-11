import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Report({ data, apiBase, costConfig, onApplyCost }) {
    const navigate = useNavigate()
    const [ceoEmail, setCeoEmail] = useState('')
    const [sending, setSending] = useState(false)
    const [toast, setToast] = useState(null)
    const [costMode, setCostMode] = useState(costConfig?.mode || 'hour')
    const [costPerHour, setCostPerHour] = useState(costConfig?.costPerHour ?? 85)
    const [costPerKloc, setCostPerKloc] = useState(costConfig?.costPerKloc ?? 2800)

    useEffect(() => {
        if (!costConfig) return
        setCostMode(costConfig.mode || 'hour')
        setCostPerHour(costConfig.costPerHour ?? 85)
        setCostPerKloc(costConfig.costPerKloc ?? 2800)
    }, [costConfig])

    if (!data) {
        return (
            <div className="page" style={{ textAlign: 'center', paddingTop: '120px' }}>
                <h2>No Analysis Data</h2>
                <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Analyze a repository first.</p>
                <button className="btn btn-primary" style={{ marginTop: '20px' }} onClick={() => navigate('/')}>← Go Home</button>
            </div>
        )
    }

    const report = data.report || {}
    const metrics = report.metrics || {}
    const riskHours = Number(metrics.total_risk_hours || 0)
    const affectedLoc = (data.code_analysis?.hotspot_files || []).reduce(
        (sum, f) => sum + Number(f.additions || 0) + Number(f.deletions || 0),
        0
    )
    const calculatedCost = costMode === 'hour'
        ? riskHours * Number(costPerHour || 0)
        : (affectedLoc / 1000) * Number(costPerKloc || 0)
    const costExplanation = costMode === 'hour'
        ? `Total Cost = ${riskHours.toFixed(1)} risk hours × $${Number(costPerHour || 0).toLocaleString()}/hour.`
        : `Total Cost = (${affectedLoc.toLocaleString()} LOC / 1000) × $${Number(costPerKloc || 0).toLocaleString()}/KLOC.`
    const displayedCost = costConfig?.appliedCost ?? (metrics.total_risk_cost || 0)
    const displayedNote = costConfig?.explanation || 'Using default model assumptions.'
    const baseModelCost = Number(metrics.total_risk_cost || 0)
    const healthScore = Number(metrics.overall_health || 0)
    const highRiskFiles = Number(metrics.high_risk_components || 0)
    const riskLevel =
        healthScore >= 80 ? 'Low'
            : healthScore >= 65 ? 'Moderate'
                : healthScore >= 45 ? 'High'
                    : 'Critical'
    const delayWeeks = Math.max(1, Math.round(riskHours / 40))
    const fixNowCost = Math.round(Number(displayedCost) * 0.35)
    const ignoreCost = Math.round(Number(displayedCost) * 1.25)

    const executiveSnapshot = {
        financialRisk: `$${Number(displayedCost).toLocaleString()} is at risk in the next 90 days and can directly affect business results.`,
        riskLevel: `${riskLevel} risk in the next quarter.`,
        timeImpact: `This can delay delivery by about ${delayWeeks} week${delayWeeks > 1 ? 's' : ''}.`,
        biggestRisk: highRiskFiles > 0
            ? 'A small set of weak areas could fail and hurt customer experience.'
            : 'Current warning signs are limited, but reliability can still drop if ignored.',
        whatToDo: 'Approve a short stabilization effort now to lower disruption risk.',
        costComparison: `Fix now: about $${fixNowCost.toLocaleString()} vs ignore: about $${ignoreCost.toLocaleString()}.`,
    }
    const healthScoreClamped = Math.max(0, Math.min(100, Math.round(healthScore)))
    const healthDonutStyle = {
        background: `conic-gradient(var(--accent-1) ${healthScoreClamped * 3.6}deg, var(--bg-secondary) 0deg)`,
    }
    const costSplitNowPct = Math.max(1, Math.min(99, Math.round((fixNowCost / Math.max(ignoreCost, 1)) * 100)))
    const costSplitIgnorePct = 100 - costSplitNowPct

    const buildAdjustedReportText = () => {
        const original = report.report_text || 'No report generated.'
        if (!costConfig || costConfig.appliedCost === null || baseModelCost <= 0) {
            return original
        }

        const oldNoComma = String(Math.round(baseModelCost))
        const oldComma = Number(baseModelCost).toLocaleString()
        const newCost = Number(displayedCost).toLocaleString()

        let text = original
        text = text.replaceAll(`$${oldComma}`, `$${newCost}`)
        text = text.replaceAll(`$${oldNoComma}`, `$${newCost}`)

        return text
    }

    const adjustedReportText = buildAdjustedReportText()

    const applyCostUpdate = () => {
        if (!onApplyCost) return
        onApplyCost({ mode: costMode, costPerHour, costPerKloc })
        showToast('Updated global cost assumptions.', 'success')
    }

    const showToast = (message, type = 'success') => {
        setToast({ message, type })
        setTimeout(() => setToast(null), 4000)
    }

    const sendEmail = async () => {
        if (!ceoEmail.trim() || !ceoEmail.includes('@')) {
            showToast('Please enter a valid email address', 'error')
            return
        }

        setSending(true)
        try {
            const res = await fetch(`${apiBase}/api/send-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    to_email: ceoEmail.trim(),
                    repo_url: data.repoUrl,
                    report_text: adjustedReportText,
                }),
            })

            const result = await res.json()
            if (!res.ok) {
                showToast(result.detail || result.error || 'Failed to send email', 'error')
                return
            }

            showToast(result.message || `Report sent to ${ceoEmail}`, 'success')
        } catch (err) {
            showToast(`Email send failed: ${err.message}`, 'error')
        } finally {
            setSending(false)
        }
    }

    const handlePrint = () => {
        window.print()
    }

    const renderReport = (text) => {
        if (!text) return <p style={{ color: 'var(--text-muted)' }}>No report generated.</p>

        const lines = text.split('\n')
        return lines.map((line, i) => {
            // H1
            if (line.startsWith('# ') && !line.startsWith('## ')) {
                return <h1 key={i} style={{ fontSize: '24px', marginBottom: '8px', marginTop: '0' }}>{line.slice(2)}</h1>
            }
            // H2
            if (line.startsWith('## ')) {
                return <h2 key={i}>{line.slice(3)}</h2>
            }
            // H3
            if (line.startsWith('### ')) {
                return <h3 key={i}>{line.slice(4)}</h3>
            }
            // Bullet
            if (line.startsWith('- ') || line.startsWith('* ')) {
                const content = line.slice(2)
                const boldified = content.split(/\*\*(.*?)\*\*/g).map((part, j) =>
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                )
                return <li key={i}>{boldified}</li>
            }
            // Numbered list
            if (/^\d+\.\s/.test(line)) {
                const content = line.replace(/^\d+\.\s/, '')
                const boldified = content.split(/\*\*(.*?)\*\*/g).map((part, j) =>
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                )
                return <li key={i}>{boldified}</li>
            }
            // Empty line
            if (line.trim() === '') return <br key={i} />
            // Paragraph with bold support
            const boldified = line.split(/\*\*(.*?)\*\*/g).map((part, j) =>
                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
            )
            return <p key={i}>{boldified}</p>
        })
    }

    const getScoreColor = (score) => {
        if (score >= 70) return 'var(--color-healthy)'
        if (score >= 40) return 'var(--color-warning)'
        return 'var(--color-critical)'
    }

    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">📋 CEO Business Impact Report</h1>
                <p className="page-subtitle">
                    Generated by AI — translating technical risk into business impact for executive stakeholders
                </p>
            </div>

            <div className="report-container">
                {/* Main report */}
                <div className="report-main">
                    <div className="exec-snapshot" aria-label="Executive Snapshot">
                        <div className="exec-snapshot-header">
                            <h3 style={{ margin: 0 }}>Executive Snapshot</h3>
                            <span className={`card-badge ${riskLevel === 'Low' ? 'badge-healthy' : riskLevel === 'Moderate' ? 'badge-warning' : 'badge-critical'}`}>
                                {riskLevel} Risk
                            </span>
                        </div>

                        <div className="exec-top-row">
                            <div className="exec-donut-wrap">
                                <div className="exec-donut" style={healthDonutStyle}>
                                    <div className="exec-donut-inner">
                                        <span className="exec-donut-value">{healthScoreClamped}</span>
                                        <span className="exec-donut-label">/100</span>
                                    </div>
                                </div>
                                <div className="exec-caption">Health Grade: {metrics.grade || 'N/A'}</div>
                            </div>

                            <div className="exec-kpis">
                                <div className="exec-kpi">
                                    <div className="exec-kpi-label">Financial Risk</div>
                                    <div className="exec-kpi-value">${Number(displayedCost).toLocaleString()}</div>
                                </div>
                                <div className="exec-kpi">
                                    <div className="exec-kpi-label">Risk Hours</div>
                                    <div className="exec-kpi-value">{riskHours.toLocaleString()} hrs</div>
                                </div>
                                <div className="exec-kpi">
                                    <div className="exec-kpi-label">Estimated Delay</div>
                                    <div className="exec-kpi-value">~{delayWeeks} week{delayWeeks > 1 ? 's' : ''}</div>
                                </div>
                                <div className="exec-kpi">
                                    <div className="exec-kpi-label">High Risk Areas</div>
                                    <div className="exec-kpi-value">{highRiskFiles}</div>
                                </div>
                            </div>
                        </div>

                        <div className="exec-cost-compare">
                            <div className="exec-cost-bar">
                                <div className="exec-cost-now" style={{ width: `${costSplitNowPct}%` }}></div>
                                <div className="exec-cost-ignore" style={{ width: `${costSplitIgnorePct}%` }}></div>
                            </div>
                            <div className="exec-cost-labels">
                                <span>Fix now: ${fixNowCost.toLocaleString()}</span>
                                <span>If ignored: ${ignoreCost.toLocaleString()}</span>
                            </div>
                        </div>

                        <div className="exec-lines">
                            <p><strong>Biggest Risk:</strong> {executiveSnapshot.biggestRisk}</p>
                            <p><strong>What to Do:</strong> {executiveSnapshot.whatToDo}</p>
                        </div>
                    </div>
                    {renderReport(adjustedReportText)}
                </div>

                {/* Sidebar */}
                <div className="report-sidebar">
                    {/* Metrics cards */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: '16px' }}>📊 Key Metrics</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Health Score</span>
                                <span style={{ fontWeight: '700', color: getScoreColor(metrics.overall_health) }}>
                                    {Math.round(metrics.overall_health || 0)} ({metrics.grade})
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Risk Cost (90d)</span>
                                <span style={{ fontWeight: '700', color: 'var(--color-critical)' }}>
                                    ${Number(displayedCost).toLocaleString()}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Risk Hours (90d)</span>
                                <span style={{ fontWeight: '700', color: 'var(--color-warning)' }}>
                                    {(metrics.total_risk_hours || 0).toLocaleString()} hrs
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>High Risk Files</span>
                                <span style={{ fontWeight: '700', color: 'var(--color-critical)' }}>
                                    {metrics.high_risk_components || 0}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Open Bugs</span>
                                <span style={{ fontWeight: '700' }}>{metrics.open_bugs || 0}</span>
                            </div>
                        </div>

                        <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                            <h4 style={{ fontSize: '13px', marginBottom: '10px' }}>Risk Cost Calculator (90d)</h4>
                            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                                <button
                                    className={`btn ${costMode === 'hour' ? 'btn-primary' : 'btn-secondary'}`}
                                    style={{ padding: '6px 10px', fontSize: '12px' }}
                                    onClick={() => setCostMode('hour')}
                                >
                                    Hour Mode
                                </button>
                                <button
                                    className={`btn ${costMode === 'loc' ? 'btn-primary' : 'btn-secondary'}`}
                                    style={{ padding: '6px 10px', fontSize: '12px' }}
                                    onClick={() => setCostMode('loc')}
                                >
                                    LOC Mode
                                </button>
                            </div>

                            {costMode === 'hour' ? (
                                <div style={{ marginBottom: '10px' }}>
                                    <label style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Cost per hour</label>
                                    <input
                                        className="input"
                                        type="number"
                                        min="0"
                                        value={costPerHour}
                                        onChange={(e) => setCostPerHour(Number(e.target.value || 0))}
                                    />
                                </div>
                            ) : (
                                <div style={{ marginBottom: '10px' }}>
                                    <label style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Cost per 1000 LOC</label>
                                    <input
                                        className="input"
                                        type="number"
                                        min="0"
                                        value={costPerKloc}
                                        onChange={(e) => setCostPerKloc(Number(e.target.value || 0))}
                                    />
                                </div>
                            )}

                            <button className="btn btn-primary" onClick={applyCostUpdate} style={{ width: '100%', justifyContent: 'center', marginBottom: '10px' }}>
                                Update Cost
                            </button>

                            <div style={{ padding: '10px', borderRadius: '10px', background: 'var(--bg-secondary)' }}>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Estimated Cost</div>
                                <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--color-critical)' }}>
                                    ${Math.round(calculatedCost).toLocaleString()}
                                </div>
                                <p style={{ fontSize: '12px', marginTop: '6px', color: 'var(--text-secondary)' }}>
                                    {costMode === 'hour'
                                        ? `${riskHours.toFixed(1)} hours × $${Number(costPerHour || 0).toLocaleString()}/hour`
                                        : `${affectedLoc.toLocaleString()} LOC at $${Number(costPerKloc || 0).toLocaleString()} per 1000 LOC`}
                                </p>
                            </div>
                            <p style={{ fontSize: '11px', marginTop: '8px', color: 'var(--text-muted)' }}>
                                {displayedNote}
                            </p>
                        </div>
                    </div>

                    {/* Email to CEO */}
                    <div className="email-card">
                        <h3>📧 Send to CEO</h3>
                        <input
                            className="input"
                            type="email"
                            placeholder="ceo@company.com"
                            value={ceoEmail}
                            onChange={(e) => setCeoEmail(e.target.value)}
                            id="ceo-email-input"
                        />
                        <button
                            className="btn btn-primary"
                            onClick={sendEmail}
                            disabled={sending}
                            id="send-email-btn"
                        >
                            {sending ? (
                                <>
                                    <span className="spinner" style={{ width: '14px', height: '14px' }}></span>
                                    Sending...
                                </>
                            ) : (
                                '📨 Send Report'
                            )}
                        </button>
                    </div>

                    {/* Print / Export */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: '12px' }}>🖨️ Export</h3>
                        <button className="btn btn-secondary" onClick={handlePrint} style={{ width: '100%', justifyContent: 'center' }}>
                            Print / Save PDF
                        </button>
                    </div>
                </div>
            </div>

            {/* Toast notification */}
            {toast && (
                <div className={`toast ${toast.type}`}>
                    {toast.type === 'success' ? '✅' : '❌'} {toast.message}
                </div>
            )}
        </div>
    )
}
