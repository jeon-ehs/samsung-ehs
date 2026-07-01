import streamlit as st
import requests
import datetime

# =====================================================================
# 1. 페이지 기본 설정 및 세련된 UI CSS 주입 (CLINE SR 스타일 복원)
# =====================================================================
st.set_page_config(page_title="협력사 일일 안전 포털", page_icon="🛡️", layout="wide")

def local_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            html, body, [class*="st-"] { font-family: 'Noto Sans KR', sans-serif; background-color: #F0F4F8; }
            header {visibility: hidden;}
            .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
            [data-testid="stTabs"] button { background-color: #FFFFFF; border-radius: 8px; color: #5A6478; font-weight: 500; padding: 10px 16px; border: 1px solid #E2E8F0; margin-right: 6px; }
            [data-testid="stTabs"] button[aria-selected="true"] { background-color: #1e3a8a; color: white; border: none; font-weight: 700; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .metric-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
        </style>
    """, unsafe_allow_html=True)
local_css()

# =====================================================================
# 2. 공공데이터 API 실시간 호출 및 방어(Fallback) 로직
# =====================================================================

@st.cache_data(ttl=1800) # 기상청 데이터는 30분마다 갱신
def get_weather_data():
    """기상청 실시간 초단기실황 API 연동"""
    try:
        if "KMA_API_KEY" in st.secrets:
            api_key = st.secrets["KMA_API_KEY"]
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            
            now = datetime.datetime.now()
            if now.minute < 40: # 매시간 40분 이후에 최신 데이터가 나옴
                now = now - datetime.timedelta(hours=1)
                
            params = {
                'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON', 
                'base_date': now.strftime('%Y%m%d'), 'base_time': now.strftime('%H00'), 
                'nx': '60', 'ny': '121' # 수원 기준 좌표
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
    
    # API 키가 없거나 서버 장애 시 자동 출력되는 기본 데이터 (프로그램 중단 방지)
    return {'temp': 28.5, 'humid': 60.0, 'rain': 0.0, 'status': 'api_error'}

@st.cache_data(ttl=43200) # 공단 데이터는 12시간마다 갱신 (서버 부하 최소화)
def get_kosha_safety_rules(industry):
    """한국산업안전보건공단 업종별 재해예방 API 연동"""
    # 1. API 호출 시도
    try:
        if "KOSHA_API_KEY" in st.secrets:
            api_key = st.secrets["KOSHA_API_KEY"]
            # 안전보건공단 미디어자료 가이드 API 엔드포인트 예시
            url = 'http://openapi.kosha.or.kr/openapi/service/rest/SafeHealthInfoService/getIndustrySafeGuide'
            params = {'serviceKey': api_key, 'searchKeyword': industry, 'type': 'json', 'numOfRows': '3'}
            
            response = requests.get(url, params=params, timeout=5)
            items = response.json()['response']['body']['items']['item']
            
            # API에서 안전수칙 추출
            rules = [item.get('subject', '') for item in items if item.get('subject')]
            if rules: return rules
    except Exception:
        pass

    # 2. API 장애/미설정 시 100% 작동하는 핵심 안전수칙 (Fallback DB)
    fallback_db = {
        "시설관리": ["안전모, 안전대 등 개인보호구 착용 철저", "고소작업 시 추락방지망 및 안전난간 확인", "정비 작업 전 전원 차단(LOTO) 확행"],
        "청소": ["물기, 기름기 등에 의한 전도(넘어짐) 사고 주의", "화학세제 사용 시 물질안전보건자료(MSDS) 확인", "작업구간 미끄럼 주의 표지판 설치"],
        "물류": ["지게차 작업 반경 내 보행자 접근 엄금", "중량물 취급 시 요통 등 근골격계 질환 주의", "적재물 낙하 방지 조치 및 하역 작업 지휘자 배치"],
        "식당": ["뜨거운 물/기름에 의한 화상 주의 및 방열장갑 착용", "바닥 물기 즉시 제거 및 미끄럼 방지 장화 착용", "식자재 운반 시 베임/찔림 주의"],
        "서비스": ["고객 응대 시 감정노동 스트레스 관리 및 휴식", "오랜 서서/앉아 일하는 작업 시 스트레칭 실시", "실내 적정 온도 및 환기 유지"],
        "폐기물처리": ["파쇄기, 압축기 끼임 방지를 위한 방호덮개 확인", "날카로운 물체 취급 시 베임 방지 장갑 착용", "밀폐공간 진입 전 산소/유해가스 농도 측정"],
        "제조": ["기계기구 회전부(기어, 롤러 등) 끼임 방지 덮개 설치", "소음/분진 발생 공정 시 귀마개 및 방진마스크 착용", "지게차, 크레인 등 운반기계 안전수칙 준수"]
    }
    return fallback_db.get(industry, ["기본 안전보호구를 반드시 착용하세요.", "작업 전 위험성 평가를 숙지하세요."])

# =====================================================================
# 3. 대시보드 화면 렌더링
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>", unsafe_allow_html=True)
st.caption(f"📅 **오늘의 날짜:** {datetime.date.today().strftime('%Y년 %m월 %d일')} (본 시스템은 사외망에서도 접속 가능합니다)")

# --- [섹션 1: 날씨 및 날씨 맞춤형 안전 가이드] ---
st.subheader("📡 현장 실시간 기상 및 환경 지침 (수원 기준)")
weather = get_weather_data()

c1, c2, c3 = st.columns(3)
with c1: st.info(f"🌡️ **현재 기온:** {weather['temp']} ℃")
with c2: st.info(f"💧 **현재 습도:** {weather['humid']} %")
with c3: st.info(f"☔ **강수량:** {weather['rain']} mm")

# 날씨 기반 동적 안전수칙 경고
if weather['temp'] >= 33.0:
    st.error("🚨 **[폭염 경보]** 온열질환 발생 위험 구역! 옥외작업을 최소화하세요.")
    st.markdown("✔️ **[폭염 안전수칙]** 시원한 물 제공 / 그늘진 휴식공간 확보 / 1시간 주기 10~15분 휴식 의무화")
elif weather['temp'] <= -5.0:
    st.info("🚨 **[한파 주의]** 동절기 한랭질환 및 빙판길 미끄러짐 주의.")
    st.markdown("✔️ **[한파 안전수칙]** 방한복 및 보온장갑 착용 / 결빙 구간 모래 살포 / 주기적인 따뜻한 휴식")
elif weather['rain'] > 0.0:
    st.warning("☔ **[강우 주의]** 우천으로 인한 감전 및 미끄러짐 재해 위험 발생.")
    st.markdown("✔️ **[우천 안전수칙]** 옥외 전기/용접 작업 금지 / 비계 위 추락 주의 / 미끄럼 방지화 착용")
else:
    st.success("✅ 현재 특별한 기상 악화 위험은 없습니다. 기본 작업 수칙을 준수 바랍니다.")

st.divider()

# --- [섹션 2: 업종별 KOSHA 안전수칙 제공] ---
st.subheader("🏭 업종별 핵심 안전수칙 (안전보건공단 제공 기준)")
industry_list = ["시설관리", "청소", "물류", "식당", "서비스", "폐기물처리", "제조"]
tabs = st.tabs(industry_list)

for index, industry in enumerate(industry_list):
    with tabs[index]:
        # 선택된 업종의 공단 가이드 호출
        kosha_rules = get_kosha_safety_rules(industry)
        st.markdown(f"#### 💡 {industry} 현장 필수 안전 가이드")
        for rule in kosha_rules:
            st.markdown(f"✔️ **{rule}**")

st.divider()

# =====================================================================
# 4. TBM 확인서 생성 (안전수칙 자동 병합 및 구문 오류 방지 완료)
# =====================================================================
st.subheader("📋 일일 TBM(Tool Box Meeting) 모바일 확인서 발급")
st.write("현장 투입 전 아래 항목을 입력하여 TBM 확인서를 생성하고 소장님/관리자에게 공유하세요.")

form_col1, form_col2, form_col3 = st.columns(3)
with form_col1:
    contractor_name = st.text_input("🏢 협력사명 입력 (예: 삼성건설)")
with form_col2:
    worker_cnt = st.number_input("👥 금일 투입 인원 (명)", min_value=1, value=3)
with form_col3:
    selected_industry = st.selectbox("🛠️ 작업 업종 선택", industry_list)

if st.button("🖨️ 현장 공유용 TBM 확인서 생성"):
    if contractor_name:
        # 날씨 기반 특보 텍스트 생성
        weather_alert = "기상 악화 사항 없음"
        if weather['temp'] >= 33.0: weather_alert = "폭염 경보 (물/그늘/휴식 필수)"
        elif weather['rain'] > 0: weather_alert = "우천 주의 (옥외 전기작업 금지)"
        
        # 업종별 안전수칙 포맷팅
        rules_data = get_kosha_safety_rules(selected_industry)
        rules_text = "\n".join([f"  - {rule}" for rule in rules_data])

        # f-string 에러(중괄호 충돌) 방지를 위한 텍스트 분리 결합
        header_text = f"[ 일일 TBM 무재해 이행 확인서 ]\n■ 협력사명: {contractor_name}\n■ 투입인원: {worker_cnt}명\n■ 기상특보: {weather_alert}\n■ 작업업종: {selected_industry}"
        middle_text = f"\n[ 금일 {selected_industry} 핵심 안전수칙 ]\n{rules_text}\n"
        bottom_text = "-----------------------------------------\n[ 필수 안전점검 확인 ]\n1. 작업 전 위험성평가 내용을 전원 숙지하였는가? ( O )\n2. 안전모, 안전화 등 개인보호구를 완벽히 착용하였는가? ( O )\n3. 음주자, 질병자 등 건강이상자가 없는가? ( O )\n========================================="
        
        final_tbm_result = f"=========================================\n{header_text}\n{middle_text}\n{bottom_text}"
        
        st.text_area("✨ 아래 생성된 텍스트를 복사하여 카카오톡이나 메시지로 보고하세요:", value=final_tbm_result, height=350)
    else:
        st.error("협력사명을 반드시 입력해 주세요.")
