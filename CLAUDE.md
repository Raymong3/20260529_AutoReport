# K-water 보고서 어시스턴트 — 프로젝트 컨텍스트

이 파일은 Claude Code가 매 세션마다 자동으로 읽는 프로젝트 헌법입니다.
상세 명세는 `PRD.md` 참조. 보고서 스타일 가이드는 `style_guide/` 폴더 참조.
이 파일에는 항상 적용되어야 할 핵심 원칙만 둡니다.

---

## 프로젝트 한 줄 정의

K-water 직원이 자연어로 보고서를 작성하고 HWPX 파일로 다운로드받게 해주는 웹 어시스턴트.

## 핵심 차별점 (절대 잊지 말 것)

1. 3가지 작성 모드: 정기 반복(A) / 양식 기반(B) / 자유 작성(C)
2. 출력은 반드시 **HWPX** (DOCX 아님)
3. 좌측 대화 + 우측 실시간 미리보기
4. 드래그 선택 → 부분 AI 명령 (Cursor의 Cmd+K 스타일)
5. 사용자 피드백이 `style_guide/learned_rules.json`에 누적 학습

## 기술 스택 (고정, 임의로 바꾸지 말 것)

- 백엔드: **FastAPI (Python 3.11+)**, anthropic SDK
- 프론트엔드: **React + Vite + Tailwind CSS**
- AI: **Anthropic Claude API**, 환경변수 `ANTHROPIC_API_KEY` 사용
- HWPX 생성: 자체 모듈 `services/hwpx_generator.py`

## 폴더 구조 (이 구조 유지)

```
kwater-report-assistant/
├── CLAUDE.md           ← 이 파일 (Claude Code 자동 로드)
├── PRD.md              ← 무엇을 만들지 (기능·API·데이터 명세)
├── README.md           ← 프로젝트 소개, 실행 방법
├── .env                ← API 키 등 (.gitignore에 포함)
├── .env.example        ← 환경변수 템플릿
├── .gitignore
│
├── style_guide/        ← 보고서 작성 규칙 (단일 진실 공급원) ★
│   ├── README.md
│   ├── base_rules.md       (구조·문체·표현·금기, 사람이 작성·수정)
│   ├── format_rules.md     (한글 서식·폰트·크기)
│   └── learned_rules.json  (사용자 피드백 누적, 자동 갱신)
│
├── backend/
│   ├── main.py                  (FastAPI 엔트리, 라우터만)
│   ├── services/
│   │   ├── prompt_builder.py    (style_guide/ 읽어 시스템 프롬프트 조립) ★
│   │   ├── ai_service.py        (Claude API 호출)
│   │   ├── hwpx_generator.py    (HWPX 생성)
│   │   └── template_analyzer.py (양식 분석, 모드 A용)
│   ├── templates/
│   │   ├── box/                 (헤드·요약 박스 HWPX)
│   │   │   ├── head_01.hwpx
│   │   │   └── summary_01.hwpx
│   │   └── form/                (모드 B용 보고서 양식, 향후)
│   ├── requirements.txt
│   └── venv/
│
└── frontend/
    ├── src/
    ├── public/
    ├── package.json
    └── vite.config.js
```

## 절대 원칙 (어기지 말 것)

### 1. 단일 진실 공급원 (Single Source of Truth)

| 정보 | 단일 출처 |
|---|---|
| 무엇을 만들지 | `PRD.md` |
| 보고서 작성 규칙 | `style_guide/` 폴더 |
| 프로젝트 핵심 컨벤션 | 이 파일 (CLAUDE.md) |

**같은 정보가 두 곳에 있으면 안 됨. 다른 곳에서는 가리키기만 할 것.**

특히 보고서 스타일 가이드 텍스트를 백엔드 코드에 절대 하드코딩하지 말 것.
모든 시스템 프롬프트는 `services/prompt_builder.py`가 `style_guide/`에서 동적으로 조립.

### 2. 박스 템플릿 분리

보고서의 헤드(제목)와 요약 블록은 별도 HWPX 박스 템플릿으로 처리:
- 헤드: `backend/templates/box/head_01.hwpx`
- 요약: `backend/templates/box/summary_01.hwpx`

AI는 텍스트만 생성, 백엔드가 해당 부분을 감지하여 박스로 감쌈.
박스 디자인 변경은 위 HWPX 파일만 교체 (코드 수정 불필요).

### 3. 회사 발급 토큰 사용

- API 키는 환경변수 `ANTHROPIC_API_KEY`에만 저장
- 절대 코드에 하드코딩 금지
- `.env` 파일은 반드시 `.gitignore`에 포함

### 4. MVP 범위 엄수

다음은 명시적으로 Out of Scope (요청받아도 만들지 말 것):
- 사용자 인증·계정 관리
- 사내 시스템 연동
- 이미지 자동 생성
- 다국어 지원
- 한글파일 수준 풀 에디터 (TipTap/Lexical) — v1.1 이후
- 사내 보안망 배포

상세는 PRD.md 4.3, 4.4 참조.

## 작업 원칙

1. **수직 슬라이스 우선**: 한 모드를 끝까지 동작시킨 뒤 다음 모드로. 완벽도보다 통합 우선.
2. **백엔드 골격부터**: UI 예쁘게 만들기 전에 "터미널에서 입력 → HWPX 출력" 동작 확인.
3. **PRD에 없는 결정은 사용자에게 먼저 확인**: 임의로 결정하지 말 것.
4. **파일 이동·삭제 전 git commit**: 안전망 확보 후 작업.

## 코드 컨벤션

- Python: PEP 8, type hint 적극 사용
- 모든 public 함수에 docstring (한국어 OK)
- 변수·함수명은 영어, 주석·문서·UI 텍스트는 한국어
- 커밋 메시지: 한국어 OK, 어떤 기능인지 명확히
- 새 의존성 추가 시 requirements.txt 또는 package.json 즉시 업데이트

## 시스템 프롬프트 조립 방식 (참고)

`services/prompt_builder.py`의 동작:

1. `style_guide/base_rules.md` 읽기
2. `style_guide/format_rules.md` 읽기
3. `style_guide/learned_rules.json`의 active=true 규칙 카테고리별 정리
4. 위 내용 + 페이지 수에 따른 분량 제한 텍스트 조립
5. 시스템 프롬프트 문자열 반환

이 함수가 `ai_service.py`에서 매 Claude API 호출 시 사용됨.
스타일 가이드 파일을 수정하면 백엔드 재시작 없이 다음 호출부터 즉시 반영됨.

## Claude Code 작업 시 확인할 것

- 어떤 작업이든 시작 전에 PRD.md의 해당 섹션 한 번 읽기
- 보고서 스타일 관련 작업은 반드시 `style_guide/` 파일에 반영 (코드에 하드코딩 금지)
- 새 기능 만들 때 PRD에 정의되지 않은 결정은 사용자(다솔)에게 먼저 확인
- 파일 위치가 위 폴더 구조와 다르면 사용자에게 보고 후 정리 제안
