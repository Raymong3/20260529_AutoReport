const LINES_PER_PAGE = 29

// ── 인라인 **bold** 파싱 ──────────────────────
function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

// ── 줄 타입 분류 ──────────────────────────────
function classifyLine(line) {
  if (line.startsWith('[요약]'))      return 'summary'
  if (/^\d+\.\s/.test(line))          return 'section'
  if (line.startsWith('□'))           return 'bullet1'
  if (/^\s+◦/.test(line))            return 'bullet2'
  if (/^\s+-/.test(line))             return 'bullet3'
  if (/^\s+\*/.test(line))           return 'ref'
  if (line.trim() === '')             return 'empty'
  return 'body'
}

// ── 줄 → JSX 렌더링 ──────────────────────────
function renderLine(line, type, idx) {
  const bodyStyle = {
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
          {line}
        </div>
      )
    case 'bullet1':
      return (
        <div key={idx} style={bodyStyle}>
          {renderInline(line)}
        </div>
      )
    case 'bullet2':
      return (
        <div key={idx} style={{ ...bodyStyle, paddingLeft: '1em' }}>
          {renderInline(line.trimStart())}
        </div>
      )
    case 'bullet3':
      return (
        <div key={idx} style={{ ...bodyStyle, paddingLeft: '2em' }}>
          {renderInline(line.trimStart())}
        </div>
      )
    case 'ref':
      return (
        <div key={idx} style={{
          fontFamily: "'중고딕', 'JoongGoThic', sans-serif",
          fontSize: '13pt',
          color: '#444',
          paddingLeft: '1em',
          lineHeight: '160%',
        }}>
          {line.trimStart()}
        </div>
      )
    case 'empty':
      return <div key={idx} style={{ height: '0.6em' }} />
    default:
      return (
        <div key={idx} style={bodyStyle}>
          {renderInline(line)}
        </div>
      )
  }
}

// ── 콘텐츠 파싱 ───────────────────────────────
// 요약 형식: [요약] ㅁ 첫 문단 / ㅁ 두 번째 문단 (최대 2개)
function parseContent(content) {
  if (!content) return { title: '', summary: '', bodyLines: [] }
  const allLines = content.split('\n')
  let title = ''
  const summaryLines = []
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
      if (trimmed === '') continue  // 제목 뒤 빈 줄 무시
      if (trimmed.startsWith('[요약]')) {
        const rest = trimmed.replace(/^\[요약\]\s*/, '')
        if (rest) summaryLines.push(rest)  // [요약] ㅁ ... 형식
        state = 'summary'
        continue
      }
      state = 'body'  // [요약] 없으면 바로 본문
      bodyLines.push(line)
      continue
    }

    if (state === 'summary') {
      if (trimmed === '') { state = 'body'; continue }  // 빈 줄 = 요약 끝
      if (trimmed.startsWith('ㅁ')) {
        summaryLines.push(trimmed)  // 추가 ㅁ 문단
        continue
      }
      state = 'body'  // ㅁ 아닌 줄 = 본문 시작
      bodyLines.push(line)
      continue
    }

    bodyLines.push(line)
  }

  while (bodyLines.length && bodyLines[0].trim() === '') bodyLines.shift()
  return { title, summary: summaryLines.join('\n'), bodyLines }
}

// ── 페이지 분할 (29줄 기준) ───────────────────
function splitPages(bodyLines) {
  const pages = []
  for (let i = 0; i < bodyLines.length; i += LINES_PER_PAGE) {
    pages.push(bodyLines.slice(i, i + LINES_PER_PAGE))
  }
  return pages.length ? pages : [[]]
}

// ── 메인 컴포넌트 ─────────────────────────────
export default function PreviewPanel({ content, pages: requestedPages = 1 }) {
  const totalLines = content ? content.split('\n').length : 0
  const maxLines   = requestedPages * LINES_PER_PAGE
  const isOver     = totalLines > maxLines

  const { title, summary, bodyLines } = parseContent(content)
  const pageChunks = splitPages(bodyLines)

  return (
    <div className="flex-1 bg-slate-200 flex flex-col overflow-hidden">
      {/* 헤더 바 */}
      <div className="px-6 py-2.5 border-b border-slate-300 bg-white flex items-center justify-between shrink-0">
        <span className="text-xs font-medium text-slate-500">보고서 미리보기</span>
        {content && (
          <span className={`text-xs px-2 py-0.5 rounded font-medium ${
            isOver ? 'bg-red-50 text-red-500' : 'bg-green-50 text-green-600'
          }`}>
            {totalLines}줄 / {maxLines}줄 ({requestedPages}p)
            {isOver ? ' · 초과' : ' · 적합'}
          </span>
        )}
      </div>

      {/* 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto py-8 px-6 space-y-10">
        {content ? (
          pageChunks.map((pageLines, pgIdx) => (
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
                    {/* 제목 박스 */}
                    <div style={{
                      border: '2px solid #1a3a6b',
                      padding: '8pt 12pt',
                      textAlign: 'center',
                      marginBottom: '6pt',
                      fontFamily: "'HY헤드라인M', 'HYHeadLineM', sans-serif",
                      fontSize: '22pt',
                      fontWeight: 'bold',
                      color: '#1a3a6b',
                      lineHeight: '140%',
                    }}>
                      {title}
                    </div>

                    {/* 요약 박스 */}
                    {summary && (
                      <div style={{
                        border: '1px solid #B8D4EC',
                        background: '#EAF2FA',
                        padding: '8pt 14pt',
                        marginBottom: '10pt',
                        fontFamily: "'휴먼명조', 'HumanMyeongjo', serif",
                        fontSize: '15pt',
                        lineHeight: '160%',
                        color: '#000',
                      }}>
                        {summary.split('\n').map((line, i) => (
                          <div key={i} style={{ marginTop: i > 0 ? '4pt' : 0 }}>
                            {renderInline(line)}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {/* 본문 줄 */}
                {pageLines.map((line, i) => {
                  const type = classifyLine(line)
                  return renderLine(line, type, i)
                })}
              </div>
            </div>
          ))
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
    </div>
  )
}
