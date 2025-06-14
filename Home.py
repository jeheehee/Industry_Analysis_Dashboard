# Home.py

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm

# 전역 폰트 적용 함수
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl


st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center;'>🎯 리뷰 & 검색량 분석 대시보드</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>좌측 사이드바에서 분석 페이지를 선택하세요</h4>", unsafe_allow_html=True)

st.markdown("---")

st.markdown("<h6 style='text-align: center;'> 대시보드는 리뷰 텍스트와 키워드 검색량 데이터를 기반으로 산업분석을 돕기 위해 구성되었습니다.</h6>", unsafe_allow_html=True)

