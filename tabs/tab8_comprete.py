import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from matplotlib.colors import LinearSegmentedColormap
import os

# 기본 설정
st.set_page_config(page_title="전자담배 시장 경쟁 분석 v2", layout="wide")
st.title("전자담배 경쟁구조 분석엔진 v2 (최종판)")

# 데이터 로딩
df_raw = pd.read_csv('./search_data/월별 검색량 데이터.csv')
df_raw = df_raw.rename(columns={'\uc6d4': 'ds'})
df_raw['ds'] = pd.to_datetime(df_raw['ds'])
df_raw = df_raw.set_index('ds')

# 제품 파일 불러오기
file_path = './search_data/250515_제품.xlsx'
df_products = pd.read_excel(file_path, sheet_name='Sheet1')
df_products['제품명_소문자'] = df_products['제품명'].str.lower()

# 분석 브랜드 제한
competitor_brands = ['아이코스', '글로전자담배', '릴하이브리드', '차이코스', '발라리안',
                     '빌리아', '아스몬', '엑스퍼', '연초', '칠렉스', '하카시그니처', '젤로전자담배']
competitor_brands_lower = [b.lower() for b in competitor_brands]

# 자동 분류 (제품명 기반)
brand_category = {b: [] for b in competitor_brands}
for brand in competitor_brands_lower:
    matching_rows = df_products[df_products['제품명_소문자'].str.contains(brand, na=False)]
    if not matching_rows.empty:
        for _, row in matching_rows.iterrows():
            original_brand = competitor_brands[competitor_brands_lower.index(brand)]
            if row['액상형'] == 'o':
                brand_category[original_brand].append('액상형')
            if row['일회용'] == 'o':
                brand_category[original_brand].append('일회용')
            if row['궐련형'] == 'o':
                brand_category[original_brand].append('궐련형')
brand_category = {k: list(set(v)) for k, v in brand_category.items()}

# 수동 분류 보강 (수동분류 파일 존재시 적용)
try:
    manual_category = pd.read_csv('./search_data/manual_brand_category.csv')
    for _, row in manual_category.iterrows():
        brand, category = row['브랜드명'], row['분류']
        if brand in brand_category:
            brand_category[brand].append(category)
        else:
            brand_category[brand] = [category]
    brand_category = {k: list(set(v)) for k, v in brand_category.items()}
except:
    st.warning("수동 분류 파일 없음 → 자동분류만 적용됨.")

# 연초는 모든 분류에 포함
if '연초' in brand_category:
    brand_category['연초'] = ['액상형', '일회용', '궐련형']

# HHI 계산 안정화
def calculate_hhi(df_slice):
    total = df_slice.sum(axis=1)
    market_share = df_slice.div(total.replace(0, np.nan), axis=0)
    hhi = (market_share.fillna(0) ** 2).sum(axis=1) * 10000
    hhi[total == 0] = 0
    return hhi, market_share

# 브랜드 첫 등장 시점 찾기
def find_brand_debut(df):
    debut_points = {}
    for brand in df.columns:
        non_zero_dates = df[df[brand] > 0].index
        if len(non_zero_dates) > 0:
            debut_points[brand] = non_zero_dates[0]
    return debut_points

def get_top_brands_tooltip(date, shares):
    try:
        shares = shares.dropna()
        tooltip = f"{date.strftime('%Y-%m')}\n\n"

        if shares.empty or shares.sum() == 0:
            tooltip += "데이터 없음"
            return tooltip

        # 상위 3위만 추출
        top_brands = shares.sort_values(ascending=False).head(3)
        tooltip += "<상위 3위><br>"
        for i, (brand, share) in enumerate(top_brands.items(), start=1):
            tooltip += f"{i}위: {brand} ({share*100:.1f}%)<br>"

        return tooltip

    except:
        return f"{date.strftime('%Y-%m')}\n툴팁 생성 오류"





# # 경쟁구조 변화 요약 테이블 생성
# def generate_competition_snapshot(hhi_series, market_share):
#     rows = []
#     for date in hhi_series.index:
#         shares = market_share.loc[date]
#         top3 = shares.dropna().sort_values(ascending=False).head(3)
#         row = {'날짜': date.strftime('%Y-%m'), 'HHI': round(hhi_series.loc[date], 1)}
#         for i, (brand, pct) in enumerate(top3.items(), start=1):
#             row[f'{i}위'] = brand
#             row[f'점유율{i}'] = round(pct*100, 1)
#         rows.append(row)
#     return pd.DataFrame(rows)

# Plotly 안정화 버전 HHI 시계열 시각화
def plot_hhi(df, brands, title):
    hhi, market_share = calculate_hhi(df[brands])
    high_th = hhi.quantile(0.9)
    low_th = hhi.quantile(0.1)

    fig = go.Figure()

    # 전체 HHI 라인
    fig.add_trace(go.Scatter(
        x=hhi.index, y=hhi, mode='lines',
        line=dict(color='blue'), name='HHI'
    ))


    # 마커 생성
    for date in hhi.index:
        val = hhi.loc[date]
        tooltip = get_top_brands_tooltip(date, market_share.loc[date])
        color = None
        if val >= high_th:
            color = 'red'
        elif val <= low_th:
            color = 'green'
        if color:
            fig.add_trace(go.Scatter(
                x=[date],
                y=[val],
                mode='markers',
                marker=dict(color=color, size=10),
                hovertext=[tooltip],   
                hoverinfo="text"       
            ))

    # 브랜드 등장 마커
    debut_points = find_brand_debut(df[brands])
    for brand, debut_date in debut_points.items():
        tooltip = f"{debut_date.strftime('%Y-%m')}<br>브랜드 등장: {brand}"
        fig.add_trace(go.Scatter(
            x=[debut_date],
            y=[hhi.loc[debut_date]],
            mode='markers',
            marker=dict(color='yellow', size=10, symbol='star'),
            customdata=[[tooltip]],
            hovertemplate="%{customdata[0]}<extra></extra>"
        ))


    fig.update_layout(
        title=title, xaxis_title='월', yaxis_title='HHI 지수',
        hoverlabel=dict(font_size=14), showlegend=False
    )
    return fig, hhi, market_share

# 메인 렌더링 함수
def render():
    st.header("전자담배 전체 시장 집중도 (HHI)")
    
    # 전체 시장: 연초 제외
    hhi_brands_total = [b for b in competitor_brands if b in df_raw.columns and b != '연초']
    fig_total, hhi_series_total, market_share_total = plot_hhi(df_raw, hhi_brands_total, "전체 전자담배 시장 HHI 추이")
    st.plotly_chart(fig_total, use_container_width=True)

    # # 전체 스냅샷 요약 제공
    # st.subheader("📊 전체 시장 경쟁구조 변화 리포트")
    # snapshot_df_total = generate_competition_snapshot(hhi_series_total, market_share_total)
    # st.dataframe(snapshot_df_total)

    # 분류 선택 및 연초 분류 적용
    if '연초' in brand_category:
        brand_category['연초'] = ['액상형', '일회용', '궐련형']

    st.header("제품 유형 선택")
    category_option = st.selectbox("분석할 제품 유형을 선택하세요:", ['액상형', '일회용', '궐련형'])
    selected_brands = [brand for brand, cats in brand_category.items() if category_option in cats]
    
    if not selected_brands:
        st.warning(f"선택한 {category_option} 분류에 해당하는 브랜드 데이터가 없습니다.")
        st.stop()

    hhi_brands_category = [b for b in selected_brands if b != '연초']
    st.subheader(f"{category_option} 시장 HHI 추이")
    fig_category, hhi_series_cat, market_share_cat = plot_hhi(df_raw, hhi_brands_category, f"{category_option} 시장 집중도 추이")
    st.plotly_chart(fig_category, use_container_width=True)

    # st.subheader(f"📊 {category_option} 시장 경쟁구조 변화 리포트")
    # snapshot_df_cat = generate_competition_snapshot(hhi_series_cat, market_share_cat)
    # st.dataframe(snapshot_df_cat)

    # 유의미한 상관관계 분석
    st.header("브랜드 검색량 상관관계 분석")
    competitor_df = df_raw[selected_brands].copy()
    rolling_df = competitor_df.rolling(window=3, min_periods=1).mean()
    correlation_matrix = rolling_df.corr()

    high_corr_pairs = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            val = correlation_matrix.iloc[i, j]
            if not np.isnan(val) and abs(val) >= 0.5:
                sign = '+' if val > 0 else '-'
                brand1 = correlation_matrix.columns[i]
                brand2 = correlation_matrix.columns[j]
                high_corr_pairs.append((brand1, brand2, val, sign))
    high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    if not high_corr_pairs:
        st.warning("유의미한 상관관계 쌍이 없습니다.")
        st.stop()

    top_corr_df = pd.DataFrame(high_corr_pairs, columns=['브랜드1','브랜드2','상관계수','부호'])
    st.dataframe(top_corr_df[['브랜드1','브랜드2','상관계수']].style.background_gradient(cmap='coolwarm', subset=['상관계수']).format({"상관계수": "{:.2f}"}))

    pair_options = [f"{b1} vs {b2} ({s} r={r:.2f})" for b1, b2, r, s in high_corr_pairs]
    pair_select = st.selectbox("비교할 브랜드 쌍 선택", pair_options)

    if pair_select:
        selected = pair_select.split(" vs ")
        brand_x = selected[0].strip()
        brand_y = selected[1].split(" (")[0].strip()

        st.subheader("경쟁 강도 분석 (로그-로그 회귀)")
        log_x_raw = np.log(competitor_df[brand_y].replace(0, np.nan))
        log_y_raw = np.log(competitor_df[brand_x].replace(0, np.nan))
        valid_index = log_x_raw.dropna().index.intersection(log_y_raw.dropna().index)
        log_x = log_x_raw.loc[valid_index]
        log_y = log_y_raw.loc[valid_index]

        window_size = 12
        beta_series, date_index = [], []
        for i in range(len(valid_index) - window_size + 1):
            window_idx = valid_index[i:i+window_size]
            lx = log_x.loc[window_idx].values.reshape(-1, 1)
            ly = log_y.loc[window_idx].values
            if np.isfinite(lx).all() and np.isfinite(ly).all():
                model = LinearRegression().fit(lx, ly)
                beta_series.append(model.coef_[0])
                date_index.append(window_idx[-1])

        if beta_series:
            st.metric("최근 3개월간 회귀계수", f"{beta_series[-1]:.3f}")
            st.markdown("β > 1 과열경쟁 / 0.5~1 강한경쟁 / 0~0.5 약한경쟁 / <0 보완재")

            fig_beta, ax_beta = plt.subplots(figsize=(10, 4))
            sns.lineplot(x=date_index, y=beta_series, ax=ax_beta)
            ax_beta.set_title(f"회귀계수 추이: {brand_x} vs {brand_y}")
            st.pyplot(fig_beta)

        st.subheader("브랜드 검색량 추이 비교")
        fig_line, ax_line = plt.subplots(figsize=(10, 4))
        ax_line.plot(rolling_df.index, rolling_df[brand_x], label=brand_x)
        ax_line.plot(rolling_df.index, rolling_df[brand_y], label=brand_y)
        ax_line.legend()
        ax_line.set_title(f"검색량 추이 비교: {brand_x} vs {brand_y}")
        st.pyplot(fig_line)
