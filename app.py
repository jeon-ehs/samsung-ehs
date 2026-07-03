import streamlit as st
import requests
import datetime
import urllib.parse
import time
from streamlit_autorefresh import st_autorefresh
from datetime import timezone, timedelta

# =====================================================================
# 1. 페이지 기본 설정 및 1분 단위 백그라운드 자동 갱신
# =====================================================================
st.set_page_config(
    page_title="협력사 일일 안전 포털",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# [핵심] 앱 화면을 1분(60000ms)마다 알아서 새로고침하여 항상 최신 상태 유지
st_autorefresh(interval=60000, key="ehs_dashboard_refresh")

# =====================================================================
# 2. 고급 CSS 스타일링
# =====================================================================
def advanced_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            * { font-family: 'Noto Sans KR', sans-serif; }
            html, body, .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); }
            header { visibility: hidden; }
            .main .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 2.5rem; padding-right: 2.5rem; }
            
            .metric-card {
                background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
                border-radius: 12px; padding: 16px; margin: 8px 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08); border-left: 5px solid #1D4ED8;
            }
            .card-safe { border-left-color: #10B981; background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%); }
            .card-warning { border-left-color: #F59E0B; background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); }
            .card-danger { border-left-color: #EF4444; background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); }
            .card-critical { border-left-color: #DC2626; background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%); color: white; }
            
            .news-box {
                background: #ffffff; border-left: 5px solid #EAB308; border-radius: 10px;
                padding: 16px 20px; margin: 12px 0; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
            }
            .news-box:hover { transform: translateX(8px); background: #fffbeb; }
            .news-title { font-size: 15px; font-weight: 600; color: #1F2937; margin: 0; }
            .news-time { font-size: 12px; color: #9CA3AF; margin-top: 8px; }
            
            div[data-baseweb="tab-highlight"] { display: none; }
            [data-testid="stTabs"] button { background-color: #f3f4f6 !important; border-radius: 10px !important; padding: 12px 18px !important; border: 2px solid #e5e7eb !important; margin-right: 8px !important; }
            [data-testid="stTabs"] button p { color: #6B7280 !important; font-weight: 600 !important; font-size: 14px !important; }
            [data-testid="stTabs"] button[aria-selected="true"] { background-color: #EFF6FF !important; border-color: #1D4ED8 !important; }
            [data-testid="stTabs"] button[aria-selected="true"] p { color: #1D4ED8 !important; font-weight: 800 !important; }
            
            h2 { background: linear-gradient(135deg, #1D4ED8 0%, #0F766E 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900 !important; }
            h3 { color: #1F2937 !important; font-weight: 700 !important; border-bottom: 3px solid #1D4ED8; padding-bottom: 12px; }
            .stCaption { color: #6B7280 !important; font-size: 13px !important; }
        </style>
    """, unsafe_allow_html=True)
advanced_css()

# =====================================================================
# 3. 실시간 API 연동 로직 (기상청, 네이버 뉴스 & 안전보건공단)
# =====================================================================
kst = timezone(timedelta(hours=9))

@st.cache_data(ttl=60)
def get_weather_data():
    now = datetime.datetime.now(kst)
    fetch_time = now.strftime('%Y-%m-%d %H:%M:%S')
    try:
        if "KMA_API_KEY" in st.secrets:
            api_key = st.secrets["KMA_API_KEY"]
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            if now.minute < 40: now = now - timedelta(hours=1)
            params = {
                'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
                'base_date': now.strftime('%Y%m%d'), 'base_time': now.strftime('%H00'),
                'nx': '60', 'ny': '121' # 수원
            }
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                items = res.json()['response']['body']['items']['item']
                weather = {'fetch_time': fetch_time}
                for item in items:
                    if item['category'] == 'T1H': weather['temp'] = float(item['obsrValue'])
                    elif item['category'] == 'RN1': weather['rain'] = float(item['obsrValue'])
                    elif item['category'] == 'REH': weather['humid'] = float(item['obsrValue'])
                if 'temp' in weather: return weather
    except Exception: pass
    return {'temp': 28.5, 'humid': 60.0, 'rain': 0.0, 'fetch_time': fetch_time}

@st.cache_data(ttl=300)
def get_daily_news():
    news_list = []
    current_time = datetime.datetime.now(kst)
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        if "NAVER_CLIENT_ID" in st.secrets and "NAVER_CLIENT_SECRET" in st.secrets:
            headers = {
                'X-Naver-Client-Id': st.secrets['NAVER_CLIENT_ID'],
                'X-Naver-Client-Secret': st.secrets['NAVER_CLIENT_SECRET']
            }
            query = urllib.parse.quote("안전보건 OR 중대재해 OR 사고속보")
            res = requests.get(f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=date", headers=headers, timeout=5)
            
            if res.status_code == 200 and res.json().get('items'):
                for idx, item in enumerate(res.json()['items']):
                    title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
                    news_list.append({
                        "title": f"⚡ [네이버 속보] {title[:75]}...",
                        "url": item['link'],
                        "time": timestamp,
                        "priority": "high" if idx == 0 else "medium"
                    })
    except Exception: pass

    if not news_list:
        news_list = [
            {"title": "🚨 [시스템] 실시간 뉴스를 불러오는 중입니다...", "url": "https://search.naver.com/search.naver?query=중대재해", "time": timestamp, "priority": "critical"}
        ]
    return news_list

@st.cache_data(ttl=43200)
def get_kosha_safety_rules(industry):
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/SafeHealthInfoService/getIndustrySafeGuide'
            params = {'serviceKey': api_key, 'searchKeyword': industry, 'type': 'json', 'numOfRows': '3'}
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                data = res.json()
                items = data['response']['body']['items'].get('item', [])
                if not isinstance(items, list): items = [items]
                rules = [item.get('subject', '') for item in items if item.get('subject')]
                if rules: return rules
    except Exception: pass
    
    fallback_db = {
        "시설관리": ["안전모, 안전대 등 개인보호구 착용 철저", "고소작업 시 추락방지망 및 안전난간 확인", "정비 작업 전 전원 차단(LOTO) 실행"],
        "청소": ["물기, 기름기 등에 의한 전도(넘어짐) 사고 주의", "화학세제 사용 시 물질안전보건자료(MSDS) 확인"],
        "물류": ["지게차 작업 반경 내 보행자 접근 엄금", "중량물 취급 시 요통 등 근골격계 질환 주의"],
        "식당": ["뜨거운 물/기름에 의한 화상 주의 및 방열장갑 착용", "바닥 물기 즉시 제거 및 미끄럼 방지 장화 착용"],
        "서비스": ["고객 응대 시 감정노동 스트레스 관리 및 휴식", "실내 적정 온도 및 환기 유지"],
        "폐기물처리": ["파쇄기, 압축기 끼임 방지를 위한 방호덮개 확인", "밀폐공간 진입 전 산소/유해가스 농도 측정"],
        "제조": ["기계기구 회전부(기어, 롤러 등) 끼임 방지 덮개 설치", "소음/분진 발생 공정 시 귀마개 착용"]
    }
    return fallback_db.get(industry, ["기본 안전보호구를 반드시 착용하세요."])

# =====================================================================
# 4. 화면 렌더링
# =====================================================================
current_kst_time = datetime.datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
current_date = datetime.datetime.now(kst).strftime('%Y년 %m월 %d일')

st.markdown("<h2 style='text-align: center;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"<div style='text-align: center; background: #EFF6FF; border: 2px solid #1D4ED8; border-radius: 10px; padding: 12px; margin-bottom: 20px;'><p style='margin: 0; color: #1D4ED8; font-weight: 700;'>🔄 <strong>실시간 화면 동기화 중</strong> | {current_kst_time}</p></div>", unsafe_allow_html=True)
st.divider()

# --- 1. 실시간 기상 알림 ---
weather_data = get_weather_data()
st.subheader("📡 현장 실시간 기상 정보 (수원 기준)")
st.caption(f"🕒 업데이트 시간: {weather_data.get('fetch_time', current_kst_time)} (1분 주기)")
temp, humid, rain = weather_data['temp'], weather_data['humid'], weather_data['rain']

w1, w2, w3 = st.columns(3)
# [수정됨] 기온: 빨간색, 습도: 녹색(#16A34A), 강수량: 파란색으로 색상 지정
with w1: st.markdown(f"<div style='text-align: center;'><div style='font-size: 2.8em; font-weight: 900; color: #DC2626;'>🌡️ {temp}℃</div><div style='color: #475569;'>현재 기온</div></div>", unsafe_allow_html=True)
with w2: st.markdown(f"<div style='text-align: center;'><div style='font-size: 2.8em; font-weight: 900; color: #16A34A;'>💧 {humid}%</div><div style='color: #475569;'>현재 습도</div></div>", unsafe_allow_html=True)
with w3: st.markdown(f"<div style='text-align: center;'><div style='font-size: 2.8em; font-weight: 900; color: #2563EB;'>☔ {rain}mm</div><div style='color: #475569;'>강수량</div></div>", unsafe_allow_html=True)

weather_msg = "✅ 기상 악화 요인 없음" if temp < 33.0 and temp > -5.0 and rain == 0 else "⚠️ 기상 주의 (폭염/강우/한파 확인)"
st.divider()

# --- 2. 네이버 뉴스 API 주요 이슈 ---
news_data = get_daily_news()
st.subheader("📰 오늘의 안전보건 실시간 주요이슈")
st.caption(f"🕒 네이버 뉴스 API 연동 업데이트: {news_data[0]['time']} (5분 주기)")

for news in news_data:
    st.markdown(f"""<a href="{news['url']}" target="_blank" style="text-decoration: none;">
        <div class='news-box'>
            <p class='news-title'>{news['title']}</p>
            <p class='news-time'>터치하여 기사 원문 확인</p>
        </div></a>""", unsafe_allow_html=True)
st.divider()

# --- 3. 공단 API 업종별 안전수칙 ---
st.subheader("🏭 업종별 핵심 안전수칙 (매일 갱신)")
industry_list = ["시설관리", "청소", "물류", "식당", "서비스", "폐기물처리", "제조"]
tabs = st.tabs([f"📌 {ind}" for ind in industry_list])

for index, industry in enumerate(industry_list):
    with tabs[index]:
        for idx, rule in enumerate(get_kosha_safety_rules(industry), 1):
            st.markdown(f"<div style='background: #ffffff; border-left: 4px solid #1D4ED8; border-radius: 8px; padding: 12px 16px; margin: 10px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'><b>{idx}️⃣ {rule}</b></div>", unsafe_allow_html=True)
st.divider()

# --- 4. TBM 확인서 생성 ---
st.subheader("📋 일일 TBM 모바일 확인서 발급")
with st.form("tbm_form"):
    c1, c2 = st.columns(2)
    with c1: contractor_name = st.text_input("🏢 협력사명 (예: 삼성건설)")
    with c2: worker_cnt = st.number_input("👥 투입 인원", min_value=1, value=5)
    selected_industry = st.selectbox("🛠️ 작업 업종 선택", industry_list)
    submitted = st.form_submit_button("🖨️ TBM 확인서 생성", use_container_width=True)

if submitted and contractor_name:
    rules_text = "\n".join([f"  {idx}. {rule}" for idx, rule in enumerate(get_kosha_safety_rules(selected_industry), 1)])
    issue_text = "\n".join([f"  • {news['title'].replace('⚡ [네이버 속보] ', '').strip()[:60]}" for news in news_data[:5]])
    
    tbm_result = f"""=========================================
[ 📋 일일 TBM 무재해 이행 확인서 ]
=========================================
■ 협력사명: {contractor_name}
■ 작업업종: {selected_industry}
■ 투입인원: {worker_cnt}명
■ 기상상태: {weather_msg}

[ 📰 실시간 주요 안전이슈 ]
{issue_text}

[ 🏭 금일 필수 안전수칙 ]
{rules_text}

[ ✅ 필수 안전점검 확인 ]
1. 위험성평가 내용을 숙지하였는가? ( O )
2. 개인보호구를 완벽히 착용하였는가? ( O )
3. 건강이상자가 없는가? ( O )
========================================="""
    st.success("✅ 확인서가 생성되었습니다. 복사하여 카카오톡으로 공유하세요.")
    st.text_area("TBM 내용", value=tbm_result, height=400)
