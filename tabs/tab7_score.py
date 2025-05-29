
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime


# 긍정/부정 단어 사전
positive_words = ["좋다", "훌륭하다", "만족", "강하다", "높다", "추천", "최고", "튼튼하다", "완벽하다", "괜찮다", "잘되다"]
negative_words = ["낮다", "안좋다", "별로", "부족", "문제", "약하다", "실망", "떨어지다", "이상", "싫다", "불량", "최악", "나쁘다"]

# 키워드 사전
extended_keywords = {
    "성능": ["연무", "연무량", "흡입", "흡입감", "배터리", "성능", "내구성", "목넘김", "강도", "출력", "사용감", "소음", "발열", "전원", "지속력", "반응속도", "전압", "효율"],
    "디자인": ["디자인", "색상", "컬러", "예쁨", "이쁨", "모양", "스타일", "감성", "외형", "마감", "재질", "크기", "휴대성", "무게", "고급스러움", "간지", "미관", "디테일", "브랜드 느낌"],
    "가격": ["가격", "가성비", "비쌈", "싸다", "저렴", "할인", "구성비", "값", "지출", "경제적", "비용", "이벤트", "쿠폰", "혜택", "정가", "세일", "지갑", "합리적", "프로모션"]
}


# 분석 함수
def analyze_sentiment_with_examples(df, rating_range=(1, 5)):
    df = df.copy()
    df['리뷰 내용'] = df['리뷰 내용'].fillna("").str.lower()
    df['리뷰작성일'] = pd.to_datetime(df['리뷰작성일'], errors='coerce', format="%Y%m%d")
    df = df[(df['별점'] >= rating_range[0]) & (df['별점'] <= rating_range[1])]
    # if start_date:
    #     df = df[df['리뷰작성일'] >= pd.to_datetime(start_date)]
    # if end_date:
    #     df = df[df['리뷰작성일'] <= pd.to_datetime(end_date)]

    scores = {k: 0 for k in extended_keywords}
    examples = {k: [] for k in extended_keywords}
    total_mentions = 0

    for review in df['리뷰 내용']:
        for criterion, keywords in extended_keywords.items():
            if any(keyword in review for keyword in keywords):
                if any(neg in review for neg in negative_words):
                    continue
                if any(pos in review for pos in positive_words):
                    scores[criterion] += 1
                    if len(examples[criterion]) < 5:
                        highlighted = review
                        for kw in keywords:
                            highlighted = re.sub(f"({kw})", r"<span style='color:#d62728;font-weight:bold;'>\1</span>", highlighted)
                        examples[criterion].append(highlighted)
                    total_mentions += 1

    ratios = {k: round(v / total_mentions * 100, 2) if total_mentions else 0 for k, v in scores.items()}
    return ratios, examples

def weekly_sentiment_trend(df, rating_range=(1, 5)):
    df = df.copy()
    df['리뷰 내용'] = df['리뷰 내용'].fillna("").str.lower()
    df['리뷰작성일'] = pd.to_datetime(df['리뷰작성일'], errors='coerce', format="%Y%m%d")
    df = df[(df['별점'] >= rating_range[0]) & (df['별점'] <= rating_range[1])]
    df['week'] = df['리뷰작성일'].dt.to_period("W").apply(lambda r: r.start_time)

    results = []
    for week, group in df.groupby("week"):
        total_reviews = len(group)
        week_data = {"week": week, "total": total_reviews}
        for criterion, keywords in extended_keywords.items():
            count = 0
            for review in group['리뷰 내용']:
                if any(keyword in review for keyword in keywords):
                    if any(neg in review for neg in negative_words):
                        continue
                    if any(pos in review for pos in positive_words):
                        count += 1
            week_data[criterion] = round(count / total_reviews * 100, 2) if total_reviews else 0
        results.append(week_data)

    return pd.DataFrame(results)

# Streamlit UI
def render(tag_grouped_dfs):
    brand = st.selectbox("브랜드 선택", list(tag_grouped_dfs.keys()))
    # start_date = st.date_input("시작일", None)
    # end_date = st.date_input("종료일", None)
    rating_range = st.slider("별점 범위", 1, 5, (1, 5))

    if brand:
        df = tag_grouped_dfs[brand]
        ratios, examples = analyze_sentiment_with_examples(df, rating_range)
        best = max(ratios, key=ratios.get)

        st.markdown(f"### ✅ 가장 긍정적으로 언급된 기준: **{best}**")
        pie_df = pd.DataFrame({
            "기준": ratios.keys(),
            "비율": ratios.values()
        }).sort_values(by="비율", ascending=False)

        fig = px.pie(pie_df, values="비율", names="기준", hole=0.4, width=600, height=500)
        st.plotly_chart(fig)

        # selected = st.radio("🔍 기준별 대표 리뷰 보기", list(ratios.keys()))
        # st.markdown(f"#### 💬 `{selected}` 관련 대표 리뷰")
        # for review in examples[selected]:
        #     st.markdown(f"<div style='margin-bottom:10px;'>{review}</div>", unsafe_allow_html=True)

    # 전체 브랜드 분석
    positioning_data = []
    for tag, df in tag_grouped_dfs.items():
        ratios, _ = analyze_sentiment_with_examples(df, rating_range)
        if sum(ratios.values()) > 0:
            positioning_data.append({
                "브랜드": tag,
                "성능": ratios["성능"],
                "디자인": ratios["디자인"],
                "가격": ratios["가격"]
            })

    # 결과 시각화
    if positioning_data:

        col1, col2 = st.columns([1, 2])
        with col1:
            df_pos = pd.DataFrame(positioning_data).sort_values(by=["성능", "디자인", "가격"], ascending=False)
            st.subheader("브랜드별 기준 비율 순위표")
            st.dataframe(df_pos.set_index("브랜드").style.highlight_max(axis=0, color="lightgreen"))

        with col2:
            st.subheader("3D 포지셔닝 맵")
            fig3d = px.scatter_3d(df_pos, x="가격", y="성능", z="디자인", text="브랜드", color="브랜드", opacity=0.8, width=1000, height=800)
            fig3d.update_layout(scene=dict(xaxis_title="가격", yaxis_title="성능", zaxis_title="디자인"))
            st.plotly_chart(fig3d)

        st.subheader("2D 포지셔닝 맵 (기준 조합 시각화)")
        dim1 = st.selectbox("X축 기준 선택", ["가격", "성능", "디자인"], index=0)
        dim2 = st.selectbox("Y축 기준 선택", ["성능", "디자인", "가격"], index=1)

        if dim1 != dim2:
            fig2d = px.scatter(df_pos, x=dim1, y=dim2, text="브랜드", color="브랜드", size_max=60)
            fig2d.update_traces(textposition="top center")
            fig2d.update_layout(width=800, height=600, xaxis_title=dim1, yaxis_title=dim2)
            st.plotly_chart(fig2d)
            
        # 주간 변화 추이 시각화
    st.subheader("주간 감성 변화 추이")
    if brand:
        trend_df = weekly_sentiment_trend(tag_grouped_dfs[brand], rating_range)
        fig_week = px.line(
            trend_df, x="week", y=["성능", "디자인", "가격"],
            labels={"value": "긍정 비율 (%)", "week": "주간"},
            height=800, width=1200, markers=True
        )
        st.plotly_chart(fig_week)

# 순위표 높이 고정 (기존 col1 내부 수정)
        # st.markdown('<div style="height:800px; overflow:auto;">', unsafe_allow_html=True)
        # st.dataframe(df_pos.set_index("브랜드").style.highlight_max(axis=0, color="lightgreen"))
        # st.markdown('</div>', unsafe_allow_html=True)
