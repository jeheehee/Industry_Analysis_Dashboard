import streamlit as st
import re
from konlpy.tag import Okt
from collections import Counter

STOPWORDS = set([
    '이', '가', '을', '를', '은', '는', '와', '과', '도', '에서', '에게', '보다', '까지', '부터',
    '수', '것', '등', '정도', '경우', '함께', '모두', '언제', '어디서', '무슨', '아무', '있어서', '제품도', '제품이',
    '좋아요', '좋고', '좋습니다', '만족합니다', '좋은', '좋네요', '좋다',
    '없고', '없어서',
    '그러나', '하지만', '그리고', '또한', '그러므로', '그래서', '너무', '매우', '정말', '진짜', '너무너무',
    '많이', '다만', '약간', '뭔가', '조금',
    '해당', '자체', '이상', '이하', '통해', '위해', '대한', '그냥', '계속', '아주', '엄청', '완전',
    '배송', '빠른', '배송도', '빠르고', '배송이', '빠른배송', '배송빠르고', '빨라서',
])

synonym_map = {
    '불편하다': '불편', '불편함': '불편', '불편': '불편',
    '고장나다': '고장', '고장남': '고장', '고장났다': '고장', '고장': '고장',
    '느리다': '느림', '느림감': '느림', '느림': '느림',
    '실망스럽다': '실망', '실망스러운': '실망', '실망': '실망',
    '짜증나다': '짜증', '짜증나는': '짜증', '짜증': '짜증',
    '화나다': '화남', '화남': '화남',
    '불만족': '불만', '불만족스럽다': '불만', '불만': '불만',
    '아쉽다': '아쉬움', '아쉬움': '아쉬움',
    '부족하다': '부족', '부족한': '부족', '부족': '부족',
    '불쾌하다': '불쾌', '불쾌한': '불쾌', '불쾌': '불쾌',
    '지루하다': '지루', '지루한': '지루', '지루': '지루',
    '불친절하다': '불친절', '불친절한': '불친절', '불친절': '불친절',
    '복잡하다': '복잡', '복잡한': '복잡', '복잡': '복잡',
    '헷갈리다': '헷갈림', '헷갈림': '헷갈림',
    '약하다': '약함', '약한': '약함', '약함': '약함',
    '무겁다': '무거움', '무거움': '무거움',
    '불량하다': '불량', '불량품': '불량', '불량': '불량'
}

okt = Okt()

def clean_text(text):
    return re.sub(r'[^가-힣\s]', '', str(text))

# def clean_tag_text(text):
#     text = str(text).replace("KT&G", "릴") 
#     return re.sub(r'[^가-힣\s]', '', text)

@st.cache_data
def extract_context(texts, targets, stopwords=STOPWORDS):
    phrases = []
    for text in texts:
        words = re.findall(r'[가-힣]{2,}', text)
        phrases.extend([
            words[i - 1] for i, word in enumerate(words)
            if i > 0 and any(t in word for t in targets) and words[i - 1] not in stopwords
        ])
    return Counter(phrases)

# 단어 정규화 및 가중치 빈도 분석
@st.cache_data
def normalize_texts(texts):
    result = []
    for text in texts:
        tokens = okt.pos(text, stem=True)
        words = []
        for word, pos in tokens:
            if pos in ['Noun', 'Adjective', 'Verb'] and word not in STOPWORDS:
                word = synonym_map.get(word, word)
                words.append(word)
        result.append(' '.join(words))
    return result