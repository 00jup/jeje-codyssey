#!/usr/bin/env python3
"""
삼성전자(005930.KS) 시계열 트렌드 및 변동성 대시보드 (Streamlit)
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# 통계 패키지
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# 페이지 기본 설정
st.set_page_config(
    page_title="삼성전자 주가 시계열 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 캐시된 데이터 로드
@st.cache_data
def get_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "samsung_2023_2024.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
    else:
        import yfinance as yf
        stock = yf.Ticker("005930.KS")
        df = stock.history(start="2023-01-01", end="2024-12-31", auto_adjust=False)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path)
    return df

df_raw = get_data()

# ---------------------------------------------------------
# 사이드바 컨트롤 패널
# ---------------------------------------------------------
st.sidebar.title("⚙️ 분석 필터 및 옵션")

min_date = df_raw.index.min().date()
max_date = df_raw.index.max().date()

# 1. 기간 선택
selected_dates = st.sidebar.date_input(
    "조회 기간 선택",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_filter, end_filter = selected_dates
else:
    start_filter, end_filter = min_date, max_date

# 2. 이동평균선 선택
st.sidebar.markdown("---")
st.sidebar.subheader("이동평균선(MA) 표시")
show_ma20 = st.sidebar.checkbox("20일 이동평균선 (단기)", value=True)
show_ma60 = st.sidebar.checkbox("60일 이동평균선 (중기)", value=True)
show_ma120 = st.sidebar.checkbox("120일 이동평균선 (장기)", value=True)

# 3. 롤링 변동성 윈도우 크기
st.sidebar.markdown("---")
vol_window = st.sidebar.slider("롤링 변동성 계산 윈도우 (거래일)", min_value=5, max_value=60, value=20, step=5)

# 4. 특이 이벤트 표시 토글
show_events = st.sidebar.checkbox("주요 시장 이벤트 표시 (블랙먼데이/자사주)", value=True)

# ---------------------------------------------------------
# 데이터 필터링 및 파생변수 산출
# ---------------------------------------------------------
mask = (df_raw.index.date >= start_filter) & (df_raw.index.date <= end_filter)
df = df_raw.loc[mask].copy()

if df.empty or len(df) < 5:
    st.error("선택한 기간의 데이터가 충분하지 않습니다. 더 긴 기간을 선택하세요.")
    st.stop()

# 기술적 지표 계산
df["Daily_Return"] = df["Close"].pct_change()
df["MA20"] = df["Close"].rolling(window=20).mean()
df["MA60"] = df["Close"].rolling(window=60).mean()
df["MA120"] = df["Close"].rolling(window=120).mean()
df["Volatility"] = df["Daily_Return"].rolling(window=vol_window).std() * np.sqrt(252) * 100

# ---------------------------------------------------------
# 상단 헤더 & 핵심 메트릭 카드
# ---------------------------------------------------------
st.title("📈 삼성전자(005930.KS) 시계열 트렌드 & 변동성 탐색기")
st.caption(f"선택 분석 기간: **{start_filter} ~ {end_filter}** (총 **{len(df)}**개 거래일)")

start_price = df["Close"].iloc[0]
end_price = df["Close"].iloc[-1]
ret = (end_price - start_price) / start_price * 100
max_price = df["Close"].max()
min_price = df["Close"].min()
avg_vol = df["Volatility"].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("시작가", f"{int(start_price):,}원")
col2.metric("최종 종가", f"{int(end_price):,}원", f"{ret:+.2f}%")
col3.metric("기간 최고가", f"{int(max_price):,}원")
col4.metric("기간 최저가", f"{int(min_price):,}원")
col5.metric(f"평균 변동성({vol_window}일)", f"{avg_vol:.2f}%" if pd.notnull(avg_vol) else "-")

st.markdown("---")

# ---------------------------------------------------------
# 탭 구성
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 주가 & 이동평균선",
    "📦 거래량 & 롤링 변동성",
    "🗓️ 월별 수익률 & 계절성",
    "🔮 시계열 분해 & 예측 (보너스)"
])

# -------------------------
# 탭 1: 주가 & 이동평균선
# -------------------------
with tab1:
    st.subheader("주가 추세 및 이동평균선 크로스오버")
    
    chart_data = pd.DataFrame({"종가": df["Close"]})
    if show_ma20 and "MA20" in df:
        chart_data["MA20 (단기)"] = df["MA20"]
    if show_ma60 and "MA60" in df:
        chart_data["MA60 (중기)"] = df["MA60"]
    if show_ma120 and "MA120" in df:
        chart_data["MA120 (장기)"] = df["MA120"]
        
    st.line_chart(chart_data)
    
    st.markdown("""
    > **💡 탐색 팁**: 
    > - **2023년 상반기**: 20일선이 60일선을 상향 돌파(골든크로스)하며 55,000원에서 70,000원대 중반까지 추세적 상승세를 보였습니다.
    > - **2024년 7~8월**: 88,000원 근방 고점 형성 이후 급격한 데드크로스가 발생하여 11월 49,900원까지 장기 하락 국면으로 전개되었습니다.
    """)

# -------------------------
# 탭 2: 거래량 & 변동성
# -------------------------
with tab2:
    st.subheader(f"일별 거래량 및 {vol_window}일 롤링 변동성 (연율화 %)")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.write("##### 일별 거래량 (Volume)")
        st.bar_chart(df["Volume"] / 1_000_000)
        st.caption("단위: 백만 주")
        
    with col_v2:
        st.write(f"##### {vol_window}일 롤링 변동성 (%)")
        st.line_chart(df["Volatility"])
        st.caption(f"연율화(sqrt(252)) 기준, 기간 평균 {avg_vol:.2f}%")
        
    if show_events:
        st.info("""
        **⚡ 주요 시장 충격 이벤트 관측**:
        - **2024-08-05 (글로벌 블랙 먼데이)**: 하루 낙폭 -10.30% 기록, 엔캐리 청산에 따른 충격으로 거래량 급증.
        - **2024-11-15 (10조 원 자사주 매입 발표)**: 5만 전자 붕괴(49,900원) 직후 하루 +7.21% 급반등하며 역사적 거래량 폭발.
        """)

# -------------------------
# 탭 3: 월별 수익률 & 계절성
# -------------------------
with tab3:
    st.subheader("연도별·월별 수익률 비교")
    
    m_prices = df["Close"].resample("ME").last()
    m_ret = m_prices.pct_change() * 100
    m_df = pd.DataFrame({
        "Year": m_ret.index.year,
        "Month": m_ret.index.month,
        "Return": m_ret.values
    }).dropna()
    
    if not m_df.empty:
        pivot_ret = m_df.pivot(index="Month", columns="Year", values="Return")
        pivot_ret.index = [f"{m}월" for m in pivot_ret.index]
        
        st.write("##### 월별 수익률 표 (%)")
        st.dataframe(pivot_ret.style.format("{:+.2f}%").background_gradient(cmap="coolwarm", vmin=-15, vmax=15))
        
        st.bar_chart(pivot_ret)
    else:
        st.warning("선택한 기간에 충분한 월 단위 데이터가 없습니다.")

# -------------------------
# 탭 4: 시계열 분해 & 예측
# -------------------------
with tab4:
    st.subheader("시계열 성분 분해 (STL Additive) & 지수평활 베이스라인 예측")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.write("##### 주가 시계열 성분 분해 (주기 30일)")
        daily_full = df["Close"].asfreq("D").ffill()
        if len(daily_full) >= 60:
            decomp = seasonal_decompose(daily_full, model="additive", period=30)
            decomp_df = pd.DataFrame({
                "추세(Trend)": decomp.trend,
                "계절성(Seasonal)": decomp.seasonal,
                "잔차(Residual)": decomp.resid
            }).dropna()
            st.line_chart(decomp_df[["추세(Trend)"]])
            st.line_chart(decomp_df[["계절성(Seasonal)", "잔차(Residual)"]])
        else:
            st.warning("분해를 수행하기 위해 최소 60일 이상의 연속 데이터가 필요합니다.")
            
    with col_d2:
        st.write("##### 최근 20거래일 베이스라인 예측 vs 실측치")
        if len(df) > 50:
            h = 20
            train = df["Close"].iloc[:-h]
            test = df["Close"].iloc[-h:]
            
            fit = ExponentialSmoothing(train.values, trend="add", damped_trend=True).fit()
            pred = fit.forecast(h)
            
            comp_df = pd.DataFrame({
                "실제 종가(Test)": test.values,
                "지수평활 예측(Pred)": pred
            }, index=test.index)
            
            st.line_chart(comp_df)
            
            mae = np.mean(np.abs(test.values - pred))
            mape = np.mean(np.abs((test.values - pred) / test.values)) * 100
            st.write(f"• **평균 절대 오차 (MAE)**: {mae:,.0f}원")
            st.write(f"• **평균 절대 백분율 오차 (MAPE)**: {mape:.2f}%")
            st.caption("⚠️ 단순 시계열 베이스라인 모델은 거시경제 충격이나 실적 변수를 고려하지 못해 실제 급변 구간에서 래깅(지연) 오차가 발생합니다.")
        else:
            st.warning("예측 모델을 테스트하기 위해 최소 50일 이상의 거래일이 필요합니다.")
