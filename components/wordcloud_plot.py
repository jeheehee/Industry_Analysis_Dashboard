import streamlit as st
from wordcloud import WordCloud
from io import BytesIO

@st.cache_data
def generate_wordcloud_image(counter, colormap="Blues", width=800, height=400):
    if not counter:
        return None

    # 업로드된 폰트 경로
    font_path = "assets/NanumGothic.ttf"

    wc = WordCloud(
        font_path=font_path,
        background_color='white',
        width=width,
        height=height,
        colormap=colormap
    ).generate_from_frequencies(counter)

    buf = BytesIO()
    wc.to_image().save(buf, format="PNG")
    buf.seek(0)
    return buf



def plot_wordcloud(counter, label, colormap="Blues"):
    buf = generate_wordcloud_image(counter, colormap)
    if buf:
        st.image(buf, caption=f"{label} 워드클라우드", use_container_width=True)
    else:
        st.info(f"{label} 키워드 부족")
        