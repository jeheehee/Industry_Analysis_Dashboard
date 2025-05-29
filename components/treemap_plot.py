import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
from utils.text_cleaner import extract_context

def prepare_treemap_data(tag_grouped_dfs, targets, stopwords):
    all_texts = [text for df in tag_grouped_dfs.values() for text in df['리뷰 내용']]
    full_counter = extract_context(all_texts, targets, stopwords)
    top_keywords = set([word for word, _ in full_counter.most_common(20)])

    rows = []
    keyword_freq_by_brand = {}
    for tag, df in tag_grouped_dfs.items():
        counter = extract_context(df['리뷰 내용'], targets, stopwords)
        for word, freq in counter.items():
            if word in top_keywords:
                keyword_freq_by_brand.setdefault(word, []).append((tag, freq))

    for word, brand_list in keyword_freq_by_brand.items():
        top_brands = sorted(brand_list, key=lambda x: x[1], reverse=True)[:7]  # Limit to 7
        for tag, freq in top_brands:
            rows.append({"키워드": word, "제품": tag, "빈도": freq})

    return pd.DataFrame(rows)

def prepare_log_nom_treemap_data(tag_grouped_dfs, targets, stopwords):
    all_texts = [text for df in tag_grouped_dfs.values() for text in df['리뷰 내용']]
    full_counter = extract_context(all_texts, targets, stopwords)
    top_keywords = set([word for word, _ in full_counter.most_common(20)])

    rows = []
    review_counts = {tag: len(df) for tag, df in tag_grouped_dfs.items()}

    keyword_freq_by_brand = {}
    for tag, df in tag_grouped_dfs.items():
        counter = extract_context(df['리뷰 내용'], targets, stopwords)
        total_reviews = review_counts[tag]
        for word, freq in counter.items():
            if word in top_keywords:
                raw_ratio = freq / total_reviews if total_reviews > 0 else 0
                log_norm_freq = np.log1p(raw_ratio)
                keyword_freq_by_brand.setdefault(word, []).append((tag, log_norm_freq))

    for word, brand_list in keyword_freq_by_brand.items():
        top_brands = sorted(brand_list, key=lambda x: x[1], reverse=True)[:7]  # Limit to 7
        for tag, log_norm_freq in top_brands:
            rows.append({"키워드": word, "제품": tag, "로그정규화_빈도": log_norm_freq})

    return pd.DataFrame(rows)

def show_treemap(df_plot, value_col, title):
    if df_plot.empty:
        st.info("📊 시각화할 데이터가 없습니다.")
        return

    fig = px.treemap(
        df_plot,
        path=["키워드", "제품"],
        values=value_col,
        color="키워드",
        title=title,
        height=600,
        custom_data=[value_col]
    )

    fig.update_traces(
        texttemplate="%{label}",
        textposition="middle center",
        hovertemplate=f"<span style='font-size:22px'>%{{customdata[0]}}</span><extra></extra>",
        textfont=dict(size=20)
    )

    st.plotly_chart(fig, use_container_width=True)