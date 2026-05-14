"""
페이지 3: 통합 체크리스트 + 비탄 케어 챗봇
"""

import streamlit as st
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.list_module import generate_action_list
from modules.chatbot_module import GriefChatbot

st.set_page_config(page_title="통합 체크리스트", page_icon="📋", layout="wide")
st.title("📋 통합 체크리스트 & 비탄 케어")

# =========================================================
# 📌 가독성 향상용 CSS (글씨 크기 ↑, 줄간격 ↑)
# =========================================================
st.markdown("""
<style>
/* 체크리스트 가이드 박스 */
.guide-box {
    font-size: 17px;
    line-height: 1.9;
    color: #2c2c2c;
    padding: 12px 16px;
    background-color: #fafafa;
    border-left: 4px solid #4CAF50;
    border-radius: 6px;
    margin-top: 8px;
    word-break: keep-all;   /* 한글 단어 단위 줄바꿈 */
}
.guide-box p {
    margin: 0 0 10px 0;
}
.guide-box ul {
    margin: 6px 0 10px 20px;
    padding-left: 0;
}
.guide-box li {
    margin-bottom: 6px;
}
/* 감지된 항목 라벨 */
.detected-label {
    font-size: 16px;
    font-weight: 600;
    color: #1f6feb;
    margin-bottom: 4px;
}
.detected-item {
    font-size: 15.5px;
    line-height: 1.8;
    margin-left: 10px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_chatbot():
    return GriefChatbot()


bot = load_chatbot()


# =========================================================
# 📌 가이드 텍스트를 읽기 좋게 정렬하는 헬퍼
# =========================================================
def format_guide_text(text: str) -> str:
    """
    LLM이 반환한 가이드 텍스트를 가독성 있는 HTML로 변환.
    - 마크다운 볼드(**) / 이탤릭(*) → HTML 태그
    - 문장 종결부(. ! ?) 뒤에서 줄바꿈
    - '-', '·', 숫자.' 으로 시작하는 항목은 리스트로 변환
    - 빈 줄 기준 문단 분리
    """
    if not text:
        return ""

    # 전처리: '**1.\n신고 의무자**' 처럼 별표 안에 줄바꿈이 낀 경우 합치기
    text = re.sub(r"\*\*(\d+\.)\s*\n\s*([^\n*]+)\*\*", r"**\1 \2**", text)

    lines = [ln.strip() for ln in text.split("\n")]
    html_parts = []
    in_ul = False

    for line in lines:
        if not line:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            continue

        # 리스트 항목 감지
        if re.match(r"^([-•·\*]|\d+[.)])\s+", line):
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            item_text = re.sub(r"^([-•·\*]|\d+[.)])\s+", "", line)
            html_parts.append(f"<li>{item_text}</li>")
        else:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            sentence_split = re.sub(r"(?<=[.!?。])\s+(?=[가-힣A-Z])", "<br>", line)
            html_parts.append(f"<p>{sentence_split}</p>")

    if in_ul:
        html_parts.append("</ul>")

    html = "".join(html_parts)

    # 🔥 마크다운 → HTML 변환
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)

    return f'<div class="guide-box">{html}</div>'


# 탭으로 두 기능 분리
tab1, tab2 = st.tabs(["📋 통합 체크리스트", "💬 비탄 케어 챗봇"])

# =========================================================
# 탭 1: 통합 체크리스트
# =========================================================
with tab1:
    st.subheader("CV·LLM 분석 결과를 기반으로 유족 안내 체크리스트를 생성합니다.")

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
            with st.spinner("맞춤형 체크리스트 생성 중... (30~40초)"):
                result = generate_action_list(
                    cv_result or {"items": []},
                    llm_result or {}
                )
            st.session_state["checklist_result"] = result  # 재실행 대비 저장

    # 저장된 결과가 있으면 항상 표시 (expander 토글로 사라지지 않도록)
    result = st.session_state.get("checklist_result")
    if result:
        if "error" in result:
            st.error(f"❌ 생성 실패: {result['error']}")
        else:
            st.success("✅ 체크리스트 생성 완료!")
            st.markdown("---")
            st.markdown("### ✅ 유족 안내 체크리스트")

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
                with st.expander(f"{icon}  {category}", expanded=True):
                    if data["items"]:
                        st.markdown(
                            '<div class="detected-label">📌 감지된 항목</div>',
                            unsafe_allow_html=True,
                        )
                        items_html = "".join(
                            [f'<div class="detected-item">• {item}</div>'
                             for item in data["items"]]
                        )
                        st.markdown(items_html, unsafe_allow_html=True)
                        st.markdown("")  # 살짝 간격

                    # 🔥 핵심: 포맷팅된 가이드 출력
                    st.markdown(
                        format_guide_text(data["guide"]),
                        unsafe_allow_html=True,
                    )

# =========================================================
# 탭 2: 비탄 케어 챗봇 (변경 없음)
# =========================================================
with tab2:
    st.subheader("💬 마음을 나눠주세요. 함께 들어드릴게요.")

    with st.expander("🆘 위기 시 즉시 연락처"):
        st.markdown("""
        - 자살예방상담전화: **1393** (24시간)
        - 정신건강위기상담전화: **1577-0199** (24시간)
        - 보건복지상담센터: **129**
        - 국가트라우마센터: **02-2204-0001**
        """)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_display = [
            {"role": "assistant", "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
        ]

    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("당신의 마음을 적어주세요..."):
        st.session_state.chat_display.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("..."):
                response = bot.chat(user_input, history=st.session_state.chat_history)

            st.write(response["text"])

            if response["is_crisis"]:
                st.error("⚠️ 위기 상황이 감지되었습니다. 위 전문기관에 꼭 연락해 주세요.")

        st.session_state.chat_history = response["history"]
        st.session_state.chat_display.append(
            {"role": "assistant", "content": response["text"]}
        )

    if st.session_state.chat_display and len(st.session_state.chat_display) > 1:
        if st.button("🔄 대화 다시 시작"):
            st.session_state.chat_history = []
            st.session_state.chat_display = [
                {"role": "assistant", "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
            ]
            st.rerun()
