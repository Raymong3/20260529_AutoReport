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
    result = generate_report(body.text, body.currentReport)
    return GenerateResponse(**result)


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
