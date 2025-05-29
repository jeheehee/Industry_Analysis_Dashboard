import streamlit as st
import matplotlib.pyplot as plt
from utils.data_loader import load_data
from tabs import (
    tab1_emotion, tab2_emotion2, tab3_brand_keyword,
    tab4_compare, tab6_absa, tab7_score
)

st.title("리뷰 분석 대시보드")
# 데이터 로딩
category_grouped_dfs, tag_grouped_dfs = load_data()

# 탭처럼 보이는 radio UI
tab_choice = st.radio(
    "분석 항목을 선택하세요",
    options=[
        "제품 유형별 리뷰분석",
        "제품 종류별 리뷰분석",
        "상위 리뷰 키워드 비교",
        "경쟁사 분석",
        # "ABSA",
        "브랜드 포지셔닝 맵"
    ],
    horizontal=True
)
st.markdown("---")

# 선택된 탭에 따라 render 함수 실행
if "유형" in tab_choice:
    tab1_emotion.render(category_grouped_dfs)

elif "종류" in tab_choice:
    tab2_emotion2.render(tag_grouped_dfs)

elif "상위 리뷰" in tab_choice:
    tab3_brand_keyword.render(tag_grouped_dfs)

elif "경쟁사" in tab_choice:
    tab4_compare.render(tag_grouped_dfs)
    
# elif "ABSA" in tab_choice:
#     tab6_absa.render(tag_grouped_dfs)
    
elif "포지셔닝" in tab_choice:
    tab7_score.render(tag_grouped_dfs)
