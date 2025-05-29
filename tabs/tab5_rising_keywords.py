import pandas as pd
from prophet import Prophet
import streamlit as st
import plotly.graph_objs as go
import matplotlib as mpl
from collections import Counter

TARGETS = ['좋', '만족', '훌륭', '깔끔', '편하', '빠르', '예쁘', '감동', '신나', '행복', '사랑', '유용', '기분좋', '재밌', '즐겁', '고급', '세련', '친절', '정확', '튼튼',
           '별로', '불편', '고장', '느리', '느림', '실망', '짜증', '화남', '불만', '아쉬', '부족', '망함', '불쾌', '지루', '불친절', '복잡', '헷갈림', '약함', '무거움', '불량']

# 폰트 설정
mpl.rc('font', family='Malgun Gothic')

# 데이터 불러오기
df_raw = pd.read_csv('./search_data/월별 검색량 데이터.csv')
df_raw = df_raw.rename(columns={'월': 'ds'})
df_raw['ds'] = pd.to_datetime(df_raw['ds'])
df_melted = df_raw.melt(id_vars=['ds'], var_name='keyword', value_name='search_volume')

# 성장률 계산
recent_data = df_raw.tail(3)
previous_data = df_raw.iloc[-6:-3]
growth_rates = {}
for keyword in df_raw.columns[1:]:
    recent_avg = recent_data[keyword].mean()
    previous_avg = previous_data[keyword].mean()
    if previous_avg > 0:
        growth = (recent_avg - previous_avg) / previous_avg * 100
    else:
        growth = 0
    growth_rates[keyword] = growth

top_keywords = pd.Series(growth_rates).sort_values(ascending=False).head(5)
bottom_keywords = pd.Series(growth_rates).sort_values().head(5)

def get_related_reviews(keyword, tag_grouped_dfs, max_examples=5):
    results = []
    for brand_df in tag_grouped_dfs.values():
        reviews = brand_df['리뷰 내용'].astype(str)
        matches = reviews[reviews.str.contains(keyword, case=False, na=False)].tolist()
        results.extend(matches)
        if len(results) >= max_examples:
            break
    return results[:max_examples]

# 간단한 이벤트 설명 매핑 (예시)
# event_map = {
#     "아스몬": "신제품 출시 및 유튜브 리뷰 확산 (2025.03)",
#     "하카전자담배": "편의점 입점 확대 및 SNS 바이럴 (2025.02)",
#     "빌리아": "기획 할인 이벤트로 검색량 증가 (2025.01)"
# }

# Prophet 예측 함수
def get_forecast(keyword):
    df_target = df_melted[df_melted['keyword'] == keyword][['ds', 'search_volume']]
    df_target = df_target.rename(columns={'search_volume': 'y'})
    model = Prophet(seasonality_mode='multiplicative', changepoint_prior_scale=0.5)
    model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    model.fit(df_target)
    future = model.make_future_dataframe(periods=6, freq='M')
    forecast = model.predict(future)
    return df_target, forecast

# 리뷰 연관 키워드 추출
def get_related_keywords(keyword, tag_grouped_dfs, top_n=10):
    co_occurrence = []
    for brand_df in tag_grouped_dfs.values():
        reviews = brand_df['리뷰 내용'].astype(str)
        for text in reviews:
            if keyword in text:
                co_occurrence += [word for word in TARGETS if word in text and word != keyword]
    return Counter(co_occurrence).most_common(top_n)

# Streamlit UI
def render(tag_grouped_dfs):
    st.subheader("급상승 키워드 분석")
    months = st.slider("표시할 기간 (개월):", min_value=6, max_value=24, step=3, value=12)
    cutoff = pd.to_datetime(df_raw['ds'].max()) - pd.DateOffset(months=months)

    # 급상승 키워드
    st.markdown("### 🔼 최근 급상승 키워드 검색량")
    fig_top = go.Figure()
    for kw in top_keywords.index:
        df = df_melted[df_melted['keyword'] == kw]
        df = df[df['ds'] >= cutoff]
        fig_top.add_trace(go.Scatter(x=df['ds'], y=df['search_volume'],
                                     mode='lines', name=f"{kw} ({growth_rates[kw]:.1f}%)"))
    fig_top.update_layout(title='급상승 키워드 검색량')
    st.plotly_chart(fig_top)

    # 급하락 키워드
    st.markdown("### 🔽 최근 급하락 키워드 검색량")
    fig_bottom = go.Figure()
    for kw in bottom_keywords.index:
        df = df_melted[df_melted['keyword'] == kw]
        df = df[df['ds'] >= cutoff]
        fig_bottom.add_trace(go.Scatter(x=df['ds'], y=df['search_volume'],
                                        mode='lines', name=f"{kw} ({growth_rates[kw]:.1f}%)"))
    fig_bottom.update_layout(title='급하락 키워드 검색량')
    st.plotly_chart(fig_bottom)

    # 키워드 선택
    keyword_options = [f"{kw} ({growth_rates[kw]:.1f}%)" for kw in top_keywords.index]
    selected_label = st.selectbox("🔍 분석할 키워드를 선택하세요:", keyword_options)
    selected_keyword = selected_label.split(' ')[0]

    # 트렌드 예측 + 신뢰구간
    st.markdown(f"### `{selected_keyword}` 검색량 트렌드")
    df_target, forecast = get_forecast(selected_keyword)
    forecast_filtered = forecast[forecast['ds'] >= cutoff]

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=forecast_filtered['ds'], y=forecast_filtered['yhat'],
                                   mode='lines', name='예측값', line=dict(color='blue')))
    fig_trend.add_trace(go.Scatter(x=forecast_filtered['ds'], y=forecast_filtered['yhat_upper'],
                                   mode='lines', name='상한', line=dict(width=0), showlegend=False))
    fig_trend.add_trace(go.Scatter(x=forecast_filtered['ds'], y=forecast_filtered['yhat_lower'],
                                   fill='tonexty', mode='lines', name='신뢰구간',
                                   line=dict(width=0), fillcolor='rgba(0,100,200,0.1)'))
    fig_trend.update_layout(title=f"검색량 트렌드 + 신뢰구간")
    st.plotly_chart(fig_trend)

    # # 연관 리뷰 키워드
    # st.markdown(f"### `{selected_keyword}` 관련 리뷰 키워드")
    # related = get_related_keywords(selected_keyword, tag_grouped_dfs)
    # if related:
    #     st.write({k: v for k, v in related})
    # else:
    #     st.info("리뷰에서 연관 키워드를 찾지 못했습니다.")

    # # 리뷰 예시 출력
    # st.markdown(f"### `{selected_keyword}` 관련 리뷰 예시")
    # examples = get_related_reviews(selected_keyword, tag_grouped_dfs)
    # if examples:
    #     for i, text in enumerate(examples, 1):
    #         st.markdown(f"**{i}.** {text}")
    # else:
    #     st.info("해당 키워드가 포함된 리뷰를 찾을 수 없습니다.")

    # 관련 이벤트 정보
    # st.markdown("### 📰 관련 뉴스/이벤트")
    # event_text = event_map.get(selected_keyword, "해당 키워드에 대한 뉴스/이벤트 정보가 없습니다.")
    # st.info(event_text)
