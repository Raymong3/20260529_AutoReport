import { useState, useEffect, useRef } from 'react'
import ChatPanel from './ChatPanel'
import PreviewPanel from './PreviewPanel'

// Vite 프록시 우회 — /api/generate 는 백엔드에 직접 연결
const API_BASE = 'http://127.0.0.1:8000'

const MODE_LABEL = { A: '정기 반복', B: '양식 기반', C: '자유 작성' }

const WELCOME = {
  A: '기존 HWPX 파일을 업로드하거나, 갱신할 보고서의 목적과 핵심 내용을 알려주세요.',
  B: '어떤 양식의 보고서를 작성할까요? (예: 회의 결과 보고, 월간 점검 결과 등)',
  C: '보고서의 목적과 핵심 내용을 자유롭게 입력해주세요.',
}

function loadState(mode) {
  try {
    const saved = localStorage.getItem(`kw_ws_${mode}`)
    if (saved) return JSON.parse(saved)
  } catch {}
  return null
}

export default function Workspace({ mode, onBack }) {
  const saved = loadState(mode)

  const [messages, setMessages] = useState(
    saved?.messages ?? [{ role: 'assistant', content: WELCOME[mode] }]
  )
  const [report, setReport]       = useState(saved?.report ?? '')
  const [tables, setTables]       = useState(saved?.tables ?? {})
  const [isMock, setIsMock]       = useState(saved?.isMock ?? false)
  const [pages, setPages]         = useState(saved?.pages ?? 1)
  const [loading, setLoading]     = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [elapsed, setElapsed]     = useState(0)
  const timerRef                  = useRef(null)

  // 상태 변경될 때마다 localStorage에 저장
  useEffect(() => {
    localStorage.setItem(`kw_ws_${mode}`, JSON.stringify({ messages, report, tables, isMock, pages }))
  }, [messages, report, tables, isMock, pages, mode])

  // loading 상태에 따라 타이머 시작/정지
  useEffect(() => {
    if (loading) {
      setElapsed(0)
      timerRef.current = setInterval(() => {
        setElapsed(prev => prev + 1)
      }, 1000)
    } else {
      clearInterval(timerRef.current)
      setElapsed(0)
    }
    return () => clearInterval(timerRef.current)
  }, [loading])

  async function handleDownload() {
    if (!report) return
    setDownloading(true)
    const reportTitle  = report.split('\n')[0].trim() || '보고서'
    const safeFilename = reportTitle.replace(/[\\/:*?"<>|]/g, '_') + '.hwpx'
    try {
      const res = await fetch('/api/export/hwpx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: report, title: reportTitle, tables }),
      })
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        let detail = `서버 오류: ${res.status}`
        try { detail = JSON.parse(text).detail || detail } catch {}
        console.error('HWPX export 실패:', res.status, text)
        throw new Error(detail)
      }
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href = url
      a.download = safeFilename
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert(`다운로드에 실패했습니다.\n${err.message}`)
    }
    setDownloading(false)
  }

  async function handlePartialEdit(instruction, selectedText) {
    const preview = selectedText.length > 40
      ? selectedText.slice(0, 40) + '…'
      : selectedText
    const updated = [
      ...messages,
      { role: 'user', content: `[선택 텍스트 수정]\n"${preview}"\n\n${instruction}` },
    ]
    setMessages(updated)
    setLoading(true)

    const controller = new AbortController()
    const clientTimeout = setTimeout(() => controller.abort(), 130_000)

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: instruction, currentReport: report, selectedText }),
        signal: controller.signal,
      })
      clearTimeout(clientTimeout)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(err.detail || `서버 오류 (${res.status})`)
      }
      const data = await res.json()
      if (data.is_report !== false) {
        setReport(data.content)
        setTables(prev => {
          const merged = { ...prev, ...(data.tables ?? {}) }
          for (const key of Object.keys(merged)) {
            if (!data.content.includes(`[[TABLE:${key}]]`)) delete merged[key]
          }
          return merged
        })
        setIsMock(data.mock)
        setPages(data.pages ?? 1)
        const lineCount = data.content.split('\n').length
        const maxLines  = (data.pages ?? 1) * 29
        setMessages([
          ...updated,
          {
            role: 'assistant',
            content: `선택한 부분을 수정했습니다. (${lineCount}줄 / 최대 ${maxLines}줄)\n우측에서 확인해주세요.`,
          },
        ])
      } else {
        setMessages([...updated, { role: 'assistant', content: data.content }])
      }
    } catch (err) {
      clearTimeout(clientTimeout)
      const msg = err.name === 'AbortError'
        ? 'AI 응답 시간 초과(130초). 다시 시도해주세요.'
        : err.message
      setMessages([
        ...updated,
        { role: 'assistant', content: `오류가 발생했습니다.\n${msg}` },
      ])
    }

    setLoading(false)
  }

  async function handleSend(text) {
    const updated = [...messages, { role: 'user', content: text }]
    setMessages(updated)
    setLoading(true)

    // 클라이언트 측 130초 타임아웃 (백엔드 2분보다 10초 여유)
    const controller = new AbortController()
    const clientTimeout = setTimeout(() => controller.abort(), 130_000)

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, currentReport: report }),
        signal: controller.signal,
      })
      clearTimeout(clientTimeout)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(err.detail || `서버 오류 (${res.status})`)
      }
      const data = await res.json()
      if (data.is_report !== false) {
        // 보고서 → 우측 패널 업데이트
        const wasEditing = report !== ''
        setReport(data.content)
        // 기존 table 데이터 보존: 새 content에 마커가 남아있으면 기존 데이터 유지,
        // AI가 새 TABLE_DATA를 반환하면 덮어씀, 마커가 사라진 표는 제거
        setTables(prev => {
          const merged = { ...prev, ...(data.tables ?? {}) }
          for (const key of Object.keys(merged)) {
            if (!data.content.includes(`[[TABLE:${key}]]`)) delete merged[key]
          }
          return merged
        })
        setIsMock(data.mock)
        setPages(data.pages ?? 1)
        const lineCount = data.content.split('\n').length
        const maxLines  = (data.pages ?? 1) * 29
        setMessages([
          ...updated,
          {
            role: 'assistant',
            content: data.mock
              ? '샘플 보고서를 생성했습니다. (목업 모드)\n우측에서 확인해주세요.'
              : wasEditing
              ? `보고서를 수정했습니다. (${lineCount}줄 / 최대 ${maxLines}줄)\n우측에서 확인 후 추가 수정 사항을 말씀해주세요.`
              : `보고서 초안을 작성했습니다. (${lineCount}줄 / 최대 ${maxLines}줄)\n우측에서 확인 후 수정 사항을 말씀해주세요.`,
          },
        ])
      } else {
        // 질문/대화 → 채팅에만 표시, 보고서 패널 유지
        setMessages([...updated, { role: 'assistant', content: data.content }])
      }
    } catch (err) {
      clearTimeout(clientTimeout)
      const msg = err.name === 'AbortError'
        ? 'AI 응답 시간 초과(130초). 다시 시도해주세요.'
        : err.message
      setMessages([
        ...updated,
        {
          role: 'assistant',
          content: `오류가 발생했습니다.\n${msg}\n\n백엔드 서버(포트 8000)가 실행 중인지 확인해주세요.`,
        },
      ])
    }

    setLoading(false)
  }

  // 진행 바: 90초 기준, 최대 95%까지 채움
  const progressPct = loading ? Math.min(95, (elapsed / 90) * 100) : 0
  const progressLabel = elapsed < 5
    ? 'AI 연결 중...'
    : elapsed < 30
    ? `보고서 작성 중... (${elapsed}초)`
    : `마무리 중... (${elapsed}초)`

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-blue-800 text-white px-6 py-3 flex items-center gap-3 shrink-0">
        <button
          onClick={onBack}
          className="text-blue-200 hover:text-white text-sm transition-colors"
        >
          ← 모드 선택
        </button>
        <span className="text-blue-400">|</span>
        <span className="font-semibold">K-water 보고서 어시스턴트</span>
        <span className="text-blue-300 text-sm">
          모드 {mode} · {MODE_LABEL[mode]}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
          report ? 'bg-amber-400 text-amber-900' : 'bg-green-400 text-green-900'
        }`}>
          {report ? '수정 모드' : '작성 모드'}
        </span>

        <div className="ml-auto flex items-center gap-3">
          {/* 새 보고서 버튼 */}
          <button
            onClick={() => {
              if (!window.confirm('현재 작업 내용을 초기화하고 새로 시작할까요?')) return
              localStorage.removeItem(`kw_ws_${mode}`)
              setMessages([{ role: 'assistant', content: WELCOME[mode] }])
              setReport('')
              setTables({})
              setIsMock(false)
              setPages(1)
            }}
            className="text-blue-200 hover:text-white text-sm transition-colors"
          >
            새 보고서
          </button>
          <span className="text-blue-600">|</span>
          {/* 진행 표시 */}
          {loading && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-blue-200 whitespace-nowrap">{progressLabel}</span>
              <div className="w-32 h-2 bg-blue-900 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-300 rounded-full transition-all duration-1000"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <span className="text-xs text-blue-300 w-8 text-right">
                {Math.round(progressPct)}%
              </span>
            </div>
          )}

          {isMock && !loading && (
            <span className="text-xs bg-amber-500 text-white px-2 py-0.5 rounded">
              목업
            </span>
          )}
          <button
            onClick={handleDownload}
            disabled={!report || downloading || loading}
            className="bg-white text-blue-800 text-sm px-4 py-1.5 rounded hover:bg-blue-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {downloading ? '생성 중...' : 'HWPX 다운로드'}
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <ChatPanel messages={messages} onSend={handleSend} loading={loading} />
        <PreviewPanel
          content={report}
          pages={pages}
          tables={tables}
          onPartialEdit={report && !loading ? handlePartialEdit : undefined}
          onDirectEdit={report && !loading ? (text, newTables) => {
            setReport(text)
            if (newTables !== undefined) setTables(newTables)
          } : undefined}
        />
      </div>
    </div>
  )
}
