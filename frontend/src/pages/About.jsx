export default function About() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">About GITam AI</h1>
                <p className="page-subtitle">Predictive engineering intelligence for better decisions.</p>
            </div>

            <div className="card" style={{ marginBottom: '16px' }}>
                <h3 className="card-title" style={{ marginBottom: '10px' }}>What is GITam AI</h3>
                <p>
                    GITam AI is a platform that reviews GitHub repositories, finds early warning signs,
                    predicts failures up to 90 days ahead, and shows the business impact in simple language.
                </p>
            </div>

            <div className="card" style={{ marginBottom: '16px' }}>
                <h3 className="card-title" style={{ marginBottom: '10px' }}>The Problem</h3>
                <p>
                    Most teams respond after failures happen. That delay increases cost, creates downtime,
                    and affects delivery confidence.
                </p>
            </div>

            <div className="card" style={{ marginBottom: '16px' }}>
                <h3 className="card-title" style={{ marginBottom: '10px' }}>Our Solution</h3>
                <p>
                    GITam AI highlights risk early, ranks what needs attention first, and helps teams act
                    before issues become expensive incidents.
                </p>
            </div>

            <div className="card" style={{ marginBottom: '16px' }}>
                <h3 className="card-title" style={{ marginBottom: '10px' }}>Why It Matters</h3>
                <p>
                    Early action reduces avoidable costs, lowers downtime risk, and gives leaders a clear
                    view of engineering impact on business outcomes.
                </p>
            </div>

            <div className="card">
                <h3 className="card-title" style={{ marginBottom: '10px' }}>Key Features</h3>
                <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)' }}>
                    <li>Risk prediction</li>
                    <li>Code analysis</li>
                    <li>Business impact reports</li>
                    <li>CEO-friendly insights</li>
                </ul>
            </div>
        </div>
    )
}
