from typing import List, Dict, Any, Optional
from app.models.data import DataSummary, MetricsSummary

class AnalysisService:
    @staticmethod
    def compute_summary(records: List[Dict[str, Any]]) -> DataSummary:
        """
        시계열 데이터 목록을 분석하여 요약 통계 및 트렌드를 산출합니다.
        """
        if not records:
            return DataSummary(
                period="기록 없음",
                count=0,
                metrics=MetricsSummary(
                    total=0,
                    average=0,
                    max=0,
                    max_date="-",
                    min=0,
                    min_date="-"
                ),
                trend="데이터가 없습니다."
            )

        # 날짜 오름차순 정렬
        sorted_records = sorted(records, key=lambda x: str(x.get("date", "")))
        count = len(sorted_records)
        first_date = sorted_records[0].get("date", "")
        last_date = sorted_records[-1].get("date", "")
        period = f"{first_date} ~ {last_date}"

        values = [int(r.get("value", 0)) for r in sorted_records]
        total = sum(values)
        average = round(total / count) if count > 0 else 0

        # 최고 및 최저 매출 탐색
        max_rec = max(sorted_records, key=lambda x: int(x.get("value", 0)))
        min_rec = min(sorted_records, key=lambda x: int(x.get("value", 0)))

        max_val = int(max_rec.get("value", 0))
        max_date = str(max_rec.get("date", "-"))
        min_val = int(min_rec.get("value", 0))
        min_date = str(min_rec.get("date", "-"))

        # 트렌드 계산 (최근 14~30일과 이전 기간 비교)
        trend = AnalysisService._calculate_trend(sorted_records)

        return DataSummary(
            period=period,
            count=count,
            metrics=MetricsSummary(
                total=total,
                average=average,
                max=max_val,
                max_date=max_date,
                min=min_val,
                min_date=min_date,
            ),
            trend=trend,
            details={
                "first_date": first_date,
                "last_date": last_date,
            }
        )

    @staticmethod
    def _calculate_trend(records: List[Dict[str, Any]]) -> str:
        count = len(records)
        if count < 4:
            return "데이터 축적 중 (비교 데이터 부족)"

        # 절반 또는 최근 14~30일 분할 비교
        window = min(30, count // 2)
        recent_records = records[-window:]
        previous_records = records[-2 * window:-window]

        recent_avg = sum(int(r.get("value", 0)) for r in recent_records) / len(recent_records)
        prev_avg = sum(int(r.get("value", 0)) for r in previous_records) / len(previous_records)

        if prev_avg == 0:
            return "신규 유입 구간"

        diff_percent = ((recent_avg - prev_avg) / prev_avg) * 100

        if diff_percent >= 5.0:
            return f"상승세 (최근 {window}일 대비 +{diff_percent:.1f}%)"
        elif diff_percent <= -5.0:
            return f"하락세 (최근 {window}일 대비 {diff_percent:.1f}%)"
        else:
            return f"안정보합 (최근 {window}일 변동률 {diff_percent:+.1f}%)"

analysis_service = AnalysisService()
