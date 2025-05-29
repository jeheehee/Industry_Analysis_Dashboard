# api키 따로 관리, 깃 ignore에 추가

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import signaturehelper
from openpyxl import load_workbook

# API 설정값
BASE_URL = 'https://api.naver.com'
API_KEY = 'a' # 1. https://manage.searchad.naver.com/ 접속 2. 사이트에서 api발급 3. 도구 -> api 사용 관리 4. 액세스라이선스키 입력
SECRET_KEY = 'b' #비밀키 입력
CUSTOMER_ID = 'c' #customer_id 입력
URI = '/keywordstool'
METHOD = 'GET'
DOWNLOAD_PATH = r"C:\Users\user\workspace\keyword\code" #파일 저장 경로 설정

# 광고 API Header 생성
def get_header():
    timestamp = str(round(time.time() * 1000))
    signature = signaturehelper.Signature.generate(timestamp, METHOD, URI, SECRET_KEY)
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': API_KEY,
        'X-Customer': str(CUSTOMER_ID),
        'X-Signature': signature
    }

# 키워드 검색량 API 호출
def get_monthly_volume(keyword):
    params = {'hintKeywords': keyword, 'showDetail': '1'}
    res = requests.get(BASE_URL + URI, params=params, headers=get_header())
    if res.status_code == 200:
        for item in res.json().get('keywordList', []):
            if item['relKeyword'] == keyword:
                pc = int(item.get('monthlyPcQcCnt') or 0)
                mobile = int(item.get('monthlyMobileQcCnt') or 0)
                return pc + mobile
    return None

# Selenium 설정
def init_driver():
    options = Options()
    options.add_argument("--headless")  # 디버깅 필요시 주석 설정
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_PATH,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    return webdriver.Chrome(options=options)

# 다운로드된 엑셀 파일 경로 추출
def get_latest_excel():
    files = [f for f in os.listdir(DOWNLOAD_PATH) if f.endswith(".xlsx") and f.startswith("datalab")]
    if not files:
        return None
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_PATH, x)), reverse=True)
    return os.path.join(DOWNLOAD_PATH, files[0])

# 키워드 추정 검색량 계산 함수
def process_keyword(keyword, driver, wait, start_date, end_date, volume):
    print(f"{keyword}에 대한 데이터 생성 중 (API 검색량: {volume})")

    try:
        # 1. 네이버 데이터랩 접속
        driver.get("https://datalab.naver.com/keyword/trendSearch.naver")

        # 2. 검색어 입력
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#item_sub_keyword1_1"))) #변경 가능성 있음
        search_input.clear()
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.RETURN)

        # 3. 기간 선택: 전체
        period_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            "#content > div > div.keyword_trend > div.section_step > div > form > fieldset > div > div.form_row.hr > div.set_period > label:nth-child(2)" #변경 가능성 있음
        )))
        period_button.click()

        # 4. 조회 버튼 클릭
        view_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            "#content > div > div.keyword_trend > div.section_step > div > form > fieldset > a > span" #변경 가능성 있음
        )))
        view_button.click()

        # 5. 다운로드 버튼 클릭
        download_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            "#content > div.section_keyword > div.keyword_trend > div.section_ca_board.w_space > div > div > div > div > div > div.graph_area > div.cont_file_down > a" #변경 가능성 있음
        )))
        download_button.click()
        print("다운로드 요청 완료")

        # 6. 다운로드 대기
        timeout = 15
        file_path = None
        while timeout > 0:
            time.sleep(1)
            file_path = get_latest_excel()
            if file_path:
                break
            timeout -= 1

        if not file_path:
            print("다운로드 실패 OR 시간 초과")
            return None

        # 7. 엑셀 읽기 및 날짜 상대값 추출
        raw_df = pd.read_excel(file_path, engine='openpyxl', header=None)
        start_idx = raw_df[0][raw_df[0] == "날짜"].index[0] + 1
        date_df = raw_df.iloc[start_idx:, [0, 1]].copy()
        date_df.columns = ["날짜", "비중"]
        date_df.dropna(inplace=True)
        date_df["비중"] = pd.to_numeric(date_df["비중"], errors="coerce")
        date_df["날짜"] = pd.to_datetime(date_df["날짜"])

        # 8. 최근 30일 기준 합산
        today = datetime.today()
        recent_30_start = (today - timedelta(days=30)).date()
        recent_30_end = (today - timedelta(days=1)).date()
        recent_df = date_df[(date_df["날짜"] >= pd.to_datetime(recent_30_start)) &
                            (date_df["날짜"] <= pd.to_datetime(recent_30_end))].copy()

        recent_sum = recent_df["비중"].sum()
        if recent_sum == 0:
            print(f"{keyword}의 최근 30일 비중 합이 0 입니다.")
            return None

        unit_value = volume / recent_sum
        date_df["추정검색량"] = date_df["비중"] * unit_value
        date_df["키워드"] = keyword
        date_df["API검색량"] = volume
        date_df["수집기간"] = f"{recent_30_start}~{recent_30_end}"

        print(f"✅ {keyword} 처리 완료")
        return date_df[["날짜", "키워드", "추정검색량", "API검색량", "수집기간"]]

    except Exception as e:
        print(f"{keyword} 처리 중 오류: {e}")
        return None
    
# 전체 처리 함수
def process_keywords(keywords):
    today = datetime.today()
    start_date = (today - timedelta(days=31)).strftime('%Y.%m.%d')
    end_date = (today - timedelta(days=1)).strftime('%Y.%m.%d')

    driver = init_driver()
    wait = WebDriverWait(driver, 10)
    result_frames = []

    for kw in keywords:
        print(f"처리 중: {kw}")
        vol = get_monthly_volume(kw)
        if not vol:
            print(f"{kw}: 검색량 없음")
            continue

        df = process_keyword(kw, driver, wait, start_date, end_date, vol)
        if df is not None:
            result_frames.append(df)

    driver.quit()

    if result_frames:
        return pd.concat(result_frames, ignore_index=True)
    else:
        return pd.DataFrame()

# 실행
if __name__ == "__main__":
    keyword_list = ["전자담배", "하카전자담배", "릴전자담배"] #API 특성상 키워드 최대 5개 제한되므로 방법 강구 필요 1.for문으로 처리 2. 축적되는 데이터는 어떻게 처리할지 3. etc 
    final_df = process_keywords(keyword_list)

    if not final_df.empty:
        output_path = os.path.join(DOWNLOAD_PATH, "입력_키워드_검색량.csv") # 파일명 변경
        final_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"저장 완료: {output_path}")
    else:
        print("결과 없음")
