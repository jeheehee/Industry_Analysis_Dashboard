import streamlit as st
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import os
from utils.data_loader import load_data
from tabs import (
    tab1_emotion, tab2_emotion2, tab3_brand_keyword,
    tab4_compare, tab6_absa, tab7_score
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


st.title("리뷰 분석 대시보드")
# 데이터 로딩
category_grouped_dfs, tag_grouped_dfs = load_data()

# 탭처럼 보이는 radio UI
tab_choice = st.radio(
    "분석 항목을 선택하세요",
    options=[
        "제품 유형별 리뷰분석",
        "브랜드 포지셔닝 맵",
        "경쟁사 분석",
        "제품(브랜드)별 리뷰분석",
        "전체 리뷰 상위 키워드 비교",
        # "ABSA",
    ],
    horizontal=True
)
st.markdown("---")

# 선택된 탭에 따라 render 함수 실행
if "유형" in tab_choice:
    tab1_emotion.render(category_grouped_dfs)

elif "포지셔닝" in tab_choice:
    tab7_score.render(tag_grouped_dfs)
    
elif "경쟁사" in tab_choice:
    tab4_compare.render(tag_grouped_dfs)
    
elif "제품(브랜드)" in tab_choice:
    tab2_emotion2.render(tag_grouped_dfs)

elif "전체 리뷰" in tab_choice:
    tab3_brand_keyword.render(tag_grouped_dfs)
    
# elif "ABSA" in tab_choice:
#     tab6_absa.render(tag_grouped_dfs)
