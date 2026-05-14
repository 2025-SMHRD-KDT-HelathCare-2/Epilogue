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

# 샘플 데이터 제공
sample_text = """
[이메일 - 2024.10.15]
삼성생명 무배당 종신보험 갱신 안내드립니다.
가입자: 홍길동 (901231-1234567)
수익자: 배우자
연 보험료: 1,200,000원

[카드 결제 내역 - 2024.11]
- Netflix 정기결제 17,000원
- 멜론 정기결제 10,900원
- 쿠팡 와우 멤버십 7,890원

[SNS 마지막 게시글]
가족들 모두 사랑한다. 잘 지내길.
"""

text_input = st.text_area(
    "디지털 기록 텍스트를 붙여넣으세요",
    value=sample_text,
    height=300,
    help="이메일, SNS 게시글, 결제내역 등을 자유롭게 입력"
)

# =========================================================
# 분석 실행
# =========================================================
st.markdown("---")
st.subheader("2️⃣ AI 분석")

if st.button("🚀 분석 시작", type="primary"):
    if not text_input.strip():
        st.warning("텍스트를 입력해주세요.")
    else:
        # Step 1: 비식별화
        with st.spinner("개인정보 비식별화 중..."):
            cleaned = clean_text(text_input)
            masked = mask_personal_info(cleaned)
        
        with st.expander("🔒 비식별화된 텍스트 보기"):
            st.text(masked)
        
        # Step 2: LLM 분석
        with st.spinner("Gemini 2.5 flash 분석 중... (15~30초 소요)"):
            result = gemini.extract_digital_assets(masked)
        
        # 결과 표시
        st.markdown("### 📊 분석 결과")
        
        # 보험 정보
        if result.get("insurance"):
            st.markdown("#### 🏦 보험 정보")
            for ins in result["insurance"]:
                st.write(
                    f"- **{ins.get('company', 'N/A')}** | "
                    f"{ins.get('product', 'N/A')} | "
                    f"수익자: {ins.get('beneficiary', 'N/A')}"
                )
        
        # 구독 서비스
        if result.get("subscriptions"):
            st.markdown("#### 📺 구독 서비스 (해지 권장)")
            for sub in result["subscriptions"]:
                st.write(
                    f"- **{sub.get('name', 'N/A')}** | "
                    f"{sub.get('fee', 'N/A')} / {sub.get('cycle', 'N/A')}"
                )
        
        # 유언/추모
        if result.get("wills"):
            st.markdown("#### 💌 유언/추모 메시지")
            for will in result["wills"]:
                st.info(will)
        
        # JSON 원본
        with st.expander("📄 전체 JSON 보기"):
            st.json(result)
        
        # 세션 저장
        st.session_state["last_report"] = result
 
        