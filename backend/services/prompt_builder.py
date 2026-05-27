"""
시스템 프롬프트 조립 모듈

style_guide/ 폴더의 파일들을 읽어 Claude API에 전달할 시스템 프롬프트를 동적으로 조립합니다.
파일을 수정하면 백엔드 재시작 없이 다음 호출부터 즉시 반영됩니다.
"""
import json
import os
from pathlib import Path

# style_guide/ 는 프로젝트 루트 기준 — backend/services/ 에서 두 단계 위
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STYLE_GUIDE_DIR = _PROJECT_ROOT / "style_guide"

BASE_RULES_PATH = STYLE_GUIDE_DIR / "base_rules.md"
FORMAT_RULES_PATH = STYLE_GUIDE_DIR / "format_rules.md"
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


def build_system_prompt(pages: int = 1) -> str:
    """
    style_guide/ 파일들을 조합해 시스템 프롬프트를 반환합니다.

    Args:
        pages: 요청 페이지 수 (분량 제한 계산에 사용)

    Returns:
        Claude API system 파라미터에 전달할 완성된 프롬프트 문자열
    """
    base_rules = _read_text(BASE_RULES_PATH)
    format_rules = _read_text(FORMAT_RULES_PATH)
    learned_rules = _load_learned_rules()
    learned_section = _format_learned_rules(learned_rules)

    max_lines = pages * 29

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

    if learned_section:
        parts += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            learned_section,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

    parts += [
        "",
        "[이번 요청 분량]",
        f"요청: {pages}페이지 → 최대 {max_lines}줄",
        f"반드시 {max_lines}줄 이내로 작성하고, 작성 후 줄 수를 직접 세어 확인하세요.",
    ]

    return "\n".join(parts)
