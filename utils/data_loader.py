import streamlit as st
import os
import pandas as pd
from utils.text_cleaner import clean_text

CATEGORY_KEYWORDS = {
    '궐련형': ['궐련', '릴', '아이코스'],
    '액상형': ['액상', '입호흡', '폐호흡', '베이포레소', '아스파이어'],
    '일회용': ['일회용', '일회']
}

@st.cache_data
def load_data(folder="./data"):
    tag_grouped_dfs = {}
    category_grouped_dfs = {'궐련형': [], '액상형': [], '일회용': []}

    for fname in os.listdir(folder):
        if fname.endswith(".csv"):
            tag = fname.split('_')[0].strip('[]').replace("KT&G", "릴") 
            lower_name = fname.lower()
            matched_category = None
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(k in lower_name for k in keywords):
                    matched_category = category
                    break
            path = os.path.join(folder, fname)
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
                if '리뷰 내용' not in df.columns:
                    continue
                df['리뷰 내용'] = df['리뷰 내용'].astype(str).apply(clean_text)
                tag_grouped_dfs.setdefault(tag, []).append(df)
                if matched_category:
                    category_grouped_dfs[matched_category].append(df)
            except Exception as e:
                print(f"⚠️ 파일 로딩 실패: {fname} - {e}")

    for tag in tag_grouped_dfs:
        tag_grouped_dfs[tag] = pd.concat(tag_grouped_dfs[tag], ignore_index=True)
    for cat in category_grouped_dfs:
        if category_grouped_dfs[cat]:
            category_grouped_dfs[cat] = pd.concat(category_grouped_dfs[cat], ignore_index=True)
        else:
            category_grouped_dfs[cat] = pd.DataFrame(columns=['리뷰 내용'])

    return category_grouped_dfs, tag_grouped_dfs