"""
Claude API 호출 모듈

보고서 생성 요청을 받아 Claude API를 호출하고 결과를 반환합니다.
시스템 프롬프트는 prompt_builder.py가 style_guide/에서 동적으로 조립합니다.
"""
import os
import re

from anthropic import Anthropic, APIConnectionError, APITimeoutError, AuthenticationError
from fastapi import HTTPException

from services.prompt_builder import build_system_prompt

MOCK_RESPONSE = """'26년 단양수도지사 수도사업장 예초 용역 시행계획 (샘플)
[요약] ㅁ API 키 미설정으로 샘플 보고서를 반환함
ㅁ .env 파일에 ANTHROPIC_API_KEY를 설정하면 실제 AI 응답으로 전환됨

1. 현황
□ **(개발환경)** 백엔드·프론트엔드 연동 테스트 진행 중임
 ◦ **(확인사항)** POST /api/generate 엔드포인트 정상 동작 확인됨
 ◦ **(진행상황)** K-water 스타일가이드 적용 및 분량 제한 기능 구현됨

2. 향후 계획
□ **'26. 06.** : API 키 발급 후 실제 AI 생성 보고서로 교체 예정
□ **'26. 06.** : HWPX 다운로드 기능 완성 예정"""


def detect_pages(text: str) -> int:
    """요청 텍스트에서 페이지 수를 추출합니다. 기본값 1."""
    match = re.search(r'(\d+)\s*페이지', text)
    if match:
        return min(int(match.group(1)), 10)
    if any(kw in text for kw in ['한 페이지', '한페이지', '1장', '한 장', '한장']):
        return 1
    return 1


def generate_report(text: str, current_report: str = "") -> dict:
    """
    보고서를 생성합니다.

    Args:
        text: 사용자 요청 텍스트
        current_report: 기존 보고서 내용 (수정 요청 시)

    Returns:
        {'content': str, 'mock': bool, 'pages': int}

    Raises:
        HTTPException: API 오류 시
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return {"content": MOCK_RESPONSE, "mock": True, "pages": 1}

    pages = detect_pages(text)
    client = Anthropic(api_key=api_key, timeout=120.0)

    messages = []
    if current_report:
        messages.append({"role": "assistant", "content": current_report})
    messages.append({"role": "user", "content": text})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=build_system_prompt(pages),
            messages=messages,
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="API 키가 유효하지 않습니다. .env 파일을 확인하세요.")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI 응답 시간 초과(2분). 다시 시도해주세요.")
    except APIConnectionError as e:
        raise HTTPException(status_code=503, detail=f"API 서버 연결 실패: {e}")

    return {
        "content": response.content[0].text,
        "mock": False,
        "pages": pages,
    }
