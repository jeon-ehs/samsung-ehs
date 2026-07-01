import streamlit as st
import requests
import datetime
import streamlit.components.v1 as components
import urllib.parse # URL 인코딩을 위한 기본 라이브러리 추가

# =====================================================================
# [자동 새로고침] 1분(60초) 단위 데이터 및 화면 갱신
# =====================================================================
def auto_refresh(interval_seconds):
    components.html(
        f"""
        <script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {interval_seconds * 1000});
        </script>
        """,
        height=0, width=0,
    )
auto_refresh(60)

# =====================================================================
# 1. 페이지 기본 설정 및 [다크/라이트 모드 자동 호환] CSS 주입
# =====================================================================
st.set_page_config(page_title="협력사 일일 안전 포털", page_icon="🛡️", layout="wide")

def local_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            
            html, body, .stApp { font-family: 'Noto Sans KR', sans-serif; }
            header {visibility: hidden;}
            .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
            
            div[data-baseweb="input"], div[data-baseweb="select"] > div { 
                background-color: var(--secondary-background-color) !important; 
                border: 1px solid rgba(148, 163, 184, 0.5) !important; 
                border-radius: 6px !important; 
                color: var(--text-color) !important;
            }
            div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within { 
                border-color: #1D4ED8 !important; 
                box-shadow: 0 0 0 1px #1D4ED8 !important; 
            }
            
            .news-box { 
                background-color: var(--secondary-background-color); 
                border-left: 5px solid #EAB308; 
                padding: 15px 18px; 
                margin-bottom: 10px; 
                border-radius: 6px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
                font-size: 15.5px; 
                color: var(--text-color); 
                transition: all 0.2s ease-in-out; 
            }
            .news-box:hover {
                transform: translateX(5px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                background-color: rgba(234, 179, 8, 0.1);
                cursor: pointer;
            }
            
            div[data-baseweb="tab-highlight"] { display: none; }
            
            [data-testid="stTabs"] button { 
                background-color: var(--secondary-background-color) !important; 
                border-radius: 8px !important; 
                padding: 10px 16px !important; 
                border: 1px solid rgba(148, 163, 184, 0.3) !important; 
                margin-right: 6px !important; 
                transition: all 0.3s ease-in-out !important; 
            }
            [data-testid="stTabs"] button p { color: var(--text-color) !important; font-weight: 500 !important; opacity: 0.8; }
            
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] { background-color: #EFF6FF !important; border-color: #1D4ED8 !important; }
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] p { color: #1D4ED8 !important; font-weight: 800 !important; opacity: 1;}
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] { background-color: #F0FDFA !important; border-color: #0F766E !important; }
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] p { color: #0F766E !important; font-weight: 800 !important; opacity: 1;}
            [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] { background-color: #FFF7ED !important; border-color: #C2410C !important; }
            [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] p { color: #C2410C !important; font-weight: 800 !important; opacity: 1;}
            [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] { background-color: #FEF2F2 !important; border-color: #B91C1C !important; }
            [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] p { color: #B91C1C !important; font-weight: 800 !important; opacity: 1;}
            [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] { background-color: #FAF5FF !important; border-color: #6D28D9 !important; }
            [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] p { color: #6D28D9 !important; font-weight: 800 !important; opacity: 1;}
            [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] { background-color: #FEF3C7 !important; border-color: #B45309 !important; }
            [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] p { color: #B45309 !important; font-weight: 800 !important; opacity: 1;}
            [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] { background-color: #F8FAFC !important; border-color: #334155 !important; }
            [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] p { color: #334155 !important; font-weight: 800 !important; opacity: 1;}
        </style>
    """, unsafe_allow_html=True)
local_css()

# =====================================================================
# 2. 공공데이터 API 실시간 호출 (데이터 갱신 주기 1분)
# =====================================================================
@st.cache_data(ttl=60)
def get_weather_data():
    try:
        if "KMA_API_KEY" in st.secrets:
            api_key = st.secrets["KMA_API_KEY"]
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            now = datetime.datetime.now()
            if now.minute < 40: now = now - datetime.timedelta(hours=1)
            params = {
                'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON', 
                'base_date': now.strftime('%Y%m%d'), 'base_time': now.strftime('%H00'), 'nx': '60', 'ny': '121' 
            }
            response = requests.get(url, params=params, timeout=5)
            items = response.json()['response']['body']['items']['item']
            weather = {}
            for item in items:
                if item['category'] == 'T1H': weather['temp'] = float(item['obsrValue'])
                elif item['category'] == 'RN1': weather['rain'] = float(item['obsrValue'])
                elif item['category'] == 'REH': weather['humid'] = float(item['obsrValue'])
            return weather
    except Exception:
        pass
    return {'temp': 28.5, 'humid': 60.0, 'rain': 0.0}

@st.cache_data(ttl=60)
def get_kosha_daily_news():
    """근본적 해결: 공단 API의 불량 URL을 버리고, 해당 제목으로 네이버 뉴스 검색 자동 연동"""
    news_list = []
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/BoardService/getBoardList'
            params = {'serviceKey': api_key, 'boardId': 'news', 'numOfRows': '3', 'type': 'json'}
            response = requests.get(url, params=params, timeout=5)
            items = response.json()['response']['body']['items']['item']
            
            for item in items:
                title = item.get('title', '')
                if not title: continue
                
                # 핵심: 해당 제목으로 네이버 통합검색 링크 생성 (404 에러 절대 발생 안 함)
                # '안전보건공단' 키워드를 덧붙여 정확도를 높임
                search_query = urllib.parse.quote(f"안전보건공단 {title}")
                safe_link = f"https://search.naver.com/search.naver?query={search_query}"
                
                news_list.append({"title": title, "url": safe_link})
            
            if news_list:
                return news_list
    except Exception:
        pass
    
    # API 오류 시 나타나는 기본값(Fallback)도 네이버 스마트 검색으로 통일
    fallback_data = [
        "타 현장 지붕 보수공사 중 채광창 파손 추락사고 발생",
        "혹서기 근로자 휴게시설 설치 기준 및 에어컨 가동 집중 점검 기간",
        "온열질환(열사병 등) 예방을 위한 '물·그늘·휴식' 3대 수칙 준수 강조"
    ]
    
    for title in fallback_data:
        search_query = urllib.parse.quote(f"안전보건공단 {title}")
        safe_link = f"https://search.naver.com/search.naver?query={search_query}"
        news_list.append({"title": f"🚨 {title}", "url": safe_link})
        
    return news_list

@st.cache_data(ttl=43200)
def get_kosha_safety_rules(industry):
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/SafeHealthInfoService/getIndustrySafeGuide'
            params = {'serviceKey': api_key, 'searchKeyword': industry, 'type': 'json', 'numOfRows': '3'}
            response = requests.get(url, params=params, timeout=5)
            items = response.json()['response']['body']['items']['item']
            rules = [item.get('subject', '') for item in items if item.get('subject')]
            if rules: return rules
    except Exception:
        pass
    fallback_db = {
        "시설관리": ["안전모, 안전대 등 개인보호구 착용 철저", "고소작업 시 추락방지망 및 안전난간 확인", "정비 작업 전 전원 차단(LOTO) 확행"],
        "청소": ["물기, 기름기 등에 의한 전도(넘어짐) 사고 주의", "화학세제 사용 시 물질안전보건자료(MSDS) 확인", "작업구간 미끄럼 주의 표지판 설치"],
        "물류": ["지게차 작업 반경 내 보행자 접근 엄금", "중량물 취급 시 요통 등 근골격계 질환 주의", "적재물 낙하 방지 조치 및 하역 작업 지휘자 배치"],
        "식당": ["뜨거운 물/기름에 의한 화상 주의 및 방열장갑 착용", "바닥 물기 즉시 제거 및 미끄럼 방지 장화 착용", "식자재 운반 시 베임/찔림 주의"],
        "서비스": ["고객 응대 시 감정노동 스트레스 관리 및 휴식", "오랜 서서/앉아 일하는 작업 시 스트레칭 실시", "실내 적정 온도 및 환기 유지"],
        "폐기물처리": ["파쇄기, 압축기 끼임 방지를 위한 방호덮개 확인", "날카로운 물체 취급 시 베임 방지 장갑 착용", "밀폐공간 진입 전 산소/유해가스 농도 측정"],
        "제조": ["기계기구 회전부(기어, 롤러 등) 끼임 방지 덮개 설치", "소음/분진 발생 공정 시 귀마개 및 방진마스크 착용", "지게차, 크레인 등 운반기계 안전수칙 준수"]
    }
    return fallback_db.get(industry, ["기본 안전보호구를 반드시 착용하세요."])

# =====================================================================
# 3. 대시보드 화면 렌더링
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>", unsafe_allow_html=True)

current_time_str = datetime.datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
st.caption(f"📅 **오늘의 날짜:** {current_time_str} 기준 (1분 단위 실시간 자동 업데이트 중 🔄)")

# --- [날씨 섹션] ---
st.subheader("📡 현장 실시간 기상 및 환경 지침 (수원 기준)")
weather = get_weather_data()
c1, c2, c3 = st.columns(3)
with c1: st.info(f"🌡️ **현재 기온:** {weather['temp']} ℃")
with c2: st.info(f"💧 **현재 습도:** {weather['humid']} %")
with c3: st.info(f"☔ **강수량:** {weather['rain']} mm")

if weather['temp'] >= 33.0:
    st.error("🚨 **[폭염 경보]** 온열질환 발생 위험 구역! 옥외작업을 최소화하세요.")
elif weather['temp'] <= -5.0:
    st.info("🚨 **[한파 주의]** 동절기 한랭질환 및 빙판길 미끄러짐 주의.")
elif weather['rain'] > 0.0:
    st.warning("☔ **[강우 주의]** 우천으로 인한 감전 및 미끄러짐 재해 위험 발생.")
else:
    st.success("✅ 현재 특별한 기상 악화 위험은 없습니다. 기본 작업 수칙을 준수 바랍니다.")

st.divider()

# --- [이슈 섹션 (스마트 검색 연동 완료)] ---
st.subheader("📰 오늘의 안전보건 주요 이슈 (클릭 시 세부 내용 즉시 검색)")
daily_news = get_kosha_daily_news()

for news in daily_news:
    clickable_box = f"""
    <a href="{news['url']}" target="_blank" style="text-decoration: none;">
        <div class='news-box'>🔗 {news['title']}</div>
    </a>
    """
    st.markdown(clickable_box, unsafe_allow_html=True)

st.divider()

# --- [업종별 탭 섹션] ---
st.subheader("🏭 업종별 핵심 안전수칙 (클릭하여 확인하세요)")
industry_list = ["시설관리", "청소", "물류", "식당", "서비스", "폐기물처리", "제조"]
tabs = st.tabs(industry_list)
for index, industry in enumerate(industry_list):
    with tabs[index]:
        kosha_rules = get_kosha_safety_rules(industry)
        st.markdown(f"#### 💡 {industry} 현장 필수 안전 가이드")
        for rule in kosha_rules:
            st.markdown(f"✔️ **{rule}**")

st.divider()

# =====================================================================
# 4. TBM 확인서 생성
# =====================================================================
st.subheader("📋 일일 TBM(Tool Box Meeting) 모바일 확인서 발급")

form_col1, form_col2, form_col3 = st.columns(3)
with form_col1: contractor_name = st.text_input("🏢 협력사명 입력 (예: 삼성건설)")
with form_col2: worker_cnt = st.number_input("👥 투입 인원 (명)", min_value=1, value=3)
with form_col3: selected_industry = st.selectbox("🛠️ 작업 업종 선택", industry_list)

st.markdown("<hr style='margin: 15px 0 25px 0; border: 1px solid rgba(148, 163, 184, 0.3);'>", unsafe_allow_html=True)

if st.button("🖨️ 현장 공유용 TBM 확인서 생성"):
    if contractor_name:
        weather_alert = "기상 악화 사항 없음"
        if weather['temp'] >= 33.0: weather_alert = "폭염 경보 (물/그늘/휴식 필수)"
        elif weather['rain'] > 0: weather_alert = "우천 주의 (옥외 전기작업 금지)"
        
        rules_data = get_kosha_safety_rules(selected_industry)
        rules_text = "\n".join([f"  - {rule}" for rule in rules_data])

        header_text = f"[ 일일 TBM 무재해 이행 확인서 ]\n■ 협력사명: {contractor_name}\n■ 투입인원: {worker_cnt}명\n■ 기상특보: {weather_alert}\n■ 작업업종: {selected_industry}"
        middle_text = f"\n[ 금일 {selected_industry} 핵심 안전수칙 ]\n{rules_text}\n"
        bottom_text = "-----------------------------------------\n[ 필수 안전점검 확인 ]\n1. 작업 전 위험성평가 내용을 전원 숙지하였는가? ( O )\n2. 안전모, 안전화 등 개인보호구를 완벽히 착용하였는가? ( O )\n3. 음주자, 질병자 등 건강이상자가 없는가? ( O )\n========================================="
        
        final_tbm_result = f"=========================================\n{header_text}\n{middle_text}\n{bottom_text}"
        st.text_area("✨ 카카오톡/메시지 복사 공유용 텍스트:", value=final_tbm_result, height=350)
    else:
        st.error("협력사명을 반드시 입력해 주세요.")
