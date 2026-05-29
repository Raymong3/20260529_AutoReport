"""
Claude API 호출 모듈

보고서 생성/수정 요청을 받아 Claude API를 호출하고 결과를 반환합니다.
- currentReport 없음 → build_system_prompt_create (새 보고서 작성 모드)
- currentReport 있음 → build_system_prompt_edit  (기존 보고서 수정 모드)

AI 응답에 ===TABLE_DATA_START===...===TABLE_DATA_END=== 블록이 있으면
파싱하여 tables dict를 별도 반환한다.
"""
import json
import os
import re

from anthropic import Anthropic, APIConnectionError, APITimeoutError, AuthenticationError
from fastapi import HTTPException

from services.prompt_builder import build_system_prompt_create, build_system_prompt_edit

_TABLE_START          = "===TABLE_DATA_START==="
_TABLE_END            = "===TABLE_DATA_END==="
_ESTIMATED_START      = "===ESTIMATED_START==="
_ESTIMATED_END        = "===ESTIMATED_END==="
_USER_PROVIDED_START  = "===USER_PROVIDED_START==="
_USER_PROVIDED_END    = "===USER_PROVIDED_END==="


def _parse_tables(text: str) -> tuple[str, dict]:
    """AI 응답에서 TABLE_DATA 블록을 추출한다.

    Returns:
        (content_without_block, tables_dict)
        블록이 없으면 (원본 text, {}) 반환.
        블록이 있으면 파싱 성공 여부와 무관하게 블록을 제거한 텍스트를 반환.
    """
    start = text.find(_TABLE_START)
    if start == -1:
        return text, {}
    end = text.find(_TABLE_END, start)
    if end == -1:
        # 종료 마커가 없으면 시작 마커 이후를 모두 제거
        return text[:start].strip(), {}

    json_text = text[start + len(_TABLE_START):end].strip()
    clean_content = (text[:start].rstrip() + "\n" + text[end + len(_TABLE_END):]).strip()

    try:
        tables = json.loads(json_text)
        return clean_content, tables
    except json.JSONDecodeError:
        return clean_content, {}


def _parse_estimated(text: str) -> tuple[str, list]:
    """AI 응답에서 ESTIMATED 블록을 추출한다.

    Returns:
        (content_without_block, estimated_phrases_list)
    """
    start = text.find(_ESTIMATED_START)
    if start == -1:
        return text, []
    end = text.find(_ESTIMATED_END, start)
    if end == -1:
        return text[:start].strip(), []

    json_text = text[start + len(_ESTIMATED_START):end].strip()
    clean_content = (text[:start].rstrip() + "\n" + text[end + len(_ESTIMATED_END):]).strip()

    try:
        phrases = json.loads(json_text)
        if isinstance(phrases, list):
            return clean_content, [str(p) for p in phrases if p]
        return clean_content, []
    except json.JSONDecodeError:
        return clean_content, []


def _parse_user_provided(text: str) -> tuple[str, list]:
    """AI 응답에서 USER_PROVIDED 블록을 추출한다.

    Returns:
        (content_without_block, user_provided_phrases_list)
    """
    start = text.find(_USER_PROVIDED_START)
    if start == -1:
        return text, []
    end = text.find(_USER_PROVIDED_END, start)
    if end == -1:
        return text[:start].strip(), []

    json_text = text[start + len(_USER_PROVIDED_START):end].strip()
    clean_content = (text[:start].rstrip() + "\n" + text[end + len(_USER_PROVIDED_END):]).strip()

    try:
        phrases = json.loads(json_text)
        if isinstance(phrases, list):
            return clean_content, [str(p) for p in phrases if p]
        return clean_content, []
    except json.JSONDecodeError:
        return clean_content, []


MOCK_RESPONSE = """'26년 단양수도지사 수도사업장 예초 용역 시행계획 (샘플)
【주관】[단양관리단] [팀장]홍길동(1234), [담당]김철수(5678) / ('26. 05. 27.)
 * 관련근거 : 수도사업장 시설관리 지침

[요약] ◈ API 키 미설정으로 샘플 보고서를 반환함
 ◈ .env 파일에 ANTHROPIC_API_KEY를 설정하면 실제 AI 응답으로 전환됨

1. 현황
□ **(개발환경)** 백엔드·프론트엔드 연동 테스트 진행 중임
 ◦ **(확인사항)** POST /api/generate 엔드포인트 정상 동작 확인됨

2. 향후 계획
□ **'26. 06.** : API 키 발급 후 실제 AI 생성 보고서로 교체 예정"""


def detect_pages(text: str) -> int:
    """요청 텍스트에서 페이지 수를 추출합니다. 기본값 1."""
    match = re.search(r'(\d+)\s*페이지', text)
    if match:
        return min(int(match.group(1)), 10)
    if any(kw in text for kw in ['한 페이지', '한페이지', '1장', '한 장', '한장']):
        return 1
    return 1


def generate_report(text: str, current_report: str = "", selected_text: str = "") -> dict:
    """
    보고서를 생성하거나 수정합니다.

    current_report가 비어있으면 새 보고서 작성 모드,
    있으면 수정 모드로 동작합니다.

    Args:
        text: 사용자 요청 텍스트
        current_report: 기존 보고서 내용 (수정 요청 시)
        selected_text: 미리보기에서 드래그 선택한 원문 (부분수정 시)

    Returns:
        {'content': str, 'mock': bool, 'pages': int, 'is_report': bool, 'tables': dict}
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return {"content": MOCK_RESPONSE, "mock": True, "pages": 1, "is_report": True, "tables": {}}

    pages = detect_pages(text)
    client = Anthropic(api_key=api_key, timeout=120.0)

    # ── 모드 분기 ───────────────────────────────────────────
    if current_report.strip():
        # 수정 모드: 기존 보고서를 시스템 프롬프트에 포함, 사용자 요청만 전달
        system_prompt = build_system_prompt_edit(current_report, pages, selected_text)
        messages = [{"role": "user", "content": text}]
        mode = "edit"
    else:
        # 새 보고서 작성 모드
        system_prompt = build_system_prompt_create(pages)
        messages = [{"role": "user", "content": text}]
        mode = "create"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="API 키가 유효하지 않습니다. .env 파일을 확인하세요.")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI 응답 시간 초과(2분). 다시 시도해주세요.")
    except APIConnectionError as e:
        raise HTTPException(status_code=503, detail=f"API 서버 연결 실패: {e}")

    raw = response.content[0].text.strip()

    # AI는 반드시 [보고서] 또는 [질문]으로 시작해야 함
    if raw.startswith('[보고서]'):
        body = raw[len('[보고서]'):].lstrip('\n').lstrip()
        content, tables = _parse_tables(body)
        content, estimated = _parse_estimated(content)
        content, user_provided = _parse_user_provided(content)
        is_report = True
    elif raw.startswith('[질문]'):
        content = raw[len('[질문]'):].strip()
        tables = {}
        estimated = []
        user_provided = []
        is_report = False
    else:
        # 마커 없는 예외 응답 → 채팅창에만 표시 (보고서 패널 보호)
        content = raw
        tables = {}
        estimated = []
        user_provided = []
        is_report = False

    return {
        "content": content,
        "mock": False,
        "pages": pages,
        "is_report": is_report,
        "tables": tables,
        "estimated": estimated,
        "user_provided": user_provided,
    }
