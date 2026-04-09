import { useState, useRef, useEffect } from 'react'

export default function Chatbot({ data, apiBase }) {
    const [open, setOpen] = useState(false)
    const [messages, setMessages] = useState([
        { role: 'bot', text: 'Hey! 👋 I\'m Gitam AI assistant. Ask me anything about this repository\'s health — code quality, bugs, predictions, or recommendations.' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const sendMessage = async () => {
        if (!input.trim() || loading) return
        const userMsg = input.trim()
        setInput('')
        setMessages(prev => [...prev, { role: 'user', text: userMsg }])
        setLoading(true)

        try {
            const res = await fetch(`${apiBase}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: userMsg,
                    repo_url: data.repoUrl,
                }),
            })
            const result = await res.json()
            setMessages(prev => [...prev, { role: 'bot', text: result.answer || 'Sorry, couldn\'t process that.' }])
        } catch (err) {
            setMessages(prev => [...prev, { role: 'bot', text: `Error connecting to server: ${err.message}` }])
        }
        setLoading(false)
    }

    const suggestedQuestions = [
        'What is the overall health of this repo?',
        'Which files are most risky?',
        'What should we fix first?',
        'How many bugs are open?',
    ]

    return (
        <>
            <button className="chat-fab" onClick={() => setOpen(!open)} title="Chat with Gitam AI">
                {open ? '✕' : '💬'}
            </button>

            {open && (
                <div className="chat-panel">
                    <div className="chat-header">
                        <span>🤖 Gitam AI Chat</span>
                        <button onClick={() => setOpen(false)}>✕</button>
                    </div>
                    <div className="chat-messages">
                        {messages.map((msg, i) => (
                            <div key={i} className={`chat-msg ${msg.role}`}>
                                {msg.text}
                            </div>
                        ))}
                        {loading && (
                            <div className="chat-msg bot" style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                                <span className="spinner" style={{ width: '14px', height: '14px' }}></span>
                                Thinking...
                            </div>
                        )}
                        {messages.length === 1 && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Try asking:</span>
                                {suggestedQuestions.map((q, i) => (
                                    <button
                                        key={i}
                                        onClick={() => { setInput(q); }}
                                        style={{
                                            background: 'var(--bg-input)',
                                            border: '1px solid var(--border-subtle)',
                                            borderRadius: '8px',
                                            padding: '6px 10px',
                                            fontSize: '12px',
                                            color: 'var(--text-secondary)',
                                            cursor: 'pointer',
                                            textAlign: 'left',
                                            transition: 'all 0.2s',
                                            fontFamily: 'inherit',
                                        }}
                                        onMouseEnter={(e) => e.target.style.borderColor = 'var(--accent-1)'}
                                        onMouseLeave={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                    <div className="chat-input-area">
                        <input
                            className="input"
                            placeholder="Ask about the analysis..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                        />
                        <button className="btn btn-primary" onClick={sendMessage} disabled={loading}>
                            ↑
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}
