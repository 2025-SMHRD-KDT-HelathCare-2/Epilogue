"""
=========================================================
페이지 1: 스마트 유품 카탈로그 (CV 기능)
=========================================================

[역할]
사용자가 유품 이미지를 업로드하면 Keras 분류 모델 + EasyOCR 로 분석하여
카테고리·탐지 객체·추출 텍스트를 카탈로그 형태로 보여줍니다.

[연동 모듈]
- modules.cv_module.YOLODetector   : Keras 기반 이미지 분류기 (best_final.keras)
- modules.cv_module.OCRReader      : EasyOCR(한/영) 텍스트 추출기
- modules.cv_module.create_item_catalog : 위 두 모델 결과를 카탈로그 dict로 조립

[세션 저장 키]
- st.session_state["last_catalog"]  : 마지막 분석 결과 1건 (dict)
- st.session_state["catalog_list"]  : 누적 분석 결과 리스트 (list[dict])
  └ 페이지 3(통합 체크리스트)에서 CV 결과로 사용
"""

import os
import sys
import time
from datetime import datetime

import streamlit as st
from PIL import Image

# 상위 폴더(프로젝트 루트)를 import 경로에 추가
# → modules/, utils/ 패키지를 페이지에서 import 가능하게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cv_module import YOLODetector, OCRReader, create_item_catalog


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="유품 카탈로그",
    page_icon="📦",
    layout="wide",
)

st.title("📦 스마트 유품 카탈로그")
st.markdown("유품 이미지를 업로드하면 AI가 자동으로 분류하고 정리합니다.")


# =========================================================
# 상수 정의
# =========================================================

# 업로드 임시 저장 폴더 (프로젝트 루트 기준 절대경로 → 어디서 실행해도 안전)
SAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "samples",
)

# 카테고리별 이모지 매핑 (cv_preprocessing.CLASS_TO_CATEGORY 값과 매칭)
CATEGORY_EMOJI = {
    "귀중품":   "💎",
    "추억물품": "📷",
    "가전":     "📺",
    "폐기물":   "🗑️",
    "의료문서": "🏥",
    "서류":     "📄",
    "기타":     "📦",
}

# 허용 파일 확장자
ALLOWED_EXT = ["jpg", "jpeg", "png"]


# =========================================================
# 모델 로딩 (캐싱: 한 번만 로드해서 재사용)
# =========================================================

@st.cache_resource(show_spinner=False)
def load_models():
    """
    Keras 분류 모델 + EasyOCR 리더를 한 번만 로드하여 캐싱.

    [@st.cache_resource 란?]
    모델처럼 무거운 객체를 메모리에 보관하여 재사용하는 데코레이터.
    페이지를 새로고침하거나 다른 페이지로 이동했다 돌아와도 다시 로드하지 않음.
    → 첫 진입 시에만 수십 초 소요, 이후엔 즉시 사용 가능.

    Returns
    -------
    detector : YOLODetector
        best_final.keras 기반 이미지 분류기.
    ocr : OCRReader
        EasyOCR(ko, en) 기반 텍스트 추출기.
    """
    # YOLODetector 는 내부에서 data/cv_model/best_final.keras 를 자동 로드.
    # (cv_module.py 시그니처가 model_path=""  이므로 인자 없이 호출)
    detector = YOLODetector()
    ocr = OCRReader()
    return detector, ocr


# 최초 진입 시 모델 로딩 (스피너 표시)
with st.spinner("AI 모델 로딩 중... (최초 1회 30초 내외)"):
    try:
        detector, ocr = load_models()
    except Exception as e:
        st.error(f"❌ 모델 로딩 실패: {e}")
        st.stop()  # 모델 없이는 분석이 불가하므로 페이지 실행 중단

st.success("✅ 모델 준비 완료")


# =========================================================
# 세션 상태 초기화
# =========================================================
# catalog_list: 페이지 3(통합 체크리스트)에서 CV 결과로 활용하기 위한 누적 리스트
if "catalog_list" not in st.session_state:
    st.session_state["catalog_list"] = []


# =========================================================
# 1) 이미지 업로드
# =========================================================
st.markdown("---")
st.subheader("1️⃣ 유품 이미지 업로드")

uploaded_file = st.file_uploader(
    "이미지 파일을 선택하세요 (jpg, jpeg, png)",
    type=ALLOWED_EXT,
)


def _save_uploaded_file(file) -> str:
    """
    업로드된 파일을 디스크에 저장하고 절대경로를 반환.

    동일 파일명을 여러 번 업로드해도 충돌하지 않도록
    파일명 앞에 타임스탬프를 붙여 고유한 이름으로 저장한다.

    Parameters
    ----------
    file : UploadedFile
        st.file_uploader 가 반환한 파일 객체.

    Returns
    -------
    str
        저장된 파일의 절대경로.
    """
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.name}"
    save_path = os.path.join(SAMPLES_DIR, safe_name)
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    return save_path


def _render_objects(objects: list) -> None:
    """탐지된 객체를 신뢰도 진행바와 함께 표시."""
    if not objects:
        st.write("탐지된 객체 없음")
        return

    for obj in objects:
        conf = float(obj.get("confidence", 0.0))
        st.write(f"- **{obj['class']}** &nbsp;({conf * 100:.1f}%)")
        st.progress(min(max(conf, 0.0), 1.0))


def _render_texts(texts: list) -> None:
    """추출된 텍스트를 신뢰도와 함께 표시. 5개 초과 시 표 형태로."""
    if not texts:
        st.write("추출된 텍스트 없음")
        return

    if len(texts) > 5:
        # 텍스트가 많으면 표로 보여주는 게 가독성 좋음
        st.dataframe(
            [{"text": t["text"], "confidence": f"{t.get('confidence', 0)*100:.1f}%"}
             for t in texts],
            use_container_width=True,
            hide_index=True,
        )
    else:
        for txt in texts:
            conf = txt.get("confidence")
            if conf is not None:
                st.write(f"- {txt['text']} &nbsp;_({conf * 100:.1f}%)_")
            else:
                st.write(f"- {txt['text']}")


# =========================================================
# 2) 이미지 표시 & 분석
# =========================================================
if uploaded_file is not None:
    # 업로드 파일을 임시 경로에 저장 (모델이 파일 경로를 받기 때문)
    temp_path = _save_uploaded_file(uploaded_file)

    # 2열 레이아웃: 왼쪽 원본, 오른쪽 분석 결과
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📸 원본 이미지")
        # 저장된 경로로부터 다시 열어야 파일 포인터 문제 없음
        image = Image.open(temp_path)
        st.image(image, use_container_width=True)

        # 이미지 메타 정보(부가 안내)
        st.caption(
            f"파일명: `{uploaded_file.name}` &nbsp;|&nbsp; "
            f"크기: {image.size[0]} × {image.size[1]} px"
        )

    with col2:
        st.markdown("#### 🔍 분석 결과")

        # 분석 실행 버튼 (type='primary' 로 강조)
        if st.button("🚀 AI 분석 시작", type="primary", use_container_width=True):
            t0 = time.time()
            try:
                with st.spinner("분석 중... (30~40초 소요)"):
                    result = create_item_catalog(temp_path, detector, ocr)
            except Exception as e:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {e}")
                # 오류 시 저장된 임시 파일 정리
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                st.stop()

            elapsed = time.time() - t0

            # ── 카테고리 ────────────────────────────────────
            category = result.get("category", "기타")
            emoji = CATEGORY_EMOJI.get(category, "📦")
            st.markdown(f"### {emoji} 카테고리: **{category}**")
            st.caption(f"⏱️ 분석 소요 시간: {elapsed:.1f}초")

            # ── 탐지된 객체 ─────────────────────────────────
            st.markdown("**탐지된 객체:**")
            _render_objects(result.get("objects", []))

            # ── 추출된 텍스트 ───────────────────────────────
            st.markdown("**추출된 텍스트:**")
            _render_texts(result.get("extracted_texts", []))

                        # ── 세션 저장 ───────────────────────────────────
            # 🔑 페이지 3(통합 체크리스트)이 읽는 키와 정확히 맞춰야 합니다.
            #    list_module.classify_physical_items() 가 기대하는 형식:
            #      {"items": [{"label": "냉장고", "confidence": 0.92}, ...]}

            # (1) 페이지 3 입력용 — list_module 표준 형식
            cv_payload = {
                "items": [
                    {"label": o["class"], "confidence": o.get("confidence", 0.0)}
                    for o in result.get("objects", [])
                ],
                "texts": result.get("extracted_texts", []),
                "category": category,
            }

            # (2) 사이드바 미리보기용 — 파일명까지 포함한 확장 형식
            #     사이드바는 어떤 파일을 분석했는지 보여줘야 하므로 file 키가 필요합니다.
            catalog_entry = {
                **cv_payload,
                "file": uploaded_file.name,
            }

            # 단건(최근 1건) — 페이지 2에서 단건 참조용
            st.session_state["last_catalog"] = result

            # 누적 리스트 — 사이드바와 페이지 3 양쪽에서 사용
            st.session_state["catalog_list"].append(catalog_entry)

            # 누적된 모든 items 를 하나의 cv_result 로 병합
            # → 여러 사진을 분석했을 때 페이지 3 에서 한 번에 처리 가능
            merged_items = []
            for c in st.session_state["catalog_list"]:
                merged_items.extend(c.get("items", []))
            st.session_state["cv_result"] = {"items": merged_items}

            st.success(
                f"✅ 카탈로그에 추가되었습니다. "
                f"(누적 {len(st.session_state['catalog_list'])}건)"
            )

else:
    st.info("👆 위에서 이미지를 업로드하세요.")


# =========================================================
# 3) 누적 카탈로그 미리보기 (사이드바)
# =========================================================
# 지금까지 분석한 결과들을 한눈에 확인하고, 필요하면 초기화할 수 있게 함.
# - dict.get("key", 기본값) 을 쓰는 이유:
#   세션에 저장된 항목 형식이 바뀌더라도 KeyError 로 페이지가 죽지 않게 하기 위함.
with st.sidebar:
    st.markdown("### 🗂️ 누적 카탈로그")
    catalog_list = st.session_state.get("catalog_list", [])
    st.metric("총 분석 건수", f"{len(catalog_list)}건")

    if catalog_list:
        # 최근 5건만 간단히 표시 (오래된 항목이 너무 많아지지 않게)
        for c in reversed(catalog_list[-5:]):
            category = c.get("category", "기타")
            file_name = c.get("file", "(파일명 없음)")
            emoji = CATEGORY_EMOJI.get(category, "📦")
            st.caption(f"{emoji} {category} — `{file_name}`")

        if st.button("🗑️ 카탈로그 초기화", use_container_width=True):
            st.session_state["catalog_list"] = []
            st.session_state.pop("last_catalog", None)
            st.session_state.pop("cv_result", None)  # 페이지 3 입력도 함께 비움
            st.rerun()

