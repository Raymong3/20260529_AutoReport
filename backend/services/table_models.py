"""표 데이터 구조 정의 및 검증 모델."""

from pydantic import BaseModel, model_validator


# 지원하는 열 수 → 대응 템플릿 파일명
SUPPORTED_COLUMN_COUNTS: dict[int, str] = {
    3: "table_3col.hwpx",
    4: "table_4col.hwpx",
    5: "table_5col.hwpx",
}


class TableData(BaseModel):
    """AI가 생성하거나 사용자가 전달하는 표 데이터."""

    caption: str
    """표 제목. 예: '점검 일정', '사업비 현황'"""

    headers: list[str]
    """헤더 셀 목록. 예: ['차수', '시기', '대상']"""

    rows: list[list[str]]
    """데이터 행 목록. 각 행의 길이는 headers와 동일해야 함."""

    @property
    def column_count(self) -> int:
        """열 수 (헤더 기준)."""
        return len(self.headers)

    @property
    def template_filename(self) -> str | None:
        """열 수에 해당하는 템플릿 파일명. 지원되지 않는 열 수면 None."""
        return SUPPORTED_COLUMN_COUNTS.get(self.column_count)

    @model_validator(mode="after")
    def validate_row_lengths(self) -> "TableData":
        """모든 데이터 행의 열 수가 헤더와 일치하는지 검증."""
        for i, row in enumerate(self.rows):
            if len(row) != self.column_count:
                raise ValueError(
                    f"행 {i + 1}의 열 수({len(row)})가 "
                    f"헤더 열 수({self.column_count})와 다릅니다."
                )
        return self

    def is_supported(self) -> bool:
        """현재 열 수가 지원되는지 여부."""
        return self.column_count in SUPPORTED_COLUMN_COUNTS

    def validation_error_message(self) -> str | None:
        """삽입 전 검증. 문제 없으면 None, 있으면 오류 메시지 반환."""
        if not self.headers:
            return "헤더가 비어있습니다."
        if not self.is_supported():
            supported = sorted(SUPPORTED_COLUMN_COUNTS.keys())
            return (
                f"{self.column_count}열 표는 지원하지 않습니다. "
                f"지원 열 수: {supported}"
            )
        return None
