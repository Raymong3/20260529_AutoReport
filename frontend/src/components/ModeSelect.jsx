const MODES = [
  {
    id: 'A',
    title: '정기 반복',
    desc: '기존 HWPX 업로드 후 새 데이터로 갱신',
    badge: '모드 A',
  },
  {
    id: 'B',
    title: '양식 기반',
    desc: '표준 양식을 선택하고 단계별로 작성',
    badge: '모드 B',
  },
  {
    id: 'C',
    title: '자유 작성',
    desc: '양식 없이 목적과 내용을 자유롭게 입력',
    badge: '모드 C',
  },
]

export default function ModeSelect({ onSelect }) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-8">
      <div className="mb-12 text-center">
        <div className="text-sm font-semibold text-blue-600 tracking-widest uppercase mb-3">
          K-water
        </div>
        <h1 className="text-3xl font-bold text-slate-800 mb-2">
          보고서 어시스턴트
        </h1>
        <p className="text-slate-500">작성 방식을 선택해주세요</p>
      </div>

      <div className="grid grid-cols-3 gap-5 w-full max-w-2xl">
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => onSelect(m.id)}
            className="bg-white border border-slate-200 rounded-xl p-6 text-left hover:border-blue-400 hover:shadow-md transition-all group"
          >
            <span className="inline-block text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded mb-4">
              {m.badge}
            </span>
            <div className="font-semibold text-slate-800 mb-1 group-hover:text-blue-700">
              {m.title}
            </div>
            <div className="text-sm text-slate-500">{m.desc}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
