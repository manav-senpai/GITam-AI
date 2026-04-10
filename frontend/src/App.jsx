import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import CodeReview from './pages/CodeReview'
import Report from './pages/Report'
import Home from './pages/Home'
import Chatbot from './components/Chatbot'
import './index.css'

const API_BASE = 'http://localhost:8000'

function App() {
  const [analysisData, setAnalysisData] = useState(null)
  const [repoUrl, setRepoUrl] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('gitam-theme') || 'light')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('gitam-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  const parseRepoUrl = (url) => {
    const clean = url.trim().replace(/\/$/, '')
    const parts = clean.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
    if (parts.length >= 2) return { owner: parts[0], repo: parts[1] }
    return null
  }

  const startAnalysis = async (url) => {
    const repoInfo = parseRepoUrl(url)
    if (!repoInfo) {
      alert('Please enter a valid GitHub URL (e.g., https://github.com/pallets/flask)')
      return
    }

    setRepoUrl(url)
    setAnalyzing(true)
    setProgress({ step: 0, total: 6, agent: 'Initializing', status: 'Starting analysis...', progress: 0 })

    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: url, days: 180 }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          try {
            const data = JSON.parse(line.replace('data: ', ''))
            setProgress(data)

            if (data.done) {
              const dashRes = await fetch(`${API_BASE}/api/dashboard/${repoInfo.owner}/${repoInfo.repo}`)
              const dashData = await dashRes.json()
              const reportRes = await fetch(`${API_BASE}/api/report/${repoInfo.owner}/${repoInfo.repo}`)
              const reportData = await reportRes.json()

              setAnalysisData({
                ...dashData,
                report: reportData,
                repoUrl: url,
                owner: repoInfo.owner,
                repo: repoInfo.repo,
              })
              setAnalyzing(false)
              setProgress(null)
            }

            if (data.error) {
              alert(`Error: ${data.error}`)
              setAnalyzing(false)
              setProgress(null)
            }
          } catch (e) { /* skip */ }
        }
      }
    } catch (err) {
      alert(`Failed to connect to backend: ${err.message}. Make sure the backend is running on port 8000.`)
      setAnalyzing(false)
      setProgress(null)
    }
  }

  const agentSteps = [
    { name: 'Data Collector', desc: 'Connecting to GitHub...' },
    { name: 'Code Analyzer', desc: 'Analyzing code churn...' },
    { name: 'Bug Analyzer', desc: 'Mining bug patterns...' },
    { name: 'Health Scorer', desc: 'Computing health scores...' },
    { name: 'Predictor', desc: 'Predicting failures...' },
    { name: 'Report Generator', desc: 'Writing CEO report...' },
  ]

  return (
    <Router>
      {analyzing && progress && (
        <div className="progress-overlay">
          <div className="progress-card">
            <div style={{ fontSize: '44px', marginBottom: '14px' }}>🔬</div>
            <h2>Analyzing Repository</h2>
            <p>{progress.status}</p>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${progress.progress || 0}%` }}></div>
            </div>
            <div className="progress-steps">
              {agentSteps.map((step, i) => {
                const stepNum = i + 1
                const isActive = progress.step === stepNum
                const isDone = progress.step > stepNum
                return (
                  <div key={i} className={`progress-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
                    <div className="progress-step-icon">
                      {isDone ? '✓' : isActive ? '◉' : '○'}
                    </div>
                    <span><strong>{step.name}</strong> — {step.desc}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      <nav className="navbar">
        <NavLink to="/" className="navbar-brand" style={{ textDecoration: 'none' }}>
          <div className="navbar-logo">G</div>
          <div>
            <div className="navbar-title">GITam AI</div>
            <div className="navbar-subtitle">Predictive Engineering Intelligence</div>
          </div>
        </NavLink>
        <div className="navbar-right">
          <div className="navbar-links">
            <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              🏠 Home
            </NavLink>
            {analysisData && (
              <>
                <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  📊 Dashboard
                </NavLink>
                <NavLink to="/code-review" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  🔍 Code Review
                </NavLink>
                <NavLink to="/report" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  📋 Report
                </NavLink>
              </>
            )}
          </div>
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Home onAnalyze={startAnalysis} analysisData={analysisData} />} />
        <Route path="/dashboard" element={<Dashboard data={analysisData} />} />
        <Route path="/code-review" element={<CodeReview data={analysisData} apiBase={API_BASE} />} />
        <Route path="/report" element={<Report data={analysisData} apiBase={API_BASE} />} />
      </Routes>

      {/* Chatbot - only shows when analysis is done */}
      {analysisData && <Chatbot data={analysisData} apiBase={API_BASE} />}
    </Router>
  )
}

export default App
