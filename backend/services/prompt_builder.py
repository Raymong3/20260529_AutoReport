"""
시스템 프롬프트 조립 모듈

style_guide/ 폴더의 파일들을 읽어 Claude API에 전달할 시스템 프롬프트를 동적으로 조립합니다.
파일을 수정하면 백엔드 재시작 없이 다음 호출부터 즉시 반영됩니다.

함수:
  build_system_prompt_create(pages)       → 새 보고서 작성용
  build_system_prompt_edit(report, pages) → 기존 보고서 수정용
"""
import json
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STYLE_GUIDE_DIR = _PROJECT_ROOT / "style_guide"

BASE_RULES_PATH    = STYLE_GUIDE_DIR / "base_rules.md"
FORMAT_RULES_PATH  = STYLE_GUIDE_DIR / "format_rules.md"
LEARNED_RULES_PATH = STYLE_GUIDE_DIR / "learned_rules.json"


def _read_text(path: Path) -> str:
    """파일을 읽어 텍스트 반환. 없으면 빈 문자열."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _load_learned_rules() -> list[dict]:
    """learned_rules.json에서 active=true인 규칙만 반환."""
    try:
        rules = json.loads(LEARNED_RULES_PATH.read_text(encoding="utf-8"))
        return [r for r in rules if r.get("active", True)]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _format_learned_rules(rules: list[dict]) -> str:
    """학습 규칙을 카테고리별로 정리해 문자열로 변환."""
    if not rules:
        return ""

    by_category: dict[str, list[str]] = {}
    for rule in rules:
        cat = rule.get("category", "general")
        by_category.setdefault(cat, []).append(rule["rule_text"])

    lines = ["[사용자 피드백으로 학습된 추가 규칙]"]
    for cat, texts in by_category.items():
        lines.append(f"\n{cat}:")
        for t in texts:
            lines.append(f"  - {t}")
    return "\n".join(lines)


def _build_base_parts() -> list[str]:
    """공통 부분 (스타일 가이드 + 학습 규칙)."""
    base_rules   = _read_text(BASE_RULES_PATH)
    format_rules = _read_text(FORMAT_RULES_PATH)
    learned      = _format_learned_rules(_load_learned_rules())

    parts = [
        "당신은 K-water(한국수자원공사) 직원의 보고서 작성을 돕는 AI 어시스턴트입니다.",
        "아래 스타일 가이드의 모든 규칙을 반드시 준수하여 보고서를 작성하세요.",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "[보고서 작성 규칙]",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        base_rules,
    ]

    if format_rules:
        parts += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "[서식 규칙 참고]",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            format_rules,
        ]

    if learned:
        parts += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            learned,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

    return parts


def build_system_prompt_create(pages: int = 1) -> str:
    """
    새 보고서 작성용 시스템 프롬프트.

    Args:
        pages: 요청 페이지 수

    Returns:
        Claude API system 파라미터에 전달할 완성된 프롬프트 문자열
    """
    max_lines = pages * 29
    parts = _build_base_parts()
    parts += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "[응답 형식 — 최우선 준수]",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "응답의 첫 번째 줄은 반드시 '[보고서]'여야 합니다. 다른 어떤 텍스트도 그 앞에 오면 안 됩니다.",
        "두 번째 줄부터 [보고서 작성 규칙]의 표준 출력 순서에 따라 보고서를 작성하세요.",
        "",
        "절대 금지:",
        "- '네, 알겠습니다', '먼저 확인드리겠습니다' 등 대화체 문장을 응답 어디에도 포함 금지",
        "- 질문 목록, 추가 정보 요청, 안내 문구 포함 금지",
        "- [보고서] 마커 없이 응답 시작 금지",
        "- 요약 불릿은 반드시 ◈ 기호만 사용 (◆, ◇ 등 다른 기호 사용 금지)",
        "",
        "정보 부족 시: '[정보 필요: 내용]' 플레이스홀더를 넣고 보고서를 완성하세요.",
        "",
        "[표 삽입 규칙] (표가 필요한 경우에만 적용)",
        "사용자가 표를 요청하거나 항목 비교·일정 등 표가 명확히 필요한 경우:",
        "  1. 본문에서 표가 들어갈 위치에 [[TABLE:t1]] 마커를 단독 줄로만 삽입",
        "     (표 여러 개면 t1, t2, t3 순으로 ID 부여)",
        "  2. ★ 표 제목(【 제목 】)은 본문에 별도 텍스트로 절대 작성하지 마세요.",
        "     제목은 아래 TABLE_DATA의 caption 필드에만 넣으면 자동으로 가운데 정렬되어 표시됩니다.",
        "  3. 응답 맨 끝(보고서 내용 이후)에 다음 블록을 추가:",
        "     ===TABLE_DATA_START===",
        '     {"t1": {"caption": "표 제목", "headers": ["열1", "열2"], "rows": [["값1", "값2"]]}}',
        "     ===TABLE_DATA_END===",
        "  4. 열 수는 반드시 3, 4, 5 중 하나로만 구성",
        "  5. 표가 필요 없으면 마커도 블록도 출력 금지",
        "",
        "[이번 요청 분량]",
        f"요청: {pages}페이지 → 최대 {max_lines}줄",
        f"반드시 {max_lines}줄 이내로 작성하고, 작성 후 줄 수를 직접 세어 확인하세요.",
    ]
    return "\n".join(parts)


def build_system_prompt_edit(current_report: str, pages: int = 1, selected_text: str = "") -> str:
    """
    기존 보고서 수정용 시스템 프롬프트.

    Args:
        current_report: 수정 대상이 되는 기존 보고서 전문
        pages: 보고서 페이지 수 (분량 기준 유지용)
        selected_text: 사용자가 미리보기에서 드래그 선택한 원문 (없으면 빈 문자열)

    Returns:
        Claude API system 파라미터에 전달할 완성된 프롬프트 문자열
    """
    max_lines = pages * 29
    parts = _build_base_parts()
    parts += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "[응답 형식 — 최우선 준수]",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "응답은 반드시 다음 두 형식 중 하나로만 시작하세요:",
        "",
        "형식 A — 수정된 보고서 전문:",
        "  [보고서]",
        "  (두 번째 줄부터 스타일 가이드에 따른 보고서 전체)",
        "",
        "형식 B — 수정 의도 확인 질문 (요청이 불명확한 경우에만):",
        "  [질문] (질문 내용)",
        "",
        "[보고서] 또는 [질문] 외의 텍스트로 응답을 시작하는 것은 절대 금지합니다.",
        "요약 불릿은 반드시 ◈ 기호만 사용하세요.",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "[수정 모드 — 절대 준수]",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "지금은 새 보고서 작성이 아니라 기존 보고서 수정 작업입니다.",
        "",
        "다음을 반드시 지키세요:",
        "",
        "1. 사용자가 명시적으로 수정을 요청한 부분만 변경하세요.",
        "2. 수정 요청에 포함되지 않은 모든 부분(제목, 요약, 다른 섹션, 표 등)은",
        "   글자 하나도 바꾸지 말고 입력받은 원문을 그대로 복사하세요.",
        "3. 새 정보를 추가하라는 요청이 아니라면 절대 새 내용을 추가하지 마세요.",
        "4. 보고서 전체를 출력하되, 변경되지 않은 부분도 빠뜨리지 말고 모두 포함하세요.",
        "5. 요청이 모호하면 '[질문] ...' 형식으로만 응답하고, 보고서는 전혀 출력하지 마세요.",
        "6. 수정 시에도 위 [보고서 작성 규칙] 섹션의 스타일 가이드를 모두 준수하세요.",
        "7. 기존 보고서에 [[TABLE:t1]] 마커가 있으면 그대로 유지하세요.",
        "   표 추가·수정 요청 시에는 [표 삽입 규칙]에 따라 마커와 TABLE_DATA 블록을 출력하세요.",
        "",
        "[표 삽입 규칙] (표가 필요한 경우에만 적용)",
        "사용자가 표를 요청하거나 항목 비교·일정 등 표가 명확히 필요한 경우:",
        "  1. 본문에서 표가 들어갈 위치에 [[TABLE:t1]] 마커를 단독 줄로만 삽입",
        "     (표 여러 개면 t1, t2, t3 순으로 ID 부여)",
        "  2. ★ 표 제목(【 제목 】)은 본문에 별도 텍스트로 절대 작성하지 마세요.",
        "     제목은 아래 TABLE_DATA의 caption 필드에만 넣으면 자동으로 가운데 정렬되어 표시됩니다.",
        "  3. 응답 맨 끝(보고서 내용 이후)에 다음 블록을 추가:",
        "     ===TABLE_DATA_START===",
        '     {"t1": {"caption": "표 제목", "headers": ["열1", "열2"], "rows": [["값1", "값2"]]}}',
        "     ===TABLE_DATA_END===",
        "  4. 열 수는 반드시 3, 4, 5 중 하나로만 구성",
        "  5. 표가 필요 없으면 마커도 블록도 출력 금지",
        "",
        f"[분량 기준] 최대 {max_lines}줄 이내 유지",
    ]

    if selected_text.strip():
        parts += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "[선택 텍스트 집중 수정 모드]",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "사용자가 미리보기에서 아래 텍스트를 직접 선택하여 수정을 요청했습니다.",
            "반드시 이 선택된 부분에만 집중하여 수정하고, 나머지는 원문 그대로 유지하세요.",
            "",
            "─────────────",
            selected_text.strip(),
            "─────────────",
        ]

    parts += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "[현재 보고서 — 수정의 기준이 되는 원본]",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        current_report,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "요청한 부분만 수정 후 '[보고서]' 마커 다음에 보고서 전체를 출력하세요.",
    ]
    return "\n".join(parts)


# 하위 호환성 유지 (기존 코드가 build_system_prompt를 import하는 경우 대비)
def build_system_prompt(pages: int = 1) -> str:
    return build_system_prompt_create(pages)
