import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from components.wordcloud_plot import generate_wordcloud_image
from components.treemap_plot import prepare_log_nom_treemap_data, show_treemap
from utils.text_cleaner import STOPWORDS, extract_context
from collections import Counter
import os

POS_TARGETS = ['좋', '만족', '훌륭', '깔끔', '편하', '빠르', '예쁘', '감동', '신나', '행복', '사랑', '유용', '기분좋', '재밌', '즐겁', '고급', '세련', '친절', '정확', '튼튼']
NEG_TARGETS = ['별로', '불편', '고장', '느리', '느림', '실망', '짜증', '화남', '불만', '아쉬', '부족', '망함', '불쾌', '지루', '불친절', '복잡', '헷갈림', '약함', '무거움', '불량']

# 폰트 경로 (업로드된 파일 기준)
font_path = "assets/NanumGothic.ttf"  # 업로드한 폰트 경로
if not os.path.exists(font_path):
    st.error("❌ 폰트 파일을 찾을 수 없습니다.")
else:
    font_prop = fm.FontProperties(fname=font_path)

def render(category_grouped_dfs):
    st.subheader("제품 유형별 리뷰 분석")

    if not category_grouped_dfs:
        st.warning("⚠️ 사용할 수 있는 제품 분류 데이터가 없습니다.")
        return

    product_options = list(category_grouped_dfs.keys())
    if not product_options:
        st.warning("⚠️ 선택할 수 있는 제품 종류가 없습니다.")
        return

    selected = st.selectbox("제품 유형 선택", product_options)

    if not selected or selected not in category_grouped_dfs:
        st.warning("⚠️ 유효한 제품을 선택해주세요.")
        return

    df = category_grouped_dfs[selected]
    if df is None or df.empty:
        st.warning("⚠️ 해당 제품의 리뷰 데이터가 없습니다.")
        return

    if '리뷰작성일' not in df.columns:
        st.warning("⚠️ '리뷰작성일' 컬럼이 누락되었습니다.")
        return

    df = df.copy()
    df['리뷰작성일'] = pd.to_datetime(df['리뷰작성일'], format='%Y%m%d', errors='coerce')
    df = df.dropna(subset=['리뷰작성일'])
    df['월'] = df['리뷰작성일'].dt.to_period('M')

    months = sorted(df['월'].unique())
    if len(months) >= 2:
        date_range = [p.to_timestamp() for p in months]
        start_date = date_range[0].date()
        end_date = date_range[-1].date()
        selected_range = st.slider(
            "기간 선택 (월 단위)",
            min_value=start_date,
            max_value=end_date,
            value=(start_date, end_date),
            format="YYYY-MM"
        )
        df = df[(df['리뷰작성일'] >= pd.to_datetime(selected_range[0])) &
                (df['리뷰작성일'] <= pd.to_datetime(selected_range[1]) + pd.offsets.MonthEnd(0))]

    df['월'] = df['리뷰작성일'].dt.to_period('M').astype(str)
    df['리뷰길이'] = df['리뷰 내용'].astype(str).apply(len)

    monthly_summary = df.groupby('월').agg({'리뷰 내용': 'count', '별점': 'mean'}).rename(columns={'리뷰 내용': '리뷰 수'}).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    step = 1 if len(monthly_summary) <= 12 else 2 if len(monthly_summary) <= 24 else 4
    ticks = monthly_summary['월'].tolist()[::step]
    sns.lineplot(data=monthly_summary, x='월', y='리뷰 수', ax=axes[0], marker='o')
    axes[0].set_xticks(ticks)
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].set_title('월별 리뷰 수', fontproperties=font_prop)
    axes[0].set_xlabel('월', fontproperties=font_prop)
    axes[0].set_ylabel('리뷰 수', fontproperties=font_prop)

    sns.lineplot(data=monthly_summary, x='월', y='별점', ax=axes[1], marker='o', color='orange')
    axes[1].set_xticks(ticks)
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].set_title('월별 평균 별점', fontproperties=font_prop)
    axes[1].set_xlabel('월', fontproperties=font_prop)
    axes[1].set_ylabel('별점', fontproperties=font_prop)
    st.pyplot(fig)

    pos = extract_context(df['리뷰 내용'], POS_TARGETS)
    neg = extract_context(df['리뷰 내용'], NEG_TARGETS)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("긍정 키워드 TOP 20")
        st.dataframe(pd.DataFrame(pos.most_common(20), columns=["단어", "빈도"]))
        buf = generate_wordcloud_image(pos, "Blues")
        if buf: st.image(buf, use_container_width=True)
    with col2:
        st.subheader("부정 키워드 TOP 20")
        st.dataframe(pd.DataFrame(neg.most_common(20), columns=["단어", "빈도"]))
        buf = generate_wordcloud_image(neg, "Reds")
        if buf: st.image(buf, use_container_width=True)
        
    st.markdown("---")
    
    
    st.markdown("### TOP20 긍정 키워드별 상품 종류 분포")
    df_plot = prepare_log_nom_treemap_data(category_grouped_dfs, POS_TARGETS, STOPWORDS)
    show_treemap(df_plot, "로그정규화_빈도", "정규화된 긍정 키워드")

    st.markdown("### TOP20 부정 키워드별 상품 종류 분포")
    df_plot = prepare_log_nom_treemap_data(category_grouped_dfs, NEG_TARGETS, STOPWORDS)
    show_treemap(df_plot, "로그정규화_빈도", "정규화된 부정 키워드")
