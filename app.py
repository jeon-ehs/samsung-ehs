import streamlit as st
import requests
import datetime

# =====================================================================
# 1. 페이지 기본 설정 및 커스텀 CSS (CLINE SR UI 디자인 복원)
# =====================================================================
st.set_page_config(page_title="협력사 일일 안전 포털", page_icon="🛡️", layout="wide")

def local_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
            html, body, [class*="st-"] { font-family: 'Noto Sans KR', sans-serif; background-color: #F0F4F8; }
            header {visibility: hidden;}
            .main .block-container { padding-top: 1.5rem; padding-bottom: 1rem; padding-left: 2rem; padding-right: 2rem; }
            /* 탭 UI 커스텀 */
            [data-testid="stTabs"] button { background-color: #F0F4F8; border-radius: 12px; color: #5A6478; font-weight: 500; padding: 10px 18px; margin-right: 8px; }
            [data-testid="stTabs"] button[aria-selected="true"] { background-color: #1565C0; color: white; font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)
local_css()

# =====================================================================
# 2. 데이터 호출 함수 (기상청 및 안전보건공단 API 뼈대)
# =====================================================================
@st.cache_data(ttl=3600)
def get_current_weather():
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
            response = requests.get(url, params=params)
            items = response.json()['response']['body']['items']['item']
            weather_data = {}
            for item in items:
                if item['category'] == 'T1H': weather_data['temp'] = float(item['obsrValue'])
                elif item['category'] == 'RN1': weather_data['rain'] = float(item['obsrValue'])
                elif item['category'] == 'REH': weather_data['humid'] = float(item['obsrValue'])
            return weather_data
        else:
            # API 키가 세팅되기 전까지 작동 가능한 임시 데모용 날씨
            return {'temp': 34.5, 'humid': 70.0, 'rain': 0.0} 
    except Exception as e:
        return None

@st.cache_data(ttl=86400)
def get_kosha_safety_info(industry_keyword):
    # 공단 API 연동 및 UI 표출용 업종별 핵심 안전수칙 데이터베이스
    rules_db = {
        "시설관리": ["추락 방지: 2m 이상 고소작업 시 안전대/안전모 착용 필수", "감전 예방: 정비 전 전원차단 및 LOTO 조치 확행"],
        "청소": ["전도 방지: 작업 구간 '미끄럼 주의' 표지판 설치 및 미끄럼방지화 착용", "화학물질: 세제 혼합 금지 및 MSDS 경고표지 준수"],
        "물류": ["충돌 예방: 지게차 작업 반경 내 보행자 절대 출입 금지", "낙하 방지: 고단 랙 적재 시 랩핑 고정 철저"],
        "식당": ["화상 예방: 방열장갑 착용 및 튀김기름 온도 관리 철저", "전도 방지: 바닥 물기/기름기 즉시 제거 및 미끄럼 방지 장화 착용"],
        "서비스": ["감정노동: 문제상황 발생 시 관리자 지원 및 휴식 보장", "VDT 증후군: 50분 컴퓨터 작업 후 10분 휴식 및 스트레칭"],
        "폐기물처리": ["협착 예방: 파쇄기 정비 시 반드시 전원 차단(LOTO)", "자상 예방: 날카로운 물질 수거 시 절단 방지 특수 장갑 착용"],
        "제조": ["끼임 방지: 구동 회전체 방호덮개 임의 해제 절대 금지", "직업병 예방: 고소음/분진 발생 공정 시 귀마개 및 마스크 착용"]
    }
    return rules_db.get(industry_keyword, ["해당 업종의 데이터가 없습니다."])

# =====================================================================
# 3. 메인 대시보드 화면 렌더링
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ 협력사 일일 안전보건 정보 포털</h2>", unsafe_allow_html=True)
st.caption(f"📅 **오늘의 날짜:** {datetime.date.today().strftime('%Y년 %m월 %d일')}")

# --- [날씨 및 안전 가이드] ---
st.subheader("📡 현장 실시간 기상 및 맞춤형 안전 지침 (수원 기준)")
weather = get_current_weather()
if weather:
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ 현재 기온", f"{weather['temp']} ℃")
    col2.metric("💧 현재 습도", f"{weather['humid']} %")
    col3.metric("☔ 1시간 강수량", f"{weather['rain']} mm")
    
    if weather['temp'] >= 33.0:
        st.error("🚨 **[폭염 경보]** 온열질환 발생 위험이 매우 높습니다. 옥외작업 제한 권고.")
        with st.expander("👉 온열질환 예방 3대 수칙 상세 보기"):
            st.markdown("- **물:** 시원하고 깨끗한 물 규칙적 제공\n- **그늘:** 햇빛 차단 휴식 공간 마련\n- **휴식:** 1시간 주기 15분 이상 휴식")
    elif weather['temp'] <= -5.0:
        st.info("🚨 **[한파 주의]** 동상, 저체온증 및 빙판길 전도 재해 주의.")
    elif weather['rain'] > 0:
        st.warning("☔ **[강우 주의]** 감전 및 미끄러짐 재해 위험 발생. 옥외 작업 통제")
    else:
        st.success("✅ 기상에 따른 특별 재해 위험은 낮습니다. 기본 수칙을 준수하세요.")

st.divider()

# --- [업종별 탭 메뉴] ---
st.subheader("🏭 업종별 핵심 안전수칙 가이드")
industry_list = ["시설관리", "청소", "물류", "식당", "서비스", "폐기물처리", "제조"]
tabs = st.tabs(industry_list)

for index, industry in enumerate(industry_list):
    with tabs[index]:
        kosha_data = get_kosha_safety_info(industry)
        st.markdown(f"#### 💡 {industry} 현장 안전보건 가이드")
        for item in kosha_data:
            st.info(f"✔️ {item}")

st.divider()

# =====================================================================
# 4. TBM 서명 카드 (업종 자동 연동 및 이중 중괄호 닫기 에러 수정)
# =====================================================================
st.subheader("📋 일일 TBM(Tool Box Meeting) 모바일 확인서")
c1, c2, c3 = st.columns(3)
with c1:
    contractor_name = st.text_input("협력사명을 입력하세요 (예: 삼성안전)")
with c2:
    worker_cnt = st.number_input("금일 작업 투입 인원 (명)", min_value=1, value=3)
with c3:
    selected_industry = st.selectbox("작업 업종을 선택하세요", industry_list)

if st.button("🖨️ TBM 확인서 텍스트 생성"):
    if contractor_name:
        # 선택된 업종의 안전수칙 텍스트 변환
        tbm_rules = get_kosha_safety_info(selected_industry)
        safety_rules_text = "\n".join([f"  - {rule}" for rule in tbm_rules])

        # 문법 충돌 예방을 위해 변수 영역과 고정 문자 영역 분리 조립
        header_text = f"[ 일일 TBM 무재해 이행 확인서 ]\n■ 협력사명: {contractor_name} (투입인원: {worker_cnt}명)\n■ 작업업종: {selected_industry}"
        rules_section = f"[ 금일 {selected_industry} 핵심 안전수칙 ]\n{safety_rules_text}"
        body_text = "-----------------------------------------\n[ 필수 안전점검 확인 ]\n1. 작업 전 위험성평가 내용을 전원 숙지하였는가? ( O )\n2. 안전모, 안전화 등 개인보호구를 완벽히 착용하였는가? ( O )\n3. 음주자, 질병자 등 건강이상자가 없는가? ( O )"
        
        tbm_result = f"=========================================\n{header_text}\n\n{rules_section}\n\n{body_text}\n========================================="
        
        st.text_area("현장 소장님/관리자께 아래 내용을 복사하여 공유하세요:", value=tbm_result, height=350)
    else:
        st.error("협력사명을 먼저 입력해 주세요.")
