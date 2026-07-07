import streamlit as st
import requests
import datetime
import urllib.parse
import time
import html
import re
from streamlit_autorefresh import st_autorefresh
from datetime import timezone, timedelta

# =====================================================================
# 1. 페이지 기본 설정 및 자동 갱신
# =====================================================================
st.set_page_config(
    page_title="협력사 안전보건 정보제공",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 1분 단위 자동 새로고침 (전체 페이지)
st_autorefresh(interval=60000, key="ehs_dashboard_refresh")

# =====================================================================
# 2. 대시보드 맞춤형 CSS 스타일링
# =====================================================================
def dashboard_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            
            /* 전체 배경 및 폰트 설정 */
            [data-testid="stAppViewContainer"] { background-color: #f4f6f8; font-family: 'Noto Sans KR', sans-serif; }
            [data-testid="stHeader"] { background-color: transparent; }
            .block-container { padding-top: 2rem !important; max-width: 1400px; }
            
            /* 상단 헤더 타이틀 영역 */
            .dashboard-header {
                display: flex; justify-content: space-between; align-items: flex-end;
                border-bottom: 2px solid #cbd5e1; padding-bottom: 12px; margin-bottom: 24px;
            }
            .dashboard-title { font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; }
            .dashboard-time { font-size: 13px; color: #64748b; font-weight: 600; }
            
            /* 카드 공통 스타일 */
            .dash-card {
                background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
                padding: 20px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); margin-bottom: 20px;
            }
            .card-header {
                font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 16px;
                display: flex; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px;
            }
            .card-header-sub { font-size: 12px; color: #94a3b8; margin-left: 8px; font-weight: 400; }
            
            /* 기상 정보 구역 */
            .weather-wrap { display: flex; justify-content: space-around; text-align: center; margin: 15px 0 25px 0; }
            .w-label { font-size: 13px; color: #64748b; margin-bottom: 6px; font-weight: 500; }
            .w-val { font-size: 26px; font-weight: 800; }
            .c-temp { color: #dc2626; }  /* 기온: 빨강 */
            .c-humid { color: #16a34a; } /* 습도: 녹색 */
            .c-rain { color: #2563eb; }  /* 강수량: 파랑 */
            .w-status { 
                background-color: #f8fafc; color: #334155; font-size: 14px; font-weight: 600; 
                padding: 14px; border-radius: 6px; text-align: center; border: 1px solid #e2e8f0; 
            }
            
            /* 주요이슈 리스트 구역 */
            .news-item { 
                background: #ffffff; padding: 12px 14px; border-radius: 6px; margin-bottom: 10px;
                border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; transition: all 0.2s;
            }
            .news-item:hover { background: #f8fafc; transform: translateX(4px); }
            .news-title { font-size: 13px; font-weight: 600; color: #1e293b; text-decoration: none; display: block; margin-bottom: 4px; line-height: 1.4; }
            .news-date { font-size: 11px; color: #94a3b8; }
            
            /* 안전수칙 리스트 구역 */
            .rule-item { 
                font-size: 13px; color: #334155; background: #f8fafc; padding: 12px; 
                border-radius: 6px; border: 1px solid #f1f5f9; margin-bottom: 8px; display: flex; line-height: 1.5; 
            }
            .rule-num { color: #3b82f6; font-weight: 800; margin-right: 10px; }
            
            /* TBM 폼 구역 */
            div[data-testid="stForm"] {
                background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; 
                box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); padding: 20px;
            }
            .stSelectbox label, .stTextInput label, .stNumberInput label { 
                font-size: 13px !important; font-weight: 600 !important; color: #1e293b !important; 
            }
        </style>
    """, unsafe_allow_html=True)

dashboard_css()

# =====================================================================
# 3. 텍스트 세척 및 API 연동 로직
# =====================================================================
kst = timezone(timedelta(hours=9))

def clean_html_text(raw_text):
    if not raw_text: return ""
    text = re.sub(r'<[^>]+>', '', raw_text)
    text = html.unescape(text)
    text = text.replace('\\"', '"').replace('\\\'', "'")
    return text.strip()

@st.cache_data(ttl=60)
def get_weather_data(current_min_trigger): # 1분 단위 갱신 트리거
    now = datetime.datetime.now(kst)
    try:
        if "KMA_API_KEY" in st.secrets:
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            if now.minute < 40: now = now - timedelta(hours=1)
            params = {
                'serviceKey': st.secrets["KMA_API_KEY"], 'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
                'base_date': now.strftime('%Y%m%d'), 'base_time': now.strftime('%H00'),
                'nx': '60', 'ny': '121'
            }
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                items = res.json()['response']['body']['items']['item']
                weather = {}
                for item in items:
                    if item['category'] == 'T1H': weather['temp'] = float(item['obsrValue'])
                    elif item['category'] == 'RN1': weather['rain'] = float(item['obsrValue'])
                    elif item['category'] == 'REH': weather['humid'] = float(item['obsrValue'])
                if 'temp' in weather: return weather
    except Exception: pass
    return {'temp': 28.5, 'humid': 60.0, 'rain': 0.0}

# time_block 파라미터를 통해 5분마다 완벽하게 캐시를 무효화
@st.cache_data(ttl=300)
def get_daily_news(time_block):
    news_list = []
    timestamp = datetime.datetime.now(kst).strftime('%Y-%m-%d %H:%M')
    try:
        if "NAVER_CLIENT_ID" in st.secrets and "NAVER_CLIENT_SECRET" in st.secrets:
            headers = {
                'X-Naver-Client-Id': st.secrets['NAVER_CLIENT_ID'],
                'X-Naver-Client-Secret': st.secrets['NAVER_CLIENT_SECRET']
            }
            # [핵심 수정] 건설업 배제 및 대상 업종 키워드 조합으로 쿼리 최적화
            query_str = "안전보건 OR 산업재해 OR 중대재해 (제조 OR 물류 OR 시설관리 OR 식당 OR 미화 OR 서비스) -건설 -건축 -아파트"
            query = urllib.parse.quote(query_str)
            res = requests.get(f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=date", headers=headers, timeout=5)
            
            if res.status_code == 200 and res.json().get('items'):
                for item in res.json()['items']:
                    clean_title = clean_html_text(item['title'])
                    news_list.append({
                        "title": f"⚡ [속보] {clean_title[:70]}...",
                        "url": item['link'],
                        "time": timestamp
                    })
    except Exception: pass
    
    if not news_list:
        news_list = [{"title": "🚨 [시스템] 관련 업종 실시간 뉴스를 불러오는 중입니다...", "url": "#", "time": timestamp}]
    return news_list

# date_str 인자를 통해 일단위로 캐시 무효화 + 업종별 로테이션 알고리즘
@st.cache_data(ttl=86400)
def get_kosha_safety_rules(industry, date_str):
    day_of_year = datetime.datetime.now(kst).timetuple().tm_yday # 올해의 몇 번째 일인지 계산
    fetched_rules = []
    
    try:
        if "KOSHA_API_KEY" in st.secrets:
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/SafeHealthInfoService/getIndustrySafeGuide'
            # [핵심 수정] 30개를 가져와서 날짜에 따라 5개씩 순환 노출되도록 조치
            params = {'serviceKey': st.secrets["KOSHA_API_KEY"], 'searchKeyword': industry, 'type': 'json', 'numOfRows': '30'}
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                items = res.json()['response']['body']['items'].get('item', [])
                if not isinstance(items, list): items = [items]
                fetched_rules = [clean_html_text(item.get('subject', '')) for item in items if item.get('subject')]
    except Exception: pass
    
    # KOSHA API 실패 시 자체 DB 활용 (로테이션을 위해 업종별 항목 수 보강)
    fallback_db = {
        "시설관리": [
            "안전모, 안전대 등 개인보호구 착용 철저", "고소작업 시 추락방지망 및 안전난간 확인", "정비 작업 전 전원 차단(LOTO) 실행", 
            "사다리 작업 시 2인 1조 준수", "밀폐공간 진입 전 산소농도 측정", "작업장 주변 조도(밝기) 확보",
            "가연성 물질 주변 용접 작업 금지", "기계실 내 회전부 방호덮개 체결 확인"
        ],
        "청소": [
            "물기, 기름기 등에 의한 전도(넘어짐) 사고 주의", "화학세제 사용 시 물질안전보건자료(MSDS) 확인", "안전표지판(미끄럼 주의) 설치 철저",
            "계단 청소 시 안전난간대 지지 및 추락 주의", "화장실 청소 시 환기팬 가동", "세제 혼용 사용 금지 및 전용 용기 사용",
            "쓰레기 수거 시 찔림/베임 주의 장갑 착용"
        ],
        "물류": [
            "지게차 작업 반경 내 보행자 접근 엄금", "중량물 취급 시 요통 등 근골격계 질환 주의", "상하차 작업 시 작업지휘자 배치",
            "지게차 운전자 시야 확보 및 제한속도 준수", "컨베이어 벨트 비상정지 스위치 위치 확인", "적재물 무너짐 방지 결속 상태 확인",
            "야간 작업 시 시인성 높은 형광조끼 착용"
        ],
        "제조": [
            "기계기구 회전부(기어, 롤러 등) 끼임 방지 덮개 설치", "소음/분진 발생 공정 시 귀마개/방진마스크 착용", "안전센서 및 인터록 장치 임의 해제 금지",
            "화학물질 취급 시 국소배기장치 가동", "비정형 작업(수리, 정비) 시 관리감독자 입회", "크레인 등 양중기 로프 손상 여부 점검",
            "작업장 내 보행통로 확보 및 정리정돈"
        ],
        "식당": [
            "뜨거운 물/기름에 의한 화상 주의 및 방열장갑 착용", "바닥 물기 즉시 제거 및 미끄럼 방지 장화 착용", "칼 등 날카로운 도구 사용 시 베임 방지 장갑 착용",
            "육류 절단기 사용 시 밀대 사용 및 안전가드 확인", "식자재 운반 시 카트 사용(근골격계 예방)", "가스 누출 여부 작업 전후 점검",
            "오븐/튀김기 주변 가연성 물질 방치 금지"
        ],
        "서비스": [
            "고객 응대 시 감정노동 스트레스 관리 및 휴식", "실내 적정 온도 및 환기 유지", "장시간 서서 일하는 근로자 의자 비치",
            "진열장 등 중량물 전도 방지 고정 상태 확인", "매장 내 전선 걸림 등 넘어짐 위험 요소 제거"
        ],
        "폐기물처리": [
            "파쇄기, 압축기 끼임 방지를 위한 방호덮개 확인", "밀폐공간 진입 전 산소/유해가스 농도 측정", "폐기물 반입/반출 시 신호수 배치",
            "오염물질 접촉 방지를 위한 방호복 및 화학물질용 장갑 착용", "지게차, 굴착기 등 장비와 작업자 간 동선 분리"
        ]
    }
    
    final_rules = fetched_rules if len(fetched_rules) >= 5 else fallback_db.get(industry, ["기본 안전보호구를 반드시 착용하세요."])
    
    # [핵심 수정] 리스트에서 5개씩 날짜에 따라 롤링(순환) 추출
    if len(final_rules) > 5:
        max_idx = len(final_rules) - 5
        start_idx = day_of_year % (max_idx + 1)
        return final_rules[start_idx : start_idx + 5]
    
    return final_rules[:5]

# =====================================================================
# 4. 화면 렌더링 (코드 노출 원천 차단 및 간격 동기화)
# =====================================================================
now_kst = datetime.datetime.now(kst)
current_time_str = now_kst.strftime('%Y-%m-%d %H:%M')

industry_list = ["시설관리", "청소", "물류", "제조", "식당", "서비스", "폐기물처리"]

# 헤더
header_html = f'<div class="dashboard-header"><h2 class="dashboard-title">협력사 안전보건 정보제공 DASHBOARD</h2><span class="dashboard-time">🔄 동기화 기준: {current_time_str}</span></div>'
st.markdown(header_html, unsafe_allow_html=True)

# 2기둥 레이아웃
left_col, right_col = st.columns(2, gap="large")

# ----------------- 좌측 단 -----------------
with left_col:
    # 1. 기상 정보 카드 (1분 단위 갱신 파라미터)
    weather_data = get_weather_data(now_kst.minute)
    temp, humid, rain = weather_data['temp'], weather_data['humid'], weather_data['rain']
    weather_msg = "✅ 기상 악화 요인 없음 (정상 작업 가능)" if -5.0 < temp < 33.0 and rain == 0 else "⚠️ 기상 주의 (폭염/강우/한파 안전대책 요망)"
    
    weather_html = f'<div class="dash-card"><div class="card-header">현장 기상정보 <span class="card-header-sub">Weather Status</span></div><div class="weather-wrap"><div><div class="w-label">현재 기온</div><div class="w-val c-temp">{temp}℃</div></div><div><div class="w-label">현재 습도</div><div class="w-val c-humid">{humid}%</div></div><div><div class="w-label">강수량</div><div class="w-val c-rain">{rain}mm</div></div></div><div class="w-status">{weather_msg}</div></div>'
    st.markdown(weather_html, unsafe_allow_html=True)

    # 2. 실시간 주요 이슈 카드 (5분 단위 갱신 파라미터)
    time_block_5min = now_kst.minute // 5
    news_data = get_daily_news(time_block_5min)
    
    news_html = '<div class="dash-card"><div class="card-header">실시간 타겟업종 주요이슈 <span class="card-header-sub">Safety News (5분 주기)</span></div>'
    for news in news_data:
        news_html += f'<div class="news-item"><a href="{news["url"]}" target="_blank" class="news-title">{news["title"]}</a><div class="news-date">{news["time"]} 업데이트</div></div>'
    news_html += '</div>'
    st.markdown(news_html, unsafe_allow_html=True)

# ----------------- 우측 단 -----------------
with right_col:
    # 3. 업종별 핵심 안전수칙 카드 (일단위 갱신 파라미터)
    st.markdown('<div style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">업종별 핵심 안전수칙 <span style="font-size: 12px; color: #94a3b8; font-weight: 400; margin-left: 8px;">Safety Rules (일단위 순환)</span></div>', unsafe_allow_html=True)
    selected_ind_view = st.selectbox("업종 선택", industry_list, label_visibility="collapsed")
    
    date_str = now_kst.strftime('%Y-%m-%d')
    rules = get_kosha_safety_rules(selected_ind_view, date_str)
    
    rules_html = '<div class="dash-card" style="margin-top:-10px;">'
    for idx, rule in enumerate(rules, 1):
        rules_html += f'<div class="rule-item"><span class="rule-num">{idx}</span> {rule}</div>'
    rules_html += '</div>'
    st.markdown(rules_html, unsafe_allow_html=True)

    # 4. TBM 확인서 발급 폼
    st.markdown('<div style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">일일 TBM 모바일 확인서 발급 <span style="font-size: 12px; color: #94a3b8; font-weight: 400; margin-left: 8px;">TBM Form</span></div>', unsafe_allow_html=True)
    with st.form("tbm_form"):
        f_col1, f_col2 = st.columns(2)
        with f_col1: 
            contractor_name = st.text_input("🏢 협력사명", placeholder="예: 삼성이엔지")
        with f_col2: 
            worker_cnt = st.number_input("👥 투입 인원", min_value=1, value=5)
        
        selected_industry_form = st.selectbox("🛠️ 금일 작업 업종", industry_list)
        submitted = st.form_submit_button("🖨️ 확인서 발급 생성", use_container_width=True)

# ----------------- TBM 생성 결과 -----------------
if submitted and contractor_name:
    form_rules = "\n".join([f"  {idx}. {rule}" for idx, rule in enumerate(get_kosha_safety_rules(selected_industry_form, date_str), 1)])
    form_news = "\n".join([f"  • {news['title'].replace('⚡ [속보] ', '').strip()[:50]}" for news in news_data[:3]])
    
    tbm_result = f"""=========================================
[ 📋 일일 TBM 무재해 이행 확인서 ]
=========================================
■ 협력사명: {contractor_name}
■ 작업업종: {selected_industry_form}
■ 투입인원: {worker_cnt}명
■ 기상상태: {weather_msg}

[ 📰 실시간 주요 안전이슈 ]
{form_news}

[ 🏭 금일 필수 안전수칙 ]
{form_rules}

[ ✅ 필수 안전점검 확인 ]
1. 위험성평가 내용을 숙지하였는가? ( O )
2. 개인보호구를 완벽히 착용하였는가? ( O )
3. 건강이상자가 없는가? ( O )
========================================="""
    st.success("✅ 확인서가 생성되었습니다. 아래 내용을 복사하여 카카오톡으로 공유하세요.")
    st.text_area("TBM 복사 영역", value=tbm_result, height=250, label_visibility="collapsed")
