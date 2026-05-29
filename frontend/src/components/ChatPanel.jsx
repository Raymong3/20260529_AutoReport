import { useState, useRef, useEffect } from 'react'

export default function ChatPanel({ messages, onSend, loading }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSend(input.trim())
    setInput('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="w-2/5 border-r border-slate-200 flex flex-col bg-white">
      <div className="px-4 py-2.5 border-b border-slate-100 bg-slate-50">
        <span className="text-sm font-semibold text-slate-600">AI 대화</span>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-sm lg:max-w-md rounded-2xl px-4 py-2.5 text-base leading-relaxed whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-slate-100 text-slate-800 rounded-bl-sm'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-2.5 text-base text-slate-400">
              작성 중...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-slate-200 flex gap-2 items-end"
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="내용 입력… (Enter 전송 / Shift+Enter 줄바꿈)"
          rows={4}
          className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-base resize-none focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white px-4 py-2.5 rounded-lg text-base font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors h-fit"
        >
          전송
        </button>
      </form>
    </div>
  )
}
