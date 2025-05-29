import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import re
from utils.text_cleaner import extract_context
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 폰트 경로 확인
font_path = "assets/NanumGothic.ttf"  # 업로드한 폰트 경로
if not os.path.exists(font_path):
    st.error("❌ 폰트 파일을 찾을 수 없습니다.")
else:
    font_prop = fm.FontProperties(fname=font_path)

TARGETS = ['좋', '만족', '훌륭', '깔끔', '편하', '빠르', '예쁘', '감동', '신나', '행복', '사랑', '유용', '기분좋', '재밌', '즐겁', '고급', '세련', '친절', '정확', '튼튼',
           '별로', '불편', '고장', '느리', '느림', '실망', '짜증', '화남', '불만', '아쉬', '부족', '망함', '불쾌', '지루', '불친절', '복잡', '헷갈림', '약함', '무거움', '불량']

def render(tag_grouped_dfs):
    st.subheader("브랜드 리뷰 비교")

    if not tag_grouped_dfs:
        st.warning("⚠️ 비교할 데이터가 없습니다.")
        return

    brand_list = list(tag_grouped_dfs.keys())

    # 세션 상태 초기화
    if 'selected_brands_tab4' not in st.session_state:
        st.session_state.selected_brands_tab4 = []

    # 체크박스 기반 브랜드 선택
    st.markdown("### 🏷️ 브랜드 태그 선택 (2개까지 가능)")
    selected = []
    cols = st.columns(min(5, len(brand_list)))
    for i, tag in enumerate(brand_list):
        with cols[i % len(cols)]:
            checked = st.checkbox(
                tag, 
                value=(tag in st.session_state.selected_brands_tab4),
                key=f"brand_checkbox_{tag}"
            )
            if checked:
                selected.append(tag)

    # 2개까지만 허용
    if len(selected) > 2:
        st.warning("❗ 브랜드는 2개까지 선택 가능합니다. 처음 2개만 적용됩니다.")
        selected = selected[:2]

    # 세션 상태 업데이트
    st.session_state.selected_brands_tab4 = selected

    # 초기화 버튼
    if st.button("🔄 선택 초기화"):
        # for tag in brand_list:
        #     st.session_state[f"brand_checkbox_{tag}"] = False
        st.session_state.selected_brands_tab4 = []
        # st.experimental_rerun()

    # 2개 미만 선택 시 안내 후 종료
    if len(selected) != 2:
        st.info("비교할 2개 브랜드를 선택해주세요.")
        return

    # --------- 분석 시작 (2개 선택 시 자동) ---------
    df1, df2 = tag_grouped_dfs[selected[0]], tag_grouped_dfs[selected[1]]

    def summarize(df):
        return {
            '리뷰 수': len(df),
            '평균 별점': df['별점'].mean(),
            '평균 리뷰 길이': df['리뷰 내용'].astype(str).apply(len).mean()
        }

    def plot_wordcloud(freq, title):
        if not freq:
            st.info("키워드 데이터가 부족합니다.")
            return
        try:
            wc = WordCloud(
                font_path='assets/NanumGothic.ttf', 
                background_color='white', 
                width=600, 
                height=400
            ).generate_from_frequencies(freq)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(title, fontsize=14, pad=20)
            st.pyplot(fig)
            plt.close(fig)
        except Exception as e:
            st.error(f"워드클라우드 생성 중 오류: {e}")

    def plot_rating_distribution(df, title):
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.countplot(x='별점', data=df, ax=ax, palette='coolwarm')
            ax.set_title(title, fontsize=14, pad=20, fontproperties=font_prop)
            ax.set_xlabel('별점', fontproperties=font_prop)
            ax.set_ylabel('리뷰 수', fontproperties=font_prop)
            st.pyplot(fig)
            plt.close(fig)
        except Exception as e:
            st.error(f"별점 분포 차트 생성 중 오류: {e}")

    # 요약 비교
    st.markdown("### 기본 통계 비교")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### 📍 {selected[0]}")
        summary1 = summarize(df1)
        st.metric("리뷰 수", summary1['리뷰 수'])
        st.metric("평균 별점", f"{summary1['평균 별점']:.2f}")
        st.metric("평균 리뷰 길이", f"{summary1['평균 리뷰 길이']:.1f}자")
    with col2:
        st.markdown(f"#### 📍 {selected[1]}")
        summary2 = summarize(df2)
        st.metric("리뷰 수", summary2['리뷰 수'])
        st.metric("평균 별점", f"{summary2['평균 별점']:.2f}")
        st.metric("평균 리뷰 길이", f"{summary2['평균 리뷰 길이']:.1f}자")

    st.markdown("### 별점 분포 비교")
    col3, col4 = st.columns(2)
    with col3:
        plot_rating_distribution(df1, f"{selected[0]} 별점 분포")
    with col4:
        plot_rating_distribution(df2, f"{selected[1]} 별점 분포")

    st.markdown("### 키워드 워드클라우드")
    col5, col6 = st.columns(2)
    with col5:
        st.markdown(f"#### {selected[0]}")
        freq1 = extract_context(df1['리뷰 내용'], TARGETS)
        plot_wordcloud(freq1, f"{selected[0]} 키워드")
    with col6:
        st.markdown(f"#### {selected[1]}")
        freq2 = extract_context(df2['리뷰 내용'], TARGETS)
        plot_wordcloud(freq2, f"{selected[1]} 키워드")


