import streamlit as st
import requests
import datetime

# =====================================================================
# 1. 페이지 기본 설정 및 [반응형 컬러 탭] CSS 주입
# =====================================================================
st.set_page_config(page_title="협력사 일일 안전 포털", page_icon="🛡️", layout="wide")

def local_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            html, body, [class*="st-"] { font-family: 'Noto Sans KR', sans-serif; background-color: #F0F4F8; }
            header {visibility: hidden;}
            .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
            
            /* 기본 탭 숨김 처리 (기본 밑줄 제거) */
            div[data-baseweb="tab-highlight"] { display: none; }
            
            /* 공통 탭 버튼 기본 스타일 (부드러운 애니메이션 적용) */
            [data-testid="stTabs"] button { 
                background-color: #FFFFFF; 
                border-radius: 8px; 
                color: #64748B; 
                font-weight: 600; 
                padding: 12px 18px; 
                border: 2px solid #E2E8F0; 
                margin-right: 8px; 
                transition: all 0.3s ease-in-out; /* 마우스 반응 애니메이션 */
            }
            
            /* 1. 시설관리 (파랑 테마) */
            [data-testid="stTabs"] button:nth-of-type(1):hover { background-color: #EFF6FF; color: #1D4ED8; border-color: #93C5FD; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(1)[aria-selected="true"] { background-color: #1D4ED8; color: white; border-color: #1D4ED8; box-shadow: 0 4px 10px rgba(29,78,216,0.3); }

            /* 2. 청소 (청록 테마) */
            [data-testid="stTabs"] button:nth-of-type(2):hover { background-color: #F0FDFA; color: #0F766E; border-color: #5EEAD4; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(2)[aria-selected="true"] { background-color: #0F766E; color: white; border-color: #0F766E; box-shadow: 0 4px 10px rgba(15,118,110,0.3); }

            /* 3. 물류 (주황 테마) */
            [data-testid="stTabs"] button:nth-of-type(3):hover { background-color: #FFF7ED; color: #C2410C; border-color: #FDBA74; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(3)[aria-selected="true"] { background-color: #C2410C; color: white; border-color: #C2410C; box-shadow: 0 4px 10px rgba(194,65,12,0.3); }

            /* 4. 식당 (빨강 테마) */
            [data-testid="stTabs"] button:nth-of-type(4):hover { background-color: #FEF2F2; color: #B91C1C; border-color: #FCA5A5; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(4)[aria-selected="true"] { background-color: #B91C1C; color: white; border-color: #B91C1C; box-shadow: 0 4px 10px rgba(185,28,28,0.3); }

            /* 5. 서비스 (보라 테마) */
            [data-testid="stTabs"] button:nth-of-type(5):hover { background-color: #FAF5FF; color: #6D28D9; border-color: #D8B4FE; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(5)[aria-selected="true"] { background-color: #6D28D9; color: white; border-color: #6D28D9; box-shadow: 0 4px 10px rgba(109,40,217,0.3); }

            /* 6. 폐기물처리 (갈색 테마) */
            [data-testid="stTabs"] button:nth-of-type(6):hover { background-color: #FEF3C7; color: #B45309; border-color: #FCD34D; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(6)[aria-selected="true"] { background-color: #B45309; color: white; border-color: #B45309; box-shadow: 0 4px 10px rgba(180,83,9,0.3); }

            /* 7. 제조 (진회색 테마) */
            [data-testid="stTabs"] button:nth-of-type(7):hover { background-color: #F8FAFC; color: #334155; border-color: #CBD5E1; transform: translateY(-2px); }
            [data-testid="stTabs"] button:nth-of-type(7)[aria-selected="true"] { background-color: #334155; color: white; border-color: #334155; box-shadow: 0 4px 10px rgba(51,65,85,0.3); }
        </style>
    """, unsafe_allow_html=True)
local_css()

# =====================================================================
# 2. 공공데이터 API 실시간 호출 및 방어(Fallback) 로직
# =====================================================================
@st.cache_data(ttl=1800)
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
st.caption(f"📅 **오늘의 날짜:** {datetime.date.today().strftime('%Y년 %m월 %d일')} (사외 접속 가능)")

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
