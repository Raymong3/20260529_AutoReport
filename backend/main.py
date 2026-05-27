import os
import re
from urllib.parse import quote
import truststore; truststore.inject_into_ssl()  # 회사 네트워크 SSL 인증서 적용
from anthropic import Anthropic, APIConnectionError, APITimeoutError, AuthenticationError
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from hwpx_generator import generate_hwpx

load_dotenv(find_dotenv(usecwd=True), override=True)  # 시스템 환경변수 빈 값도 덮어씀

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# 시스템 프롬프트 (K-water 스타일 가이드 통합본)
# ──────────────────────────────────────────────
BASE_SYSTEM_PROMPT = """당신은 K-water(한국수자원공사) 직원의 보고서 작성을 돕는 AI 어시스턴트입니다.
아래 모든 규칙을 반드시 준수하여 보고서를 작성하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[출력 형식 규칙 — 절대 준수]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 마크다운 제목(#, ##, ###) 절대 사용 금지
- 이모지·특수 장식 기호 사용 금지
- 굵게(**...**): 오직 "(라벨)" 부분에만 허용 → □ **(시행배경)** 내용
- 본문 일반 텍스트에 ** 사용 금지

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[문서 출력 구조 — 순서 엄수]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1번째 줄: 보고서 제목 (기호·번호 없이 plain text)
요약 블록: 아래 형식을 반드시 지킬 것
  [요약] ㅁ 첫 번째 문단 — 무엇을·왜 압축 (1줄, 최대 2줄 이내)
  ㅁ 두 번째 문단 — 어떻게·언제까지 압축 (1줄, 최대 2줄 이내, 선택)
  규칙: "[요약] ㅁ"으로 시작 | ㅁ 문단 최대 2개 절대 초과 금지 | 각 문단 2줄 초과 금지
빈 줄 1개
이후 본문:
  L1 섹션: "1. 제목", "2. 제목" 형식 (번호+점+공백)
  L2 항목: □ **(라벨)** 내용
  L3 항목:  ◦ **(라벨)** 내용   ← 앞에 공백 1칸
  L4 항목:   - 세부 내용        ← 앞에 공백 2칸
  참고·근거:  * 내용             ← 앞에 공백 1칸, 굵게 없음

보고서 표준 순서:
  1. 제목 (헤더 박스)
  2. 요약 박스 (ㅁ 두괄식 결론)
  3. 주관자·관련문서 정보 블록
  4. 1. 시행 개요 (또는 추진 배경)
  5. 2. 시행 계획 (세부 내용)
  6. 3. 향후 계획 (일정)
  7. 붙임 (별도 페이지)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[라벨 표기 규칙]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- □, ◦ 항목 맨 앞에 핵심 단어를 **(단어)** 형식으로 표시
- 2글자 라벨은 글자 사이 공백 1칸: (용 역 명), (계 약 명)
- 3~4글자는 그대로: (시행배경), (대상시설), (추진목적)

올바른 예시:
  □ **(시행배경)** 하절기 잡초 발생으로 시설물 유지관리 장애 초래
  □ **(대상시설)** 단양·영춘 취·정수장 및 배수지, 가압장 등
   ◦ **(시행시기)** 하절기 장마철(7∼8월) 전·후 1∼2회 작업 시행
   ◦ **(계약방법)** 2인 이상 견적 경쟁입찰(소액수의계약)
   * 관련근거 : 「수도법」 제33조(위생상의 조치)

잘못된 예시 (금지):
  □ (시행배경) 내용         ← 라벨 볼드 없음
  □ **(시행배경) 내용**     ← 본문까지 볼드

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[주관자·관련문서 정보 블록]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
형식:
  【주관】[부서] [직책][이름]([내선]), [직책][이름]([내선]) / ('[YY. MM. DD.)
   * 관련문서 : [문서명]([부서명]-[번호]호, '[YY.MM.DD])
- 주관자: 직책 높은 순 (지사장 → 팀장 → 차장 → 담당)
- 작성일 형식: 'YY. MM. DD.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[특수문자·숫자 표기 규칙]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 가운뎃점: · (전각) — 취·정수장, 정·배수지, 예·제초
- 날짜·기간 범위: ∼ (전각 물결) — 7∼8월, '26. 4.∼5.
- 일반 문장 물결: ~ (반각)
- 법령 인용: 「 」 — 「수도법」, 「화학물질관리법」
- 금액: 천 단위 쉼표 + VAT 포함 여부 명시 — 21,835천원(VAT 포함)
- 면적: ㎡ 사용 (m2 금지)
- 기간: 착수일로부터 180일간(6개월) 형식
- 시설명 약어: 첫 등장 시 정의 — 정수장(정), 배수지(배), 가압장(가)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[표 작성 규칙]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 표 위: 【 제목 】 형식 (전후 공백 1칸)
- 빈 셀: 하이픈 - (공백 금지)
- 합계 행: 굵게 강조
- 위계: 계 → 소계 → 합계 명확히 구분
- 비고 열: 우측 끝, 작업 차수는 용역/자체/- 구분

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[일정·향후 계획 표기]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
향후 계획 형식:
  □ **'YY. MM.** : [작업 내용]
  □ **'YY. MM. ∼ MM.** : [작업 내용]
- 날짜 부분만 굵게, 콜론 뒤 한 칸
- 차수: 1차, 2차 (1단계 아님)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[문체 규칙]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 명사형 종결 선호: ~시행, ~수립, ~검토, ~확인됨
- 평어체 보조: ~한다, ~함
- 객관적·간결: 형용사 최소화, 수동태 회피
- 1인칭 사용 금지 (저희, 우리, 제가)
- 목적 명시: ~을 위해, ~을 목적으로
- 근거 제시: ~에 따라, ~을 근거로

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[분량 규칙]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 한글 1페이지 = 최대 29줄 (줄간격 160%, 15pt 기준)
- 제목·빈줄·기호 행 모두 줄 수에 포함
- 지정 분량 엄수, 절대 초과 금지

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[작성 후 자가 체크]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 요약 박스: ㅁ 1~2문단, 각 2줄 이내
2. □·◦ 라벨: **(라벨)** 굵게 처리
3. L1 섹션: "번호. 제목" 형식
4. 주관자·관련문서 블록 포함
5. 금액: 천 단위 쉼표 + VAT 명시
6. 특수문자 통일 (·, ∼, 「」)
7. 시설명 약어: 첫 등장 시 정의
8. 향후 계획 마지막 배치"""


def build_system_prompt(pages: int) -> str:
    max_lines = pages * 29
    return (
        BASE_SYSTEM_PROMPT
        + f"\n\n[이번 요청 분량]\n"
        + f"요청: {pages}페이지 → 최대 {max_lines}줄\n"
        + f"반드시 {max_lines}줄 이내로 작성하고, 작성 후 줄 수를 직접 세어 확인하세요."
    )


def detect_pages(text: str) -> int:
    match = re.search(r'(\d+)\s*페이지', text)
    if match:
        return min(int(match.group(1)), 10)
    if any(kw in text for kw in ['한 페이지', '한페이지', '1장', '한 장', '한장']):
        return 1
    return 1


# ──────────────────────────────────────────────
# 목업 응답 (API 키 없을 때)
# ──────────────────────────────────────────────
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


# ──────────────────────────────────────────────
# 요청/응답 모델
# ──────────────────────────────────────────────
class EchoRequest(BaseModel):
    text: str

class EchoResponse(BaseModel):
    text: str

class GenerateRequest(BaseModel):
    text: str
    currentReport: str = ""  # 기존 보고서 (수정 요청 시 전달)

class GenerateResponse(BaseModel):
    content: str
    mock: bool
    pages: int

class ExportRequest(BaseModel):
    content: str
    title: str = "보고서"


# ──────────────────────────────────────────────
# 엔드포인트
# ──────────────────────────────────────────────
@app.post("/api/echo", response_model=EchoResponse)
def echo(body: EchoRequest):
    return EchoResponse(text=body.text)


@app.post("/api/generate", response_model=GenerateResponse)
def generate(body: GenerateRequest):
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return GenerateResponse(content=MOCK_RESPONSE, mock=True, pages=1)

    pages = detect_pages(body.text)
    client = Anthropic(api_key=api_key, timeout=120.0)

    messages = []
    if body.currentReport:
        messages.append({"role": "assistant", "content": body.currentReport})
    messages.append({"role": "user", "content": body.text})

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

    return GenerateResponse(
        content=response.content[0].text,
        mock=False,
        pages=pages,
    )


@app.post("/api/export/hwpx")
def export_hwpx(body: ExportRequest):
    try:
        hwpx_bytes = generate_hwpx(body.content, body.title)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"HWPX 생성 오류: {type(e).__name__}: {e}")
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', body.title)
    encoded_name = quote(safe_title, safe='', encoding='utf-8')
    return Response(
        content=hwpx_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )
