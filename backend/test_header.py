from urllib.parse import quote
import re

title = '‘26년 단양수도지사 수도사업장 예초 용역 시행계획 (샘플)'
safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
encoded_name = quote(safe_title, safe='', encoding='utf-8')
header_val = f"attachment; filename*=UTF-8''{encoded_name}"
print(f'encoded_name: {encoded_name[:60]}')
print(f'header_val: {header_val[:80]}')
try:
    header_val.encode('ascii')
    print('ascii encode: OK — header is safe')
except UnicodeEncodeError as e:
    print(f'ascii encode FAILED: {e}')
