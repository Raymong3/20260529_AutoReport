"""
HWPX 생성 모듈 (v9 - 중고딕→한컴돋움 폰트 치환)

구조:
  templates/box/head_01.hwpx    → 제목 박스 ({{report_title}})
  templates/box/summary_01.hwpx → 요약 박스 ({{summary_line_1}}, {{summary_line_2}})

폰트 매핑 (charPrIDRef, head 템플릿 기준):
  8  → HY헤드라인M 20pt  (제목 박스, 템플릿 고정)
  9  → HY헤드라인M 15pt  (1./2./3. 섹션 제목)
  10 → 휴먼명조 15pt, 자간 -10% (□/◦/- 본문, 긴 단락)
  11 → 한컴돋움 13pt, 자간 -10%  (* 참고/각주, 긴 단락)
  12 → 휴먼명조 15pt, 자간  0%  (□/◦/- 본문, 짧은 단락)
  13 → 한컴돋움 13pt, 자간  0%  (* 참고/각주, 짧은 단락)
  14 → 휴먼명조 15pt, 자간 -20% (본문 강제 1줄용)
  15 → 한컴돋움 13pt, 자간 -20% (주관자 블록 강제 1줄용)

단락 스타일 매핑 (paraPrIDRef):
  0  → JUSTIFY 160% (본문 단락)
  19 → CENTER  160% (제목 박스 셀 — 템플릿 고정, 재사용 금지)
  20 → JUSTIFY FIXED 5pt (빈 줄 전용, 패치로 추가)

표 관련 ID (table_inserter._patch_header_for_table 추가):
  charPr 16 → 한컴돋움 13pt, 자간 0% (표 데이터 셀)
  charPr 17 → 한컴돋움 13pt, 자간 0% (표 헤더 셀)
  paraPr 21 → CENTER 150% (표 셀 단락)
  paraPr 22 → CENTER 160% (표 캡션 단락)
"""
import html
import io
import os
import re
import zipfile

_BOX_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "box")
HEAD_TPL = os.path.join(_BOX_DIR, "head_01.hwpx")
SUMM_TPL = os.path.join(_BOX_DIR, "summary_01.hwpx")

SKIP_FILES = {"Contents/section0.xml", "Preview/PrvImage.png", "Preview/PrvText.txt"}

# ── 헤더 패치: 새 폰트 및 charPr 삽입 ─────────────────────────
_NEW_FONTS = (
    '<hh:font id="3" face="휴먼명조" type="TTF" isEmbedded="0">'
    '<hh:typeInfo familyType="FCAT_ROMAN" weight="5" proportion="4" contrast="5" '
    'strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/>'
    '</hh:font>'
    '<hh:font id="4" face="한컴돋움" type="TTF" isEmbedded="0">'
    '<hh:typeInfo familyType="FCAT_GOTHIC" weight="5" proportion="4" contrast="0" '
    'strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/>'
    '</hh:font>'
)


def _charpr_xml(cid: int, height: int, font: int, spacing: int = 0) -> str:
    f = str(font)
    sp = str(spacing)
    return (
        f'<hh:charPr id="{cid}" height="{height}" textColor="#000000" shadeColor="none" '
        f'useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">'
        f'<hh:fontRef hangul="{f}" latin="{f}" hanja="{f}" japanese="{f}" other="{f}" symbol="{f}" user="{f}"/>'
        f'<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
        f'<hh:spacing hangul="{sp}" latin="{sp}" hanja="{sp}" japanese="{sp}" other="{sp}" symbol="{sp}" user="{sp}"/>'
        f'<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
        f'<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
        f'<hh:underline type="NONE" shape="SOLID" color="#000000"/>'
        f'<hh:strikeout shape="NONE" color="#000000"/>'
        f'<hh:outline type="NONE"/>'
        f'<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
        f'</hh:charPr>'
    )


_NEW_CHARPR = (
    _charpr_xml(9,  1500, 2, 0)      # HY헤드라인M 15pt – 섹션 제목
    + _charpr_xml(10, 1500, 3, -10)  # 휴먼명조 15pt    – 본문 (자간 -10%, 긴 단락)
    + _charpr_xml(11, 1300, 4, -10)  # 중고딕 13pt      – 참고/각주 (자간 -10%, 긴 단락)
    + _charpr_xml(12, 1500, 3, 0)    # 휴먼명조 15pt    – 본문 (자간 0%, 짧은 단락)
    + _charpr_xml(13, 1300, 4, 0)    # 중고딕 13pt      – 참고/각주 (자간 0%, 짧은 단락)
    + _charpr_xml(14, 1500, 3, -20)  # 휴먼명조 15pt    – 본문 (자간 -20%, 강제 1줄)
    + _charpr_xml(15, 1300, 4, -20)  # 중고딕 13pt      – 참고/각주 (자간 -20%, 주관자 블록 강제 1줄)
)

# 빈 줄용 paraPr: FIXED 500 HWPUNIT = 5pt 고정 줄높이
# (paraPr id=0의 PERCENT 160%이면 15pt×160%=24pt → 빈 줄이 너무 커짐)
_PARA_MARGIN = (
    '<hh:margin>'
    '<hc:intent value="0" unit="HWPUNIT"/>'
    '<hc:left value="0" unit="HWPUNIT"/>'
    '<hc:right value="0" unit="HWPUNIT"/>'
    '<hc:prev value="0" unit="HWPUNIT"/>'
    '<hc:next value="0" unit="HWPUNIT"/>'
    '</hh:margin>'
)
_NEW_PARA = (
    '<hh:paraPr id="20" tabPrIDRef="0" condense="0" fontLineHeight="0" '
    'snapToGrid="1" suppressLineNumbers="0" checked="0">'
    '<hh:align horizontal="JUSTIFY" vertical="BASELINE"/>'
    '<hh:heading type="NONE" idRef="0" level="0"/>'
    '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" '
    'widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
    '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
    '<hp:switch>'
    '<hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">'
    + _PARA_MARGIN +
    '<hh:lineSpacing type="FIXED" value="500" unit="HWPUNIT"/>'
    '</hp:case>'
    '<hp:default>'
    + _PARA_MARGIN +
    '<hh:lineSpacing type="FIXED" value="500" unit="HWPUNIT"/>'
    '</hp:default>'
    '</hp:switch>'
    '<hh:border borderFillIDRef="2" offsetLeft="0" offsetRight="0" '
    'offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/>'
    '</hh:paraPr>'
)


def _patch_header(header_xml: str) -> str:
    """header.xml에 새 폰트·charPr·paraPr 정의를 삽입한다."""
    # 1. fontface 그룹별 fontCnt 3→5, 새 폰트 2개 추가
    header_xml = re.sub(
        r'(<hh:fontface lang="[^"]*" fontCnt=)"3"',
        r'\1"5"',
        header_xml,
    )
    header_xml = header_xml.replace('</hh:fontface>', _NEW_FONTS + '</hh:fontface>')

    # 2. charProperties itemCnt 9→16, 새 charPr 7개 추가 (id=9~15)
    header_xml = re.sub(
        r'(<hh:charProperties itemCnt=)"9"',
        r'\1"16"',
        header_xml,
    )
    header_xml = header_xml.replace('</hh:charProperties>', _NEW_CHARPR + '</hh:charProperties>')

    # 3. paraProperties itemCnt 20→21, 빈 줄용 paraPr 추가
    header_xml = re.sub(
        r'(<hh:paraProperties itemCnt=)"20"',
        r'\1"21"',
        header_xml,
    )
    header_xml = header_xml.replace('</hh:paraProperties>', _NEW_PARA + '</hh:paraProperties>')

    return header_xml


# ── 헬퍼 ──────────────────────────────────────────────────────

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
    """'◈ 내용' / 'ㅁ 내용' → '내용' (템플릿 안에 이미 ◈ 기호가 있으므로 제거)."""
    return re.sub(r'^[ㅁ◈]\s*', '', text).strip()


def _strip_bold(text: str) -> str:
    """**...** 마커 제거 (HWPX는 plain text)."""
    return re.sub(r'\*\*([^*]+)\*\*', r'\1', text)


# 자간별 1줄 수용 한글 환산 글자 수 (A4 170mm 기준)
# -N%  자간 → 수용 글자 ≈ 0% 기준값 / (1 - N/100)
_BODY_LINE_0     = 33  # 휴먼명조 15pt, 자간  0%
_BODY_LINE_NEG10 = 37  # 휴먼명조 15pt, 자간 -10%
_BODY_LINE_NEG20 = 41  # 휴먼명조 15pt, 자간 -20%
_REF_LINE_0      = 37  # 중고딕 13pt,   자간  0%
_REF_LINE_NEG10  = 41  # 중고딕 13pt,   자간 -10%
_REF_LINE_NEG20  = 46  # 중고딕 13pt,   자간 -20%


def _ko_char_len(text: str) -> float:
    """한글 환산 문자 길이. 한글·CJK = 1.0, 그 외(ASCII·숫자·공백) = 0.5."""
    clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    return sum(1.0 if ord(ch) > 0x3000 else 0.5 for ch in clean)


def _split_line(line: str) -> tuple[str, str]:
    """줄을 (접두사, 내용)으로 분리. 접두사 = 마커+라벨, 내용 = 나머지.
    □/**(라벨)**/, ◦/**(라벨)**/, - , *, 【...】 패턴을 처리."""
    # □ **(라벨)** 내용  /  ◦ **(라벨)** 내용
    m = re.match(r'^(\s*[□◦]\s*(?:\*\*[^*]+\*\*\s*)?)(.*)', line, re.DOTALL)
    if m and m.group(1).strip():
        return m.group(1), m.group(2)
    # - 내용  /  * 내용 (들여쓰기 + 마커만)
    m = re.match(r'^(\s*[-*]\s+)(.*)', line, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    # 【주관】 내용
    m = re.match(r'^(【[^】]+】\s*)(.*)', line, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return '', line


def _is_new_item(line: str) -> bool:
    """True이면 새 단락을 시작하는 줄 (□·◦·-·*·【·번호. 등)."""
    s = line.strip()
    if not s:
        return True
    if s.startswith('□') or s.startswith('【'):
        return True
    if re.match(r'^\d+\.', s):
        return True
    stripped = line.lstrip()
    if stripped.startswith('◦') or stripped.startswith('*'):
        return True
    if stripped.startswith('-') and line != stripped:
        return True
    return False


def _para_body(para_id: int, line: str, force_single: bool = False) -> str:
    """본문 단락. 접두사(마커·라벨)는 자간 0%, 내용부는 임계값으로 자간 자동 선택.

    force_single=False (기본, 본문):
      ①자간 0%로 들어감 → 0%, ②자간 -10%로만 들어감 → -10%,
      ③-10%로도 초과 → 0%(자연 줄바꿈 허용)

    force_single=True (주관자 블록):
      -10%로도 안 되면 -20%까지 압축하여 최대한 1줄 유지
    """
    s = line.lstrip()

    # 섹션 제목: 자간 0% 단일 run
    if re.match(r'^\d+\.', s):
        return (
            f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="9"><hp:t>'
            f'{html.escape(_strip_bold(line), quote=False)}</hp:t></hp:run>'
            f'</hp:p>'
        )

    is_ref   = s.startswith('【') or s.startswith('*')
    line_0   = _REF_LINE_0    if is_ref else _BODY_LINE_0
    line_n10 = _REF_LINE_NEG10 if is_ref else _BODY_LINE_NEG10
    line_n20 = _REF_LINE_NEG20 if is_ref else _BODY_LINE_NEG20
    cpr_0    = 13 if is_ref else 12  # 자간  0%
    cpr_n10  = 11 if is_ref else 10  # 자간 -10%
    cpr_n20  = 15 if is_ref else 14  # 자간 -20% (강제 1줄용)

    prefix, content = _split_line(line)
    pfx_len  = _ko_char_len(prefix)
    ctn_len  = _ko_char_len(content)
    cap_0    = line_0   - pfx_len
    cap_n10  = line_n10 - pfx_len

    if force_single:
        # 주관자 블록: -10% → -20% 순으로 단계적 압축
        content_cpr = (
            cpr_0   if ctn_len <= cap_0 else
            cpr_n10 if ctn_len <= cap_n10 else
            cpr_n20  # -20%까지 압축하여 최대한 1줄 유지
        )
    else:
        # 기존 로직: 0%→-10%, 그래도 안 되면 0%(자연 줄바꿈)
        content_cpr = cpr_n10 if (ctn_len > cap_0 and ctn_len <= cap_n10) else cpr_0

    if not content:
        return (
            f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{cpr_0}"><hp:t>'
            f'{html.escape(_strip_bold(line), quote=False)}</hp:t></hp:run>'
            f'</hp:p>'
        )

    return (
        f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{cpr_0}"><hp:t>'
        f'{html.escape(_strip_bold(prefix), quote=False)}</hp:t></hp:run>'
        f'<hp:run charPrIDRef="{content_cpr}"><hp:t>'
        f'{html.escape(_strip_bold(content), quote=False)}</hp:t></hp:run>'
        f'</hp:p>'
    )


def _para_empty(para_id: int) -> str:
    """빈 줄 단락. paraPr id=20 (FIXED 5pt) 사용 — 본문 160%보다 간격 크게 안 됨."""
    return (
        f'<hp:p id="{para_id}" paraPrIDRef="20" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="10"/>'
        f'</hp:p>'
    )


# ── 메인 함수 ─────────────────────────────────────────────────

def generate_hwpx(content: str, title: str = "보고서") -> bytes:
    """AI 생성 텍스트를 HWPX 바이너리로 변환."""

    for path in (HEAD_TPL, SUMM_TPL):
        if not os.path.exists(path):
            raise FileNotFoundError(f"템플릿 파일 없음: {path}")

    lines = content.split("\n")

    # ── 콘텐츠 파싱 ───────────────────────────────────────────
    # 순서: 제목(0번줄) → 주관자 블록(선택) → [요약] 블록 → 본문
    report_title = lines[0].strip() if lines else title
    if not report_title or report_title.startswith('['):
        report_title = title

    pre_summary_lines: list[str] = []  # 주관자·날짜 블록 (요약 앞)
    summary_lines: list[str] = []
    summary_ref_lines: list[str] = []  # * 참고줄 (요약 박스 뒤, 중고딕 13pt)
    body_start_idx = 1

    if len(lines) > 1:
        idx = 1
        # 제목 직후 빈 줄 건너뜀
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1

        # [요약] 전까지 모든 줄을 pre_summary로 수집 (주관자 블록 포함)
        while idx < len(lines) and not lines[idx].strip().startswith('[요약]'):
            pre_summary_lines.append(lines[idx])
            idx += 1

        # [요약] 블록 파싱
        if idx < len(lines) and lines[idx].strip().startswith('[요약]'):
            rest = lines[idx].strip().removeprefix('[요약]').strip()
            if rest:
                summary_lines.append(rest)
            idx += 1
            while idx < len(lines):
                stripped = lines[idx].strip()
                if not stripped:
                    break  # 빈 줄 → 요약 블록 종료
                if (re.match(r'^\d+\.', stripped) or stripped.startswith('□')
                        or stripped.startswith('【')):
                    break  # 본문 마커 → 요약 블록 종료
                if stripped.startswith(('◈', 'ㅁ', '◆', '◇')):
                    summary_lines.append(stripped)
                elif stripped.startswith('*'):
                    summary_ref_lines.append(stripped)
                elif summary_lines:
                    summary_lines[-1] += ' ' + stripped  # 이전 불릿의 continuation
                idx += 1
            if idx < len(lines) and lines[idx].strip() == '':
                idx += 1

        # pre_summary 끝의 빈 줄 제거
        while pre_summary_lines and pre_summary_lines[-1].strip() == '':
            pre_summary_lines.pop()

        body_start_idx = idx

    # ── 템플릿 XML 읽기 ────────────────────────────────────────
    with zipfile.ZipFile(HEAD_TPL, 'r') as z:
        head_section_xml = z.read("Contents/section0.xml").decode("utf-8", errors="replace")
        head_header_xml = z.read("Contents/header.xml").decode("utf-8", errors="replace")

    with zipfile.ZipFile(SUMM_TPL, 'r') as z:
        summ_section_xml = z.read("Contents/section0.xml").decode("utf-8", errors="replace")

    # ── 헤더에 폰트/charPr 패치 적용 ──────────────────────────
    patched_header_xml = _patch_header(head_header_xml).encode("utf-8")

    # ── 제목 박스: {{report_title}} 교체 ──────────────────────
    section_xml = head_section_xml.replace(
        '{{report_title}}',
        html.escape(report_title, quote=False)
    )

    # ── 요약 박스: rect 추출 후 플레이스홀더 교체 ─────────────
    rect_xml = _extract_rect(summ_section_xml)

    # summary 템플릿의 charPrIDRef/paraPrIDRef는 summary 헤더 기준.
    # 생성 문서는 head 헤더 기준이므로 재매핑이 필요:
    #   summary charPr 8 (휴먼명조 15pt) → head charPr 10
    #   summary charPr 9 (휴먼명조 15pt) → head charPr 10
    #   summary paraPr 19 (CENTER) → head paraPr 0 (JUSTIFY)
    rect_xml = re.sub(r'charPrIDRef="[89]"', 'charPrIDRef="10"', rect_xml)
    rect_xml = rect_xml.replace('paraPrIDRef="19"', 'paraPrIDRef="0"')

    line1 = _strip_bullet(summary_lines[0]) if len(summary_lines) > 0 else ''
    line2 = _strip_bullet(summary_lines[1]) if len(summary_lines) > 1 else ''

    # {{summary_line_1}} 치환
    rect_xml = rect_xml.replace('{{summary_line_1}}', html.escape(line1, quote=False))

    # {{summary_line_2}} 치환: 내용이 없으면 ◈ 기호만 남는 빈 단락이 생기므로 단락째 제거
    if line2:
        rect_xml = rect_xml.replace('{{summary_line_2}}', html.escape(line2, quote=False))
    else:
        # 플레이스홀더 위치를 기점으로 해당 <hp:p>...</hp:p> 블록만 제거
        # (regex DOTALL은 앞 단락까지 삼켜버리므로 문자열 위치 탐색 사용)
        _marker = '{{summary_line_2}}'
        _pos = rect_xml.find(_marker)
        if _pos != -1:
            _p_start = rect_xml.rfind('<hp:p', 0, _pos)
            _p_end   = rect_xml.find('</hp:p>', _pos) + len('</hp:p>')
            if _p_start != -1 and _p_end > len('</hp:p>') - 1:
                rect_xml = rect_xml[:_p_start] + rect_xml[_p_end:]

    # * 참고줄을 rect 내부(</hp:subList> 앞)에 삽입 — 박스 바깥으로 빠지지 않도록
    # ※ 태그명은 hp:subList (camelCase) — hs:sub-list 아님
    if summary_ref_lines:
        ref_paras_xml = ''.join(
            f'<hp:p id="{3_000_000 + i}" paraPrIDRef="0" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="11"><hp:t>{html.escape(_strip_bold(ln), quote=False)}</hp:t></hp:run>'
            f'</hp:p>'
            for i, ln in enumerate(summary_ref_lines)
        )
        rect_xml = rect_xml.replace('</hp:subList>', ref_paras_xml + '</hp:subList>', 1)

    summary_para = (
        '<hp:p id="2692885479" paraPrIDRef="0" styleIDRef="0" '
        'pageBreak="0" columnBreak="0" merged="0">'
        '<hp:run charPrIDRef="7">'
        + rect_xml +
        '<hp:t/></hp:run>'
        '</hp:p>'
    )

    # ── 주관자 블록 단락 생성 (요약 앞) ─────────────────────────
    # force_single=True: 자간 -20%까지 단계적 압축으로 각 줄이 1줄에 들어오도록 최대화
    pre_paragraphs = []
    for i, line in enumerate(pre_summary_lines):
        pid = 1_000_000 + i
        if line.strip() == "":
            pre_paragraphs.append(_para_empty(pid))
        else:
            pre_paragraphs.append(_para_body(pid, line, force_single=True))

    # ── 본문 단락 생성 (연속 줄은 하나의 단락으로 합침) ─────────
    # AI가 35~40자 줄바꿈을 삽입하더라도 HWPX에서는 단락 내 word-wrap에 맡김.
    # 새 항목 마커(□·◦·-·*·【·번호.)로 시작하지 않는 줄은 이전 단락에 이어 붙임.
    # L1 섹션 제목(번호.) 앞에는 스타일가이드 규정에 따라 빈 줄 1개를 자동 삽입.
    body_lines = lines[body_start_idx:]
    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)

    paragraphs = []
    para_pid = 2_000_000
    cur_line: str | None = None
    prev_was_empty = True   # 첫 섹션 앞에는 빈 줄 삽입 안 함

    for line in body_lines:
        if line.strip() == "":
            if cur_line is not None:
                paragraphs.append(_para_body(para_pid, cur_line))
                para_pid += 1
                cur_line = None
            paragraphs.append(_para_empty(para_pid))
            para_pid += 1
            prev_was_empty = True
        elif _is_new_item(line):
            if cur_line is not None:
                paragraphs.append(_para_body(para_pid, cur_line))
                para_pid += 1
                cur_line = None
                prev_was_empty = False
            # L1 섹션 제목 앞: 빈 줄이 없으면 자동 삽입 (스타일가이드: 목차 전환 시 1칸 띄움)
            if re.match(r'^\d+\.', line.strip()) and paragraphs and not prev_was_empty:
                paragraphs.append(_para_empty(para_pid))
                para_pid += 1
                prev_was_empty = True
            cur_line = line
        else:
            # 연속 줄 — 이전 단락에 이어 붙임 (공백 1칸)
            if cur_line is not None:
                cur_line += " " + line.strip()
            else:
                cur_line = line
            prev_was_empty = False

    if cur_line is not None:
        paragraphs.append(_para_body(para_pid, cur_line))

    # ── XML 조립: 제목 → 주관자 블록 → 요약 박스 → 본문 ────────
    sec_close = '</hs:sec>'
    insert_pos = section_xml.rfind(sec_close)
    if insert_pos == -1:
        insert_pos = len(section_xml)
        sec_close = ''

    new_section_xml = (
        section_xml[:insert_pos]
        + "".join(pre_paragraphs)
        + summary_para
        + "".join(paragraphs)
        + sec_close
    ).encode("utf-8")

    # ── HWPX 재패키징 (head 템플릿 기반) ─────────────────────
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
                elif name == "Contents/header.xml":
                    out.writestr(name, patched_header_xml)
                else:
                    out.writestr(tmpl.getinfo(name), tmpl.read(name))

            out.writestr("Contents/section0.xml", new_section_xml)
            out.writestr("Preview/PrvText.txt", content.encode("utf-8"))

    return buf.getvalue()
