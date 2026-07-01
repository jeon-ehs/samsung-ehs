import streamlit as st
import requests
import datetime
import urllib.parse
from streamlit_autorefresh import st_autorefresh

# =====================================================================
# 1. 페이지 기본 설정 및 백그라운드 갱신
# =====================================================================
st.set_page_config(page_title="협력사 일일 안전 포털", page_icon="🛡️", layout="wide")
st_autorefresh(interval=60000, key="ehs_dashboard_refresh")

def local_css():
    st.markdown("""
        <style>
            /* CSS 스타일 코드는 이전과 동일합니다 (변경 없음) */
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            html, body, .stApp { font-family: 'Noto Sans KR', sans-serif; }
            header {visibility: hidden;}
            .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
            div[data-baseweb="input"], div[data-baseweb="select"] > div { background-color: var(--secondary-background-color) !important; border: 1px solid rgba(148, 163, 184, 0.5) !important; border-radius: 6px !important; color: var(--text-color) !important; }
            div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: #1D4ED8 !important; box-shadow: 0 0 0 1px #1D4ED8 !important; }
            .news-box { background-color: var(--secondary-background-color); border-left: 5px solid #EAB308; padding: 15px 18px; margin-bottom: 10px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); font-size: 15.5px; color: var(--text-color); transition: all 0.2s ease-in-out; }
            .news-box:hover { transform: translateX(5px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); background-color: rgba(234, 179, 8, 0.1); cursor: pointer; }
            div[data-baseweb="tab-highlight"] { display: none; }
            [data-testid="stTabs"] button { background-color: var(--secondary-background-color) !important; border-radius: 8px !important; padding: 10px 16px !important; border: 1px solid rgba(148, 163, 184, 0.3) !important; margin-right: 6px !important; transition: all 0.3s ease-in-out !important; }
            [data-testid="stTabs"] button p { color: var(--text-color) !important; font-weight: 500 !important; opacity: 0.8; }
            [data-testid="stTabs"] button[aria-selected="true"] { opacity: 1; }
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] { background-color: #EFF6FF !important; border-color: #1D4ED8 !important; } [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] p { color: #1D4ED8 !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] { background-color: #F0FDFA !important; border-color: #0F766E !important; } [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] p { color: #0F766E !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] { background-color: #FFF7ED !important; border-color: #C2410C !important; } [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] p { color: #C2410C !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] { background-color: #FEF2F2 !important; border-color: #B91C1C !important; } [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] p { color: #B91C1C !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] { background-color: #FAF5FF !important; border-color: #6D28D9 !important; } [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] p { color: #6D28D9 !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] { background-color: #FEF3C7 !important; border-color: #B45309 !important; } [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] p { color: #B45309 !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] { background-color: #F8FAFC !important; border-color: #334155 !important; } [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] p { color: #334155 !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)
local_css()

# =====================================================================
# 2. 공공데이터 API 실시간 호출 (1분 주기 캐싱)
# =====================================================================
@st.cache_data(ttl=60)
def get_weather_data():
    try:
        if "KMA_API_KEY" in st.secrets:
            # ... (기상청 API 호출 코드, 변경 없음) ...
            return weather_data, datetime.datetime.now() # [개선] 데이터와 함께 현재 시간 반환
    except Exception:
        pass
    return ({'temp': 28.5, 'humid': 60.0, 'rain': 0.0}, datetime.datetime.now())

@st.cache_data(ttl=60)
def get_daily_news():
    news_list = []
    # [핵심 개선] 1. 네이버 뉴스 API로 최신 속보 가져오기
    try:
        if "NAVER_CLIENT_ID" in st.secrets and "NAVER_CLIENT_SECRET" in st.secrets:
            headers = {
                'X-Naver-Client-Id': st.secrets['NAVER_CLIENT_ID'],
                'X-Naver-Client-Secret': st.secrets['NAVER_CLIENT_SECRET'],
            }
            # '중대재해' 또는 '사고속보' 키워드로 최신 뉴스 1개 검색
            query = urllib.parse.quote("중대재해 OR 사고속보")
            response = requests.get(f"https://openapi.naver.com/v1/search/news.json?query={query}&display=1&sort=sim", headers=headers, timeout=5)
            if response.status_code == 200 and response.json()['items']:
                latest_news = response.json()['items'][0]
                title = f"⚡ **[최신속보]** {latest_news['title'].replace('<b>', '').replace('</b>', '')}"
                news_list.append({"title": title, "url": latest_news['link']})
    except Exception:
        pass # 네이버 API 실패해도 다른 API로 계속 진행

    # 2. 기존 안전보건공단 API 데이터 가져오기 (스마트 검색 링크 방식 유지)
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/BoardService/getBoardList'
            params = {'serviceKey': api_key, 'boardId': 'news', 'numOfRows': '2', 'type': 'json'} # 네이버 뉴스가 1개 추가되므로 2개로 조정
            response = requests.get(url, params=params, timeout=5)
            items = response.json()['response']['body']['items']['item']
            for item in items:
                title = item.get('title', '')
                if not title: continue
                search_query = urllib.parse.quote(f"안전보건공단 {title}")
                safe_link = f"https://search.naver.com/search.naver?query={search_query}"
                news_list.append({"title": title, "url": safe_link})
    except Exception:
        pass

    # 3. 모든 API 실패 시 보여줄 최종 대체 데이터
    if not news_list:
        fallback_data = ["타 현장 지붕 보수공사 중 채광창 파손 추락사고 발생", "혹서기 근로자 휴게시설 설치 기준 및 에어컨 가동 집중 점검 기간"]
        for title in fallback_data:
            search_query = urllib.parse.quote(f"안전보건공단 {title}")
            safe_link = f"https://search.naver.com/search.naver?query={search_query}"
            news_list.append({"title": f"🚨 {title}", "url": safe_link})

    return news_list, datetime.datetime.now() # [개선] 데이터와 함께 현재 시간 반환

@st.cache_data(ttl=43200)
def get_kosha_safety_rules(industry):
    # ... (업종별 안전수칙 가져오는 코드, 변경 없음) ...
    pass

# =====================================================================
# 3. 대시보드 화면 렌더링
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>", unsafe_allow_html=True)
st.markdown("---")

# --- [날씨 섹션] ---
weather_data, weather_update_time = get_weather_data()
st.subheader(f"📡 현장 실시간 기상 정보 (수원 기준)")
c1, c2, c3 = st.columns(3)
with c1: st.info(f"🌡️ **현재 기온:** {weather_data['temp']} ℃")
with c2: st.info(f"💧 **현재 습도:** {weather_data['humid']} %")
with c3: st.info(f"☔ **강수량:** {weather_data['rain']} mm")

# [개선] 기상특보 및 최종 업데이트 시간 표시
if weather_data['temp'] >= 33.0: st.error("🚨 **[폭염 경보]** 온열질환 발생 위험! 옥외작업 최소화 및 휴식을 보장하세요.")
elif weather_data['temp'] <= -5.0: st.info("🚨 **[한파 주의]** 동절기 한랭질환 및 빙판길 미끄러짐에 주의하세요.")
elif weather_data['rain'] > 0.0: st.warning("☔ **[강우 주의]** 감전 및 미끄러짐 재해 위험이 높습니다.")
else: st.success("✅ 현재 특별한 기상 악화 위험은 없습니다. 기본 수칙을 준수 바랍니다.")
st.caption(f"🕒 날씨 최종 업데이트: {weather_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")


# --- [이슈 섹션] ---
news_data, news_update_time = get_daily_news()
st.subheader("📰 오늘의 안전보건 주요 이슈")
for news in news_data:
    clickable_box = f"""<a href="{news['url']}" target="_blank" style="text-decoration: none;"><div class='news-box'>🔗 {news['title']}</div></a>"""
    st.markdown(clickable_box, unsafe_allow_html=True)
# [개선] 뉴스 최종 업데이트 시간 표시
st.caption(f"🕒 뉴스 최종 업데이트: {news_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# --- [업종별 탭 및 TBM 확인서 섹션] ---
# ... (이하 코드 변경 없음) ...
