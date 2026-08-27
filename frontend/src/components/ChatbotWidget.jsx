import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import './ChatbotWidget.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Small sub-components ────────────────────────────────────────────────────

function TypingIndicator() {
    return (
        <div className="chatbot-msg bot">
            <div className="chatbot-typing">
                <span /><span /><span />
            </div>
        </div>
    )
}

function SchemeCard({ scheme }) {
    return (
        <div className="chatbot-scheme-card">
            <div className="chatbot-scheme-name">{scheme.name}</div>
            {scheme.description && (
                <div className="chatbot-scheme-desc">{scheme.description}</div>
            )}
            <div className="chatbot-scheme-meta">
                {scheme.category_name && (
                    <span className="chatbot-scheme-tag">{scheme.category_name}</span>
                )}
                {scheme.state_code && (
                    <span className="chatbot-scheme-tag green">{scheme.state_code}</span>
                )}
                {!scheme.state_code && (
                    <span className="chatbot-scheme-tag green">National</span>
                )}
            </div>
            <Link
                className="chatbot-scheme-link"
                to={`/schemes/${scheme.id}`}
                onClick={() => { }}
            >
                View Full Details →
            </Link>
        </div>
    )
}

// ── Message types ──────────────────────────────────────────────────────────

function BotMessage({ content }) {
    return (
        <div className="chatbot-msg bot">
            <div className="chatbot-msg-bubble">{content}</div>
        </div>
    )
}

function UserMessage({ content }) {
    return (
        <div className="chatbot-msg user">
            <div className="chatbot-msg-bubble">{content}</div>
        </div>
    )
}

// ── Main widget ─────────────────────────────────────────────────────────────

export default function ChatbotWidget() {
    const [open, setOpen] = useState(false)
    const [faqs, setFaqs] = useState([])
    const [expandedFaq, setExpandedFaq] = useState(null)
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const bodyRef = useRef(null)

    // Load FAQ chips on first open
    useEffect(() => {
        if (!open || faqs.length > 0) return
        fetch(`${API}/api/v1/chatbot/faqs`)
            .then((r) => r.json())
            .then((data) => setFaqs(data.faqs || []))
            .catch(() => { })
    }, [open, faqs.length])

    // Greet on first open
    useEffect(() => {
        if (open && messages.length === 0) {
            setMessages([
                {
                    id: 'welcome',
                    type: 'bot-intro',
                    text: '👋 Hi! I can help you find the right government scholarship or scheme. Type your question below or tap a common question to get started.',
                },
            ])
        }
    }, [open, messages.length])

    // Auto-scroll to bottom
    useEffect(() => {
        if (bodyRef.current) {
            bodyRef.current.scrollTop = bodyRef.current.scrollHeight
        }
    }, [messages, loading])

    const sendQuery = async (question) => {
        if (!question.trim() || loading) return

        const userMsg = { id: Date.now(), type: 'user', text: question }
        setMessages((prev) => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await fetch(`${API}/api/v1/chatbot/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            })
            const data = await res.json()

            if (data.matched) {
                const botMsgs = []

                if (data.answer) {
                    botMsgs.push({ id: Date.now() + 1, type: 'bot', text: data.answer })
                }

                if (data.scheme) {
                    botMsgs.push({
                        id: Date.now() + 2,
                        type: 'bot-scheme',
                        scheme: data.scheme,
                    })
                }

                if (botMsgs.length === 0) {
                    botMsgs.push({
                        id: Date.now() + 1,
                        type: 'bot',
                        text: 'I found a match but no details are available. Try browsing the Schemes page.',
                    })
                }

                setMessages((prev) => [...prev, ...botMsgs])
            } else {
                const suggestions = data.suggestions || []
                setMessages((prev) => [
                    ...prev,
                    {
                        id: Date.now() + 1,
                        type: 'bot-no-match',
                        text: "I couldn't find a strong match for that question. Here are some things you can ask:",
                        suggestions,
                    },
                ])
            }
        } catch {
            setMessages((prev) => [
                ...prev,
                {
                    id: Date.now() + 1,
                    type: 'bot',
                    text: '⚠️ Something went wrong. Please try again.',
                },
            ])
        } finally {
            setLoading(false)
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendQuery(input)
        }
    }

    const renderMessage = (msg) => {
        switch (msg.type) {
            case 'user':
                return <UserMessage key={msg.id} content={msg.text} />

            case 'bot':
                return <BotMessage key={msg.id} content={msg.text} />

            case 'bot-intro':
                return (
                    <div key={msg.id} className="chatbot-msg bot">
                        <div className="chatbot-msg-bubble">{msg.text}</div>
                    </div>
                )

            case 'bot-scheme':
                return (
                    <div key={msg.id} className="chatbot-msg bot">
                        <div style={{ maxWidth: '98%' }}>
                            <SchemeCard scheme={msg.scheme} />
                        </div>
                    </div>
                )

            case 'bot-no-match':
                return (
                    <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <BotMessage content={msg.text} />
                        {msg.suggestions && msg.suggestions.length > 0 && (
                            <div className="chatbot-suggestions">
                                {msg.suggestions.map((s, i) => (
                                    <button
                                        key={i}
                                        className="chatbot-suggestion-btn"
                                        onClick={() => sendQuery(s)}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )

            default:
                return null
        }
    }

    return (
        <>
            {/* Floating toggle button */}
            <button
                id="chatbot-toggle-btn"
                className="chatbot-toggle"
                onClick={() => setOpen((o) => !o)}
                aria-label={open ? 'Close chatbot' : 'Open chatbot'}
                title="Ask about schemes &amp; scholarships"
            >
                {open ? '✕' : '💬'}
            </button>

            {/* Panel */}
            {open && (
                <div className="chatbot-panel" role="dialog" aria-label="Scheme Chatbot">
                    {/* Header */}
                    <div className="chatbot-header">
                        <div className="chatbot-header-info">
                            <div className="chatbot-avatar">🤖</div>
                            <div>
                                <h3>Scheme Assistant</h3>
                            </div>
                        </div>
                        <button
                            className="chatbot-close"
                            onClick={() => setOpen(false)}
                            aria-label="Close"
                        >
                            ✕
                        </button>
                    </div>

                    {/* FAQ chips */}
                    {faqs.length > 0 && (
                        <div style={{ padding: '12px 16px 0', flexShrink: 0 }}>
                            <div className="chatbot-faq-label">Common questions</div>
                            <div className="chatbot-chips" style={{ marginTop: 8, marginBottom: 2 }}>
                                {faqs.slice(0, 8).map((faq) => (
                                  <div className="chatbot-faq-item" key={faq.id}>
                                    <button
                                        className="chatbot-chip chatbot-faq-question"
                                        onClick={() => setExpandedFaq((current) => current === faq.id ? null : faq.id)}
                                        aria-expanded={expandedFaq === faq.id}
                                    >
                                        {faq.question.length > 55
                                            ? faq.question.slice(0, 52) + '…'
                                            : faq.question}
                                    </button>
                                    {expandedFaq === faq.id && (
                                        <div className="chatbot-faq-answer">{faq.answer}</div>
                                    )}
                                  </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Conversation */}
                    <div className="chatbot-body" ref={bodyRef}>
                        {messages.map(renderMessage)}
                        {loading && <TypingIndicator />}
                    </div>

                    {/* Input */}
                    <div className="chatbot-input-row">
                        <textarea
                            id="chatbot-input"
                            className="chatbot-input"
                            rows={1}
                            placeholder="Type your question…"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={loading}
                            aria-label="Type your question"
                        />
                        <button
                            id="chatbot-send-btn"
                            className="chatbot-send"
                            onClick={() => sendQuery(input)}
                            disabled={loading || !input.trim()}
                            aria-label="Send"
                        >
                            ➤
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}
