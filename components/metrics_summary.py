import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def show_summary(df, label):
    review_count = len(df)
    mean_rating = df['별점'].mean()
    mean_length = df['리뷰 내용'].astype(str).apply(len).mean()

    st.metric(f"{label} 리뷰 수", review_count)
    st.metric(f"{label} 평균 별점", f"{mean_rating:.2f}")
    st.metric(f"{label} 평균 길이", f"{mean_length:.1f}자")
    
@st.cache_data
def show_summary_metrics(df1, df2):
    def summarize(df):
        return {
            '리뷰 수': len(df),
            '평균 별점': df['별점'].mean(),
            '평균 리뷰 길이': df['리뷰 내용'].apply(len).mean(),
        }

    summary1 = summarize(df1)
    summary2 = summarize(df2)

    col1, col2 = st.columns(2)
    with col1:
        
        st.metric("리뷰 수", summary1['리뷰 수'])
        st.metric("평균 별점", f"{summary1['평균 별점']:.2f}")
        st.metric("평균 리뷰 길이", f"{summary1['평균 리뷰 길이']:.1f}자")
    with col2:
        st.metric("리뷰 수", summary2['리뷰 수'])
        st.metric("평균 별점", f"{summary2['평균 별점']:.2f}")
        st.metric("평균 리뷰 길이", f"{summary2['평균 리뷰 길이']:.1f}자")
        

def plot_rating_comparison(df1, df2, tags):
    def plot_rating_distribution(df, title):
        fig, ax = plt.subplots()
        sns.countplot(x='별점', data=df, ax=ax, palette='coolwarm')
        ax.set_title(title)
        st.pyplot(fig)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 📊 {tags[0]} 요약")
        plot_rating_distribution(df1, f"{tags[0]} 별점 분포")
    with col2:
        st.markdown(f"### 📊 {tags[1]} 요약")
        plot_rating_distribution(df2, f"{tags[1]} 별점 분포")