"""
페이지 2: 디지털 자산 보고서 (LLM 기능)
"""

import streamlit as st
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.llm_module import GeminiAnalyzer
from utils.llm_preprocessing import mask_personal_info, clean_text

st.set_page_config(page_title="디지털 자산 보고서", page_icon="💼", layout="wide")
st.title("💼 디지털 자산 보고서")
st.markdown("고인의 디지털 기록을 분석해 보험·구독·유언 정보를 자동 추출합니다.")


# Gemini 모델 로딩
@st.cache_resource
def load_gemini():
    return GeminiAnalyzer()

try:
    gemini = load_gemini()
    st.success("✅ Gemini 2.5 flash 준비 완료")
except ValueError as e:
    st.error(str(e))
    st.stop() 


# =========================================================
# 텍스트 입력
# =========================================================
st.markdown("---")
st.subheader("1️⃣ 디지털 기록 입력")

sample_text = """
[이메일 - 2024.10.15]
삼성생명 무배당 종신보험 갱신 안내드립니다.
가입자: 홍길동
수익자: 배우자
연 보험료: 1,200,000원

[카드 결제 내역 - 2024.11]
- Netflix 정기결제 17,000원
- 멜론 정기결제 10,900원
- 쿠팡 와우 멤버십 7,890원
- 서울아산병원 45,000원
- 우리동네내과 15,000원

[SNS 마지막 게시글]
가족들 모두 사랑한다. 잘 지내길.

[의료 알림]
혈압약(암로디핀 5mg) 복용 지속 바랍니다.
다음 진료 예약일: 2025-02-20 오전 10시
"""

text_input = st.text_area(
    "디지털 기록 텍스트를 붙여넣으세요",
    value=sample_text,
    height=300,
    help="이메일, SNS 게시글, 결제내역 등을 자유롭게 입력"
)

# =========================================================
# 분석 카테고리 선택
# =========================================================
st.markdown("---")
st.subheader("2️⃣ 분석 항목 선택")

col1, col2, col3, col4 = st.columns(4)
with col1:
    do_subscription = st.checkbox("📺 구독 서비스", value=True)
with col2:
    do_insurance = st.checkbox("🏦 보험", value=True)
with col3:
    do_medical = st.checkbox("🏥 의료 기록", value=True)
with col4:
    do_card = st.checkbox("💳 카드 결제", value=True)

# =========================================================
# 분석 실행
# =========================================================
st.markdown("---")
st.subheader("3️⃣ AI 분석")

if st.button("🚀 분석 시작", type="primary"):
    if not text_input.strip():
        st.warning("텍스트를 입력해주세요.")
    else:
        # Step 1: 비식별화
        with st.spinner("개인정보 비식별화 중..."):
            cleaned = clean_text(text_input)
            masked = mask_personal_info(cleaned)

        results = {}

        # 구독 분석
        if do_subscription:
            with st.spinner("구독 서비스 분석 중..."):
                results["subscription"] = analyze_subscriptions(masked)

        # 보험 분석
        if do_insurance:
            with st.spinner("보험 정보 분석 중..."):
                results["insurance"] = analyze_insurance(masked)

        # 의료 분석
        if do_medical:
            with st.spinner("의료 기록 분석 중..."):
                results["medical"] = analyze_medical(masked)

        # 카드 분석
        if do_card:
            with st.spinner("카드 결제 분석 중..."):
                results["card"] = analyze_card(masked)

        st.success("✅ 분석 완료!")
        st.markdown("---")
        st.markdown("### 📊 분석 결과")

        # 구독 결과
        if "subscription" in results:
            sub = results["subscription"]
            st.markdown("#### 📺 구독 서비스 (해지 권장)")
            if sub and "error" not in sub:
                st.info(f"총 {sub.get('총_구독수', 0)}개 / 예상 월 지출: {sub.get('예상_월간_지출', 0):,}원")
                for item in sub.get("미해지_구독_목록", []):
                    st.write(
                        f"- **{item.get('서비스명')}** | "
                        f"{item.get('월결제금액', 0):,}원 | "
                        f"우선순위: {item.get('우선순위')} | "
                        f"{item.get('해지방법')}"
                    )
            else:
                st.error("구독 분석 실패")

        # 보험 결과
        if "insurance" in results:
            ins = results["insurance"]
            st.markdown("#### 🏦 보험 정보")
            if ins and "error" not in ins:
                st.info(f"총 {ins.get('총_보험수', 0)}개 / 청구 가능: {ins.get('청구가능_보험수', 0)}개")
                for item in ins.get("보험_목록", []):
                    st.write(
                        f"- **{item.get('보험사')}** {item.get('보험종류')} | "
                        f"월 {item.get('월납입료', 0):,}원 | "
                        f"청구가능: {'✅' if item.get('청구가능여부') else '❌'} | "
                        f"☎ {item.get('고객센터')}"
                    )
            else:
                st.error("보험 분석 실패")

        # 의료 결과
        if "medical" in results:
            med = results["medical"]
            st.markdown("#### 🏥 의료 기록")
            if med and "error" not in med:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**복약 목록**")
                    for item in med.get("복약_목록", []):
                        st.write(f"- {item.get('약물명')} ({item.get('용도')}) - {item.get('복용시간')}")
                with col2:
                    st.markdown("**주요 진단**")
                    for d in med.get("주요_진단", []):
                        st.write(f"- {d}")
                    st.markdown("**담당 병원**")
                    for h in med.get("담당_병원", []):
                        st.write(f"- {h}")
            else:
                st.error("의료 분석 실패")

        # 카드 결과
        if "card" in results:
            card = results["card"]
            st.markdown("#### 💳 카드 결제")
            if card and "error" not in card:
                st.info(f"총 지출: {card.get('총_지출', 0):,}원")
                cat = card.get("카테고리별_지출", {})
                if cat:
                    cols = st.columns(len(cat))
                    for i, (k, v) in enumerate(cat.items()):
                        with cols[i]:
                            st.metric(k, f"{v:,}원")
            else:
                st.error("카드 분석 실패")

        # JSON 원본
        with st.expander("📄 전체 JSON 보기"):
            st.json(results)

        # 세션 저장
        st.session_state["last_report"] = result
 
        