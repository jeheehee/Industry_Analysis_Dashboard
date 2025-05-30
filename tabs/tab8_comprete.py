import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from sklearn.linear_model import LinearRegression
from matplotlib.colors import LinearSegmentedColormap
import os

# 한글 폰트 경로
font_path = 'assets/NanumGothic.ttf'

# 폰트 로딩
font_prop = fm.FontProperties(fname=font_path)
mpl.rcParams['font.family'] = font_prop.get_name()
mpl.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

# 폰트 자동 로드 함수
def load_custom_font():
    font_path = "./fonts/NanumGothic.ttf"
    if os.path.exists(font_path):
        font_prop = fm.FontProperties(fname=font_path)
        mpl.rcParams['font.family'] = font_prop.get_name()
    else:
        print("⚠️ NanumGothic 폰트 파일을 찾을 수 없습니다.")
    mpl.rcParams['axes.unicode_minus'] = False

load_custom_font()

st.set_page_config(page_title="전자담배 시장 경쟁 분석", layout="wide")
st.title("전자담배 브랜드 경쟁 분석 심화 대시보드")

def render():
    df_raw = pd.read_csv('./search_data/월별 검색량 데이터.csv')
    df_raw = df_raw.rename(columns={'\uc6d4': 'ds'})
    df_raw['ds'] = pd.to_datetime(df_raw['ds'])
    df_melted = df_raw.melt(id_vars=['ds'], var_name='keyword', value_name='search_volume')

    competitor_brands = ['아이코스', '글로전자담배', '릴하이브리드', '차이코스', '발라리안', '빌리아', '아스몬', '엑스퍼', '연초']

    competitor_df = df_raw.set_index('ds')[competitor_brands].copy()
    rolling_df = competitor_df.rolling(window=3).mean()
    correlation_matrix = rolling_df.corr()

    st.subheader("시장 집중도 지표 (HHI)")
    st.markdown('HHI 값이 클수록 시장 집중도 높음')
    def calculate_hhi(df_slice):
        total = df_slice.sum(axis=1)
        market_share = df_slice.div(total, axis=0)
        return (market_share**2).sum(axis=1) * 10000

    hhi_series = calculate_hhi(competitor_df)
    fig_hhi, ax_hhi = plt.subplots(figsize=(10, 4))
    sns.lineplot(x=hhi_series.index, y=hhi_series.values, ax=ax_hhi)
    ax_hhi.set_title("전자담배 시장 집중도 추이 (HHI)", fontproperties=font_prop)
    ax_hhi.set_xlabel("월", fontproperties=font_prop)
    ax_hhi.set_ylabel("HHI 지수", fontproperties=font_prop)
    ax_hhi.grid(True)
    st.pyplot(fig_hhi)
    st.markdown('---')

    st.subheader("브랜드 검색량별 유의미한 상관관계")
    high_corr_pairs = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            val = correlation_matrix.iloc[i, j]
            if abs(val) >= 0.4:
                sign = '+' if val > 0 else '-'
                brand1 = correlation_matrix.columns[i]
                brand2 = correlation_matrix.columns[j]
                high_corr_pairs.append((brand1, brand2, val, sign))
    high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    top_corr_df = pd.DataFrame(high_corr_pairs, columns=['브랜드1','브랜드2','상관계수','부호'])
    st.dataframe(top_corr_df[['브랜드1','브랜드2','상관계수']].style.background_gradient(cmap='coolwarm', subset=['상관계수']).format({"상관계수": "{:.2f}"}))

    pair_options = [f"{b1} vs {b2} ({s} r={r:.2f})" for b1, b2, r, s in high_corr_pairs]
    pair_select = st.selectbox("비교할 브랜드 쌍 선택", pair_options)

    if pair_select:
        selected = pair_select.split(" vs ")
        brand_x = selected[0].strip()
        brand_y = selected[1].split(" (")[0].strip()


        st.subheader("경쟁 강도 분석 (로그-로그 회귀 & 시계열)")
        log_x_raw = np.log(competitor_df[brand_y].replace(0, np.nan))
        log_y_raw = np.log(competitor_df[brand_x].replace(0, np.nan))
        valid_index = log_x_raw.dropna().index.intersection(log_y_raw.dropna().index)
        log_x = log_x_raw.loc[valid_index]
        log_y = log_y_raw.loc[valid_index]

        window_size = 12
        beta_series = []
        date_index = []

        for i in range(len(valid_index) - window_size + 1):
            window_idx = valid_index[i:i+window_size]
            lx = log_x.loc[window_idx].values.reshape(-1, 1)
            ly = log_y.loc[window_idx].values
            if np.isfinite(lx).all() and np.isfinite(ly).all():
                model = LinearRegression().fit(lx, ly)
                beta_series.append(model.coef_[0])
                date_index.append(window_idx[-1])

        if beta_series:
            st.metric(f"최근 회귀계수 (마지막 윈도우)", f"{beta_series[-1]:.3f}")
            st.markdown("β > 1	과열 경쟁, 0.5~1: 강한 경쟁, 0~0.5: 약한경쟁, <0: 보완재(브랜드 공동 성장)")
            fig_beta, ax_beta = plt.subplots(figsize=(10, 4))
            sns.lineplot(x=date_index, y=beta_series, ax=ax_beta)
            ax_beta.set_title(f"회귀계수 시계열 추이: {brand_x} ~ {brand_y}", fontproperties=font_prop)
            ax_beta.set_xlabel("기준 월", fontproperties=font_prop)
            ax_beta.set_ylabel("경쟁 탄력성 (β)", fontproperties=font_prop)
            ax_beta.grid(True)
            st.pyplot(fig_beta)




        # # 스캐터플롯 추가: 상관계수가 잘 보이도록
        # st.markdown("**검색량 산점도 (상관관계 시각화)**")
        # fig_scatter, ax_scatter = plt.subplots(figsize=(6, 4))
        # ax_scatter.scatter(rolling_df[brand_x], rolling_df[brand_y])
        # ax_scatter.set_xlabel(brand_x)
        # ax_scatter.set_ylabel(brand_y)
        # ax_scatter.set_title(f"{brand_x} vs {brand_y} 검색량 산점도")
        # st.pyplot(fig_scatter)

        st.markdown("**검색량 추이 (동일 축 비교)**")
        fig_line, ax_line = plt.subplots(figsize=(10, 4))
        ax_line.plot(rolling_df.index, rolling_df[brand_x], label=brand_x)
        ax_line.plot(rolling_df.index, rolling_df[brand_y], label=brand_y)
        ax_line.legend(title_fontproperties=font_prop)
        ax_line.set_title(f"검색량 추이 비교: {brand_x} vs {brand_y}", fontproperties=font_prop)
        st.pyplot(fig_line)

        if st.checkbox("전체 브랜드 검색량 상관관계 히트맵 보기"):
            custom_colors = [(0, 'blue'), (0.499, 'white'), (0.501, 'grey'), (0.999, 'red'), (1, 'black')]
            cmap = LinearSegmentedColormap.from_list("custom_cmap", custom_colors)
            fig_corr, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap=cmap, vmin=-1, vmax=1, ax=ax)
            ax.set_title("브랜드 간 검색량 상관관계 히트맵", fontproperties=font_prop)
            st.pyplot(fig_corr)
        st.markdown('---')



