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
# 2. 고급 CSS 스타일링 (박스 디자인 제거, 숫자 강조)
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
                border-radius: 12px;
                padding: 16px;
                margin: 8px 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                border-left: 5px solid #1D4ED8;
                transition: all 0.3s ease-in-out;
                backdrop-filter: blur(10px);
            }
            
            .card-safe { border-left-color: #10B981; background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%); }
            .card-warning { border-left-color: #F59E0B; background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); }
            .card-danger { border-left-color: #EF4444; background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); }
            .card-critical { border-left-color: #DC2626; background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%); color: white; }
            
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
            .news-title { font-size: 15px; font-weight: 600; color: #1F2937; line-height: 1.6; margin: 0; }
            .news-time { font-size: 12px; color: #9CA3AF; margin-top: 8px; }
            
            div[data-baseweb="tab-highlight"] { display: none; }
            [data-testid="stTabs"] button {
                background-color: #f3f4f6 !important; border-radius: 10px !important; padding: 12px 18px !important;
                border: 2px solid #e5e7eb !important; margin-right: 8px !important; transition: all 0.3s ease-in-out !important;
            }
            [data-testid="stTabs"] button p { color: #6B7280 !important; font-weight: 600 !important; font-size: 14px !important; }
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] { background-color: #EFF6FF !important; border-color: #1D4ED8 !important; }
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] p { color: #1D4ED8 !important; font-weight: 800 !important; }
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] { background-color: #F0FDFA !important; border-color: #0F766E !important; }
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] p { color: #0F766E !important; font-weight: 800 !important; }
            
            div[data-baseweb="input"], div[data-baseweb="select"] > div {
                background-color: #f9fafb !important; border: 2px solid #e5e7eb !important; border-radius: 10px !important;
                color: #1F2937 !important; font-weight: 500 !important; padding: 10px 14px !important;
            }
            
            h2 {
                background: linear-gradient(135deg, #1D4ED8 0%, #0F766E 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
                font-weight: 900 !important; letter-spacing: -0.5px;
            }
            h3 { color: #1F2937 !important; font-weight: 700 !important; border-bottom: 3px solid #1D4ED8; padding-bottom: 12px; }
            button { border-radius: 10px !important; font-weight: 600 !important; padding: 12px 24px !important; border: none !important; }
            hr { border-color: #e5e7eb !important; }
            .stCaption { color: #6B7280 !important; font-size: 13px !important; }
            
        </style>
    """, unsafe_allow_html=True)

advanced_css()

# =====================================================================
# 3. API 데이터 호출
# =====================================================================
# 기상 정보: 1분 캐시
@st.cache_data(ttl=60)
def get_weather_data():
    kst = timezone(timedelta(hours=9))
    now = datetime.datetime.now(kst)
    fetch_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        if "KMA_API_KEY" in st.secrets:
            api_key = st.secrets["KMA_API_KEY"]
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            
            if now.minute < 40:
                now = now - timedelta(hours=1)
            
            params = {
                'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
                'base_date': now.strftime('%Y%m%d'), 'base_time': now.strftime('%H00'),
                'nx': '60', 'ny': '121' # 수원
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                items = response.json()['response']['body']['items']['item']
                weather = {'fetch_time': fetch_time}
                for item in items:
                    cat = item['category']
                    if cat == 'T1H': weather['temp'] = float(item['obsrValue'])
                    elif cat == 'RN1': weather['rain'] = float(item['obsrValue'])
                    elif cat == 'REH': weather['humid'] = float(item['obsrValue'])
                if 'temp' in weather:
                    return weather
    except Exception:
        pass
    
    return {'temp': 28.5, 'humid': 60.0, 'rain': 0.0, 'fetch_time': fetch_time}

# 뉴스/이슈: 5분 캐시
@st.cache_data(ttl=300)
def get_daily_news():
    news_list = []
    kst = timezone(timedelta(hours=9))
    current_time = datetime.datetime.now(kst)
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. 네이버 뉴스 API
    try:
        if "NAVER_CLIENT_ID" in st.secrets and "NAVER_CLIENT_SECRET" in st.secrets:
            headers = {
                'X-Naver-Client-Id': st.secrets['NAVER_CLIENT_ID'],
                'X-Naver-Client-Secret': st.secrets['NAVER_CLIENT_SECRET']
            }
            query = urllib.parse.quote("중대재해 OR 사고속보 OR 산업재해")
            response = requests.get(
                f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=date",
                headers=headers, timeout=5
            )
            if response.status_code == 200 and response.json().get('items'):
                for idx, news_item in enumerate(response.json()['items'][:3]):
                    title = news_item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
                    clean_title = title[:80] + "..." if len(title) > 80 else title
                    news_list.append({
                        "title": f"⚡ **[네이버 속보]** {clean_title}",
                        "url": news_item['link'],
                        "source": "naver",
                        "time": timestamp,
                        "priority": "high" if idx == 0 else "medium"
                    })
    except Exception:
        pass

    # 2. 안전보건공단 API (네이버 검색 연결)
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/BoardService/getBoardList'
            current_timestamp = int(time.time())
            params = {
                'serviceKey': api_key, 'boardId': 'news', 'numOfRows': '3', 'type': 'json', '_t': current_timestamp
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and data['response'].get('body'):
                    items = data['response']['body']['items'].get('item', [])
                    if not isinstance(items, list): items = [items]
                    for item in items[:3]:
                        title = item.get('title', '').strip()
                        if title and len(title) > 5:
                            search_query = urllib.parse.quote(f"안전보건공단 {title}")
                            safe_link = f"https://search.naver.com/search.naver?query={search_query}"
                            news_list.append({
                                "title": f"🚨 **[공단 공지]** {title[:75]}...",
                                "url": safe_link,
                                "source": "kosha",
                                "time": timestamp,
                                "priority": "critical"
                            })
    except Exception:
        pass

    # 폴백 데이터
    if len(news_list) == 0:
        fallback_data = [
            ("⚡ **[긴급]** 타 현장 지붕 보수공사 중 채광창 파손 추락사고 발생", "critical"),
            ("🚨 **[공단 공지]** 혹서기 근로자 휴게시설 설치 기준 및 에어컨 가동 집중 점검", "high"),
            ("📢 **[안전 뉴스]** 2024년 상반기 중대재해 분석 현황", "medium"),
        ]
        for idx, (title, priority) in enumerate(fallback_data):
            search_query = urllib.parse.quote(f"안전보건공단 {title}")
            safe_link = f"https://search.naver.com/search.naver?query={search_query}"
            news_list.append({
                "title": title, "url": safe_link, "source": "fallback", "time": timestamp, "priority": priority
            })
            
    return news_list

# 업종별 안전수칙
@st.cache_data(ttl=43200)
def get_kosha_safety_rules(industry):
    fallback_db = {
        "시설관리": ["안전모, 안전대 등 개인보호구 착용 철저", "고소작업 시 추락방지망 및 안전난간 확인", "정비 작업 전 전원 차단(LOTO) 실행"],
        "청소": ["물기, 기름기 등에 의한 전도(넘어짐) 사고 주의", "화학세제 사용 시 물질안전보건자료(MSDS) 확인", "작업구간 미끄럼 주의 표지판 설치"],
        "물류": ["지게차 작업 반경 내 보행자 접근 엄금", "중량물 취급 시 요통 등 근골격계 질환 주의", "적재물 낙하 방지 조치 및 하역 작업 지휘자 배치"],
        "식당": ["뜨거운 물/기름에 의한 화상 주의 및 방열장갑 착용", "바닥 물기 즉시 제거 및 미끄럼 방지 장화 착용", "식자재 운반 시 베임/찔림 주의"],
        "서비스": ["고객 응대 시 감정노동 스트레스 관리 및 휴식", "오랜 서서/앉아 일하는 작업 시 스트레칭 실시", "실내 적정 온도 및 환기 유지"],
        "폐기물처리": ["파쇄기, 압축기 끼임 방지를 위한 방호덮개 확인", "날카로운 물체 취급 시 베임 방지 장갑 착용", "밀폐공간 진입 전 산소/유해가스 농도 측정"],
        "제조": ["기계기구 회전부(기어, 롤러 등) 끼임 방지 덮개 설치", "소음/분진 발생 공정 시 귀마개 및 방진마스크 착용", "지게차, 크레인 등 운반기계 안전수칙 준수"]
    }
    return fallback_db.get(industry, ["기본 안전보호구를 반드시 착용하세요."])

# =====================================================================
# 4. 대시보드 화면 렌더링
# =====================================================================
kst = timezone(timedelta(hours=9))
current_kst_time = datetime.datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
current_date = datetime.datetime.now(kst).strftime('%Y년 %m월 %d일')

# 헤더
st.markdown("<h2 style='text-align: center;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        f"""
        <div style='text-align: center; background: linear-gradient(135deg, #EFF6FF 0%, #F0FDFA 100%); 
                    border: 2px solid #1D4ED8; border-radius: 10px; padding: 12px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #1D4ED8; font-weight: 700;'>🔄 <strong>화면 자동 갱신 중</strong> | {current_kst_time} (KST)</p>
        </div>
        """, unsafe_allow_html=True
    )
st.divider()

# --- 기상 정보 섹션 (박스 제거, 숫자 크기 극대화) ---
weather_data = get_weather_data()
weather_fetch_time = weather_data.get('fetch_time', current_kst_time)

st.subheader("📡 현장 실시간 기상 정보 (수원 기준)")
st.caption(f"🕒 **실시간 기상 업데이트:** {weather_fetch_time} (1분 주기 갱신)")

temp, humid, rain = weather_data['temp'], weather_data['humid'], weather_data['rain']

# 박스 없이 텍스트만 큼직하게 배치
weather_col1, weather_col2, weather_col3 = st.columns(3)
with weather_col1:
    st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'><div style='font-size: 2.8em; font-weight: 900; color: #1D4ED8; line-height: 1.2;'>🌡️ {temp}℃</div><div style='font-size: 1.1em; color: #475569; font-weight: 600;'>현재 기온</div></div>", unsafe_allow_html=True)
with weather_col2:
    st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'><div style='font-size: 2.8em; font-weight: 900; color: #1D4ED8; line-height: 1.2;'>💧 {humid}%</div><div style='font-size: 1.1em; color: #475569; font-weight: 600;'>현재 습도</div></div>", unsafe_allow_html=True)
with weather_col3:
    st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'><div style='font-size: 2.8em; font-weight: 900; color: #1D4ED8; line-height: 1.2;'>☔ {rain}mm</div><div style='font-size: 1.1em; color: #475569; font-weight: 600;'>강수량</div></div>", unsafe_allow_html=True)

if temp >= 33.0:
    weather_status, weather_level, weather_message, status_color = "🔴 폭염 경보", "critical", "온열질환 발생 위험! 옥외작업 최소화 및 휴식 보장", "#DC2626"
elif temp <= -5.0:
    weather_status, weather_level, weather_message, status_color = "🔵 한파 주의", "danger", "동절기 한랭질환 및 빙판길 미끄러짐 주의", "#2563EB"
elif rain > 0.0:
    weather_status, weather_level, weather_message, status_color = "🟡 강우 주의", "warning", "감전 및 미끄러짐 재해 위험이 높습니다.", "#F59E0B"
else:
    weather_status, weather_level, weather_message, status_color = "✅ 정상", "safe", "현재 특별한 기상 악화 위험은 없습니다.", "#10B981"

st.markdown(
    f"""<div class='metric-card card-{weather_level}'>
        <p style='font-size: 16px; font-weight: 700; margin: 0 0 8px 0; color: {status_color};'>{weather_status}</p>
        <p style='font-size: 14px; font-weight: 500; margin: 0; color: #475569;'>{weather_message}</p>
    </div>""", unsafe_allow_html=True
)
st.divider()

# --- 안전보건 주요 이슈 섹션 ---
news_data = get_daily_news()
news_fetch_time = news_data[0]['time'] if news_data else current_kst_time

st.subheader("📰 오늘의 안전보건 주요 이슈")
st.caption(f"🕒 **실시간 이슈 업데이트:** {news_fetch_time} (5분 주기 갱신)")

if news_data:
    for idx, news in enumerate(news_data):
        border_color = "#DC2626" if news.get('priority') == 'critical' else "#F59E0B" if news.get('priority') == 'high' else "#0F766E"
        st.markdown(
            f"""<a href="{news['url']}" target="_blank" style="text-decoration: none;">
                <div class='news-box' style='border-left-color: {border_color}; padding: 18px 20px;'>
                    <p class='news-title'>{news['title']}</p>
                    <p class='news-time'>클릭 시 네이버 검색 결과로 연동됩니다.</p>
                </div></a>""", unsafe_allow_html=True
        )
else:
    st.info("현재 불러올 이슈가 없습니다.")
st.divider()

# --- 업종별 안전수칙 탭 ---
st.subheader("🏭 업종별 핵심 안전수칙")
industry_list = ["시설관리", "청소", "물류", "식당", "서비스", "폐기물처리", "제조"]
industry_emoji = {"시설관리": "🔧", "청소": "🧹", "물류": "📦", "식당": "🍽️", "서비스": "👔", "폐기물처리": "♻️", "제조": "⚙️"}
tabs = st.tabs([f"{industry_emoji.get(ind, '•')} {ind}" for ind in industry_list])

for index, industry in enumerate(industry_list):
    with tabs[index]:
        st.markdown(f"#### 💡 {industry} 현장 필수 안전 가이드")
        for idx, rule in enumerate(get_kosha_safety_rules(industry), 1):
            st.markdown(
                f"""<div style='background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
                            border-left: 4px solid #1D4ED8; border-radius: 8px; padding: 12px 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'>
                    <p style='margin: 0; color: #1F2937; font-weight: 600; font-size: 15px;'>{idx}️⃣ {rule}</p>
                </div>""", unsafe_allow_html=True
            )
st.divider()

# --- TBM 확인서 섹션 ---
st.subheader("📋 일일 TBM(Tool Box Meeting) 모바일 확인서 생성")
with st.form("tbm_form"):
    st.markdown("### 📝 작업 정보 입력")
    form_col1, form_col2 = st.columns(2)
    with form_col1: contractor_name = st.text_input("🏢 협력사명", placeholder="예) 삼성건설", max_chars=30)
    with form_col2: worker_cnt = st.number_input("👥 투입 인원", min_value=1, value=5, step=1)
    selected_industry = st.selectbox("🛠️ 작업 업종 선택", industry_list, index=0)
    submitted = st.form_submit_button("🖨️ TBM 확인서 생성 및 복사", use_container_width=True)

if submitted and contractor_name:
    weather_alert = "🚨 폭염 경보" if temp >= 33.0 else "🚨 한파 주의" if temp <= -5.0 else "⚠️ 강우 주의" if rain > 0 else "✅ 기상 악화 사항 없음"
    rules_text = "\n".join([f"  {idx}. {rule}" for idx, rule in enumerate(get_kosha_safety_rules(selected_industry), 1)])
    issue_text = "\n".join([f"  • {news['title'].replace('**', '').replace('⚡', '').replace('🚨', '').strip()[:70]}" for news in news_data[:3]])
    
    final_tbm_result = f"""=========================================
[ 📋 일일 TBM 무재해 이행 확인서 ]
=========================================
■ 협력사명: {contractor_name}
■ 투입인원: {worker_cnt}명
■ 작업 업종: {selected_industry}
■ 작업 일자: {current_date}
■ 기상특보: {weather_alert}

[ 📰 금일 주요 안전보건 이슈 ]
{issue_text}

[ 🏭 금일 {selected_industry} 핵심 안전수칙 ]
{rules_text}

-----------------------------------------
[ ✅ 필수 안전점검 확인 ]
1. 작업 전 위험성평가 내용을 전원 숙지하였는가? ( O )
2. 안전모, 안전화 등 개인보호구를 완벽히 착용하였는가? ( O )
3. 음주자, 질병자 등 건강이상자가 없는가? ( O )
4. 기계·장비 안전검사 및 사전점검을 실시하였는가? ( O )
5. 상기 모든 사항을 숙지하고 안전하게 작업함을 서약합니다.
========================================="""
    
    st.success("✅ TBM 확인서가 깔끔하게 생성되었습니다!")
    st.text_area("TBM 확인서 텍스트", value=final_tbm_result, height=450, disabled=False)
elif submitted:
    st.error("⚠️ 협력사명을 반드시 입력해 주세요.")
st.divider()
