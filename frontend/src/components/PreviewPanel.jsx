import { useState, useRef, useCallback, useEffect } from 'react'

const LINES_PER_PAGE = 29

// ── 자간 자동 조정 ────────────────────────────────────────────
// HWPX _split_line() / _para_body()와 동일한 임계값·로직 사용
const KO_BODY_LINE_0     = 33  // 휴먼명조 15pt 자간 0%  1줄 한글 환산 글자 수
const KO_BODY_LINE_NEG10 = 37  // 휴먼명조 15pt 자간 -10% 1줄 한글 환산 글자 수
const KO_REF_LINE_0      = 37  // 한컴돋움 13pt 자간 0%
const KO_REF_LINE_NEG10  = 41  // 한컴돋움 13pt 자간 -10%
const KO_REF_LINE_NEG20  = 46  // 한컴돋움 13pt 자간 -20% (주관자 블록 강제 1줄용)

function koLen(text) {
  const clean = text.replace(/\*\*([^*]+)\*\*/g, '$1')
  let n = 0
  for (const ch of clean) n += ch.codePointAt(0) > 0x3000 ? 1.0 : 0.5
  return n
}

// 줄을 [접두사, 내용]으로 분리 (마커+라벨 / 나머지)
function splitPrefix(line) {
  let m = line.match(/^(\s*[□◦]\s*(?:\*\*[^*]+\*\*\s*)?)(.*)/)
  if (m && m[1].trim()) return [m[1], m[2]]
  m = line.match(/^(\s*[-*]\s+)(.*)/)
  if (m) return [m[1], m[2]]
  m = line.match(/^(【[^】]+】\s*)(.*)/)
  if (m) return [m[1], m[2]]
  return ['', line]
}

// 내용 길이가 0%~-10% 전환 범위에 딱 해당할 때만 '-0.1em', 그 외 '0'
function calcSpacing(prefix, content, line0, lineN10) {
  const cap0   = line0   - koLen(prefix)
  const capN10 = lineN10 - koLen(prefix)
  const ctnLen = koLen(content)
  return (ctnLen > cap0 && ctnLen <= capN10) ? '-0.1em' : '0'
}

// 주관자 블록용: 0% → -10% → -20% 순으로 단계적 압축해 최대한 1줄 유지
function calcSpacingForced(prefix, content, line0, lineN10, lineN20) {
  const pfxLen = koLen(prefix)
  const cap0   = line0   - pfxLen
  const capN10 = lineN10 - pfxLen
  const ctnLen = koLen(content)
  if (ctnLen <= cap0)   return '0'
  if (ctnLen <= capN10) return '-0.1em'
  return '-0.2em'
}

// ── 인라인 렌더링: 추정 표현 하이라이트 + **bold** ──
const _MARK_STYLE = {
  background: 'rgba(251,191,36,0.15)',
  borderRadius: '2px',
  fontStyle: 'normal',
  color: 'inherit',
}

// 텍스트 안에서 추정 표현을 찾아 <mark> 처리 (볼드 마커 없는 순수 텍스트 대상)
function _highlightPhrases(text, phrases, keyPfx) {
  let segs = [{ text, hi: false }]
  for (const phrase of phrases) {
    if (!phrase || phrase.length < 2) continue
    const next = []
    for (const seg of segs) {
      if (seg.hi) { next.push(seg); continue }
      let rem = seg.text, found = false, idx
      while ((idx = rem.indexOf(phrase)) !== -1) {
        found = true
        if (idx > 0) next.push({ text: rem.slice(0, idx), hi: false })
        next.push({ text: phrase, hi: true })
        rem = rem.slice(idx + phrase.length)
      }
      next.push({ text: rem, hi: found ? false : seg.hi })
    }
    segs = next
  }
  return segs.map((seg, si) =>
    seg.hi ? <mark key={`${keyPfx}h${si}`} style={_MARK_STYLE}>{seg.text}</mark> : seg.text
  )
}

// __ALL__ 모드에서 사용자 제공 표현은 하이라이트 제외
function _highlightAllExcept(text, excludePhrases, keyPfx) {
  let segs = [{ text, excluded: false }]
  for (const phrase of excludePhrases) {
    if (!phrase || phrase.length < 2) continue
    const next = []
    for (const seg of segs) {
      if (seg.excluded) { next.push(seg); continue }
      let rem = seg.text, found = false, idx
      while ((idx = rem.indexOf(phrase)) !== -1) {
        found = true
        if (idx > 0) next.push({ text: rem.slice(0, idx), excluded: false })
        next.push({ text: phrase, excluded: true })
        rem = rem.slice(idx + phrase.length)
      }
      next.push({ text: rem, excluded: found ? false : seg.excluded })
    }
    segs = next
  }
  return segs.map((seg, si) =>
    seg.excluded || !seg.text
      ? seg.text
      : <mark key={`${keyPfx}x${si}`} style={_MARK_STYLE}>{seg.text}</mark>
  )
}

function renderInline(text, estimatedPhrases = [], userProvided = []) {
  const isAll = estimatedPhrases.includes('__ALL__')

  // 1단계: 볼드 마커로 먼저 분리
  const boldParts = text.split(/(\*\*[^*]+\*\*)/g)

  return boldParts.flatMap((part, bi) => {
    if (!part) return []
    const isBold = part.startsWith('**') && part.endsWith('**')
    const inner = isBold ? part.slice(2, -2) : part

    // 2단계: 하이라이트 적용
    let content
    if (isAll && userProvided.length > 0) {
      content = _highlightAllExcept(inner, userProvided, `${bi}`)
    } else if (isAll) {
      content = <mark key={`m${bi}`} style={_MARK_STYLE}>{inner}</mark>
    } else if (estimatedPhrases.length > 0) {
      content = _highlightPhrases(inner, estimatedPhrases, `${bi}`)
    } else {
      content = inner
    }

    if (isBold) {
      return [<strong key={`b${bi}`}>{content}</strong>]
    }
    return Array.isArray(content) ? content : [content]
  })
}

// ── 줄 타입 분류 ──────────────────────────────
function classifyLine(line) {
  if (line.startsWith('[요약]'))                       return 'summary'
  if (/^\d+\.\s/.test(line))                           return 'section'
  if (line.startsWith('□'))                            return 'bullet1'
  if (/^\s+◦/.test(line))                             return 'bullet2'
  if (/^\s+-/.test(line))                              return 'bullet3'
  if (/^\s*\*/.test(line))                            return 'ref'
  if (line.startsWith('【'))                          return 'presummary'  // 주관자 블록 (강제 1줄)
  if (/^\[\[TABLE:[^\]]+\]\]$/.test(line.trim()))     return 'table'
  if (line.trim() === '')                              return 'empty'
  return 'body'
}

// ── 표 미리보기 렌더링 ────────────────────────
function renderTablePreview(tableData, idx) {
  const thStyle = {
    border: '1px solid #000',
    backgroundColor: '#F2F2F2',
    padding: '4pt 6pt',
    textAlign: 'center',
    fontFamily: "'휴먼명조', serif",
    fontSize: '13pt',
    fontWeight: 'normal',
  }
  const tdStyle = {
    border: '1px solid #000',
    padding: '4pt 6pt',
    textAlign: 'center',
    fontFamily: "'휴먼명조', serif",
    fontSize: '12pt',
  }
  return (
    <div key={idx} style={{ margin: '6pt 0 8pt' }}>
      {tableData.caption && (
        <div style={{
          fontFamily: "'휴먼명조', serif",
          fontSize: '14pt',
          lineHeight: '160%',
          marginBottom: '3pt',
          textAlign: 'center',
        }}>
          {'【 ' + tableData.caption + ' 】'}
        </div>
      )}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {tableData.headers.map((h, i) => <th key={i} style={thStyle}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => <td key={ci} style={tdStyle}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── 줄 → JSX 렌더링 ──────────────────────────
function renderLine(line, type, idx, tables = {}, estimated = [], userProvided = []) {
  const ri = (text) => renderInline(text, estimated, userProvided)
  const bodyBase = {
    fontFamily: "'휴먼명조', 'HumanMyeongjo', serif",
    fontSize: '15pt',
    lineHeight: '160%',
    color: '#000',
    whiteSpace: 'pre-wrap',
  }

  switch (type) {
    case 'section':
      return (
        <div key={idx} style={{
          fontFamily: "'HY헤드라인M', 'HYHeadLineM', sans-serif",
          fontSize: '16pt',
          fontWeight: 'bold',
          color: '#000',
          marginTop: '6pt',
          marginBottom: '2pt',
          lineHeight: '160%',
        }}>
          {ri(line)}
        </div>
      )
    case 'bullet1': {
      const [pfx, ctn] = splitPrefix(line)
      const cs = calcSpacing(pfx, ctn, KO_BODY_LINE_0, KO_BODY_LINE_NEG10)
      return (
        <div key={idx} style={bodyBase}>
          <span style={{letterSpacing: '0'}}>{ri(pfx)}</span>
          <span style={{letterSpacing: cs}}>{ri(ctn)}</span>
        </div>
      )
    }
    case 'bullet2': {
      const [pfx, ctn] = splitPrefix(line)
      const cs = calcSpacing(pfx, ctn, KO_BODY_LINE_0, KO_BODY_LINE_NEG10)
      return (
        <div key={idx} style={{ ...bodyBase, paddingLeft: '1em' }}>
          <span style={{letterSpacing: '0'}}>{ri(pfx.trimStart())}</span>
          <span style={{letterSpacing: cs}}>{ri(ctn)}</span>
        </div>
      )
    }
    case 'bullet3': {
      const [pfx, ctn] = splitPrefix(line)
      const cs = calcSpacing(pfx, ctn, KO_BODY_LINE_0, KO_BODY_LINE_NEG10)
      return (
        <div key={idx} style={{ ...bodyBase, paddingLeft: '2em' }}>
          <span style={{letterSpacing: '0'}}>{ri(pfx.trimStart())}</span>
          <span style={{letterSpacing: cs}}>{ri(ctn)}</span>
        </div>
      )
    }
    case 'ref': {
      const [pfx, ctn] = splitPrefix(line)
      const cs = calcSpacing(pfx, ctn, KO_REF_LINE_0, KO_REF_LINE_NEG10)
      return (
        <div key={idx} style={{
          fontFamily: "'중고딕', 'JoongGoThic', sans-serif",
          fontSize: '13pt',
          color: '#444',
          paddingLeft: '1em',
          lineHeight: '160%',
        }}>
          <span style={{letterSpacing: '0'}}>{ri(pfx.trimStart())}</span>
          <span style={{letterSpacing: cs}}>{ri(ctn)}</span>
        </div>
      )
    }
    case 'presummary': {
      return (
        <div key={idx} style={{
          fontFamily: "'한컴돋움', '중고딕', 'JoongGoThic', sans-serif",
          fontSize: '13pt',
          lineHeight: '160%',
          color: '#000',
          whiteSpace: 'pre-wrap',
          letterSpacing: '-0.1em',
        }}>
          {renderInline(line)}
        </div>
      )
    }
    case 'table': {
      const m = line.trim().match(/^\[\[TABLE:([^\]]+)\]\]$/)
      const tableId = m?.[1]
      const tableData = tables?.[tableId]
      if (!tableData) {
        return (
          <div key={idx} style={{
            border: '1px dashed #aaa',
            padding: '6pt 10pt',
            color: '#888',
            fontSize: '12pt',
            fontFamily: 'sans-serif',
            margin: '4pt 0',
          }}>
            [표 데이터 없음: {tableId}]
          </div>
        )
      }
      return renderTablePreview(tableData, idx)
    }
    case 'empty':
      return <div key={idx} style={{ height: '0.6em' }} />
    default: {
      const ctnLen = koLen(line)
      const cs = (ctnLen > KO_BODY_LINE_0 && ctnLen <= KO_BODY_LINE_NEG10) ? '-0.1em' : '0'
      return (
        <div key={idx} style={{ ...bodyBase, letterSpacing: cs }}>
          {ri(line)}
        </div>
      )
    }
  }
}

// ── 콘텐츠 파싱 ───────────────────────────────
// 순서: 제목 → 주관자 블록(선택) → [요약] → 본문
function parseContent(content) {
  if (!content) return { title: '', preSummaryLines: [], summary: '', summaryRefs: '', bodyLines: [] }
  const allLines = content.split('\n')
  let title = ''
  const preSummaryLines = []  // 주관자·날짜 블록 (요약 앞)
  const summaryLines = []
  const summaryRefLines = []  // * 참고줄 (요약 박스 안, 중고딕 13pt)
  const bodyLines = []
  let state = 'title' // title → pre_summary → summary → body

  for (let i = 0; i < allLines.length; i++) {
    const line = allLines[i]
    const trimmed = line.trim()

    if (state === 'title') {
      title = trimmed
      state = 'pre_summary'
      continue
    }

    if (state === 'pre_summary') {
      if (trimmed === '' && preSummaryLines.length === 0) continue  // 제목 직후 빈 줄 무시
      if (trimmed.startsWith('[요약]')) {
        // 끝부분 빈 줄 제거
        while (preSummaryLines.length && preSummaryLines[preSummaryLines.length - 1].trim() === '')
          preSummaryLines.pop()
        const rest = trimmed.replace(/^\[요약\]\s*/, '')
        if (rest) summaryLines.push(rest)
        state = 'summary'
        continue
      }
      preSummaryLines.push(line)  // 주관자 블록 등
      continue
    }

    if (state === 'summary') {
      if (trimmed === '') { state = 'body'; continue }
      // 본문 시작이 확실한 마커 → body 전환
      if (/^\d+\./.test(trimmed) || trimmed.startsWith('□') ||
          trimmed.startsWith('【') || /^\s+◦/.test(line) || /^\s+-/.test(line)) {
        state = 'body'; bodyLines.push(line); continue
      }
      // 요약 불릿: ◈·ㅁ 외에 AI가 쓸 수 있는 ◆·◇도 포함
      if (/^[◈ㅁ◆◇]/.test(trimmed)) {
        summaryLines.push(trimmed); continue
      }
      // * 참고줄 → 요약 박스 안에 포함
      if (/^\s*\*/.test(line)) {
        summaryRefLines.push(trimmed); continue
      }
      // 그 외 → 이전 불릿의 continuation (긴 줄이 다음 줄로 이어진 경우)
      if (summaryLines.length > 0) {
        summaryLines[summaryLines.length - 1] += ' ' + trimmed
      } else {
        state = 'body'; bodyLines.push(line)
      }
      continue
    }

    bodyLines.push(line)
  }

  while (bodyLines.length && bodyLines[0].trim() === '') bodyLines.shift()
  return { title, preSummaryLines, summary: summaryLines.join('\n'), summaryRefs: summaryRefLines.join('\n'), bodyLines }
}

// ── 페이지 분할 ───────────────────────────────
// tables를 받아 [[TABLE:X]] 마커는 실제 행 수만큼 시각적 줄로 계산
// page1Capacity: 첫 페이지는 제목·요약 박스 때문에 실제 담을 수 있는 줄이 더 적음
function splitPages(bodyLines, tables = {}, page1Capacity = LINES_PER_PAGE) {
  function visualLines(line) {
    const m = line.trim().match(/^\[\[TABLE:([^\]]+)\]\]$/)
    if (m) {
      const t = tables[m[1]]
      if (t) {
        const rowCount = (t.rows?.length ?? 0) + 1  // 헤더 1 + 데이터 행
        return rowCount + 2  // 캡션(1) + 행 + 여백(1)
      }
      return 3  // 표 데이터 없음 → 기본 3줄
    }
    return 1
  }

  const pages = []
  let currentPage = []
  let currentCount = 0
  let capacity = page1Capacity

  for (const line of bodyLines) {
    const vl = visualLines(line)
    if (currentCount > 0 && currentCount + vl > capacity) {
      pages.push(currentPage)
      currentPage = [line]
      currentCount = vl
      capacity = LINES_PER_PAGE  // 2페이지부터는 정상 용량
    } else {
      currentPage.push(line)
      currentCount += vl
    }
  }
  if (currentPage.length > 0) pages.push(currentPage)
  return pages.length ? pages : [[]]
}

// ── 직접 수정 모드: 표 블록 확장 / 파싱 ──────
// [[TABLE:t1]] → 사람이 읽고 수정할 수 있는 텍스트 블록으로 변환
function expandTablesForEdit(text, tables) {
  return text.replace(/\[\[TABLE:([^\]]+)\]\]/g, (_, id) => {
    const t = tables[id]
    if (!t) return `[[TABLE:${id}]]`
    return [
      `[TABLE_EDIT:${id}]`,
      `제목: ${t.caption ?? ''}`,
      `헤더: ${(t.headers ?? []).join(' | ')}`,
      ...(t.rows ?? []).map(row => row.join(' | ')),
      `[/TABLE_EDIT:${id}]`,
    ].join('\n')
  })
}

// [TABLE_EDIT:t1] 블록을 파싱해 [[TABLE:t1]] 마커와 tables 데이터로 복원
function parseTablesFromEdit(editedText) {
  const tables = {}
  const text = editedText.replace(
    /\[TABLE_EDIT:(\w+)\]\n([\s\S]*?)\[\/TABLE_EDIT:\1\]/g,
    (_, id, body) => {
      const lines = body.split('\n').filter(l => l.trim() !== '')
      let caption = '', hi = 0
      if (lines[0]?.startsWith('제목:')) {
        caption = lines[0].slice('제목:'.length).trim()
        hi = 1
      }
      const hLine = lines[hi] ?? ''
      const headers = (hLine.startsWith('헤더:') ? hLine.slice('헤더:'.length) : hLine)
        .split('|').map(h => h.trim())
      const rows = lines.slice(hi + 1).map(l => l.split('|').map(c => c.trim()))
      tables[id] = { caption, headers, rows }
      return `[[TABLE:${id}]]`
    }
  )
  return { text, tables }
}

// ── 메인 컴포넌트 ─────────────────────────────
export default function PreviewPanel({ content, pages: requestedPages = 1, tables = {}, estimated = [], userProvided = [], onPartialEdit, onDirectEdit }) {
  const [toolbar, setToolbar]           = useState(null)   // { top, left, text, rects } | null
  const [instruction, setInstruction]   = useState('')
  const [isEditing, setIsEditing]       = useState(false)
  const [editContent, setEditContent]   = useState('')     // 직접 수정 모드 textarea 내용
  const [boxDismissed, setBoxDismissed] = useState(false)
  const toolbarRef                      = useRef(null)
  const instrRef                        = useRef(null)

  // estimated가 새로 들어오면 박스 다시 표시
  useEffect(() => { setBoxDismissed(false) }, [estimated])

  // 외부 클릭 & Escape → 툴바 닫기
  useEffect(() => {
    if (!toolbar) return
    const onMouseDown = (e) => {
      if (toolbarRef.current && !toolbarRef.current.contains(e.target)) {
        setToolbar(null)
        setInstruction('')
      }
    }
    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        setToolbar(null)
        setInstruction('')
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onMouseDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [toolbar])

  // 마우스 업 → 선택 텍스트 캡처 + 커스텀 하이라이트 저장
  const handleMouseUp = useCallback(() => {
    if (!onPartialEdit || isEditing) return
    setTimeout(() => {
      const sel = window.getSelection()
      const text = sel?.toString().trim()
      if (!text || text.length < 3) return
      const range  = sel.getRangeAt(0)
      const rect   = range.getBoundingClientRect()
      // 각 줄의 화면 좌표를 저장해 커스텀 하이라이트로 사용
      const rects  = Array.from(range.getClientRects())
      const left   = Math.min(Math.max(rect.left, 16), window.innerWidth - 316)
      // 브라우저 selection은 즉시 해제 — 이후 하이라이트는 overlay div가 담당
      sel.removeAllRanges()
      setToolbar({ top: rect.bottom + 8, left, text, rects })
      setInstruction('')
    }, 10)
  }, [onPartialEdit, isEditing])

  // 수정 제출
  const handleSubmit = () => {
    if (!instruction.trim() || !toolbar) return
    onPartialEdit(instruction.trim(), toolbar.text)
    setToolbar(null)
    setInstruction('')
  }

  const totalLines = content ? content.split('\n').length : 0
  const maxLines   = requestedPages * LINES_PER_PAGE
  const isOver     = totalLines > maxLines

  const { title, preSummaryLines, summary, summaryRefs, bodyLines } = parseContent(content)
  const hasEstimated = estimated.length > 0

  // 첫 페이지 용량: 제목 박스·주관자 블록·요약 박스가 차지하는 줄 수만큼 감소
  // 실제 content 줄 수 기준으로 계산 (시각적 과대평가 방지)
  const page1Overhead = content
    ? (title ? 1 : 0)
      + preSummaryLines.filter(l => l.trim()).length
      + (summary ? summary.split('\n').filter(l => l.trim()).length : 0)
      + (summaryRefs ? summaryRefs.split('\n').filter(l => l.trim()).length : 0)
      + ((title || summary) ? 1 : 0)   // 헤더와 본문 사이 빈 줄 1개
    : 0
  const page1Capacity = Math.max(5, LINES_PER_PAGE - page1Overhead)
  const pageChunks = splitPages(bodyLines, tables, page1Capacity)

  return (
    <div className="flex-1 bg-slate-200 flex flex-col overflow-hidden relative">
      {/* 선택 영역 하이라이트 오버레이 (브라우저 selection 대신 직접 그림) */}
      {toolbar?.rects.map((r, i) => (
        <div key={i} style={{
          position: 'fixed',
          top:    r.top,
          left:   r.left,
          width:  r.width,
          height: r.height,
          backgroundColor: 'rgba(59, 130, 246, 0.22)',
          pointerEvents: 'none',
          zIndex: 40,
        }} />
      ))}

      {/* 플로팅 툴바 */}
      {toolbar && (
        <div
          ref={toolbarRef}
          className="fixed z-50 bg-white border-2 border-blue-400 rounded-xl shadow-2xl p-4"
          style={{ top: toolbar.top, left: toolbar.left, width: 380 }}
        >
          <div className="text-sm font-bold text-blue-600 mb-2">
            ✏️ 선택 텍스트 수정
          </div>
          <div className="text-sm text-gray-500 bg-gray-50 rounded p-2.5 mb-3 max-h-20 overflow-y-auto leading-relaxed">
            "{toolbar.text.length > 70 ? toolbar.text.slice(0, 70) + '…' : toolbar.text}"
          </div>
          <textarea
            ref={instrRef}
            value={instruction}
            onChange={e => setInstruction(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }
            }}
            placeholder="수정 지시사항 입력... (Enter 전송)"
            className="w-full text-base border border-gray-200 rounded-lg p-2.5 resize-none h-20 focus:outline-none focus:border-blue-400"
          />
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleSubmit}
              disabled={!instruction.trim()}
              className="flex-1 bg-blue-600 text-white text-sm font-semibold py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              수정 →
            </button>
            <button
              onClick={() => { setToolbar(null); setInstruction('') }}
              className="px-4 text-sm font-medium text-gray-400 hover:text-gray-600 transition-colors"
            >
              취소
            </button>
          </div>
        </div>
      )}

      {/* 헤더 바 */}
      <div className="px-6 py-2.5 border-b border-slate-300 bg-white flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-base font-bold text-slate-700">보고서 미리보기</span>
          {onPartialEdit && content && !isEditing && (
            <span className="text-base font-semibold text-blue-500">· 드래그 → 부분 수정</span>
          )}
          {isEditing && (
            <span className="text-sm text-amber-500 font-semibold">· 직접 수정 모드</span>
          )}
          {hasEstimated && !isEditing && (
            <span className="text-xs font-semibold px-2 py-1 rounded bg-amber-100 text-amber-700 border border-amber-300">
              ⚠️ {estimated.includes('__ALL__') ? 'AI 전체 작성' : 'AI 임의 작성 포함'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {onDirectEdit && content && (
            <button
              onClick={() => {
                if (isEditing) {
                  // 완료: 파싱 후 부모에 반영
                  const { text, tables: newTables } = parseTablesFromEdit(editContent)
                  onDirectEdit(text, newTables)
                  setIsEditing(false)
                } else {
                  // 진입: 표 마커를 편집 가능한 블록으로 확장
                  setEditContent(expandTablesForEdit(content, tables))
                  setIsEditing(true)
                }
              }}
              className={`text-sm font-semibold px-4 py-2 rounded transition-colors ${
                isEditing
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isEditing ? '✅ 완료' : '✏️ 직접 수정'}
            </button>
          )}
          {content && (
            <span className={`text-sm px-3 py-1 rounded font-semibold ${
              isOver ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-700'
            }`}>
              {totalLines}줄 / {maxLines}줄 ({requestedPages}p)
              {isOver ? ' · 초과' : ' · 적합'}
            </span>
          )}
        </div>
      </div>

      {/* 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto py-8 px-6 space-y-10" onMouseUp={handleMouseUp}>
        {content && isEditing ? (
          /* 직접 수정 모드: A4 비율 textarea */
          <div>
            <div className="text-center text-xs text-amber-600 mb-1">
              텍스트를 직접 수정한 후 ✅ 완료를 클릭하세요
            </div>
            <div className="text-center text-xs text-slate-400 mb-2">
              표는 <code className="bg-slate-100 px-1 rounded">[TABLE_EDIT:id]</code> 블록으로 표시됩니다 · 셀 구분: <code className="bg-slate-100 px-1 rounded"> | </code>
            </div>
            <div
              className="mx-auto bg-white shadow-md"
              style={{ width: '210mm', boxSizing: 'border-box' }}
            >
              <textarea
                value={editContent}
                onChange={e => setEditContent(e.target.value)}
                spellCheck={false}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '297mm',
                  padding: '15mm 20mm',
                  boxSizing: 'border-box',
                  fontFamily: "'휴먼명조', 'HumanMyeongjo', serif",
                  fontSize: '13pt',
                  lineHeight: '180%',
                  color: '#000',
                  backgroundColor: '#FEFCE8',  /* 연한 노란 배경 — 편집 중 표시 */
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  whiteSpace: 'pre-wrap',
                }}
              />
            </div>
          </div>
        ) : content ? (
          <>
              {pageChunks.map((pageLines, pgIdx) => (
            <div key={pgIdx}>
              {/* 페이지 번호 */}
              <div className="text-center text-xs text-slate-500 mb-2 flex items-center justify-center gap-2">
                <span>{pgIdx + 1} / {pageChunks.length} 페이지</span>
                {pgIdx >= requestedPages && (
                  <span className="text-red-400 font-semibold">▲ 초과 페이지</span>
                )}
              </div>

              {/* A4 용지 */}
              <div
                className={`mx-auto bg-white shadow-md ${
                  pgIdx >= requestedPages ? 'ring-2 ring-red-400' : ''
                }`}
                style={{
                  width: '210mm',
                  minHeight: '297mm',
                  boxSizing: 'border-box',
                  padding: '15mm 20mm 15mm 20mm',
                }}
              >
                {/* 첫 페이지: 제목 박스 + 요약 박스 */}
                {pgIdx === 0 && title && (
                  <>
                    {/* 제목 박스 — template_box_head_01 디자인
                        borderFill id=5: top/bottom solid #0099FF 2mm, fill #FFFFFF→#CCFFFF */}
                    <div style={{
                      borderTop: '3px solid #0099FF',
                      borderBottom: '3px solid #0099FF',
                      borderLeft: 'none',
                      borderRight: 'none',
                      background: 'linear-gradient(to bottom, #FFFFFF 0%, #CCFFFF 100%)',
                      padding: '8pt 14pt',
                      textAlign: 'center',
                      marginBottom: '8pt',
                      fontFamily: "'HY헤드라인M', 'HYHeadLineM', 'NanumGothic', sans-serif",
                      fontSize: '20pt',
                      fontWeight: 'bold',
                      color: '#000',
                      lineHeight: '140%',
                    }}>
                      {title}
                    </div>

                    {/* 주관자·날짜 블록 — 제목 박스와 요약 박스 사이 (중고딕 13pt) */}
                    {preSummaryLines.length > 0 && (
                      <div style={{ marginBottom: '6pt' }}>
                        {preSummaryLines.map((line, i) => renderLine(line, classifyLine(line), `pre-${i}`))}
                      </div>
                    )}

                    {/* 요약 박스 — template_box_summary_01 디자인
                        border: #99CCFF / fill: #F1F1F1→#FFFFFF gradient / bullet: ◈ */}
                    <div style={{
                      border: '1px solid #99CCFF',
                      background: 'linear-gradient(160deg, #F1F1F1 0%, #FFFFFF 100%)',
                      padding: '8pt 14pt',
                      marginBottom: '10pt',
                      fontFamily: "'휴먼명조', 'HumanMyeongjo', 'NanumMyeongjo', serif",
                      fontSize: '14pt',
                      lineHeight: '160%',
                      color: '#000',
                    }}>
                      {summary
                        ? summary.split('\n').map((line, i) => {
                            const text = line.replace(/^[ㅁ◈◆◇]\s*/, '')
                            return (
                              <div key={i} style={{ marginTop: i > 0 ? '4pt' : 0 }}>
                                ◈ {renderInline(text, estimated, userProvided)}
                              </div>
                            )
                          })
                        : <div style={{ color: '#aaa' }}>◈ 요약 없음</div>
                      }
                      {summaryRefs && summaryRefs.split('\n').map((line, i) => {
                        const text = line.replace(/^\*\s*/, '')
                        return (
                          <div key={`ref-${i}`} style={{
                            fontFamily: "'중고딕', 'JoongGoThic', sans-serif",
                            fontSize: '13pt',
                            color: '#444',
                            marginTop: '4pt',
                          }}>
                            * {renderInline(text, estimated, userProvided)}
                          </div>
                        )
                      })}
                    </div>
                  </>
                )}

                {/* 본문 줄 */}
                {pageLines.map((line, i) => {
                  const type = classifyLine(line)
                  return renderLine(line, type, i, tables, estimated, userProvided)
                })}
              </div>
            </div>
              ))}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm gap-2 pt-20">
            <svg className="w-10 h-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <span>왼쪽 대화창에서 보고서 내용을 입력하면</span>
            <span>페이지별로 미리보기가 표시됩니다</span>
          </div>
        )}
      </div>

      {/* A4 왼쪽 gray 영역 중앙 플로팅 알림 박스 */}
      {hasEstimated && !isEditing && !boxDismissed && (
        <div style={{
          position: 'absolute',
          right: 'calc(50% + 105mm + 16px)',
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 20,
          width: '175px',
        }}>
          <div style={{
            background: '#FFFBEB',
            borderLeft: '5px solid #F59E0B',
            borderRadius: '12px',
            boxShadow: '0 6px 20px rgba(0,0,0,0.18)',
            padding: '18px 16px',
            position: 'relative',
          }}>
            {/* X 버튼 */}
            <button
              onClick={() => setBoxDismissed(true)}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '14px',
                color: '#B45309',
                lineHeight: 1,
                padding: '2px 4px',
                borderRadius: '4px',
              }}
              title="닫기"
            >
              ✕
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', paddingRight: '16px' }}>
              <span style={{ fontSize: '22px', lineHeight: 1 }}>⚠️</span>
              <span style={{ fontSize: '15px', fontWeight: 800, color: '#92400E', lineHeight: 1.2 }}>
                {estimated.includes('__ALL__') ? 'AI 전체 작성' : 'AI 임의 작성 포함'}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#92400E', lineHeight: '1.7', margin: 0 }}>
              {estimated.includes('__ALL__')
                ? '본문 전체가 AI가 임의로 작성한 내용입니다. 검토 후 수정이 필요합니다.'
                : '노란 박스 표시 부분은 사용자가 제공하지 않아 AI가 임의로 채운 내용입니다. 검토 후 수정하세요.'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
