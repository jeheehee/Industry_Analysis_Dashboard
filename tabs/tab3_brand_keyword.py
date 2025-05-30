import streamlit as st
import pandas as pd
from components.treemap_plot import prepare_treemap_data, prepare_log_nom_treemap_data, show_treemap
from components.wordcloud_plot import generate_wordcloud_image
from utils.text_cleaner import STOPWORDS, extract_context

POS_TARGETS = ['좋', '만족', '훌륭', '깔끔', '편하', '빠르', '예쁘', '감동', '신나', '행복', '사랑', '유용', '기분좋', '재밌', '즐겁', '고급', '세련', '친절', '정확', '튼튼']
NEG_TARGETS = ['별로', '불편', '고장', '느리', '느림', '실망', '짜증', '화남', '불만', '아쉬', '부족', '망함', '불쾌', '지루', '불친절', '복잡', '헷갈림', '약함', '무거움', '불량']

@st.cache_data
def get_top_keywords(tag_grouped_dfs, targets):
    all_texts = [text for df in tag_grouped_dfs.values() for text in df['리뷰 내용']]
    return extract_context(all_texts, targets)

def render(tag_grouped_dfs):
    st.subheader("제품별 주요 감정 키워드 비교")

    with st.spinner("🔍 전체 키워드 분석 중..."):
        all_pos = get_top_keywords(tag_grouped_dfs, POS_TARGETS)
        all_neg = get_top_keywords(tag_grouped_dfs, NEG_TARGETS)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**전체 리뷰 긍정 키워드 TOP 20**")
        if all_pos:
            st.dataframe(pd.DataFrame(all_pos.most_common(20), columns=["단어", "빈도"]))
        else:
            st.info("긍정 키워드가 없습니다.")
    with col2:
        st.markdown("**전체 리뷰 부정 키워드 TOP 20**")
        if all_neg:
            st.dataframe(pd.DataFrame(all_neg.most_common(20), columns=["단어", "빈도"]))
        else:
            st.info("부정 키워드가 없습니다.")

    st.markdown("---")
    st.markdown("### 브랜드 이미지")
    df_plot = prepare_treemap_data(tag_grouped_dfs, POS_TARGETS, STOPWORDS)
    show_treemap(df_plot, "빈도", "긍정 키워드")

    st.markdown("### 브랜드 이미지")
    df_plot = prepare_treemap_data(tag_grouped_dfs, NEG_TARGETS, STOPWORDS)
    show_treemap(df_plot, "빈도", "부정 키워드")

    st.markdown("### 리뷰 수를 고려한 브랜드 이미지")
    df_plot = prepare_log_nom_treemap_data(tag_grouped_dfs, POS_TARGETS, STOPWORDS)
    show_treemap(df_plot, "로그정규화_빈도", "긍정 키워드")

    st.markdown("### 리뷰 수를 고려한 브랜드 이미지")
    df_plot = prepare_log_nom_treemap_data(tag_grouped_dfs, NEG_TARGETS, STOPWORDS)
    show_treemap(df_plot, "로그정규화_빈도", "부정 키워드")

    st.markdown("---")

    # 긍정 감정 워드클라우드
    if st.checkbox("🔵 긍정 감정 워드클라우드 모아보기"):
        for i in range(0, len(tag_grouped_dfs), 5):
            row = list(tag_grouped_dfs.items())[i:i+5]
            cols = st.columns(len(row))
            for (tag_name, df), col in zip(row, cols):
                pos_counter = extract_context(df['리뷰 내용'], POS_TARGETS)
                with col:
                    st.markdown(f"**{tag_name}**")
                    if pos_counter:
                        buf = generate_wordcloud_image(pos_counter, "Blues")
                        st.image(buf, use_container_width=True)
                    else:
                        st.info("데이터 없음")

    # 부정 감정 워드클라우드
    if st.checkbox("🔴 부정 감정 워드클라우드 모아보기"):
        for i in range(0, len(tag_grouped_dfs), 5):
            row = list(tag_grouped_dfs.items())[i:i+5]
            cols = st.columns(len(row))
            for (tag_name, df), col in zip(row, cols):
                neg_counter = extract_context(df['리뷰 내용'], NEG_TARGETS)
                with col:
                    st.markdown(f"**{tag_name}**")
                    if neg_counter:
                        buf = generate_wordcloud_image(neg_counter, "Reds")
                        st.image(buf, use_container_width=True)
                    else:
                        st.info("데이터 없음")