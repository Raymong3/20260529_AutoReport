"""새 템플릿 HWPX 구조 분석"""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with zipfile.ZipFile('template.hwpx') as z:
    print("=== 파일 목록 ===")
    for n in z.namelist():
        print(f"  {n:50s}  {z.getinfo(n).file_size:>10,} bytes")

    # PrvText.txt (평문 미리보기)
    print("\n=== PrvText.txt (처음 80줄) ===")
    txt = z.read('Preview/PrvText.txt').decode('utf-8', errors='replace')
    for i, line in enumerate(txt.splitlines()[:80]):
        print(f"{i+1:3}| {line}")

    # section0.xml 앞부분
    xml = z.read('Contents/section0.xml').decode('utf-8', errors='replace')
    print(f"\n=== section0.xml 크기: {len(xml):,} chars ===")

    # paraPrIDRef 분포
    ppr = re.findall(r'paraPrIDRef="([0-9]+)"', xml)
    from collections import Counter
    print("paraPrIDRef 빈도:", Counter(ppr).most_common(15))

    # styleIDRef 분포
    sty = re.findall(r'styleIDRef="([0-9]+)"', xml)
    print("styleIDRef 빈도:", Counter(sty).most_common(10))

    # charPrIDRef 분포
    cpr = re.findall(r'charPrIDRef="([0-9]+)"', xml)
    print("charPrIDRef 빈도:", Counter(cpr).most_common(10))

    # 표(테이블) 태그 존재 여부
    has_tbl = '<hp:tbl' in xml or '<ht:tbl' in xml or 'tbl' in xml[:5000]
    print(f"\n표(tbl) 태그 존재: {has_tbl}")
    tbl_matches = re.findall(r'<\w+:tbl[\s>]', xml)
    print(f"tbl 태그 종류: {set(tbl_matches)}")

    # header.xml 에서 style/font 정의 확인
    hdr = z.read('Contents/header.xml').decode('utf-8', errors='replace')
    print(f"\n=== header.xml 크기: {len(hdr):,} chars ===")

    # 스타일 이름 추출
    style_names = re.findall(r'<hh:style[^>]+name="([^"]+)"[^>]+>', hdr)
    print("스타일 이름:", style_names[:20])

    # 폰트 이름 추출
    font_names = re.findall(r'face="([^"]+)"', hdr)
    print("폰트 종류:", sorted(set(font_names)))

    # paraPr id별 lineSpacing 추출
    para_spacings = re.findall(r'<hh:paraPr id="([0-9]+)"[^>]*>.*?<hc:paraSpacing[^>]+lineSpacing="([0-9]+)"', hdr, re.DOTALL)
    print("paraPr lineSpacing:", para_spacings[:15])
