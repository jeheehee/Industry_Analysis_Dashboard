import matplotlib.pyplot as plt
from wordcloud import WordCloud
import streamlit as st
from io import BytesIO

def generate_wordcloud_image(counter, colormap="Blues", width=800, height=400):
    if not counter:
        return None
    wc = WordCloud(
        font_path='C:/Windows/Fonts/malgun.ttf',
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