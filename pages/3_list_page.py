"""
페이지 3: 통합 체크리스트 + 비탄 케어 챗봇
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.llm_module import GeminiAnalyzer, ChecklistGenerator

st.set_page_config(page_title="통합 체크리스트", page_icon="📋", layout="wide")
st.title("📋 통합 체크리스트 & 비탄 케어")

@st.cache_resource
def load_models():
    gemini = GeminiAnalyzer()
    checklist = ChecklistGenerator(gemini)
    return gemini, checklist

gemini, checklist_gen = load_models()

# 탭으로 두 기능 분리
tab1, tab2 = st.tabs(["📋 행정 체크리스트", "💬 비탄 케어 챗봇"])

# =========================================================
# 탭 1: 행정 체크리스트
# =========================================================
with tab1:
    st.subheader("유족 상황을 입력하시면 맞춤형 체크리스트를 생성합니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        family_relation = st.selectbox(
            "가족 관계",
            ["배우자", "자녀", "부모", "형제자매", "기타"]
        )
        
        deceased_age = st.number_input(
            "고인 연령",
            min_value=0, max_value=120, value=75
        )
    
    with col2:
        asset_types = st.multiselect(
            "확인된 자산 종류 (복수 선택)",
            ["예금", "보험", "부동산", "주식", "연금", "디지털 자산"],
            default=["예금", "보험"]
        )
        
        has_chronic_illness = st.checkbox("만성질환 보유 (가족력 알림 포함)")
    
    if st.button("📋 체크리스트 생성", type="primary"):
        situation = {
            "가족관계": family_relation,
            "고인연령": deceased_age,
            "자산종류": asset_types,
            "만성질환": has_chronic_illness
        }
        
        with st.spinner("맞춤형 체크리스트 생성 중..."):
            result = checklist_gen.generate(situation)
        
        st.markdown("### ✅ 행정 체크리스트")
        st.markdown(result)

# =========================================================
# 탭 2: 비탄 케어 챗봇
# =========================================================
with tab2:
    st.subheader("💬 마음을 나눠주세요. 함께 들어드릴게요.")
    
    # 안전 안내
    with st.expander("🆘 위기 시 즉시 연락처"):
        st.markdown("""
        - 자살예방상담전화: **1393** (24시간)
        - 정신건강위기상담전화: **1577-0199**
        - 한국생명의전화: **1588-9191**
        """)
    
    # 채팅 기록 초기화
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
        ]
    
    # 채팅 기록 표시
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # 사용자 입력
    if user_input := st.chat_input("당신의 마음을 적어주세요..."):
        # 사용자 메시지 추가
        st.session_state.chat_messages.append(
            {"role": "user", "content": user_input}
        )
        
        with st.chat_message("user"):
            st.write(user_input)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("..."):
                response = gemini.generate_grief_care_response(user_input)
            st.write(response)
        
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": response}
        )