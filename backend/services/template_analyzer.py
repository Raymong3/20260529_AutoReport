"""HWPX 템플릿 구조 분석 유틸리티 (모드 A용)"""
import zipfile
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def analyze_hwpx(filepath: str) -> dict:
    """HWPX 파일 내부 구조를 분석하여 결과를 반환합니다."""
    result = {}
    with zipfile.ZipFile(filepath) as z:
        result['files'] = [
            {'name': n, 'size': z.getinfo(n).file_size}
            for n in z.namelist()
        ]

        # PrvText.txt
        try:
            result['preview_text'] = z.read('Preview/PrvText.txt').decode('utf-8', errors='replace')
        except KeyError:
            result['preview_text'] = ''

        # section0.xml 분석
        xml = z.read('Contents/section0.xml').decode('utf-8', errors='replace')
        result['section_xml_size'] = len(xml)
        result['para_pr_freq'] = Counter(re.findall(r'paraPrIDRef="([0-9]+)"', xml)).most_common(15)
        result['style_id_freq'] = Counter(re.findall(r'styleIDRef="([0-9]+)"', xml)).most_common(10)
        result['char_pr_freq'] = Counter(re.findall(r'charPrIDRef="([0-9]+)"', xml)).most_common(10)
        result['has_table'] = bool(re.findall(r'<\w+:tbl[\s>]', xml))

        # header.xml 분석
        hdr = z.read('Contents/header.xml').decode('utf-8', errors='replace')
        result['header_xml_size'] = len(hdr)
        result['style_names'] = re.findall(r'<hh:style[^>]+name="([^"]+)"[^>]+>', hdr)[:20]
        result['font_names'] = sorted(set(re.findall(r'face="([^"]+)"', hdr)))
        result['para_spacings'] = re.findall(
            r'<hh:paraPr id="([0-9]+)"[^>]*>.*?<hc:paraSpacing[^>]+lineSpacing="([0-9]+)"',
            hdr, re.DOTALL
        )[:15]

    return result


if __name__ == '__main__':
    import json
    target = sys.argv[1] if len(sys.argv) > 1 else 'template.hwpx'
    data = analyze_hwpx(target)
    print(json.dumps(data, ensure_ascii=False, indent=2))
