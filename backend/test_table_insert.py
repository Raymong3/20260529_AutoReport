"""표 삽입 동작 테스트 스크립트.

실행: python backend/test_table_insert.py
결과 파일: backend/test_output_table.hwpx
"""
import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from services.hwpx_generator import generate_hwpx
from services.table_models import TableData
from services.table_inserter import insert_table_into_hwpx

CONTENT = """\
표 삽입 테스트 보고서

[요약]
◈ 표 삽입 기능 동작 확인
◈ 3열 양식 사용

1. 개요

다음과 같이 점검 일정을 추진함

[[TABLE:t1]]

위 일정에 따라 단계별로 진행 예정

2. 향후 계획

◦ 4열·5열 표 추가 예정
◦ AI 연동 후 자동 표 생성 적용
"""

TABLE_DATA = TableData(
    caption="점검 일정",
    headers=["차수", "시기", "점검 대상"],
    rows=[
        ["1차", "7월 중", "정수장 A"],
        ["2차", "8월 중", "정수장 B"],
        ["3차", "9월 중", "정수장 C"],
    ],
)

MARKER = "[[TABLE:t1]]"

out_path = os.path.join(os.path.dirname(__file__), "test_output_table.hwpx")


def run():
    print("1. generate_hwpx() 호출 중 ...")
    base_bytes = generate_hwpx(CONTENT, title="표 삽입 테스트")
    print(f"   base HWPX 크기: {len(base_bytes):,} bytes")

    print("2. insert_table_into_hwpx() 호출 중 ...")
    result_bytes = insert_table_into_hwpx(base_bytes, TABLE_DATA, MARKER)
    print(f"   결과 HWPX 크기: {len(result_bytes):,} bytes")

    with open(out_path, "wb") as f:
        f.write(result_bytes)

    print(f"3. 저장 완료: {out_path}")
    print()
    print("한컴오피스에서 위 파일을 열어 표가 정상 렌더링되는지 확인해주세요.")


if __name__ == "__main__":
    run()
