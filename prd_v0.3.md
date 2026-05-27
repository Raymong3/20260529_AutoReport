# K-water 보고서 어시스턴트 — PRD (Product Requirements Document)

> **문서 목적**: 바이브코딩(Antigravity 등)으로 개발할 때 AI에게 제공할 기준 문서
> **문서 버전**: v0.3 (Antigravity 요구사항 반영)
> **사용 방법**: 새 작업을 시작할 때마다 이 문서를 AI에게 컨텍스트로 제공

> **v0.3 주요 변경사항**:
> - AI 연동 방식 상세화 (회사 발급 Claude API 토큰 사용 방식 명시) — 5.3절 신설
> - 사용자 역할 명시 (단일 역할, 권한 구분 없음) — 4.4절 신설

> **v0.2 주요 변경사항**:
> - 한글 문서 서식 규칙 추가 (8장 스타일 가이드)
> - 자유도 높은 편집 UI 추가 (4장 F-13~F-15)
> - 프로젝트 핵심 구조 명시 (PRD + 스타일 가이드 이중 구조)

---

## 0. 프로젝트 핵심 구조

이 프로젝트는 두 개의 문서가 두 개의 다른 일을 합니다.

| 문서 | 역할 | 정교화 방법 |
|---|---|---|
| **PRD (이 문서)** | "무엇을 만들지" — 기능, 흐름, 데이터, API | 팀 협의로 사전 확정, 개발 중 v0.x → v1.0 확정 |
| **스타일 가이드 (8장)** | "어떻게 작성할지" — K-water 보고서 톤, 구조, 서식 | 초기 룰 + 사용자 피드백으로 자동 진화 |

두 문서를 정교하게 다듬는 것이 이 프로젝트의 핵심입니다. PRD는 UI/UX 품질을, 스타일 가이드는 결과물 품질을 결정합니다.

---

## 1. 프로젝트 한 줄 정의

K-water 직원이 보고서의 목적과 핵심 내용을 자연어로 입력하면, AI가 회사 보고서 스타일에 맞춰 본문·표·구조를 자동 생성하고 **HWPX 파일로 다운로드**할 수 있게 해주는 웹 기반 보고서 작성 어시스턴트.

---

## 2. 핵심 차별점 (이 점들이 시연 가치를 만든다)

1. **3가지 작성 모드** — "보고서 종류"가 아니라 "작성 방식"으로 분류 (정기 반복 / 양식 기반 / 자유 작성)
2. **HWPX 출력** — DOCX가 아니라 회사가 실제 쓰는 한컴 포맷, 회사 서식 규칙 그대로 적용
3. **대화 + 작업공간 하이브리드 UI** — Claude Artifacts / Cursor 스타일
4. **드래그 선택 + 부분 명령** — Cursor의 Cmd+K처럼 특정 부분만 골라 AI 수정 지시
5. **피드백 학습** — 사용자 피드백이 스타일 규칙에 누적되어 점점 K-water스러워짐

---

## 3. 사용자 흐름 (User Flow)

### 3.1 진입 → 모드 선택
사용자가 처음 들어오면 3가지 카드 중 선택:
- **모드 A 정기 반복**: 기존 HWPX 업로드 → 새 데이터로 갱신
- **모드 B 양식 기반**: 표준 양식 선택/업로드 → 단계별 작성
- **모드 C 자유 작성**: 양식 없이 자유 입력

### 3.2 메인 작업 화면 (좌우 분할)
- **좌측**: AI와의 대화창
- **우측**: 실시간 보고서 미리보기
- 사용자 입력 → AI 응답 → 미리보기 즉시 갱신

### 3.3 작성 흐름 (모드 공통)
1. 사용자가 보고서 목적·핵심 내용을 입력
2. AI가 목차 초안을 생성해 미리보기에 표시
3. AI가 부족한 정보를 2~3개씩 질문
4. 사용자 답변 (필요시 파일 첨부)
5. 모든 정보 모이면 AI가 섹션별 본문 작성
6. **사용자가 결과를 다듬는 3가지 방법**:
   - **(a) 대화창에서 요청** — "3번 섹션 다시 써줘", "전체적으로 더 격식 있게"
   - **(b) 우측에서 드래그 선택 → 명령** — 특정 부분만 골라 "표로", "더 짧게", "직접 명령" 등
   - **(c) 우측에서 직접 인라인 편집** — 한글파일처럼 클릭해서 타이핑 수정
7. **사용자 스타일 피드백** ("문단 더 짧게", "어투는 격식 있게") — 시스템에 누적 학습
8. HWPX 다운로드

---

## 4. 기능 요구사항

### 4.1 Must-Have (반드시 구현)

| ID | 기능 | 설명 |
|---|---|---|
| F-01 | 모드 선택 진입 화면 | 3개 모드 카드 + 선택 UI |
| F-02 | 좌우 분할 워크스페이스 | 대화창 + 실시간 미리보기 |
| F-03 | 멀티턴 AI 대화 | 사용자와 AI의 연속 대화 (컨텍스트 유지) |
| F-04 | 목차·구조 자동 생성 | 입력 정보로부터 보고서 구조 제안 |
| F-05 | 본문 자동 작성 | K-water 스타일 반영 본문 생성 |
| F-06 | 실시간 미리보기 갱신 | 대화 진행에 따라 우측 미리보기 즉시 반영 |
| F-07 | 부분 수정 요청 (대화창) | 자연어로 섹션 단위 재작성 ("3번 섹션 다시") |
| F-08 | **스타일 피드백 학습** | 사용자 피드백을 스타일 규칙 DB에 누적 |
| F-09 | HWPX 다운로드 | 회사 양식에 본문 치환하여 .hwpx 출력 |
| F-10 | 표 자동 삽입 | 데이터형 정보 → 표 형식 변환 |
| F-11 | HWPX 업로드 (모드 A 전용) | 기존 보고서 업로드 → 구조 분석 |
| F-12 | 양식 라이브러리 (모드 B 전용) | 사전 등록된 양식 + 사용자 업로드 양식 |
| F-13 | **드래그 선택 → 부분 명령** | 미리보기에서 텍스트 선택 후 팝업 메뉴로 부분 AI 명령 (Cursor의 Cmd+K 스타일) |

### 4.2 Nice-to-Have (시간 여유 시)

| ID | 기능 | 설명 |
|---|---|---|
| F-14 | **인라인 텍스트 편집** | 미리보기에서 더블클릭 → 직접 타이핑 수정 (contenteditable 기반) |
| F-15 | 작성 이력 저장 및 이어쓰기 | 세션 이력 관리 |
| F-16 | 다운로드 전 PDF 미리보기 | HWPX 변환 전 확인 |
| F-17 | 사용자별 피드백 분리 관리 | 다중 사용자 시 피드백 격리 |

### 4.3 Out of Scope (이번 MVP에서 명시적 제외)
- F-18 한글파일 수준 풀 에디터 (TipTap/Lexical 기반 WYSIWYG) — v1.1 이후
- 사용자 인증·계정 관리
- 사내 시스템 연동
- 이미지 자동 생성
- 다국어 지원
- 사내 보안망 배포

### 4.4 사용자 역할 정의

**이번 MVP는 단일 사용자 역할로 운영됩니다.** 권한 분기 로직을 만들지 않습니다.

| 항목 | 정의 |
|---|---|
| 사용자 역할 | 단일 (작성자) — 작성자·검토자·결재자 구분 없음 |
| 인증 방식 | 없음 (로그인·계정 불필요) |
| 권한 체계 | 없음 (모든 사용자가 모든 기능 사용 가능) |
| 다중 사용자 격리 | 없음 (MVP는 단일 사용자 시나리오 기준) |

**향후 확장 시 검토 사항** (MVP 이후):
- 작성자 / 검토자 / 결재자 권한 분리
- 사내 SSO 연동
- 부서별·직급별 양식·스타일 가이드 분리

> 이 정책은 안티그래비티 등 개발 도구가 불필요한 인증·권한 코드를 생성하지 않도록 명시하기 위함입니다.

---

## 5. 시스템 아키텍처

### 5.1 전체 구성

```
[브라우저: React 프론트엔드]
        ↕ (REST API + WebSocket/SSE)
[FastAPI 백엔드]
   ├── /api/sessions       (작성 세션 CRUD)
   ├── /api/chat           (AI 대화)
   ├── /api/generate       (보고서 본문 생성)
   ├── /api/feedback       (스타일 피드백 저장 → 규칙 학습)
   ├── /api/partial-edit   (드래그 선택 → 부분 AI 명령)
   ├── /api/sections       (인라인 편집 저장, Nice-to-Have)
   ├── /api/upload         (HWPX 업로드, 모드 A)
   ├── /api/templates      (양식 라이브러리, 모드 B)
   ├── /api/export/hwpx    (HWPX 다운로드)
   └── /api/style-rules    (현재 학습된 규칙 조회)
        ↕
[외부 서비스] Claude API (Anthropic)
[저장소]      SQLite or 파일 시스템
              - 세션 상태
              - 스타일 규칙 DB
              - 양식 라이브러리
              - 업로드 파일 임시 저장
```

### 5.2 기술 스택

| 영역 | 선택 | 비고 |
|---|---|---|
| 프론트엔드 | React + Tailwind CSS | Antigravity로 빠른 개발 |
| 상태 관리 | React useState + Context | MVP는 단순 유지 |
| 백엔드 | FastAPI (Python 3.11+) | 비동기 + AI API 친화 |
| AI 호출 | anthropic Python SDK | Claude API 공식 SDK |
| HWPX 처리 | python-hwpx 또는 유사 라이브러리 | 1주차 검증 후 확정 |
| 파일 저장 | 로컬 파일 시스템 | MVP는 단순 유지 |
| 데이터 저장 | SQLite | 단일 파일, 무설치 |
| 배포 | Vercel (프론트) + Railway/Render (백엔드) | 외부망 시연용 |

### 5.3 AI 연동 방식 (LLM API)

**사용 LLM**: Anthropic Claude API
**모델**: Claude Sonnet 또는 Opus (1주차 비용·품질 검증 후 확정)
**SDK**: `anthropic` 공식 Python SDK
**인증 방식**: API 토큰 (회사에서 발급받은 토큰 사용)

#### 5.3.1 API 토큰 관리 원칙
- **토큰 출처**: 회사(K-water)에서 프로젝트용으로 별도 발급한 Claude API 토큰 사용
- **저장 위치**: 백엔드 서버의 환경 변수 `ANTHROPIC_API_KEY` (절대 코드에 하드코딩 금지)
- **프론트엔드 노출 금지**: 토큰은 백엔드에서만 사용. 프론트엔드는 백엔드를 통해서만 AI 호출
- **로컬 개발**: `.env` 파일 사용, `.gitignore`에 반드시 포함
- **배포 환경**: Railway/Render 등 호스팅 플랫폼의 환경 변수 설정 기능 활용

#### 5.3.2 호출 패턴
```python
# 백엔드 코드 예시 (참고용)
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-5",  # 1주차 검증 후 확정
    max_tokens=4096,
    system=system_prompt,  # 8.B 조립 결과
    messages=conversation_history,
)
```

#### 5.3.3 호출 시 고려사항
- **스트리밍**: 본문 생성처럼 긴 응답은 스트리밍 사용 (사용자 대기 시간 단축)
- **컨텍스트 관리**: 멀티턴 대화는 이전 메시지를 누적 전달
- **토큰 사용량 모니터링**: 매 호출의 input/output 토큰 수를 로깅
- **재시도 로직**: 네트워크 오류 시 최대 2회 재시도, 그 외 오류는 사용자에게 안내
- **타임아웃**: 60초 이내 응답 없으면 사용자에게 알림

#### 5.3.4 비용 관리
- 회사 발급 토큰의 한도/소진 정보 사전 확인
- 개발 단계별 누적 사용량을 일 단위로 점검
- 비용 초과 시 임시로 더 저렴한 모델로 전환 가능하도록 설정 분리

---

## 6. 데이터 모델

### 6.1 Session (작성 세션)
한 사용자가 한 보고서를 작성하는 단위.

```
Session
├── id: string (UUID)
├── mode: "A" | "B" | "C"
├── template_id: string | null (모드 B에서 선택한 양식)
├── uploaded_file_path: string | null (모드 A에서 업로드한 파일)
├── messages: Message[] (대화 이력)
├── report_state: ReportState (현재 보고서 상태)
├── created_at: timestamp
└── updated_at: timestamp
```

### 6.2 Message (대화 메시지)
```
Message
├── role: "user" | "assistant" | "system"
├── content: string
├── timestamp: timestamp
└── type: "chat" | "feedback" (피드백 메시지 구분)
```

### 6.3 ReportState (보고서 상태)
```
ReportState
├── title: string
├── sections: Section[]
└── tables: Table[]

Section
├── id: string
├── heading: string (섹션 제목)
├── content: string (본문)
└── order: number

Table
├── id: string
├── caption: string
├── headers: string[]
└── rows: string[][]
```

### 6.4 StyleRule (스타일 규칙 — 핵심 차별점)
사용자 피드백이 누적되어 시스템 프롬프트에 자동 반영되는 학습 규칙. 8.A 스타일 가이드의 각 카테고리에 매핑됨.

```
StyleRule
├── id: string
├── rule_text: string (예: "문단은 3문장 이내로 작성")
├── category: "structure" | "tone" | "expression" | "format" | "taboo"
├── source: "default" | "user_feedback"
├── created_at: timestamp
├── usage_count: number (이 규칙이 적용된 횟수)
└── active: boolean (비활성화 가능)
```

### 6.5 Template (양식 라이브러리)
모드 B에서 사용하는 표준 양식.

```
Template
├── id: string
├── name: string (예: "회의 결과 보고")
├── description: string
├── hwpx_file_path: string (양식 파일 경로)
├── required_fields: Field[] (AI가 사용자에게 물어볼 필수 정보)
└── default_sections: string[] (기본 섹션 구조)

Field
├── key: string (예: "meeting_date")
├── label: string (예: "회의 일시")
├── required: boolean
└── prompt_order: number (질문 순서)
```

---

## 7. API 명세 (핵심 엔드포인트)

### 7.1 POST /api/sessions
새 작성 세션 시작.

**Request**:
```json
{
  "mode": "B",
  "template_id": "meeting_result" // 선택사항
}
```

**Response**:
```json
{
  "session_id": "uuid-here",
  "initial_message": "안녕하세요. 회의 결과 보고서를 만들어드릴게요. 먼저 회의 안건이 무엇인가요?"
}
```

### 7.2 POST /api/sessions/{id}/messages
사용자 메시지 전송 → AI 응답 받기.

**Request**:
```json
{
  "content": "2026년 4월 정기회의, 사이버보안 점검 결과 공유",
  "attachments": [] // 선택사항
}
```

**Response (스트리밍 권장)**:
```json
{
  "message": "...",
  "report_state": { /* 갱신된 ReportState */ },
  "next_action": "ask_question" | "generate_body" | "complete"
}
```

### 7.3 POST /api/sessions/{id}/feedback
스타일 피드백 전달 + 학습 규칙 저장.

**Request**:
```json
{
  "feedback": "문단이 너무 길어요. 3문장 이내로 줄여주세요",
  "apply_to_current": true // 현재 보고서에도 즉시 반영
}
```

**Response**:
```json
{
  "extracted_rule": "문단은 3문장 이내로 작성",
  "category": "structure",
  "regenerated_report": { /* ReportState */ }
}
```

### 7.4 POST /api/sessions/{id}/upload (모드 A)
기존 HWPX 업로드 → 구조 분석.

**Request**: multipart/form-data with file

**Response**:
```json
{
  "structure": {
    "title": "월간 사이버보안 점검 결과 보고",
    "sections": ["1. 점검 개요", "2. 점검 결과", "3. 조치 사항", "4. 향후 계획"],
    "data_fields": ["점검 기간", "점검 대상", "발견 건수"]
  }
}
```

### 7.5 GET /api/templates (모드 B)
양식 라이브러리 목록.

**Response**:
```json
{
  "templates": [
    {
      "id": "meeting_result",
      "name": "회의 결과 보고",
      "description": "정기·수시 회의의 결과를 정리하는 표준 양식"
    },
    // ...
  ]
}
```

### 7.6 GET /api/sessions/{id}/export/hwpx
완성된 보고서를 HWPX로 다운로드.

**Response**: HWPX 바이너리 파일

### 7.7 POST /api/sessions/{id}/partial-edit (F-13: 드래그 선택 → 부분 명령)
사용자가 미리보기에서 텍스트를 선택하고 명령을 내릴 때 호출.

**Request**:
```json
{
  "section_id": "section-3",
  "selected_text": "현재 시설은 노후화되어 잦은 고장이 발생하고 있다",
  "selection_start": 120,
  "selection_end": 152,
  "command": "표로 변환" | "더 짧게" | "격식 있게" | "{자유 입력}"
}
```

**Response**:
```json
{
  "modified_text": "...",
  "report_state": { /* 갱신된 ReportState */ }
}
```

### 7.8 PUT /api/sessions/{id}/sections/{section_id} (F-14: 인라인 편집)
사용자가 직접 편집한 내용 저장 (Nice-to-Have).

**Request**:
```json
{
  "content": "사용자가 직접 수정한 본문 내용"
}
```

### 7.9 GET /api/style-rules
현재 학습된 스타일 규칙 조회 (관리·디버깅용).

**Response**:
```json
{
  "rules": [
    {
      "id": "rule-1",
      "rule_text": "문단은 3문장 이내로 작성",
      "category": "structure",
      "source": "user_feedback",
      "usage_count": 12,
      "active": true
    }
  ]
}
```

---

## 8. AI 프롬프트 구조 + 스타일 가이드

이 장이 결과물 품질을 결정합니다. 두 부분으로 나뉘어요:
- **8.A. 스타일 가이드**: K-water 보고서의 톤·구조·서식 규칙 (시스템 프롬프트의 핵심 재료)
- **8.B. 프롬프트 조립**: AI 호출 시 위 가이드를 어떻게 시스템 프롬프트에 끼워넣는지

---

### 8.A. 스타일 가이드 (K-water 보고서 작성 규칙)

스타일 가이드는 `style_guide/` 폴더에서 관리됩니다.
`base_rules.md`(구조·문체·표현·금기), `format_rules.md`(서식),
`learned_rules.json`(학습 규칙)으로 구성되며,
`backend/services/prompt_builder.py`가 매 호출 시 동적으로 조립합니다.

스타일 가이드를 수정하면 백엔드 재시작 없이 다음 보고서부터 즉시 반영됩니다.

---

### 8.B. 프롬프트 조립 (AI 호출 시 시스템 프롬프트 동적 생성)

모든 AI 호출 시 다음 순서로 시스템 프롬프트를 조립합니다.

```
[1. 페르소나]
당신은 K-water(한국수자원공사) 직원의 보고서 작성을 돕는 AI 어시스턴트입니다.
공공기관 보고서 작성에 익숙한 선배 직원처럼 행동하세요.

[2. 모드별 작업 지시]
{현재 세션의 mode에 따라 다른 텍스트 삽입}

[3. 스타일 가이드 (8.A 전체) ★ 핵심]
다음 스타일 규칙을 반드시 준수하세요.

[구조 규칙]
{StyleRule WHERE category='structure' AND active=true}

[문체 규칙]
{StyleRule WHERE category='tone' AND active=true}

[표현 규칙]
{StyleRule WHERE category='expression' AND active=true}

[서식 규칙 — 본문 작성 시 결정 사항]
{StyleRule WHERE category='format' AND active=true}

[금기 사항]
{StyleRule WHERE category='taboo' AND active=true}

[4. 양식별 필수 정보 (모드 B 전용)]
{Template.required_fields 삽입}

[5. 행동 규칙]
- 한 번에 2~3개 이내로 질문
- 데이터·수치는 표로 정리 제안
- 정보 부족 시 추측하지 말고 사용자에게 질문
- 민감정보 입력 시 마스킹 권유
```

### 8.C. 부분 명령 프롬프트 (F-13 드래그 선택 → 부분 명령용)

사용자가 텍스트를 드래그하고 명령을 내릴 때 사용하는 별도 프롬프트.

```
[Context]
선택된 텍스트: "{selected_text}"
보고서 전체 컨텍스트: "{full_report_summary}"
사용자 명령: "{user_command}"

[작업]
위 선택된 텍스트만 수정하시오. 다음을 준수하시오:
- 8.A 스타일 가이드 전체 규칙
- 수정된 텍스트가 앞뒤 문맥과 자연스럽게 이어져야 함
- 사용자 명령이 모호하면 가장 보편적인 해석을 따름

[Output]
수정된 텍스트만 반환 (다른 설명·주석 없이)
```

### 8.D. 피드백 → 규칙 추출 프롬프트

```
[Input]
사용자 피드백: "{user_feedback_text}"
현재 활성 규칙 목록: {active_rules}

[Output JSON]
{
  "rule_text": "한 줄 규칙",
  "category": "structure" | "tone" | "expression" | "format" | "taboo",
  "conflicts_with": [기존 규칙 ID 배열]
}
```

---

## 9. 핵심 시나리오: End-to-End 예시

**시나리오**: 다솔이 "월간 사이버보안 점검 보고서"를 모드 A로 작성.

1. 진입 → 모드 A 선택
2. 지난달 점검 보고서.hwpx 업로드
3. 백엔드: HWPX 분석 → 구조 추출 ("점검 기간", "점검 대상", "발견 건수" 필드 인식)
4. AI: "지난번 보고서 구조를 분석했어요. 이번 달 데이터를 알려주세요. 점검 기간은요?"
5. 다솔: "2026년 4월, 단양수도지사 정수처리 SCADA·사무망 PC 28대·방화벽 2식"
6. AI: 추가 질문 (발견 사항, 조치 등)
7. 다솔: 답변
8. AI: 본문 자동 작성 → 우측 미리보기 갱신 (서식은 양식 파일이 자동 적용)
9. **(대화창 피드백)** 다솔: "전체적으로 문체가 너무 부드러워. 더 격식 있게"
   - 백엔드: 전체 재생성 + **"문체는 격식체로 통일"이라는 규칙 학습**
10. **(드래그 명령, F-13)** 다솔: 미리보기에서 "발견된 취약점은 다음과 같다..." 부분 드래그 → 팝업에서 "표로 변환" 클릭
    - 백엔드: 해당 텍스트만 표로 재구성하여 그 자리에 갱신
11. **(드래그 자유 명령, F-13)** 다솔: 특정 문단 드래그 → "직접 명령" 선택 → "이 부분에 인용 출처를 추가해줘" 입력
    - 백엔드: 해당 부분만 수정, 다른 부분은 그대로
12. **(인라인 편집, F-14)** 다솔: 우측에서 직접 클릭해 한 단어 오타 수정
13. HWPX 다운로드 → 한컴오피스에서 열어 확인 → 폰트·서식 모두 사내 표준대로

---

## 10. 일정 (4주, 기획서와 동일)

### 1주차: 기반 구축
- PRD 확정, 환경 구축, HWPX 라이브러리 검증
- 백엔드 골격 (Claude 호출 + HWPX 생성 PoC)
- 1주차 끝: "터미널에서 입력 → HWPX 출력" 동작

### 2주차: 모드 B 끝까지
- 모드 B의 수직 슬라이스 완성 (입력 → AI → 미리보기 → HWPX)
- 좌우 분할 UI 완성
- 피드백 학습 기본 동작
- 2주차 끝: "회의 결과 보고서 한 편을 처음부터 끝까지" 가능

### 3주차: 모드 A + C
- 모드 A의 HWPX 업로드·분석 추가
- 모드 C의 자유 작성 추가 (모드 B 코드 재활용)
- 표 자동 삽입 기능
- 3주차 끝: 3개 모드 모두 동작

### 4주차: 발표 준비
- 시연 시나리오 작성 및 리허설
- PPT 작성
- 시연 영상 사전 녹화 (백업)
- 안정성 확보

---

## 11. 리스크와 대응

| 리스크 | 영향도 | 대응 |
|---|---|---|
| HWPX 라이브러리 한계 | 높음 | 1주차 내 검증, DOCX 백업안 준비 |
| HWPX 서식(폰트·크기·자간) 라이브러리 미지원 | 중간 | 빈 양식 파일에 서식 사전 설정 → 본문 텍스트만 치환하는 전략 |
| Claude API 비용 초과 | 중간 | 사전 비용 추정, 회사 지원 확인 |
| 모드 A의 HWPX 구조 분석 난이도 | 중간 | 모드 B 코드 재활용 설계 |
| F-13 드래그 선택 + 부분 명령 구현 복잡도 | 중간 | MVP에서는 "전체 섹션 단위" 부분 명령부터 시작 → 시간 여유 시 임의 텍스트 범위 지원 |
| F-14 인라인 편집 vs AI 재생성 충돌 | 중간 | Nice-to-Have로 분류, AI 재생성 시 사용자 편집 부분 보호 또는 경고 표시 |
| 피드백 학습 충돌 (상반된 규칙 누적) | 중간 | "최근 피드백 우선" 정책 또는 충돌 감지 로직 |
| 시연 환경 인터넷·API 오류 | 높음 | 시연 영상 사전 녹화 + 사전 입력 데이터 준비 |
| 자료 보안 우려 | 중간 | 모든 학습·시연 자료 민감정보 마스킹 |

---

## 12. 작업 개시용 체크리스트

PRD 확정 후 가장 먼저 할 일.

- [ ] GitHub 저장소 생성, README에 PRD 링크
- [ ] 회사 발급 Claude API 토큰 확인 및 환경 변수 설정 (`.env` + `.gitignore` 처리)
- [ ] Python 환경 + FastAPI 셋업
- [ ] Claude API 첫 호출 테스트 ("Hello" 보내고 응답 받기)
- [ ] HWPX 라이브러리 설치 및 첫 PoC ("Hello World"를 HWPX로 출력)
- [ ] **회사 서식 표준이 적용된 빈 양식 HWPX 1종 확보** (HY헤드라인 16pt 등 8.A.4 준수)
- [ ] React 프로젝트 셋업 (Vite + Tailwind)
- [ ] 첫 백엔드 엔드포인트 (`POST /api/echo`) 동작 확인
- [ ] 프론트엔드에서 백엔드 호출 한 번 성공

이 9개가 끝나면 본격 개발 시작.

---

## 부록 A. 바이브코딩 도구에게 줄 첫 메시지 (예시)

새 채팅 시작 시 이렇게 시작하세요.

```
이 PRD 문서를 읽어주세요: [PRD 첨부]

오늘은 1주차 첫 작업으로, 백엔드 골격을 만들 거예요.
가장 단순한 형태로 시작합니다:

1. FastAPI 프로젝트를 /backend 에 생성
2. POST /api/echo 엔드포인트 — 받은 텍스트를 그대로 반환
3. POST /api/generate 엔드포인트 — 받은 텍스트를 Claude API로 보내 응답 받기
4. README에 실행 방법 명시

코드는 최대한 단순하게. 인증·DB·복잡한 구조는 나중에.
완성되면 curl 예시도 보여주세요.
```

이런 식으로 **"작은 한 걸음씩"** 시키는 게 바이브코딩의 핵심.

---

*이 PRD는 v0.3이며, 다솔의 검토 후 v1.0으로 확정됩니다.*
