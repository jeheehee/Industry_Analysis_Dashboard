import streamlit as st
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import os
from utils.data_loader import load_data
from tabs import (
    tab5_rising_keywords,
    tab8_comprete,
)

# 폰트 경로 확인
font_path = "assets/NanumGothic.ttf"  # 업로드한 폰트 경로
if not os.path.exists(font_path):
    st.error("❌ 폰트 파일을 찾을 수 없습니다.")
else:
    font_prop = fm.FontProperties(fname=font_path)
    
# 정확한 폰트 경로
font_path = 'assets/NanumGothic.ttf'
fm.fontManager.addfont(font_path)
font_name = fm.FontProperties(fname=font_path).get_name()

# rcParams에 정확한 폰트 이름으로 등록
mpl.rcParams['font.family'] = font_name
mpl.rcParams['axes.unicode_minus'] = False


st.title("검색량 분석 대시보드")
# 데이터 로딩
category_grouped_dfs, tag_grouped_dfs = load_data()

# 탭처럼 보이는 radio UI
tab_choice = st.radio(
    "분석 항목을 선택하세요",
    options=[
        "급상승 키워드 분석",
        "경쟁 브랜드 비교 분석",
    ],
    horizontal=True
)
st.markdown("---")

# 선택된 탭에 따라 render 함수 실행
if "급상승" in tab_choice:
    tab5_rising_keywords.render(tag_grouped_dfs)
    
elif "경쟁" in tab_choice:
    tab8_comprete.render()

