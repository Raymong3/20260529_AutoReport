"""HWPX 본문에 표를 삽입하는 모듈.

동작 흐름:
  1. generate_hwpx()로 만든 base HWPX 바이트를 받는다.
  2. 본문 안의 position_marker(예: [[TABLE:t1]])를 찾아 해당 단락을 삭제한다.
  3. 그 자리에 캡션 단락 + 표 단락을 삽입한다.
  4. head_01 기반 header.xml에 표용 borderFill/charPr/paraPr 정의를 추가한다.

ID 재매핑 (표 템플릿 → base 문서):
  borderFillIDRef : 4→6(외곽), 5→7(헤더셀), 6→8(헤더마지막), 7→9(데이터셀), 8→10(데이터마지막)
  charPrIDRef     : 9→16(데이터 한컴돋움 13pt), 10→17(헤더 한컴돋움 13pt)
  paraPrIDRef     : 20→21(셀 내 CENTER 150%)

charPr 번호 체계 (hwpx_generator._patch_header 이후 기준):
  0~8  : head_01.hwpx 템플릿 원본
  9~15 : hwpx_generator._patch_header 추가 (9~13=본문용, 14~15=-20%강제1줄용)
  16~17: 이 모듈 _patch_header_for_table 추가 (표 셀용 한컴돋움 13pt)

paraPr 번호 체계:
  0~20 : head_01.hwpx 원본 (0=JUSTIFY160%, 19=CENTER제목박스)
  20   : hwpx_generator 빈 줄용 FIXED 5pt
  21   : 이 모듈 표 셀 CENTER 150%
  22   : 이 모듈 표 캡션 CENTER 160%
"""
import html
import io
import os
import re
import zipfile

from .table_models import TableData

_TABLE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "table")

# ── ID 재매핑 테이블 ─────────────────────────────────────────────
_BF_REMAP = {"4": "6", "5": "7", "6": "8", "7": "9", "8": "10"}
_CP_REMAP = {"8": "16", "9": "16", "10": "17", "11": "17"}  # 마지막 열 셀은 cp=8(데이터), cp=11(헤더)
_PP_REMAP = {"19": "21", "20": "21"}  # 헤더셀=19, 데이터셀=20 → 모두 21(CENTER 150%)


# ── 단일 패스 속성값 재매핑 ──────────────────────────────────────

def _remap_attr(xml: str, attr: str, remap: dict[str, str]) -> str:
    """xml에서 attr="old" 를 attr="new" 로 단일 패스 치환한다.

    루프 replace()는 4→6→8→10 같은 연쇄 치환이 발생하므로 regex를 사용.
    """
    pattern = re.compile(
        attr + r'="(' + '|'.join(re.escape(k) for k in remap) + r')"'
    )
    return pattern.sub(lambda m: f'{attr}="{remap[m.group(1)]}"', xml)


# ── header.xml 추가 정의 ─────────────────────────────────────────

_TABLE_BF_XML = (
    # bf=6: 표 외곽선 (solid all)
    '<hh:borderFill id="6" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>'
    '</hh:borderFill>'
    # bf=7: 헤더 셀 (좌선 없음, 회색 배경)
    '<hh:borderFill id="7" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:leftBorder type="NONE" width="0.12 mm" color="#000000"/>'
    '<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>'
    '<hc:fillBrush><hc:winBrush faceColor="#F2F2F2" hatchColor="#999999" alpha="0"/></hc:fillBrush>'
    '</hh:borderFill>'
    # bf=8: 헤더 마지막 셀 (우선 없음, 회색 배경)
    '<hh:borderFill id="8" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:rightBorder type="NONE" width="0.12 mm" color="#000000"/>'
    '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>'
    '<hc:fillBrush><hc:winBrush faceColor="#F2F2F2" hatchColor="#999999" alpha="0"/></hc:fillBrush>'
    '</hh:borderFill>'
    # bf=9: 데이터 셀 (좌선 없음, 배경 없음)
    '<hh:borderFill id="9" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:leftBorder type="NONE" width="0.12 mm" color="#000000"/>'
    '<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>'
    '</hh:borderFill>'
    # bf=10: 데이터 마지막 셀 (우선 없음, 배경 없음)
    '<hh:borderFill id="10" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
    '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
    '<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:rightBorder type="NONE" width="0.12 mm" color="#000000"/>'
    '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>'
    '</hh:borderFill>'
)

# fontRef=4 = 한컴돋움 (head_01 패치 기준) — base_rules: 표 폰트 중고딕(고딕계열) 13pt
_TABLE_CHARPR_XML = (
    # cp=16: 한컴돋움 13pt, 자간 0% — 데이터 셀
    '<hh:charPr id="16" height="1300" textColor="#000000" shadeColor="none" '
    'useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">'
    '<hh:fontRef hangul="4" latin="4" hanja="4" japanese="4" other="4" symbol="4" user="4"/>'
    '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:underline type="NONE" shape="SOLID" color="#000000"/>'
    '<hh:strikeout shape="NONE" color="#000000"/>'
    '<hh:outline type="NONE"/>'
    '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
    '</hh:charPr>'
    # cp=17: 한컴돋움 13pt, 자간 0% — 헤더 셀
    '<hh:charPr id="17" height="1300" textColor="#000000" shadeColor="none" '
    'useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">'
    '<hh:fontRef hangul="4" latin="4" hanja="4" japanese="4" other="4" symbol="4" user="4"/>'
    '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
    '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
    '<hh:underline type="NONE" shape="SOLID" color="#000000"/>'
    '<hh:strikeout shape="NONE" color="#000000"/>'
    '<hh:outline type="NONE"/>'
    '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/>'
    '</hh:charPr>'
)

# pp=21: CENTER + PERCENT 150% — 표 셀 단락 스타일
# pp=22: CENTER + PERCENT 160% — 표 캡션 단락 스타일 (base_rules: 캡션 가운데 정렬)
_TABLE_PARAPR_XML = (
    '<hh:paraPr id="21" tabPrIDRef="0" condense="0" fontLineHeight="0" '
    'snapToGrid="1" suppressLineNumbers="0" checked="0">'
    '<hh:align horizontal="CENTER" vertical="BASELINE"/>'
    '<hh:heading type="NONE" idRef="0" level="0"/>'
    '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="BREAK_WORD" '
    'widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
    '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
    '<hp:switch>'
    '<hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">'
    '<hh:margin>'
    '<hc:intent value="-2345" unit="HWPUNIT"/>'
    '<hc:left value="0" unit="HWPUNIT"/>'
    '<hc:right value="0" unit="HWPUNIT"/>'
    '<hc:prev value="0" unit="HWPUNIT"/>'
    '<hc:next value="0" unit="HWPUNIT"/>'
    '</hh:margin>'
    '<hh:lineSpacing type="PERCENT" value="150" unit="HWPUNIT"/>'
    '</hp:case>'
    '<hp:default>'
    '<hh:margin>'
    '<hc:intent value="-4690" unit="HWPUNIT"/>'
    '<hc:left value="0" unit="HWPUNIT"/>'
    '<hc:right value="0" unit="HWPUNIT"/>'
    '<hc:prev value="0" unit="HWPUNIT"/>'
    '<hc:next value="0" unit="HWPUNIT"/>'
    '</hh:margin>'
    '<hh:lineSpacing type="PERCENT" value="150" unit="HWPUNIT"/>'
    '</hp:default>'
    '</hp:switch>'
    '<hh:border borderFillIDRef="2" offsetLeft="0" offsetRight="0" '
    'offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/>'
    '</hh:paraPr>'
)

# pp=22: CENTER + PERCENT 160% — 표 캡션 단락 스타일 (base_rules: 가운데 정렬)
_TABLE_CAPTION_PARAPR_XML = (
    '<hh:paraPr id="22" tabPrIDRef="0" condense="0" fontLineHeight="0" '
    'snapToGrid="1" suppressLineNumbers="0" checked="0">'
    '<hh:align horizontal="CENTER" vertical="BASELINE"/>'
    '<hh:heading type="NONE" idRef="0" level="0"/>'
    '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" '
    'widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
    '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
    '<hp:switch>'
    '<hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">'
    '<hh:margin>'
    '<hc:intent value="0" unit="HWPUNIT"/>'
    '<hc:left value="0" unit="HWPUNIT"/>'
    '<hc:right value="0" unit="HWPUNIT"/>'
    '<hc:prev value="0" unit="HWPUNIT"/>'
    '<hc:next value="0" unit="HWPUNIT"/>'
    '</hh:margin>'
    '<hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>'
    '</hp:case>'
    '<hp:default>'
    '<hh:margin>'
    '<hc:intent value="0" unit="HWPUNIT"/>'
    '<hc:left value="0" unit="HWPUNIT"/>'
    '<hc:right value="0" unit="HWPUNIT"/>'
    '<hc:prev value="0" unit="HWPUNIT"/>'
    '<hc:next value="0" unit="HWPUNIT"/>'
    '</hh:margin>'
    '<hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>'
    '</hp:default>'
    '</hp:switch>'
    '<hh:border borderFillIDRef="2" offsetLeft="0" offsetRight="0" '
    'offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/>'
    '</hh:paraPr>'
)


# ── header.xml 패치 ──────────────────────────────────────────────

def _patch_header_for_table(header_xml: str) -> str:
    """이미 _patch_header()가 적용된 header.xml에 표용 정의를 추가한다.

    idempotent: borderFill id=6이 이미 있으면 건너뜀.
    """
    if 'borderFill id="6"' in header_xml:
        return header_xml  # 이미 패치됨

    # borderFills: 5 → 10
    header_xml = re.sub(
        r'(<hh:borderFills itemCnt=)"5"', r'\1"10"', header_xml
    )
    header_xml = header_xml.replace(
        '</hh:borderFills>', _TABLE_BF_XML + '</hh:borderFills>'
    )

    # charProperties: 16 → 18 (hwpx_generator._patch_header 이후 16개 → 2개 추가 = 18개)
    header_xml = re.sub(
        r'(<hh:charProperties itemCnt=)"16"', r'\1"18"', header_xml
    )
    header_xml = header_xml.replace(
        '</hh:charProperties>', _TABLE_CHARPR_XML + '</hh:charProperties>'
    )

    # paraProperties: 21 → 23 (표 셀 paraPr id=21 + 캡션 paraPr id=22 추가)
    header_xml = re.sub(
        r'(<hh:paraProperties itemCnt=)"21"', r'\1"23"', header_xml
    )
    header_xml = header_xml.replace(
        '</hh:paraProperties>',
        _TABLE_PARAPR_XML + _TABLE_CAPTION_PARAPR_XML + '</hh:paraProperties>'
    )

    return header_xml


# ── 표 XML 조립 ──────────────────────────────────────────────────

def _build_table_xml_from_scratch(table_data: TableData) -> str:
    """템플릿 파일 없이 직접 표 XML을 생성한다.

    실제 head_01.hwpx에서 추출한 구조를 기반으로 하며,
    ID 재매핑 후 최종 ID를 직접 사용하므로 _remap_attr 불필요.

    borderFill: 6=외곽, 7=헤더셀(회색), 8=헤더마지막, 9=데이터셀, 10=데이터마지막
    charPr: 16=중고딕13pt데이터, 17=중고딕13pt헤더
    paraPr: 21=CENTER 150%
    """
    n_col = table_data.column_count
    n_row_data = len(table_data.rows)
    n_row_total = 1 + n_row_data

    # 열 너비 (A4 본문 폭 기준 ≈ 168mm)
    total_w = 47618
    col_w_base = total_w // n_col
    col_widths = [col_w_base] * (n_col - 1) + [total_w - col_w_base * (n_col - 1)]

    header_h = 2400   # 헤더 행 높이 (≈ 8.5mm)
    data_h   = 2000   # 데이터 행 높이 (≈ 7mm)
    total_h  = header_h + data_h * n_row_data

    def _cell(ci: int, ri: int, text: str, is_header: bool, w: int, h: int) -> str:
        is_last = ci == n_col - 1
        if is_header:
            bf = "8" if is_last else "7"
            cp, pp = "17", "21"  # 중고딕 13pt 헤더
        else:
            bf = "10" if is_last else "9"
            cp, pp = "16", "21"  # 중고딕 13pt 데이터
        pid = 2_147_483_648 + ri * 1000 + ci
        return (
            f'<hp:tc name="" header="{1 if is_header else 0}" hasMargin="0" '
            f'protect="0" editable="0" dirty="0" borderFillIDRef="{bf}">'
            f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
            f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" '
            f'hasTextRef="0" hasNumRef="0">'
            f'<hp:p id="{pid}" paraPrIDRef="{pp}" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{cp}"><hp:t>{html.escape(text, quote=False)}</hp:t></hp:run>'
            f'</hp:p>'
            f'</hp:subList>'
            f'<hp:cellAddr colAddr="{ci}" rowAddr="{ri}"/>'
            f'<hp:cellSpan colSpan="1" rowSpan="1"/>'
            f'<hp:cellSz width="{w}" height="{h}"/>'
            f'<hp:cellMargin left="141" right="141" top="141" bottom="141"/>'
            f'</hp:tc>'
        )

    tbl = (
        f'<hp:tbl id="9001" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" '
        f'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" '
        f'repeatHeader="1" rowCnt="{n_row_total}" colCnt="{n_col}" '
        f'cellSpacing="0" borderFillIDRef="6" noAdjust="0">'
        f'<hp:sz width="{total_w}" widthRelTo="ABSOLUTE" height="{total_h}" '
        f'heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
        f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" '
        f'vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
        f'<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
        f'<hp:inMargin left="283" right="283" top="0" bottom="0"/>'
    )

    # 헤더 행
    tbl += '<hp:tr>' + ''.join(
        _cell(ci, 0, hdr, True, w, header_h)
        for ci, (hdr, w) in enumerate(zip(table_data.headers, col_widths))
    ) + '</hp:tr>'

    # 데이터 행
    for ri, row in enumerate(table_data.rows):
        tbl += '<hp:tr>' + ''.join(
            _cell(ci, ri + 1, cell, False, w, data_h)
            for ci, (cell, w) in enumerate(zip(row, col_widths))
        ) + '</hp:tr>'

    tbl += '</hp:tbl>'
    return tbl


def _extract_cells(tr_content: str) -> list[str]:
    """<hp:tr> 내용에서 각 <hp:tc>...</hp:tc> 목록을 반환."""
    return re.findall(r'<hp:tc .*?</hp:tc>', tr_content, re.DOTALL)


def _make_cell(template_tc: str, text: str, col_addr: int, row_addr: int) -> str:
    """템플릿 셀에서 텍스트와 주소를 교체한 새 셀 XML을 반환.

    - <hp:t> 내용 교체
    - <hp:linesegarray> 제거 (재계산 필요 없음, 뷰어가 자동 처리)
    - cellAddr, p id 업데이트
    """
    tc = re.sub(
        r'<hp:t>[^<]*</hp:t>',
        f'<hp:t>{html.escape(text, quote=False)}</hp:t>',
        template_tc,
    )
    tc = re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>', '', tc, flags=re.DOTALL)
    tc = re.sub(
        r'<hp:cellAddr colAddr="\d+" rowAddr="\d+"',
        f'<hp:cellAddr colAddr="{col_addr}" rowAddr="{row_addr}"',
        tc,
    )
    tc = re.sub(
        r'<hp:p id="\d+"',
        f'<hp:p id="{2_147_483_648 + row_addr * 1000 + col_addr}"',
        tc,
    )
    return tc


def _build_table_xml(tpl_section_xml: str, table_data: TableData) -> str:
    """템플릿 section0.xml에서 hp:tbl을 추출하고 헤더·데이터 행을 교체한 표 XML을 반환."""
    tbl_start = tpl_section_xml.find('<hp:tbl ')
    tbl_end = tpl_section_xml.find('</hp:tbl>', tbl_start) + len('</hp:tbl>')
    tbl_xml = tpl_section_xml[tbl_start:tbl_end]

    new_row_count = 1 + len(table_data.rows)
    tbl_xml = re.sub(r'rowCnt="\d+"', f'rowCnt="{new_row_count}"', tbl_xml)

    tr_list = re.findall(r'<hp:tr>(.*?)</hp:tr>', tbl_xml, re.DOTALL)
    header_cells = _extract_cells(tr_list[0])
    data_cells = _extract_cells(tr_list[1])

    # 헤더 행
    new_header = '<hp:tr>' + ''.join(
        _make_cell(header_cells[col_idx], hdr_text, col_idx, 0)
        for col_idx, hdr_text in enumerate(table_data.headers)
    ) + '</hp:tr>'

    # 데이터 행들
    new_data_rows = ''.join(
        '<hp:tr>' + ''.join(
            _make_cell(data_cells[col_idx], cell_text, col_idx, row_idx + 1)
            for col_idx, cell_text in enumerate(row)
        ) + '</hp:tr>'
        for row_idx, row in enumerate(table_data.rows)
    )

    # 기존 행 블록 교체
    body_start = tbl_xml.find('<hp:tr>')
    body_end = tbl_xml.rfind('</hp:tr>') + len('</hp:tr>')
    new_tbl_xml = tbl_xml[:body_start] + new_header + new_data_rows + tbl_xml[body_end:]

    # ID 재매핑 (tbl XML 내에서만) — 단일 패스로 처리하여 연쇄 치환 방지
    new_tbl_xml = _remap_attr(new_tbl_xml, "borderFillIDRef", _BF_REMAP)
    new_tbl_xml = _remap_attr(new_tbl_xml, "charPrIDRef", _CP_REMAP)
    new_tbl_xml = _remap_attr(new_tbl_xml, "paraPrIDRef", _PP_REMAP)

    return new_tbl_xml


# ── 단락 XML 생성 헬퍼 ───────────────────────────────────────────

def _caption_para(caption: str, para_id: int) -> str:
    """캡션 단락: 표 바로 위에 '【 ... 】' 형식으로 가운데 정렬 삽입.
    paraPrIDRef=22 → CENTER 160% (base_rules: 표 캡션 가운데 정렬)
    """
    text = f'【 {caption} 】'
    return (
        f'<hp:p id="{para_id}" paraPrIDRef="22" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="10"><hp:t>'
        f'{html.escape(text, quote=False)}</hp:t></hp:run>'
        f'</hp:p>'
    )


def _table_para(table_xml: str, para_id: int) -> str:
    """표를 인라인 오브젝트로 감싼 단락 XML."""
    return (
        f'<hp:p id="{para_id}" paraPrIDRef="0" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="7">'
        f'{table_xml}'
        f'<hp:t/></hp:run>'
        f'</hp:p>'
    )


# ── 마커 교체 ────────────────────────────────────────────────────

def _replace_marker_paragraph(
    section_xml: str,
    marker: str,
    replacement_xml: str,
) -> str:
    """마커 텍스트를 포함하는 <hp:p>...</hp:p> 전체를 replacement_xml로 교체한다.

    마커를 찾지 못하면 section_xml을 그대로 반환한다.
    """
    pos = section_xml.find(marker)
    if pos == -1:
        return section_xml

    para_start = section_xml.rfind('<hp:p ', 0, pos)
    if para_start == -1:
        return section_xml

    para_end = section_xml.find('</hp:p>', pos)
    if para_end == -1:
        return section_xml
    para_end += len('</hp:p>')

    return section_xml[:para_start] + replacement_xml + section_xml[para_end:]


# ── 공개 API ─────────────────────────────────────────────────────

def insert_table_into_hwpx(
    base_hwpx_bytes: bytes,
    table_data: TableData,
    position_marker: str,
) -> bytes:
    """base HWPX에서 position_marker를 찾아 그 위치에 표를 삽입한 새 HWPX를 반환한다.

    Args:
        base_hwpx_bytes: generate_hwpx()로 만든 HWPX 바이너리.
        table_data: 삽입할 표 데이터. column_count가 3/4/5이어야 한다.
        position_marker: 표를 삽입할 위치를 표시하는 텍스트 (예: "[[TABLE:t1]]").
                         base HWPX 본문에 이 텍스트가 단독 단락으로 있어야 한다.

    Returns:
        표가 삽입된 HWPX 바이너리.

    Raises:
        ValueError: table_data 검증 실패 시.
        FileNotFoundError: 표 양식 파일이 없을 때.
    """
    err = table_data.validation_error_message()
    if err:
        raise ValueError(err)

    tpl_path = os.path.join(_TABLE_DIR, table_data.template_filename)  # type: ignore[arg-type]
    if os.path.exists(tpl_path):
        with zipfile.ZipFile(tpl_path, 'r') as z:
            tpl_section_xml = z.read("Contents/section0.xml").decode("utf-8", errors="replace")
        table_xml = _build_table_xml(tpl_section_xml, table_data)
    else:
        # 템플릿 파일 없음 → 코드에서 직접 표 XML 생성
        table_xml = _build_table_xml_from_scratch(table_data)

    # 캡션 + 표 단락 XML (para id는 마커 위치 기반으로 충분히 큰 값 사용)
    replacement_xml = (
        _caption_para(table_data.caption, 7_000_000)
        + _table_para(table_xml, 7_000_001)
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(base_hwpx_bytes), 'r') as src:
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as dst:
            for name in src.namelist():
                data = src.read(name)

                if name == "mimetype":
                    zi = zipfile.ZipInfo("mimetype")
                    zi.compress_type = zipfile.ZIP_STORED
                    dst.writestr(zi, data)

                elif name == "Contents/header.xml":
                    header_xml = data.decode("utf-8", errors="replace")
                    header_xml = _patch_header_for_table(header_xml)
                    dst.writestr(name, header_xml.encode("utf-8"))

                elif name == "Contents/section0.xml":
                    section_xml = data.decode("utf-8", errors="replace")
                    section_xml = _replace_marker_paragraph(
                        section_xml, position_marker, replacement_xml
                    )
                    dst.writestr(name, section_xml.encode("utf-8"))

                elif name in ("Preview/PrvImage.png",):
                    pass  # 미리보기 이미지는 생략 (stale)

                else:
                    dst.writestr(src.getinfo(name), data)

    return buf.getvalue()
