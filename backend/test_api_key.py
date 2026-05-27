"""API 키 연결 테스트"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import truststore; truststore.inject_into_ssl()
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(usecwd=True))

from anthropic import Anthropic, APIConnectionError, AuthenticationError, APITimeoutError

api_key = os.environ.get("ANTHROPIC_API_KEY")
print(f"API 키 존재: {'YES' if api_key else 'NO'}")
if api_key:
    print(f"API 키 앞 20자: {api_key[:20]}...")

if not api_key:
    print("ERROR: .env 파일에 ANTHROPIC_API_KEY가 없습니다")
    sys.exit(1)

print("\n연결 테스트 중 (10초 타임아웃)...")
try:
    client = Anthropic(api_key=api_key, timeout=10.0)
    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=20,
        messages=[{"role": "user", "content": "안녕"}],
    )
    print(f"SUCCESS: {resp.content[0].text}")
except AuthenticationError as e:
    print(f"AUTH ERROR: API 키가 유효하지 않습니다 → {e}")
except APITimeoutError:
    print("TIMEOUT: 10초 내에 응답 없음 → 네트워크/프록시 문제")
except APIConnectionError as e:
    print(f"CONNECTION ERROR: 서버 연결 실패 → {e}")
except Exception as e:
    print(f"OTHER ERROR: {type(e).__name__}: {e}")
