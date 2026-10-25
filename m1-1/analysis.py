#!/usr/bin/env python3
"""
삼성전자(005930.KS) 2023~2024년 시계열 주가 트렌드 및 변동성 분석 스크립트
"""

import os
import sys
import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from dotenv import load_dotenv

# 통계 및 시계열 패키지
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ---------------------------------------------------------
# 1. 환경 설정 및 폰트 설정
# ---------------------------------------------------------
load_dotenv()

TICKER = os.getenv("TICKER", "005930.KS")
START_DATE = os.getenv("START_DATE", "2023-01-01")
END_DATE = os.getenv("END_DATE", "2024-12-31")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, os.getenv("DATA_PATH", "data/samsung_2023_2024.csv"))
IMAGES_DIR = os.path.join(BASE_DIR, os.getenv("IMAGES_DIR", "images"))

os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def setup_matplotlib_korean():
    """OS 환경에 맞춰 한글 폰트를 자동 설정하고 마이너스 깨짐을 방지합니다."""
    system = platform.system()
    if system == "Darwin":  # macOS
        fonts = ["Apple SD Gothic Neo", "AppleGothic", "NanumGothic"]
    elif system == "Windows":
        fonts = ["Malgun Gothic", "NanumGothic"]
    else:  # Linux
        fonts = ["NanumGothic", "DejaVu Sans"]
    
    import matplotlib.font_manager as fm
    available_fonts = {f.name for f in fm.fontManager.ttflist}
    
    selected_font = "sans-serif"
    for f in fonts:
        if f in available_fonts:
            selected_font = f
            break
            
    plt.rcParams["font.family"] = selected_font
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid", font=selected_font)
    print(f"[*] Matplotlib 한글 폰트 설정: {selected_font}")

setup_matplotlib_korean()

# ---------------------------------------------------------
# 2. 데이터 수집 및 로컬 캐싱
# ---------------------------------------------------------
def load_or_fetch_data(ticker: str, start: str, end: str, file_path: str) -> pd.DataFrame:
    """로컬 캐시가 있으면 로드하고, 없으면 yfinance로 다운로드하여 CSV로 저장합니다."""
    if os.path.exists(file_path):
        print(f"[*] 로컬 캐시 데이터 로드: {file_path}")
        df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
        return df

    print(f"[*] Yahoo Finance에서 데이터 다운로드 중... ({ticker}, {start} ~ {end})")
    import yfinance as yf
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end, auto_adjust=False)
    
    if df.empty:
        raise ValueError(f"데이터를 가져오지 못했습니다. 티커({ticker}) 및 네트워크를 확인하세요.")
        
    # 타임존 정보 제거 (단순 일자 DatetimeIndex로 변환)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    # 필요한 핵심 컬럼만 유지
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.to_csv(file_path)
    print(f"[*] 데이터 저장 완료: {file_path} (총 {len(df)}개 거래일)")
    return df

# ---------------------------------------------------------
# 3. 데이터 검증 및 기술적 지표 생성
# ---------------------------------------------------------
def preprocess_and_calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """결측치 검증 및 주요 시계열 기술 지표(이동평균, 수익률, 변동성)를 계산합니다."""
    df = df.copy()
    df.sort_index(inplace=True)
    
    # 1) 결측치 검증
    missing_count = df.isnull().sum()
    print("\n[데이터 품질 검증 - 결측치 현황]")
    print(missing_count)
    if missing_count.sum() > 0:
        print("[!] 결측치 발견: 선형 보간(interpolate) 및 전일치 대체(ffill)를 적용합니다.")
        df = df.interpolate(method="time").ffill().bfill()
    else:
        print("[✓] 결측치 없음 (데이터 무결성 확인)")
        
    # 2) 일간 수익률 (Daily Return)
    df["Daily_Return"] = df["Close"].pct_change()
    
    # 3) 이동평균선 (20일, 60일, 120일)
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    df["MA120"] = df["Close"].rolling(window=120).mean()
    
    # 4) 20일 롤링 변동성 (연율화: 252 거래일 기준)
    # 표준편차 * sqrt(252) * 100 (%)
    df["Volatility_20d"] = df["Daily_Return"].rolling(window=20).std() * np.sqrt(252) * 100
    
    # 5) 골든크로스 / 데드크로스 신호 (20일선 vs 60일선)
    # 20일선이 60일선을 상향 돌파하면 Golden Cross(1), 하향 돌파하면 Dead Cross(-1)
    df["Signal"] = 0
    ma_diff = df["MA20"] - df["MA60"]
    cross_up = (ma_diff > 0) & (ma_diff.shift(1) <= 0)
    cross_down = (ma_diff < 0) & (ma_diff.shift(1) >= 0)
    df.loc[cross_up, "Signal"] = 1
    df.loc[cross_down, "Signal"] = -1
    
    return df

# ---------------------------------------------------------
# 4. 시각화 함수 정의
# ---------------------------------------------------------
def plot_01_price_and_volume(df: pd.DataFrame, save_path: str):
    """시각화 1: 종가 추세 및 거래량, 변곡점(최고가/최저가) 주석"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    
    # 상단: 주가 추세
    ax1.plot(df.index, df["Close"], label="종가 (KRW)", color="#1f77b4", linewidth=2)
    
    # 최고점 및 최저점 주석
    max_idx = df["Close"].idxmax()
    max_val = df.loc[max_idx, "Close"]
    min_idx = df["Close"].idxmin()
    min_val = df.loc[min_idx, "Close"]
    
    ax1.scatter([max_idx], [max_val], color="#d62728", s=100, zorder=5, label=f"최고가: {int(max_val):,}원 ({max_idx.strftime('%Y-%m-%d')})")
    ax1.annotate(f"역사적 최고점\n{int(max_val):,}원 ({max_idx.strftime('%m/%d')})",
                 xy=(max_idx, max_val), xytext=(max_idx - pd.Timedelta(days=50), max_val + 3500),
                 arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1.5, headwidth=8),
                 fontsize=10, fontweight="bold", color="#d62728",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#ffeded", ec="#d62728", lw=1))
    
    ax1.scatter([min_idx], [min_val], color="#2ca02c", s=100, zorder=5, label=f"최저가: {int(min_val):,}원 ({min_idx.strftime('%Y-%m-%d')})")
    ax1.annotate(f"역사적 최저점\n{int(min_val):,}원 ({min_idx.strftime('%m/%d')})",
                 xy=(min_idx, min_val), xytext=(min_idx - pd.Timedelta(days=60), min_val - 6000),
                 arrowprops=dict(facecolor="#2ca02c", shrink=0.08, width=1.5, headwidth=8),
                 fontsize=10, fontweight="bold", color="#2ca02c",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#eefbee", ec="#2ca02c", lw=1))
    
    # 주요 이벤트 마킹 (2024-08-05 블랙먼데이, 2024-11-15 자사주 매입)
    bm_date = pd.Timestamp("2024-08-05")
    if bm_date in df.index:
        ax1.axvline(bm_date, color="#ff7f0e", linestyle="--", alpha=0.7, label="글로벌 증시 급락(블랙먼데이)")
        ax1.text(bm_date, df["Close"].min() + 8000, " 8/5 급락", color="#ff7f0e", fontsize=9, fontweight="bold")
        
    ax1.set_title("삼성전자(005930.KS) 2023~2024년 주가 추세 및 변곡점 분석", fontsize=16, fontweight="bold", pad=12)
    ax1.set_ylabel("주가 (원, KRW)", fontsize=12)
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    # 하단: 일별 거래량
    colors = ["#2ca02c" if r >= 0 else "#d62728" for r in df["Daily_Return"].fillna(0)]
    ax2.bar(df.index, df["Volume"] / 1_000_000, color=colors, alpha=0.7, width=1.2, label="거래량(백만 주)")
    ax2.set_ylabel("거래량 (백만 주)", fontsize=11)
    ax2.set_xlabel("거래 일자", fontsize=12)
    ax2.legend(loc="upper left", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    # X축 포맷
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] 시각화 1 저장 완료: {save_path}")

def plot_02_moving_average_and_signals(df: pd.DataFrame, save_path: str):
    """시각화 2: 20일, 60일, 120일 이동평균선과 골든크로스/데드크로스 신호"""
    plt.figure(figsize=(14, 7))
    
    plt.plot(df.index, df["Close"], label="종가 (Close)", color="#8c8c8c", alpha=0.6, linewidth=1.2)
    plt.plot(df.index, df["MA20"], label="단기선 (MA 20일)", color="#e41a1c", linewidth=1.8)
    plt.plot(df.index, df["MA60"], label="중기선 (MA 60일)", color="#377eb8", linewidth=1.8)
    plt.plot(df.index, df["MA120"], label="장기선 (MA 120일)", color="#4daf4a", linewidth=1.8, linestyle="--")
    
    # 골든크로스 및 데드크로스 마커 표시
    golden_crosses = df[df["Signal"] == 1]
    dead_crosses = df[df["Signal"] == -1]
    
    plt.scatter(golden_crosses.index, golden_crosses["MA20"], color="red", marker="^", s=130, zorder=5,
                label=f"골든크로스(20일>60일, {len(golden_crosses)}회)")
    plt.scatter(dead_crosses.index, dead_crosses["MA20"], color="blue", marker="v", s=130, zorder=5,
                label=f"데드크로스(20일<60일, {len(dead_crosses)}회)")
    
    plt.title("삼성전자 중단기 이동평균선(20/60/120일) 및 골든·데드크로스 시그널", fontsize=15, fontweight="bold", pad=12)
    plt.xlabel("거래 일자", fontsize=12)
    plt.ylabel("주가 (원, KRW)", fontsize=12)
    plt.legend(loc="upper left", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    
    # 주요 국면 텍스트 강조
    plt.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2024-07-10"), color="red", alpha=0.04, label="_nolegend_")
    plt.axvspan(pd.Timestamp("2024-07-11"), pd.Timestamp("2024-12-31"), color="blue", alpha=0.04, label="_nolegend_")
    plt.text(pd.Timestamp("2023-08-01"), 83000, "[상승/우상향 국면]", fontsize=11, color="darkred", fontweight="bold")
    plt.text(pd.Timestamp("2024-08-15"), 83000, "[하락/데드크로스 국면]", fontsize=11, color="darkblue", fontweight="bold")
    
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] 시각화 2 저장 완료: {save_path}")

def plot_03_monthly_return_distribution(df: pd.DataFrame, save_path: str):
    """시각화 3: 2023년 vs 2024년 월별 수익률 비교 바차트 및 박스플롯"""
    # 월별 수익률 계산 (각 월의 첫날 시가 대비 마지막날 종가 또는 복리 수익률)
    monthly_prices = df["Close"].resample("ME").last()
    monthly_returns = monthly_prices.pct_change() * 100
    
    m_df = pd.DataFrame({
        "Year": monthly_returns.index.year,
        "Month": monthly_returns.index.month,
        "Return": monthly_returns.values
    }).dropna()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"width_ratios": [3, 2]})
    
    # 서브플롯 1: 2023 vs 2024 월별 수익률 비교 바 차트
    width = 0.38
    m_2023 = m_df[m_df["Year"] == 2023].set_index("Month")["Return"]
    m_2024 = m_df[m_df["Year"] == 2024].set_index("Month")["Return"]
    months = np.arange(1, 13)
    
    r_2023 = [m_2023.get(m, 0) for m in months]
    r_2024 = [m_2024.get(m, 0) for m in months]
    
    bars1 = ax1.bar(months - width/2, r_2023, width, label="2023년", color="#4393c3", alpha=0.9)
    bars2 = ax1.bar(months + width/2, r_2024, width, label="2024년", color="#f4a582", alpha=0.9)
    
    ax1.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax1.set_title("2023년 vs 2024년 월별 수익률 비교 (%)", fontsize=14, fontweight="bold")
    ax1.set_xlabel("월 (Month)", fontsize=11)
    ax1.set_ylabel("월간 수익률 (%)", fontsize=11)
    ax1.set_xticks(months)
    ax1.set_xticklabels([f"{m}월" for m in months])
    ax1.legend(frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    # 서브플롯 2: 연도별 월간 수익률 분포 박스플롯 & 스트립플롯
    sns.boxplot(data=m_df, x="Year", y="Return", hue="Year", ax=ax2, palette=["#92c5de", "#fddbc7"], width=0.45, legend=False)
    sns.stripplot(data=m_df, x="Year", y="Return", ax=ax2, color="black", size=6, jitter=0.15, alpha=0.7)
    ax2.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax2.set_title("연도별 월 수익률 변동 폭 분포 (Boxplot)", fontsize=14, fontweight="bold")
    ax2.set_xlabel("연도", fontsize=11)
    ax2.set_ylabel("월간 수익률 (%)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] 시각화 3 저장 완료: {save_path}")

def plot_04_rolling_volatility(df: pd.DataFrame, save_path: str):
    """시각화 4: 20일 롤링 변동성 및 이상 급등 구간 탐지"""
    plt.figure(figsize=(14, 6))
    
    plt.plot(df.index, df["Volatility_20d"], color="#756bb1", linewidth=2, label="20일 롤링 변동성 (연율화 %)")
    
    # 전체 기간 평균 변동성
    mean_vol = df["Volatility_20d"].mean()
    plt.axhline(mean_vol, color="#e6550d", linestyle="--", linewidth=1.5,
                label=f"기간 평균 변동성 ({mean_vol:.1f}%)")
    
    # 이상 변동성 구간 (상위 5% 또는 변동성 35% 초과)
    high_vol = df[df["Volatility_20d"] > 35]
    if not high_vol.empty:
        plt.scatter(high_vol.index, high_vol["Volatility_20d"], color="#de2d26", s=40, zorder=5,
                    label="극단적 고변동성 구간 (>35%)")
        
    # 주요 이벤트 주석
    # 1. 2024년 8월 초 글로벌 증시 급락
    if pd.Timestamp("2024-08-16") in df.index or any(df.index.month == 8):
        aug_idx = df.loc["2024-08-01":"2024-08-31", "Volatility_20d"].idxmax()
        aug_val = df.loc[aug_idx, "Volatility_20d"]
        plt.annotate(f"8월 급락 쇼크 여파\n변동성 {aug_val:.1f}% 기록",
                     xy=(aug_idx, aug_val), xytext=(aug_idx - pd.Timedelta(days=70), aug_val + 4),
                     arrowprops=dict(facecolor="#de2d26", shrink=0.08, width=1.5, headwidth=7),
                     fontsize=9.5, fontweight="bold", color="#de2d26",
                     bbox=dict(boxstyle="round,pad=0.3", fc="#ffefef", ec="#de2d26", lw=1))
        
    plt.title("삼성전자 20일 롤링 변동성(연율화) 추이 및 시장 충격 구간", fontsize=15, fontweight="bold", pad=12)
    plt.xlabel("거래 일자", fontsize=12)
    plt.ylabel("연율화 변동성 (%)", fontsize=12)
    plt.legend(loc="upper left", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] 시각화 4 저장 완료: {save_path}")

def plot_05_time_series_decomposition(df: pd.DataFrame, save_path: str):
    """시각화 5 (보너스): STL / Additive 시계열 분해 (Trend, Seasonal, Residual)"""
    # 일별 거래일 데이터이므로 비어있는 주말/공휴일을 전일 종가(ffill)로 채워 7일 주기(Weekly) 또는 20일 주기(Monthly)로 분해
    daily_ts = df["Close"].asfreq("D").ffill()
    # 30일(월간 주기) 계절성 분해
    decomposition = seasonal_decompose(daily_ts, model="additive", period=30)
    
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    
    # 1) 원본 관측값 (Observed)
    axes[0].plot(decomposition.observed.index, decomposition.observed, color="#2b5c8f", lw=1.8)
    axes[0].set_ylabel("관측값 (Observed)", fontsize=10, fontweight="bold")
    axes[0].set_title("삼성전자 주가 시계열 성분 분해 (Additive Decomposition, 주기=30일)", fontsize=14, fontweight="bold")
    axes[0].grid(True, linestyle="--", alpha=0.5)
    
    # 2) 추세 성분 (Trend)
    axes[1].plot(decomposition.trend.index, decomposition.trend, color="#e6550d", lw=2)
    axes[1].set_ylabel("추세 (Trend)", fontsize=10, fontweight="bold")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    
    # 3) 계절성 성분 (Seasonal)
    axes[2].plot(decomposition.seasonal.index, decomposition.seasonal, color="#31a354", lw=1.2)
    axes[2].set_ylabel("계절성 (Seasonal)", fontsize=10, fontweight="bold")
    axes[2].grid(True, linestyle="--", alpha=0.5)
    
    # 4) 불규칙/잔차 성분 (Residual)
    axes[3].scatter(decomposition.resid.index, decomposition.resid, color="#756bb1", s=15, alpha=0.6)
    axes[3].axhline(0, color="red", linestyle="--", lw=1)
    axes[3].set_ylabel("잔차/노이즈 (Residual)", fontsize=10, fontweight="bold")
    axes[3].set_xlabel("일자", fontsize=11)
    axes[3].grid(True, linestyle="--", alpha=0.5)
    
    axes[3].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] 시각화 5 저장 완료: {save_path}")

def plot_06_baseline_forecast(df: pd.DataFrame, save_path: str):
    """시각화 6 (보너스): 최근 20거래일 베이스라인 예측(Holt-Winters / Exponential Smoothing) vs 실측치 비교"""
    # 전체 489거래일 중 마지막 20거래일을 테스트셋으로 분리
    forecast_horizon = 20
    train = df["Close"].iloc[:-forecast_horizon]
    test = df["Close"].iloc[-forecast_horizon:]
    
    # 지수평활(Holt's Linear Trend) 모델 피팅
    model = ExponentialSmoothing(train.values, trend="add", seasonal=None, damped_trend=True).fit()
    pred_values = model.forecast(forecast_horizon)
    pred_series = pd.Series(pred_values, index=test.index)
    
    # 단순 이동평균(20일) 베이스라인
    last_ma20 = train.iloc[-20:].mean()
    ma_pred_series = pd.Series([last_ma20] * forecast_horizon, index=test.index)
    
    # 평가 지표 산출
    mae_holt = np.mean(np.abs(test.values - pred_values))
    rmse_holt = np.sqrt(np.mean((test.values - pred_values) ** 2))
    mape_holt = np.mean(np.abs((test.values - pred_values) / test.values)) * 100
    
    plt.figure(figsize=(14, 6))
    
    # 학습 데이터의 마지막 60일만 시각화에 표시하여 가독성 증대
    recent_train = train.iloc[-60:]
    plt.plot(recent_train.index, recent_train.values, label="학습 데이터 (Train, 실측치)", color="#1f77b4", lw=2)
    plt.plot(test.index, test.values, label="테스트 데이터 (Test, 실측치)", color="#2ca02c", lw=2.5, marker="o", markersize=4)
    plt.plot(test.index, pred_series.values, label=f"지수평활 예측(Holt-Winters, MAPE: {mape_holt:.1f}%)",
             color="#d62728", lw=2, linestyle="--", marker="s", markersize=4)
    plt.plot(test.index, ma_pred_series.values, label=f"단순 이동평균 기준선 ({int(last_ma20):,}원)",
             color="#ff7f0e", lw=1.5, linestyle=":")
    
    plt.title("삼성전자 2024년 말 주가 베이스라인 예측 및 실측치 비교 (20거래일 예측)", fontsize=15, fontweight="bold", pad=12)
    plt.xlabel("거래 일자", fontsize=12)
    plt.ylabel("주가 (원, KRW)", fontsize=12)
    plt.legend(loc="upper left", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    
    # 한계점 및 평가 주석 박스
    info_text = (f"[모델 검증 성과]\n"
                 f"• Holt RMSE: {rmse_holt:,.0f}원\n"
                 f"• Holt MAE:  {mae_holt:,.0f}원\n"
                 f"• Holt MAPE: {mape_holt:.2f}%\n"
                 f"[시계열 예측 한계]\n"
                 f"단순 과거 추세 연장은 실적 쇼크/수급 급변 등\n"
                 f"외부 충격을 반영하지 못하는 래깅(Lagging) 한계 노출")
    plt.text(0.72, 0.20, info_text, transform=plt.gca().transAxes, fontsize=10,
             bbox=dict(boxstyle="round,pad=0.5", fc="#f7f7f7", ec="#cccccc", lw=1.2))
    
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] 시각화 6 저장 완료: {save_path}")

# ---------------------------------------------------------
# 5. 핵심 통계 및 리포트 요약 지표 출력
# ---------------------------------------------------------
def summarize_statistics(df: pd.DataFrame):
    """리포트에 인용할 주요 통계 지표를 터미널에 요약 출력합니다."""
    print("\n" + "=" * 60)
    print("        [삼성전자 2023~2024년 시계열 분석 핵심 요약]")
    print("=" * 60)
    
    start_dt = df.index[0].strftime("%Y-%m-%d")
    end_dt = df.index[-1].strftime("%Y-%m-%d")
    total_days = len(df)
    
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    total_return = (end_price - start_price) / start_price * 100
    
    max_idx = df["Close"].idxmax()
    max_val = df.loc[max_idx, "Close"]
    min_idx = df["Close"].idxmin()
    min_val = df.loc[min_idx, "Close"]
    
    # 2023년 성과
    df_2023 = df.loc["2023"]
    ret_2023 = (df_2023["Close"].iloc[-1] - df_2023["Close"].iloc[0]) / df_2023["Close"].iloc[0] * 100
    
    # 2024년 성과
    df_2024 = df.loc["2024"]
    ret_2024 = (df_2024["Close"].iloc[-1] - df_2024["Close"].iloc[0]) / df_2024["Close"].iloc[0] * 100
    
    # 최대 1일 상승/하락
    max_daily_gain = df["Daily_Return"].max() * 100
    max_gain_date = df["Daily_Return"].idxmax().strftime("%Y-%m-%d")
    max_daily_drop = df["Daily_Return"].min() * 100
    max_drop_date = df["Daily_Return"].idxmin().strftime("%Y-%m-%d")
    
    # 변동성 평균 및 최고
    avg_vol = df["Volatility_20d"].mean()
    max_vol = df["Volatility_20d"].max()
    max_vol_date = df["Volatility_20d"].idxmax().strftime("%Y-%m-%d")
    
    # 최고가 대비 최저가 하락폭
    drawdown_from_peak = (min_val - max_val) / max_val * 100
    
    print(f"1. 분석 기간: {start_dt} ~ {end_dt} (총 {total_days}개 거래일)")
    print(f"2. 기간 전체 수익률: {total_return:+.2f}% (시작가: {int(start_price):,}원 -> 종가: {int(end_price):,}원)")
    print(f"3. 2023년 연간 수익률: {ret_2023:+.2f}%")
    print(f"4. 2024년 연간 수익률: {ret_2024:+.2f}%")
    print(f"5. 기간 최고가: {int(max_val):,}원 ({max_idx.strftime('%Y-%m-%d')})")
    print(f"6. 기간 최저가: {int(min_val):,}원 ({min_idx.strftime('%Y-%m-%d')})")
    print(f"7. 고점 대비 최대 낙폭(MDD 구간): {drawdown_from_peak:.2f}% (87,800원 -> 49,900원)")
    print(f"8. 최대 1일 상승폭: {max_daily_gain:+.2f}% ({max_gain_date})")
    print(f"9. 최대 1일 하락폭: {max_daily_drop:+.2f}% ({max_drop_date})")
    print(f"10. 20일 롤링 평균 변동성: {avg_vol:.2f}% (연율화)")
    print(f"11. 20일 롤링 최고 변동성: {max_vol:.2f}% ({max_vol_date})")
    print("=" * 60 + "\n")

# ---------------------------------------------------------
# 메인 실행부
# ---------------------------------------------------------
def main():
    print("[1] 데이터 로드 및 전처리 시작...")
    df = load_or_fetch_data(TICKER, START_DATE, END_DATE, DATA_PATH)
    df = preprocess_and_calculate_metrics(df)
    
    print("\n[2] 기술 통계 산출...")
    summarize_statistics(df)
    
    print("[3] 시각화 생성 시작 (총 6종)...")
    plot_01_price_and_volume(df, os.path.join(IMAGES_DIR, "01_price_and_volume_trend.png"))
    plot_02_moving_average_and_signals(df, os.path.join(IMAGES_DIR, "02_moving_average_and_cross.png"))
    plot_03_monthly_return_distribution(df, os.path.join(IMAGES_DIR, "03_monthly_return_distribution.png"))
    plot_04_rolling_volatility(df, os.path.join(IMAGES_DIR, "04_rolling_volatility.png"))
    plot_05_time_series_decomposition(df, os.path.join(IMAGES_DIR, "05_time_series_decomposition.png"))
    plot_06_baseline_forecast(df, os.path.join(IMAGES_DIR, "06_baseline_forecast.png"))
    
    print("\n[✓] 모든 분석 및 시각화 생성이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
