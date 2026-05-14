"""
페이지 1: 스마트 유품 카탈로그 (CV 기능)
사용자가 유품 이미지를 업로드하면 YOLO+OCR로 분석합니다.
"""

import streamlit as st
import sys
import os
# from PIL import Image

# 상위 폴더의 modules를 import할 수 있도록 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from modules.cv_module import YOLODetector, OCRReader, create_item_catalog

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(page_title="유품 카탈로그", page_icon="📦", layout="wide")
st.title("📦 스마트 유품 카탈로그")
st.markdown("유품 이미지를 업로드하면 AI가 자동으로 분류하고 정리합니다.")

# =========================================================
# 모델 로딩 (캐싱: 한 번만 로드해서 재사용)
# =========================================================
'''
@st.cache_resource  # 이 데코레이터가 핵심!
def load_models():

     
    [@st.cache_resource란?]
    모델 같은 무거운 객체를 한 번 로딩하면 메모리에 보관.
    페이지를 새로고침해도 다시 로딩 안 함 → 속도 ↑ 
    
    
    detector = YOLODetector("yolov8n.pt")
    ocr = OCRReader()
    return detector, ocr

with st.spinner("AI 모델 로딩 중..."):
    detector, ocr = load_models()

st.success("✅ 모델 준비 완료") 
'''

# =========================================================
# 이미지 업로드
# =========================================================
st.markdown("---")
st.subheader("1️⃣ 유품 이미지 업로드")

'''
uploaded_file = st.file_uploader(
    "이미지 파일을 선택하세요 (jpg, png)",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # 임시 저장
    temp_path = f"data/samples/{uploaded_file.name}"
    os.makedirs("data/samples", exist_ok=True)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 2열 레이아웃
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📸 원본 이미지")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
    
    with col2:
        st.markdown("#### 🔍 분석 결과")
        
        # 분석 실행 버튼
        if st.button("🚀 AI 분석 시작", type="primary"):
            with st.spinner("분석 중... (10~20초 소요)"):
                # CV 모듈 호출
                result = create_item_catalog(temp_path, detector, ocr)
            
            # 카테고리 표시
            category_emoji = {
                "귀중품": "💎", "추억물품": "📷", "가전": "📺",
                "폐기물": "🗑️", "의료문서": "🏥"
            }
            emoji = category_emoji.get(result["category"], "📦")
            st.markdown(f"### {emoji} 카테고리: **{result['category']}**")
            
            # 탐지된 객체
            st.markdown("**탐지된 객체:**")
            if result["objects"]:
                for obj in result["objects"]:
                    st.write(
                        f"- {obj['class']} "
                        f"(신뢰도: {obj['confidence']*100:.1f}%)"
                    )
            else:
                st.write("탐지된 객체 없음")
            
            # 추출된 텍스트
            st.markdown("**추출된 텍스트:**")
            if result["extracted_texts"]:
                for txt in result["extracted_texts"]:
                    st.write(f"- {txt['text']}")
            else:
                st.write("추출된 텍스트 없음")
            
            # 결과를 세션에 저장 (다른 페이지에서 사용 가능)
            st.session_state["last_catalog"] = result

# 안내
else:
    st.info("👆 위에서 이미지를 업로드하세요.")

'''