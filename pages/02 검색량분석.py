import streamlit as st
import matplotlib.pyplot as plt
from utils.data_loader import load_data
from tabs import (
    tab5_rising_keywords,
)

st.set_page_config(layout="wide")
st.title("검색량분석 대시보드")

# 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로딩
category_grouped_dfs, tag_grouped_dfs = load_data()

# 탭처럼 보이는 radio UI
tab_choice = st.radio(
    "분석 항목을 선택하세요",
    options=[
        "급상승 키워드 분석",
    ],
    horizontal=True
)
st.markdown("---")

# 선택된 탭에 따라 render 함수 실행
if "급상승" in tab_choice:
    tab5_rising_keywords.render(tag_grouped_dfs)

