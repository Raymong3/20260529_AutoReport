"""
HWPX 생성 모듈 (v5 - 사용자 템플릿 박스 직접 적용)

구조:
  templates/box/head_01.hwpx    → 제목 박스 ({{report_title}})
  templates/box/summary_01.hwpx → 요약 박스 ({{summary_line_1}}, {{summary_line_2}})

생성 흐름:
  1. head 템플릿을 기반으로 문서 구조·스타일 유지
  2. {{report_title}} 교체
  3. 요약 박스(rect)를 summary 템플릿에서 추출해 삽입
  4. 본문 단락을 </hs:sec> 앞에 추가
"""
import html
import io
import os
import re
import zipfile

# backend/services/ 기준 → backend/templates/box/
_BOX_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "box")
HEAD_TPL = os.path.join(_BOX_DIR, "head_01.hwpx")
SUMM_TPL = os.path.join(_BOX_DIR, "summary_01.hwpx")

SKIP_FILES = {"Contents/section0.xml", "Preview/PrvImage.png", "Preview/PrvText.txt"}


# ─────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────

def _extract_rect(section_xml: str) -> str:
    """section0.xml에서 <hp:rect ...>...</hp:rect> 전체 추출."""
    start = section_xml.find('<hp:rect ')
    if start == -1:
        return ''
    end = section_xml.find('</hp:rect>', start)
    if end == -1:
        return ''
    return section_xml[start:end + len('</hp:rect>')]


def _strip_bullet(text: str) -> str:
    """'ㅁ 내용' → '내용' (템플릿 안에 이미 ◈ 기호가 있으므로 제거)."""
    return text.lstrip('ㅁ').strip()


def _strip_bold(text: str) -> str:
    """**...** 마커 제거 (HWPX는 plain text)."""
    return re.sub(r'\*\*([^*]+)\*\*', r'\1', text)


def _para_body(para_id: int, text: str) -> str:
    """본문 일반 단락."""
    clean = _strip_bold(text)
    escaped = html.escape(clean, quote=False)
    return (
        f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="8"><hp:t>{escaped}</hp:t></hp:run>'
        f'</hp:p>'
    )


def _para_empty(para_id: int) -> str:
    """빈 줄 단락."""
    return (
        f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="8"/>'
        f'</hp:p>'
    )


# ─────────────────────────────────────────────────────────────
# 메인 함수
# ─────────────────────────────────────────────────────────────

def generate_hwpx(content: str, title: str = "보고서") -> bytes:
    """AI 생성 텍스트를 HWPX 바이너리로 변환."""

    for path in (HEAD_TPL, SUMM_TPL):
        if not os.path.exists(path):
            raise FileNotFoundError(f"템플릿 파일 없음: {path}")

    lines = content.split("\n")

    # ── 콘텐츠 파싱 ────────────────────────────────────────────
    report_title = lines[0].strip() if lines else title
    if not report_title or report_title.startswith('['):
        report_title = title

    summary_lines: list[str] = []
    body_start_idx = 1
    if len(lines) > 1:
        idx = 1
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        if idx < len(lines) and lines[idx].strip().startswith('[요약]'):
            rest = lines[idx].strip().removeprefix('[요약]').strip()
            if rest:
                summary_lines.append(rest)
            idx += 1
            while idx < len(lines) and lines[idx].strip().startswith('ㅁ'):
                summary_lines.append(lines[idx].strip())
                idx += 1
            if idx < len(lines) and lines[idx].strip() == '':
                idx += 1
            body_start_idx = idx

    # ── 템플릿 XML 읽기 ─────────────────────────────────────────
    with zipfile.ZipFile(HEAD_TPL, 'r') as z:
        head_xml = z.read("Contents/section0.xml").decode("utf-8", errors="replace")

    with zipfile.ZipFile(SUMM_TPL, 'r') as z:
        summ_xml = z.read("Contents/section0.xml").decode("utf-8", errors="replace")

    # ── 제목 박스: {{report_title}} 교체 ───────────────────────
    section_xml = head_xml.replace(
        '{{report_title}}',
        html.escape(report_title, quote=False)
    )

    # ── 요약 박스: rect 추출 후 플레이스홀더 교체 ──────────────
    rect_xml = _extract_rect(summ_xml)
    line1 = _strip_bullet(summary_lines[0]) if len(summary_lines) > 0 else ''
    line2 = _strip_bullet(summary_lines[1]) if len(summary_lines) > 1 else ''
    rect_xml = rect_xml.replace(
        '{{summary_line_1}}', html.escape(line1, quote=False)
    ).replace(
        '{{summary_line_2}}', html.escape(line2, quote=False)
    )

    summary_para = (
        '<hp:p id="2692885479" paraPrIDRef="0" styleIDRef="0" '
        'pageBreak="0" columnBreak="0" merged="0">'
        '<hp:run charPrIDRef="7">'
        + rect_xml +
        '<hp:t/></hp:run>'
        '</hp:p>'
    )

    # ── 본문 단락 생성 ─────────────────────────────────────────
    body_lines = lines[body_start_idx:]
    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)

    paragraphs = []
    for i, line in enumerate(body_lines):
        pid = 2_000_000 + i
        if line.strip() == "":
            paragraphs.append(_para_empty(pid))
        else:
            paragraphs.append(_para_body(pid, line))

    # ── XML 조립: </hs:sec> 앞에 요약 박스 + 본문 삽입 ─────────
    sec_close = '</hs:sec>'
    insert_pos = section_xml.rfind(sec_close)
    if insert_pos == -1:
        insert_pos = len(section_xml)
        sec_close = ''

    new_section_xml = (
        section_xml[:insert_pos]
        + summary_para
        + "".join(paragraphs)
        + sec_close
    ).encode("utf-8")

    # ── HWPX 재패키징 (head 템플릿 기반) ─────────────────────────
    buf = io.BytesIO()
    with zipfile.ZipFile(HEAD_TPL, 'r') as tmpl:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
            for name in tmpl.namelist():
                if name in SKIP_FILES:
                    continue
                if name == "mimetype":
                    zi = zipfile.ZipInfo("mimetype")
                    zi.compress_type = zipfile.ZIP_STORED
                    out.writestr(zi, tmpl.read(name))
                else:
                    out.writestr(tmpl.getinfo(name), tmpl.read(name))

            out.writestr("Contents/section0.xml", new_section_xml)
            out.writestr("Preview/PrvText.txt", content.encode("utf-8"))

    return buf.getvalue()
