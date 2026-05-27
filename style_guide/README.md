# 스타일 가이드 (Style Guide)

이 폴더는 K-water 보고서 작성 시 AI가 따라야 할 규칙을 관리합니다.

## 파일 구조

```
style_guide/
├── README.md          ← 이 파일
├── base_rules.md      ← 보고서 구조·문체·표현 규칙 (사람이 작성·수정)
├── format_rules.md    ← 한글 서식 규칙 (폰트·크기 등)
└── learned_rules.json ← 사용자 피드백으로 누적 학습된 규칙 (자동 갱신)
```

## 동작 원리

1. 사용자가 보고서 작성 요청 → 백엔드의 `prompt_builder.py`가 이 폴더의 파일들을 읽음
2. 읽은 내용을 시스템 프롬프트로 조립해 Claude API에 전달
3. Claude가 이 규칙들에 따라 보고서 작성
4. 사용자가 피드백 주면 `learned_rules.json`에 한 줄씩 추가됨
5. 다음 보고서부터 자동 반영

## 수정 방법

### base_rules.md / format_rules.md 직접 수정
- 텍스트 에디터로 열어서 수정 → 저장
- 백엔드 재시작 없이 다음 보고서 생성부터 즉시 반영
- Git으로 변경 이력 관리 (권장)

### learned_rules.json 검토·정리
- 자동 누적된 규칙을 주기적으로 검토
- 어색한 규칙·중복 규칙은 직접 삭제
- 시연 직전에는 한 번 정리하는 것을 권장

## 형식 표준

### base_rules.md, format_rules.md
- 일반 마크다운
- 사람이 읽기 편한 형태로 자유롭게 작성

### learned_rules.json
```json
[
  {
    "id": "rule-001",
    "rule_text": "문단은 3문장 이내로 작성",
    "category": "structure",
    "source": "user_feedback",
    "created_at": "2026-05-27T10:30:00",
    "active": true
  }
]
```

카테고리는 다음 중 하나: `structure` | `tone` | `expression` | `format` | `taboo`

## 주의사항

- 이 폴더의 파일을 수정해도 **이미 생성된 보고서는 변경되지 않습니다**
- 새로 생성되는 보고서부터 적용됩니다
- 박스 템플릿(헤드·요약)의 시각적 디자인은 `backend/templates/box/` 에서 관리합니다
