import streamlit as st
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from konlpy.tag import Okt
import openai
import os

# ✅ OpenAI 클라이언트
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    gpt_enabled = True
except Exception:
    gpt_enabled = False

# 형태소 분석 함수
def tokenize(text: str) -> str:
    okt = Okt()
    return ' '.join(okt.nouns(text)) if isinstance(text, str) else ''

# 키워드 기반 간단한 분류 (Fallback)
def summarize_topic_keywords(keywords: list[str]) -> str:
    joined = ' '.join(keywords)
    if any(word in joined for word in ['배송', '빠름', '정확', '하루']):
        return '📦 배송 관련'
    elif any(word in joined for word in ['맛', '고소', '달콤', '진하다', '초코']):
        return '🍫 맛과 향미'
    elif any(word in joined for word in ['가격', '저렴', '비싸다', '할인']):
        return '💰 가격 이슈'
    elif any(word in joined for word in ['포장', '깔끔', '깨끗', '상자']):
        return '🎁 포장 상태'
    else:
        return '🌀 기타'

# GPT 주제 라벨링 함수 (오류 시 fallback 사용)
def get_topic_label(keywords: list[str]) -> str:
    if not gpt_enabled:
        return summarize_topic_keywords(keywords)

    prompt = f"""
다음 키워드들을 대표할 수 있는 주제를 한국어로 간결하게 만들어 주세요.
키워드: {', '.join(keywords)}
형식: 하나의 주제 이름만 출력 (예: '가격 평가', '맛', '배송 경험')
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return summarize_topic_keywords(keywords)

# 전체 분석 함수
def render(df: pd.DataFrame, n_topics: int = 4, n_keywords: int = 10):
    st.title("ABSA 주제 분석")
    st.subheader('**주제 이름은 참고만 부탁 드립니다**')

    selected_brand = st.selectbox("브랜드를 선택하세요", df.keys())
    df = df[selected_brand]

    if '리뷰 내용' not in df.columns:
        st.error("❗ '리뷰 내용' 컬럼이 없습니다.")
        st.write("컬럼 목록:", df.columns.tolist())
        return

    df = df.copy()
    df['형태소'] = df['리뷰 내용'].astype(str).apply(tokenize)

    vectorizer = TfidfVectorizer(max_df=0.9, min_df=2)
    dtm = vectorizer.fit_transform(df['형태소'])

    if dtm.shape[0] == 0 or dtm.shape[1] == 0:
        st.warning("❗ 유효한 텍스트가 부족합니다.")
        return

    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(dtm)

    vocab = vectorizer.get_feature_names_out()
    topic_data = []

    st.info("🔍 주제 추출 중...")

    for idx, topic in enumerate(lda.components_):
        keywords = [vocab[i] for i in topic.argsort()[:-n_keywords - 1:-1]]
        label = get_topic_label(keywords)

        topic_data.append({
            "주제 번호": f"주제 {idx+1}",
            "주제 이름": label,
            "키워드 목록": ', '.join(keywords)
        })

    st.success("✅ 분석 완료!")
    st.table(pd.DataFrame(topic_data))

# # 실행 부분
# if __name__ == "__main__":
#     st.set_page_config(layout="wide")

#     st.sidebar.header("📂 데이터 업로드")
#     uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (리뷰 내용 포함)", type="csv")

#     if uploaded_file:
#         df = pd.read_csv(uploaded_file)
#         run_absa(df)
#     else:
#         st.warning("왼쪽에서 CSV 파일을 업로드해주세요.")
