import streamlit as st
import requests
import datetime
import urllib.parse
import time
import json
from streamlit_autorefresh import st_autorefresh
from datetime import timezone, timedelta

# =====================================================================
# 1. 페이지 기본 설정 및 1분 단위 백그라운드 갱신
# =====================================================================
st.set_page_config(
    page_title="협력사 일일 안전 포털",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 전체 페이지는 1분(60초)마다 자동 새로고침 됨
st_autorefresh(interval=60000, key="ehs_dashboard_refresh")

# =====================================================================
# 2. 고급 CSS 스타일링 (그래픽 가독성 강화)
# =====================================================================
def advanced_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            
            * { font-family: 'Noto Sans KR', sans-serif; }
            html, body, .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); }
            
            /* 헤더 스타일 */
            header { visibility: hidden; }
            .main .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 2.5rem; padding-right: 2.5rem; }
            
            /* 카드 스타일 (메인 요소) */
            .metric-card {
                background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
                border-radius: 12px;
                padding: 20px;
                margin: 8px 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                border-left: 5px solid #1D4ED8;
                transition: all 0.3s ease-in-out;
                backdrop-filter: blur(10px);
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(29, 78, 216, 0.15);
            }
            
            /* 위험도별 카드 색상 */
            .card-safe { border-left-color: #10B981; background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%); }
            .card-warning { border-left-color: #F59E0B; background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); }
            .card-danger { border-left-color: #EF4444; background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); }
            .card-critical { border-left-color: #DC2626; background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%); color: white; }
            
            /* 날씨 정보 박스 */
            .weather-box {
                background: linear-gradient(135deg, #ECF0FF 0%, #F0F9FF 100%);
                border: 2px solid #1D4ED8;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(29, 78, 216, 0.15);
            }
            .weather-value {
                font-size: 2.5em;
                font-weight: 900;
                color: #1D4ED8;
                line-height: 1;
            }
            .weather-label {
                font-size: 0.9em;
                color: #475569;
                margin-top: 8px;
                font-weight: 600;
            }
            
            /* 뉴스/이슈 박스 */
            .news-box {
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border-left: 5px solid #EAB308;
                border-radius: 10px;
                padding: 16px 20px;
                margin: 12px 0;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
                transition: all 0.3s ease;
                border-top: 1px solid rgba(234, 179, 8, 0.3);
            }
            .news-box:hover {
                transform: translateX(8px);
                box-shadow: 0 6px 20px rgba(234, 179, 8, 0.2);
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            }
            .news-title {
                font-size: 15px;
                font-weight: 600;
                color: #1F2937;
                line-height: 1.6;
                margin: 0;
            }
            .news-time {
                font-size: 12px;
                color: #9CA3AF;
                margin-top: 8px;
            }
            
            /* 탭 스타일 */
            div[data-baseweb="tab-highlight"] { display: none; }
            [data-testid="stTabs"] button {
                background-color: #f3f4f6 !important;
                border-radius: 10px !important;
                padding: 12px 18px !important;
                border: 2px solid #e5e7eb !important;
                margin-right: 8px !important;
                transition: all 0.3s ease-in-out !important;
                font-weight: 500 !important;
            }
            [data-testid="stTabs"] button p {
                color: #6B7280 !important;
                font-weight: 600 !important;
                font-size: 14px !important;
            }
            
            /* 탭 활성화 상태 - 색상 테마별 */
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] {
                background-color: #EFF6FF !important;
                border-color: #1D4ED8 !important;
                box-shadow: 0 4px 12px rgba(29, 78, 216, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] p {
                color: #1D4ED8 !important;
                font-weight: 800 !important;
            }
            
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] {
                background-color: #F0FDFA !important;
                border-color: #0F766E !important;
                box-shadow: 0 4px 12px rgba(15, 118, 110, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] p {
                color: #0F766E !important;
                font-weight: 800 !important;
            }
            
            [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] {
                background-color: #FFF7ED !important;
                border-color: #C2410C !important;
                box-shadow: 0 4px 12px rgba(194, 65, 12, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] p {
                color: #C2410C !important;
                font-weight: 800 !important;
            }
            
            [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] {
                background-color: #FEF2F2 !important;
                border-color: #B91C1C !important;
                box-shadow: 0 4px 12px rgba(185, 28, 28, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] p {
                color: #B91C1C !important;
                font-weight: 800 !important;
            }
            
            [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] {
                background-color: #FAF5FF !important;
                border-color: #6D28D9 !important;
                box-shadow: 0 4px 12px rgba(109, 40, 217, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] p {
                color: #6D28D9 !important;
                font-weight: 800 !important;
            }
            
            [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] {
                background-color: #FEF3C7 !important;
                border-color: #B45309 !important;
                box-shadow: 0 4px 12px rgba(180, 83, 9, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] p {
                color: #B45309 !important;
                font-weight: 800 !important;
            }
            
            [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] {
                background-color: #F8FAFC !important;
                border-color: #334155 !important;
                box-shadow: 0 4px 12px rgba(51, 65, 85, 0.15) !important;
            }
            [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] p {
                color: #334155 !important;
                font-weight: 800 !important;
            }
            
            /* 입력 필드 스타일 */
            div[data-baseweb="input"], div[data-baseweb="select"] > div {
                background-color: #f9fafb !important;
                border: 2px solid #e5e7eb !important;
                border-radius: 10px !important;
                color: #1F2937 !important;
                font-weight: 500 !important;
                padding: 10px 14px !important;
            }
            div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
                border-color: #1D4ED8 !important;
                box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.1) !important;
            }
            
            /* 제목 스타일 */
            h2 {
                background: linear-gradient(135deg, #1D4ED8 0%, #0F766E 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 900 !important;
                letter-spacing: -0.5px;
            }
            
            h3 {
                color: #1F2937 !important;
                font-weight: 700 !important;
                border-bottom: 3px solid #1D4ED8;
                padding-bottom: 12px;
            }
            
            /* 진행률 바 */
            .progress-bar {
                background: linear-gradient(90deg, #1D4ED8 0%, #0F766E 100%);
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
            }
            
            /* 버튼 스타일 */
            button {
                border-radius: 10px !important;
                font-weight: 600 !important;
                padding: 12px 24px !important;
                transition: all 0.3s ease !important;
                border: none !important;
            }
            
            /* divider 스타일 */
            hr { border-color: #e5e7eb !important; }
            
            /* 캡션 스타일 */
            .stCaption {
                color: #6B7280 !important;
                font-size: 13px !important;
            }
            
            /* 반응형 레이아웃 */
            @media (max-width: 768px) {
                .main .block-container { padding-left: 1rem; padding-right: 1rem; }
                .weather-value { font-size: 2em; }
                .news-title { font-size: 14px; }
            }
        </style>
    """, unsafe_allow_html=True)

advanced_css()

# =====================================================================
# 3. 개선된 API 데이터 호출 전략
# =====================================================================

# [개선안 1] 기상 정보: 1분 캐시 (실시간성 유지)
@st.cache_data(ttl=60)
def get_weather_data():
    try:
        if "KMA_API_KEY" in st.secrets:
            api_key = st.secrets["KMA_API_KEY"]
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            kst = timezone(timedelta(hours=9))
            now = datetime.datetime.now(kst)
            
            # 기상청 API는 40분 이전 데이터만 제공
            if now.minute < 40:
                now = now - timedelta(hours=1)
            
            params = {
                'serviceKey': api_key,
                'pageNo': '1',
                'numOfRows': '10',
                'dataType': 'JSON',
                'base_date': now.strftime('%Y%m%d'),
                'base_time': now.strftime('%H00'),
                'nx': '60',  # 수원
                'ny': '121'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                items = response.json()['response']['body']['items']['item']
                weather = {}
                for item in items:
                    cat = item['category']
                    if cat == 'T1H':
                        weather['temp'] = float(item['obsrValue'])
                    elif cat == 'RN1':
                        weather['rain'] = float(item['obsrValue'])
                    elif cat == 'REH':
                        weather['humid'] = float(item['obsrValue'])
                
                if weather:
                    return weather
    except Exception as e:
        st.error(f"기상 데이터 로드 실패: {str(e)}")
    
    return {'temp': 28.5, 'humid': 60.0, 'rain': 0.0}

# [개선안 2] 뉴스/이슈: 5분 캐시 (기존 1시간 → 5분으로 단축)
# → 실제로는 1분마다 화면 새로고침되고, 5분마다 API 호출 (중간의 4번은 캐시 사용)
@st.cache_data(ttl=300)  # 변경: 3600 → 300초 (1시간 → 5분)
def get_daily_news():
    news_list = []
    kst = timezone(timedelta(hours=9))
    current_time = datetime.datetime.now(kst)
    timestamp = current_time.strftime('%Y-%m-%d %H:%M')
    
    # 네이버 뉴스 API 처리
    try:
        if "NAVER_CLIENT_ID" in st.secrets and "NAVER_CLIENT_SECRET" in st.secrets:
            headers = {
                'X-Naver-Client-Id': st.secrets['NAVER_CLIENT_ID'],
                'X-Naver-Client-Secret': st.secrets['NAVER_CLIENT_SECRET']
            }
            query = urllib.parse.quote("중대재해 OR 사고속보 OR 산업재해")
            response = requests.get(
                f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=date",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200 and response.json().get('items'):
                for idx, news_item in enumerate(response.json()['items'][:3]):
                    title = news_item['title'].replace('<b>', '').replace('</b>', '')
                    clean_title = title[:80] + "..." if len(title) > 80 else title
                    
                    news_list.append({
                        "title": f"⚡ **[네이버 뉴스]** {clean_title}",
                        "url": news_item['link'],
                        "source": "naver",
                        "time": timestamp,
                        "priority": "high" if idx == 0 else "medium"
                    })
    except Exception as e:
        st.warning(f"네이버 뉴스 로드 실패")

    # [개선안 3] 안전보건공단 API 개선된 파싱 로직
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/BoardService/getBoardList'
            
            # 캐시 무력화를 위한 타임스탐프
            current_timestamp = int(time.time())
            
            params = {
                'serviceKey': api_key,
                'boardId': 'news',
                'numOfRows': '5',
                'type': 'json',
                '_t': current_timestamp
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            # JSON 파싱 개선
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # API 응답 구조 확인
                    if 'response' in data and data['response'].get('body'):
                        body = data['response']['body']
                        
                        # items가 리스트인지 확인
                        if 'items' in body:
                            items = body['items'].get('item', [])
                            if not isinstance(items, list):
                                items = [items]
                            
                            for item in items[:4]:  # 최대 4개까지만
                                title = item.get('title', '').strip()
                                if title and len(title) > 5:
                                    safe_link = f"https://kosha.or.kr"  # 공단 메인 링크
                                    news_list.append({
                                        "title": f"🚨 **[공단 공지]** {title[:75]}...",
                                        "url": safe_link,
                                        "source": "kosha",
                                        "time": timestamp,
                                        "priority": "critical"
                                    })
                except json.JSONDecodeError:
                    st.warning("공단 API 응답 파싱 실패")
                    
    except requests.exceptions.Timeout:
        st.warning("공단 API 응답 시간 초과")
    except Exception as e:
        st.warning(f"공단 API 로드 실패")

    # 폴백 데이터 (API 실패 시)
    if len(news_list) == 0:
        fallback_data = [
            ("⚡ **[긴급]** 타 현장 지붕 보수공사 중 채광창 파손 추락사고 발생", "critical"),
            ("🚨 **[공단 공지]** 혹서기 근로자 휴게시설 설치 기준 및 에어컨 가동 집중 점검 기간", "high"),
            ("📢 **[공단 공지]** 2024년 상반기 중대재해 분석 현황 발표", "medium"),
        ]
        for idx, (title, priority) in enumerate(fallback_data):
            news_list.append({
                "title": title,
                "url": "https://kosha.or.kr",
                "source": "fallback",
                "time": timestamp,
                "priority": priority
            })

    return news_list

# 업종별 안전수칙: 12시간 캐시 (변경 없음)
@st.cache_data(ttl=43200)
def get_kosha_safety_rules(industry):
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/SafeHealthInfoService/getIndustrySafeGuide'
            params = {
                'serviceKey': api_key,
                'searchKeyword': industry,
                'type': 'json',
                'numOfRows': '3'
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and data['response'].get('body'):
                    items = data['response']['body']['items'].get('item', [])
                    if not isinstance(items, list):
                        items = [items]
                    rules = [item.get('subject', '') for item in items if item.get('subject')]
                    if rules:
                        return rules
    except Exception:
        pass
    
    # 폴백 데이터베이스 (변경 없음)
    fallback_db = {
        "시설관리": [
            "안전모, 안전대 등 개인보호구 착용 철저",
            "고소작업 시 추락방지망 및 안전난간 확인",
            "정비 작업 전 전원 차단(LOTO) 실행"
        ],
        "청소": [
            "물기, 기름기 등에 의한 전도(넘어짐) 사고 주의",
            "화학세제 사용 시 물질안전보건자료(MSDS) 확인",
            "작업구간 미끄럼 주의 표지판 설치"
        ],
        "물류": [
            "지게차 작업 반경 내 보행자 접근 엄금",
            "중량물 취급 시 요통 등 근골격계 질환 주의",
            "적재물 낙하 방지 조치 및 하역 작업 지휘자 배치"
        ],
        "식당": [
            "뜨거운 물/기름에 의한 화상 주의 및 방열장갑 착용",
            "바닥 물기 즉시 제거 및 미끄럼 방지 장화 착용",
            "식자재 운반 시 베임/찔림 주의"
        ],
        "서비스": [
            "고객 응대 시 감정노동 스트레스 관리 및 휴식",
            "오랜 서서/앉아 일하는 작업 시 스트레칭 실시",
            "실내 적정 온도 및 환기 유지"
        ],
        "폐기물처리": [
            "파쇄기, 압축기 끼임 방지를 위한 방호덮개 확인",
            "날카로운 물체 취급 시 베임 방지 장갑 착용",
            "밀폐공간 진입 전 산소/유해가스 농도 측정"
        ],
        "제조": [
            "기계기구 회전부(기어, 롤러 등) 끼임 방지 덮개 설치",
            "소음/분진 발생 공정 시 귀마개 및 방진마스크 착용",
            "지게차, 크레인 등 운반기계 안전수칙 준수"
        ]
    }
    return fallback_db.get(industry, ["기본 안전보호구를 반드시 착용하세요."])

# =====================================================================
# 4. 대시보드 화면 렌더링 (그래픽 업그레이드)
# =====================================================================

kst = timezone(timedelta(hours=9))
current_kst_time = datetime.datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
current_date = datetime.datetime.now(kst).strftime('%Y년 %m월 %d일')

# 헤더
st.markdown(
    f"<h2 style='text-align: center;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>",
    unsafe_allow_html=True
)

# 실시간 동기화 상태 표시
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        f"""
        <div style='text-align: center; background: linear-gradient(135deg, #EFF6FF 0%, #F0FDFA 100%); 
                    border: 2px solid #1D4ED8; border-radius: 10px; padding: 12px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #1D4ED8; font-weight: 700;'>
                🔄 <strong>실시간 동기화</strong> | {current_kst_time} (KST)
            </p>
            <p style='margin: 4px 0 0 0; color: #0F766E; font-size: 13px; font-weight: 500;'>
                ✅ 기상: 1분 갱신 | 📰 이슈: 5분 갱신 | 📋 수칙: 12시간 갱신
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# =====================================================================
# 5. 기상 정보 섹션 (그래픽 강화)
# =====================================================================
st.subheader("📡 현장 실시간 기상 정보 (수원 기준)")

weather_data = get_weather_data()
temp = weather_data['temp']
humid = weather_data['humid']
rain = weather_data['rain']

# 날씨 상태 판단
if temp >= 33.0:
    weather_status = "🔴 폭염 경보"
    weather_level = "critical"
    weather_message = "온열질환 발생 위험! 옥외작업 최소화 및 휴식을 보장하세요."
    status_color = "#DC2626"
elif temp <= -5.0:
    weather_status = "🔵 한파 주의"
    weather_level = "danger"
    weather_message = "동절기 한랭질환 및 빙판길 미끄러짐에 주의하세요."
    status_color = "#2563EB"
elif rain > 0.0:
    weather_status = "🟡 강우 주의"
    weather_level = "warning"
    weather_message = "감전 및 미끄러짐 재해 위험이 높습니다."
    status_color = "#F59E0B"
else:
    weather_status = "✅ 정상"
    weather_level = "safe"
    weather_message = "현재 특별한 기상 악화 위험은 없습니다."
    status_color = "#10B981"

# 날씨 카드
weather_col1, weather_col2, weather_col3 = st.columns(3)

with weather_col1:
    st.markdown(
        f"""
        <div class='weather-box'>
            <div class='weather-value'>🌡️ {temp}℃</div>
            <div class='weather-label'>현재 기온</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with weather_col2:
    st.markdown(
        f"""
        <div class='weather-box'>
            <div class='weather-value'>💧 {humid}%</div>
            <div class='weather-label'>현재 습도</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with weather_col3:
    st.markdown(
        f"""
        <div class='weather-box'>
            <div class='weather-value'>☔ {rain}mm</div>
            <div class='weather-label'>강수량</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# 경고 메시지
alert_class = f"card-{weather_level}"
st.markdown(
    f"""
    <div class='metric-card {alert_class}'>
        <p style='font-size: 16px; font-weight: 700; margin: 0 0 8px 0; color: {status_color};'>
            {weather_status}
        </p>
        <p style='font-size: 14px; font-weight: 500; margin: 0; color: #475569;'>
            {weather_message}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(f"📊 업데이트: {current_kst_time} | 데이터 출처: 기상청(KMA)")
st.divider()

# =====================================================================
# 6. 안전보건 주요 이슈 섹션 (개선된 뉴스 디스플레이)
# =====================================================================
st.subheader("📰 오늘의 안전보건 주요 이슈 (5분 단위 갱신)")

news_data = get_daily_news()

if news_data:
    for idx, news in enumerate(news_data):
        priority = news.get('priority', 'medium')
        if priority == 'critical':
            priority_indicator = "🚨"
            border_color = "#DC2626"
        elif priority == 'high':
            priority_indicator = "⚠️"
            border_color = "#F59E0B"
        else:
            priority_indicator = "📌"
            border_color = "#0F766E"
        
        st.markdown(
            f"""
            <a href="{news['url']}" target="_blank" style="text-decoration: none;">
                <div class='news-box' style='border-left-color: {border_color}; padding: 18px 20px;'>
                    <p class='news-title'>{priority_indicator} {news['title']}</p>
                    <p class='news-time'>📅 {news['time']} | 📍 {news['source'].upper()}</p>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("현재 불러올 이슈가 없습니다.")

st.caption(f"🔄 마지막 업데이트: {current_kst_time} | ⏱️ 5분마다 자동 갱신")
st.divider()

# =====================================================================
# 7. 업종별 안전수칙 탭 (개선됨)
# =====================================================================
st.subheader("🏭 업종별 핵심 안전수칙")

industry_list = ["시설관리", "청소", "물류", "식당", "서비스", "폐기물처리", "제조"]
industry_emoji = {
    "시설관리": "🔧",
    "청소": "🧹",
    "물류": "📦",
    "식당": "🍽️",
    "서비스": "👔",
    "폐기물처리": "♻️",
    "제조": "⚙️"
}

tabs = st.tabs([f"{industry_emoji.get(ind, '•')} {ind}" for ind in industry_list])

for index, industry in enumerate(industry_list):
    with tabs[index]:
        st.markdown(f"#### 💡 {industry} 현장 필수 안전 가이드")
        kosha_rules = get_kosha_safety_rules(industry)
        
        for idx, rule in enumerate(kosha_rules, 1):
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
                            border-left: 4px solid #1D4ED8; border-radius: 8px;
                            padding: 12px 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'>
                    <p style='margin: 0; color: #1F2937; font-weight: 600; font-size: 15px;'>
                        {idx}️⃣ {rule}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

st.divider()

# =====================================================================
# 8. TBM 확인서 섹션 (개선됨)
# =====================================================================
st.subheader("📋 일일 TBM(Tool Box Meeting) 모바일 확인서 생성")

with st.form("tbm_form"):
    st.markdown("### 📝 작업 정보 입력")
    
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        contractor_name = st.text_input(
            "🏢 협력사명",
            placeholder="예) 삼성건설, ABC안전관리",
            max_chars=30
        )
    
    with form_col2:
        worker_cnt = st.number_input(
            "👥 투입 인원",
            min_value=1,
            value=5,
            step=1
        )
    
    selected_industry = st.selectbox(
        "🛠️ 작업 업종 선택",
        industry_list,
        index=0
    )
    
    submitted = st.form_submit_button(
        "🖨️ TBM 확인서 생성 및 복사",
        use_container_width=True
    )

if submitted and contractor_name:
    # 기상 상황 판단
    if temp >= 33.0:
        weather_alert = "🚨 폭염 경보 (물/그늘/휴식 필수)"
    elif temp <= -5.0:
        weather_alert = "🚨 한파 주의 (동상/저체온증 주의)"
    elif rain > 0:
        weather_alert = "⚠️ 강우 주의 (옥외 전기작업 금지)"
    else:
        weather_alert = "✅ 기상 악화 사항 없음"
    
    # 안전수칙 정리
    rules_data = get_kosha_safety_rules(selected_industry)
    rules_text = "\n".join([f"  {idx}. {rule}" for idx, rule in enumerate(rules_data, 1)])
    
    # 주요 이슈 정리
    issue_text = "\n".join([f"  • {news['title'].replace('**', '').replace('⚡', '').replace('🚨', '').strip()[:70]}" 
                           for news in news_data[:3]])
    
    # TBM 텍스트 조립
    header_text = f"""
=========================================
[ 📋 일일 TBM 무재해 이행 확인서 ]
=========================================
■ 협력사명: {contractor_name}
■ 투입인원: {worker_cnt}명
■ 작업 업종: {selected_industry}
■ 작업 일자: {current_date}
■ 기상특보: {weather_alert}
"""

    news_section = f"""
[ 📰 본일 주요 안전보건 이슈 ]
{issue_text}
"""

    middle_text = f"""
[ 🏭 금일 {selected_industry} 핵심 안전수칙 ]
{rules_text}
"""

    check_section = """
[ ✅ 필수 안전점검 확인 ]
1. 작업 전 위험성평가 내용을 전원 숙지했는가?
   □ 확인 완료 (서명: ___________________)

2. 안전모, 안전화 등 개인보호구를 완벽히 착용했는가?
   □ 확인 완료 (서명: ___________________)

3. 음주자, 질병자 등 건강이상자가 없는가?
   □ 확인 완료 (서명: ___________________)

4. 기계·장비 안전검사 및 정점검을 실시했는가?
   □ 확인 완료 (서명: ___________________)

5. 상기 모든 사항을 숙지하고 안전하게 작업함을 서약합니다.

=========================================
   작성일: {current_date}
   협력사 담당자: ______________ (인)
   발주처 감독자: ______________ (인)
=========================================
"""

    final_tbm_result = header_text + news_section + middle_text + check_section
    
    # 결과 표시
    st.success("✅ TBM 확인서가 생성되었습니다!")
    st.markdown("### 📌 아래 텍스트를 복사하여 카카오톡/메신저/이메일로 공유하세요.")
    
    st.text_area(
        "TBM 확인서 텍스트",
        value=final_tbm_result,
        height=500,
        disabled=False
    )
    
    st.markdown("---")
    st.markdown("#### 💡 활용팁")
    col_tip1, col_tip2, col_tip3 = st.columns(3)
    with col_tip1:
        st.markdown("📱 **모바일 공유**\n카카오톡 또는 메신저로 전달")
    with col_tip2:
        st.markdown("📧 **이메일 전송**\n협력사 근로자에게 이메일 발송")
    with col_tip3:
        st.markdown("🖨️ **인쇄**\n현장 게시판에 출력 게시")

elif submitted:
    st.error("⚠️ 협력사명을 반드시 입력해 주세요.")

st.divider()

# 푸터
st.markdown(
    """
    <div style='text-align: center; color: #9CA3AF; font-size: 12px; margin-top: 30px;'>
        <p>🛡️ 협력사 안전보건 관리 시스템 | 기상청(KMA) + 안전보건공단(KOSHA) 실시간 연계</p>
        <p>⚠️ 본 정보는 참고용이며, 업체별 특성에 맞게 조정하여 사용하시기 바랍니다.</p>
    </div>
    """,
    unsafe_allow_html=True
)
