"""
=========================================================
Streamlit 메인 페이지
=========================================================

[Streamlit이란?]
파이썬 코드만으로 웹 앱을 만들 수 있는 프레임워크.

[기본 구조]
- st.title(): 큰 제목
- st.write(): 일반 텍스트
- st.button(): 버튼
- st.file_uploader(): 파일 업로드
- st.image(): 이미지 표시

[멀티페이지 구조]
pages/ 폴더에 파일을 두면 자동으로 사이드바 메뉴가 생성됨.
파일명 앞에 숫자(1_, 2_)를 붙이면 순서 지정 가능.
"""

import streamlit as st

# 페이지 설정 (반드시 첫 번째 Streamlit 명령으로!)
st.set_page_config(
    page_title="Epilogue : 유품 및 디지털 유산 통합 정리 솔루션",
    page_icon="🕊️",
    layout="wide",  # wide=가로 전체 사용, centered=가운데 정렬
    initial_sidebar_state="expanded"  # 사이드바 펼친 상태로 시작
)

# 메인 제목
st.title("🕊️ 유품 및 디지털 유산 통합 정리 솔루션")
st.markdown("##### *AI 기반 플랫폼 Epilogue*")
st.markdown("---")

# 2열 레이아웃
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🎯 서비스 소개
    
    1인 가구와 고독사 증가에 따른 사후 정리 공백 문제를 
    AI로 해결하는 통합 솔루션입니다.
    
    **유족의 행정적·심리적 부담을 혁신적으로 완화**합니다.
    """)

with col2:
    st.markdown("""
    ### 📊 사회적 배경
    
    - **1인 가구**: 전체 가구의 34.5%
    - **고독사**: 매년 3,000명 이상
    - **디지털 계정**: 1인당 평균 100개 이상
    """)

st.markdown("---")

# 기능 소개
st.markdown("### 🚀 주요 기능")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.info("""
    **📦 스마트 유품 카탈로그**
    
    Tensorflow + OCR로 유품을 
    자동 분류하고 명세서를 
    생성합니다.
    """)

with feature_col2:
    st.info("""
    **💼 디지털 자산 보고서**
    
    Gemini 2.5 Flash가 디지털 
    유산을 분석해 보험·구독 
    정보를 추출합니다.
    """)

with feature_col3:
    st.info("""
    **📋 통합 체크리스트**
    
    행정 절차 안내 + 비탄 
    케어 챗봇으로 유족을 
    돕습니다.
    """)

st.markdown("---")

# 사용 안내
st.success("👈 좌측 사이드바에서 원하는 기능을 선택하세요.")

# 푸터
st.markdown("---")
st.caption("© 2025 DiDimDol Team | K-Digital Training")


# 가상환경 활성화
# venv\Scripts\activate

# .env 파일에 Gemini API 키 입력
# GEMINI_API_KEY=실제_키_입력

# Streamlit 실행
# streamlit run app.py

# 브라우저에 http://localhost:8501이 열리고 좌측 사이드바에 3개 페이지가 나타납니다.