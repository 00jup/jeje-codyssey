from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class DataCreate(BaseModel):
    date: str = Field(..., description="기록 일자 (YYYY-MM-DD)", examples=["2024-10-15"])
    value: int = Field(..., ge=0, description="일 매출액 (원 단위)", examples=[620000])
    memo: str = Field(..., max_length=300, description="비고/메모", examples=["가을 신제품 프로모션"])

class DataUpdate(BaseModel):
    date: Optional[str] = Field(None, description="기록 일자 (YYYY-MM-DD)")
    value: Optional[int] = Field(None, ge=0, description="일 매출액 (원 단위)")
    memo: Optional[str] = Field(None, max_length=300, description="비고/메모")

class DataResponse(BaseModel):
    id: str
    date: str
    value: int
    memo: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MetricsSummary(BaseModel):
    total: int
    average: int
    max: int
    max_date: Optional[str] = None
    min: int
    min_date: Optional[str] = None

class DataSummary(BaseModel):
    period: str = Field(..., description="데이터 분석 기간 (예: 2024-07-01 ~ 2024-10-31)")
    count: int = Field(..., description="데이터 총 개수")
    metrics: MetricsSummary = Field(..., description="기본 통계 지표")
    trend: str = Field(..., description="최근 추세 (예: 상승 (월평균 +12%))")
    details: Optional[Dict[str, Any]] = None
