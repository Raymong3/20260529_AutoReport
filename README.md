# K-water 보고서 어시스턴트

K-water 직원이 보고서의 목적과 핵심 내용을 자연어로 입력하면, AI가 회사 보고서 스타일에 맞춰 본문·표·구조를 자동 생성하고 **HWPX 파일로 다운로드**할 수 있게 해주는 웹 기반 보고서 작성 어시스턴트.

상세 명세: [prd_v0.3.md](./prd_v0.3.md)

---

## 개발 서버 실행 (터미널 2개 필요)

### 터미널 1 — 백엔드

```powershell
cd backend
venv\Scripts\uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 터미널 2 — 프론트엔드

```powershell
cd frontend
npm run dev
```

브라우저에서 http://localhost:5173 접속

> ANTHROPIC_API_KEY가 없으면 목업 모드로 동작합니다.
> 실제 AI 연동은 `.env` 파일에 키 설정 후 백엔드 재시작.

---

## 최초 환경 설정

```powershell
# .env 설정
copy .env.example .env
# .env 열어 ANTHROPIC_API_KEY 입력

# 백엔드 패키지 (최초 1회)
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 프론트엔드 패키지 (최초 1회)
cd ..\frontend
npm install
```

---

## 프로젝트 구조

```
.
├── .env.example
├── .gitignore
├── prd_v0.3.md
├── README.md
├── backend/
│   ├── main.py            # FastAPI 서버 (POST /api/echo, /api/generate)
│   ├── requirements.txt
│   └── venv/              # git 제외
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── ModeSelect.jsx   # 모드 선택 화면
    │       ├── Workspace.jsx    # 좌우 분할 워크스페이스
    │       ├── ChatPanel.jsx    # 좌측 AI 대화창
    │       └── PreviewPanel.jsx # 우측 보고서 미리보기
    └── vite.config.js     # Tailwind + /api 프록시 설정
```

---

## 1주차 체크리스트 (PRD 12장)

- [x] `.gitignore`, `.env.example` 생성
- [x] Python 환경 + FastAPI 셋업
- [x] `POST /api/echo` 엔드포인트 동작 확인
- [x] `POST /api/generate` 목업 모드 구현
- [x] React 프로젝트 셋업 (Vite + Tailwind)
- [x] 프론트엔드 → 백엔드 호출 구조 완성
- [ ] Claude API 실제 연동 (API 키 준비 후)
- [ ] HWPX 라이브러리 설치 및 PoC
- [ ] 회사 서식 표준 적용된 빈 양식 HWPX 1종 확보
