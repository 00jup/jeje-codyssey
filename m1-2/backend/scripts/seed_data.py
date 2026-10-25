import datetime
import random
from typing import List, Dict, Any

MEMO_TEMPLATES = [
    "평일 일반 영업",
    "단골 고객 단체 주문",
    "SNS 바이럴 효과로 신규 고객 급증",
    "주말 피크 타임 매장 만석",
    "비 오는 날씨로 방문객 다소 감소",
    "신제품 프로모션 이벤트 진행",
    "주말 배달 및 포장 주문 급증",
    "재고 정기 점검 및 조기 마감",
    "인근 오피스 단체 점심 케이터링",
    "월말 결산 및 정기 고객 감사 쿠폰 발송",
    "가을 시즌 한정 메뉴 런칭",
    "태풍 영향으로 배달 지연 및 매출 감소",
    "주말 가족 단위 고객 방문 증가",
    "인플루언서 방문 후 리뷰 등록 효과",
    "평일 저녁 세트 메뉴 판매 호조",
]

def generate_seed_data(start_date_str: str = "2024-06-01", count: int = 120) -> List[Dict[str, Any]]:
    """
    최소 100개 이상의 현실감 있는 일별 매출 시계열 데이터를 생성합니다.
    """
    start_date = datetime.date.fromisoformat(start_date_str)
    records = []
    
    # 기본 베이스 매출 및 점진적 성장 추세 부여
    base_sales = 450000
    
    for i in range(count):
        current_date = start_date + datetime.timedelta(days=i)
        is_weekend = current_date.weekday() >= 5  # 토, 일
        
        # 월이 지날수록 살짝 성장하는 트렌드
        growth_factor = 1.0 + (i / count) * 0.25  # 최대 +25% 성장
        
        if is_weekend:
            # 주말: 70만 ~ 120만
            daily_base = random.randint(700000, 1150000)
            memo = random.choice([
                "주말 피크 타임 매장 만석",
                "주말 배달 및 포장 주문 급증",
                "주말 가족 단위 고객 방문 증가",
                "SNS 바이럴 효과로 신규 고객 급증"
            ])
        else:
            # 평일: 35만 ~ 65만
            daily_base = random.randint(350000, 620000)
            memo = random.choice([
                "평일 일반 영업",
                "인근 오피스 단체 점심 케이터링",
                "비 오는 날씨로 방문객 다소 감소",
                "평일 저녁 세트 메뉴 판매 호조",
                "신제품 프로모션 이벤트 진행"
            ])
            
        # 특별 이벤트 (최고 매출 / 최저 매출 이벤트 몇 개 삽입)
        if i == 45:
            # 7월 중순 대형 단체 주문 최고 실적
            value = 1850000
            memo = "기업 창립기념일 대규모 단체 주문 (역대 최고 매출)"
        elif i == 80:
            # 8월 하순 시설 보수로 반나절만 영업
            value = 150000
            memo = "수도 배관 긴급 보수로 반나절 조기 마감"
        else:
            value = int(round(daily_base * growth_factor, -3)) # 1000원 단위 반올림

        records.append({
            "id": f"seed_{i+1:03d}",
            "date": current_date.isoformat(),
            "value": value,
            "memo": memo,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        })
        
    return records

if __name__ == "__main__":
    data = generate_seed_data(count=120)
    print(f"Generated {len(data)} seed records.")
    print(f"First record: {data[0]}")
    print(f"Last record: {data[-1]}")
