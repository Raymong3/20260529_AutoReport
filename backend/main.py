import os
import re
from urllib.parse import quote

import truststore; truststore.inject_into_ssl()  # 회사 네트워크 SSL 인증서 적용
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from services.ai_service import generate_report
from services.hwpx_generator import generate_hwpx
from services.table_inserter import insert_table_into_hwpx
from services.table_models import TableData

load_dotenv(find_dotenv(usecwd=True), override=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# 요청/응답 모델
# ──────────────────────────────────────────────

class EchoRequest(BaseModel):
    text: str

class EchoResponse(BaseModel):
    text: str

class GenerateRequest(BaseModel):
    text: str
    currentReport: str = ""
    selectedText: str = ""   # 미리보기 드래그 선택 원문 (부분수정 시)

class GenerateResponse(BaseModel):
    content: str
    mock: bool
    pages: int
    is_report: bool = True  # True=보고서(우측패널), False=질문/대화(채팅창만)
    tables: dict = {}       # {table_id: {caption, headers, rows}}
    estimated: list = []    # AI 임의 작성 표시용 (미리보기 하이라이팅)
    user_provided: list = [] # 사용자가 직접 제공한 표현 목록 (하이라이트 제외용)

class ExportRequest(BaseModel):
    content: str
    title: str = "보고서"
    tables: dict = {}       # {table_id: {caption, headers, rows}}


# ──────────────────────────────────────────────
# 엔드포인트
# ──────────────────────────────────────────────

@app.post("/api/echo", response_model=EchoResponse)
def echo(body: EchoRequest):
    return EchoResponse(text=body.text)


@app.post("/api/generate", response_model=GenerateResponse)
def generate(body: GenerateRequest):
    result = generate_report(body.text, body.currentReport, body.selectedText)
    return GenerateResponse(**result)


@app.post("/api/export/hwpx")
def export_hwpx(body: ExportRequest):
    try:
        hwpx_bytes = generate_hwpx(body.content, body.title)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"HWPX 생성 오류: {type(e).__name__}: {e}")

    try:
        for table_id, table_raw in body.tables.items():
            table_data = TableData(**table_raw)
            hwpx_bytes = insert_table_into_hwpx(
                hwpx_bytes, table_data, f"[[TABLE:{table_id}]]"
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"표 삽입 오류: {type(e).__name__}: {e}")
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', body.title)
    encoded_name = quote(safe_title, safe='', encoding='utf-8')
    return Response(
        content=hwpx_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )
