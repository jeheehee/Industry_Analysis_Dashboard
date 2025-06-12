import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def calculate_summary(df: pd.DataFrame):
    if df.empty or '제품 유형' not in df.columns or '리뷰작성일' not in df.columns or '감정' not in df.columns:
        return None

    recent_threshold = datetime.today() - timedelta(days=30)
    recent_df = df[df['리뷰작성일'] >= recent_threshold]
    prev_df = df[df['리뷰작성일'] < recent_threshold]

    total_count = len(df)
    category_count = df['제품 유형'].nunique()
    main_type = df['제품 유형'].mode()[0]
    main_ratio = (df[df['제품 유형'] == main_type].shape[0] / total_count) * 100 if total_count > 0 else 0

    def growth_rate(df_recent, df_prev, keyword, sentiment):
        r = df_recent[(df_recent['감정'] == sentiment) & (df_recent['리뷰 내용'].str.contains(keyword, na=False))]
        p = df_prev[(df_prev['감정'] == sentiment) & (df_prev['리뷰 내용'].str.contains(keyword, na=False))]
        if len(p) == 0:
            return 100.0 if len(r) > 0 else 0.0
        return ((len(r) - len(p)) / len(p)) * 100

    pos_keyword = "디자인"
    neg_keyword = "가격"
    pos_growth = growth_rate(recent_df, prev_df, pos_keyword, '긍정')
    neg_growth = growth_rate(recent_df, prev_df, neg_keyword, '부정')

    return {
        "category_count": category_count,
        "main_type": main_type,
        "main_ratio": round(main_ratio, 1),
        "pos_keyword": pos_keyword,
        "neg_keyword": neg_keyword,
        "pos_growth": round(pos_growth, 1),
        "neg_growth": round(neg_growth, 1)
    }

def show_summary_box(summary):
    if not summary:
        return
    st.markdown(
        f"""
        <div style="background-color:#f9f9f9; padding: 1.2em; border-left: 5px solid #4CAF50; border-radius: 6px; font-size: 1rem;">
        <b>📌 요약:</b> 제품 유형 {summary['category_count']}가지 중 <b>{summary['main_type']}</b>은 전체 리뷰 수 중 <b>{summary['main_ratio']}%</b>를 차지하며, 최근 1개월 간 
        “<b>{summary['pos_keyword']}</b>” 관련 <span style='color:green; font-weight:bold;'>긍정 키워드 {summary['pos_growth']}% 증가</span>, 
        “<b>{summary['neg_keyword']}</b>” 관련 <span style='color:red; font-weight:bold;'>부정 키워드 {summary['neg_growth']}% 증가</span>했습니다.
        </div>
        """,
        unsafe_allow_html=True
    )
