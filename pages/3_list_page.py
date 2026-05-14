"""
페이지 3: 통합 체크리스트 + 비탄 케어 챗봇
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.list_module import generate_action_list
from modules.chatbot_module import GriefChatbot

st.set_page_config(page_title="통합 체크리스트", page_icon="📋", layout="wide")
st.title("📋 통합 체크리스트 & 비탄 케어")


@st.cache_resource
def load_chatbot():
    return GriefChatbot()


bot = load_chatbot()

# 탭으로 두 기능 분리
tab1, tab2 = st.tabs(["📋 통합 체크리스트", "💬 비탄 케어 챗봇"])

# =========================================================
# 탭 1: 통합 체크리스트
# =========================================================
with tab1:
    st.subheader("CV·LLM 분석 결과를 기반으로 유족 안내 체크리스트를 생성합니다.")

    # 이전 페이지에서 저장된 결과 확인
    cv_result = st.session_state.get("cv_result")
    llm_result = st.session_state.get("last_report")

    col1, col2 = st.columns(2)
    with col1:
        if cv_result:
            st.success("✅ CV 분석 결과 로드됨")
        else:
            st.warning("⚠️ CV 분석 결과 없음 (페이지 1에서 먼저 실행)")
    with col2:
        if llm_result:
            st.success("✅ LLM 분석 결과 로드됨")
        else:
            st.warning("⚠️ LLM 분석 결과 없음 (페이지 2에서 먼저 실행)")

    if st.button("📋 체크리스트 생성", type="primary"):
        if not cv_result and not llm_result:
            st.error("CV 또는 LLM 분석 결과가 필요합니다.")
        else:
            with st.spinner("맞춤형 체크리스트 생성 중... (10~20초)"):
                result = generate_action_list(
                    cv_result or {"items": []},
                    llm_result or {}
                )

            if "error" in result:
                st.error(f"❌ 생성 실패: {result['error']}")
            else:
                st.success("✅ 체크리스트 생성 완료!")
                st.markdown("---")
                st.markdown("### ✅ 유족 안내 체크리스트")

                # 카테고리별 아이콘
                icons = {
                    "사망신고":  "📝",
                    "안심상속":  "🏦",
                    "귀중품":    "💍",
                    "서류":      "📄",
                    "추억물품":  "💝",
                    "가전":      "🔌",
                    "폐기물":    "🗑️",
                    "보험":      "🏥",
                    "구독":      "📺",
                    "계정":      "👤",
                }

                for category, data in result.items():
                    icon = icons.get(category, "✔️")
                    with st.expander(f"{icon} {category}", expanded=True):
                        if data["items"]:
                            st.markdown("**[감지된 항목]**")
                            for item in data["items"]:
                                st.write(f"- {item}")
                            st.markdown("---")
                        st.markdown(data["guide"])

# =========================================================
# 탭 2: 비탄 케어 챗봇
# =========================================================
with tab2:
    st.subheader("💬 마음을 나눠주세요. 함께 들어드릴게요.")

    # 안전 안내
    with st.expander("🆘 위기 시 즉시 연락처"):
        st.markdown("""
        - 자살예방상담전화: **1393** (24시간)
        - 정신건강위기상담전화: **1577-0199** (24시간)
        - 보건복지상담센터: **129**
        - 국가트라우마센터: **02-2204-0001**
        """)

    # 채팅 기록 초기화
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_display = [
            {"role": "assistant", "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
        ]

    # 채팅 기록 표시
    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 사용자 입력
    if user_input := st.chat_input("당신의 마음을 적어주세요..."):
        # 사용자 메시지 표시
        st.session_state.chat_display.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.write(user_input)

        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("..."):
                response = bot.chat(user_input, history=st.session_state.chat_history)

            st.write(response["text"])

            # 위기 감지 시 경고
            if response["is_crisis"]:
                st.error("⚠️ 위기 상황이 감지되었습니다. 위 전문기관에 꼭 연락해 주세요.")

        # 대화 기록 업데이트
        st.session_state.chat_history = response["history"]
        st.session_state.chat_display.append(
            {"role": "assistant", "content": response["text"]}
        )

    # 대화 초기화 버튼
    if st.session_state.chat_display and len(st.session_state.chat_display) > 1:
        if st.button("🔄 대화 다시 시작"):
            st.session_state.chat_history = []
            st.session_state.chat_display = [
                {"role": "assistant", "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
            ]
            st.rerun()