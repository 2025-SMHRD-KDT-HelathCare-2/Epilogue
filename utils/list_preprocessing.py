"""
=========================================================
utils/list_preprocessing.py
=========================================================

[역할]
data/ 폴더의 txt 가이드 파일을 읽어서
Gemini에게 넘길 수 있는 형태로 전처리하는 유틸리티 모듈.

list_module.py에서 호출하여 사용.

[체크리스트 구성 원칙]
- 사망신고 / 안심상속 원스톱서비스 : 항상 포함 (필수)
- 귀중품 / 추억물품 / 가전 / 폐기물 / 서류 : CV 결과에 해당 항목 있을 때만
- 보험                                      : LLM 결과에 보험 내역 있을 때만
- 구독 / 계정                               : LLM 결과에 해당 내역 있을 때만
"""

import os
import re


# ─────────────────────────────────────────────
# 가이드 파일 경로 설정
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

GUIDE_FILES = {
    "disposal":    os.path.join(DATA_DIR, "admin", "disposal_guide.txt"),    # 귀중품·추억물품·가전·폐기물·서류 처리
    "account":     os.path.join(DATA_DIR, "admin", "account_guide.txt"),     # 디지털 계정·구독 해지
    "inheritance": os.path.join(DATA_DIR, "admin", "inheritance_guide.txt"), # 사망신고·안심상속·보험·금융
    "grief":       os.path.join(DATA_DIR, "grief_care", "grief_guide.txt"),  # 애도 상담 가이드 (chatbot_module.py에서 사용)
}


def load_guide(key: str) -> str:
    path = GUIDE_FILES.get(key, "")
    if not path or not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_all_guides() -> dict:
    return {key: load_guide(key) for key in GUIDE_FILES}


# ─────────────────────────────────────────────
# 섹션 추출
# ─────────────────────────────────────────────

def extract_section(guide_text: str, section_name: str) -> str:
    """
    txt 가이드에서 특정 섹션만 추출.

    섹션 구분자: [섹션명] 형태
    구분선(===): 다음 섹션 시작 신호

    Parameters
    ----------
    guide_text : str
        가이드 파일 전체 텍스트
    section_name : str
        추출할 섹션명 (예: "가전", "Netflix 계정 해지")

    Returns
    -------
    str
        해당 섹션 텍스트. 없으면 빈 문자열.
    """
    pattern = rf'\[{re.escape(section_name)}\](.*?)(?==={{2,}}|\Z)'
    match = re.search(pattern, guide_text, re.DOTALL)
    if match:
        return f"[{section_name}]\n" + match.group(1).strip()
    return ""


def extract_sections_for_category(category: str, guides: dict, items: list = None) -> str:
    """
    카테고리에 해당하는 가이드 섹션만 추출하여 반환.
    구독 카테고리는 인식된 서비스명에 해당하는 섹션만 동적으로 추출.

    Parameters
    ----------
    category : str
        체크리스트 카테고리명
    guides : dict
        load_all_guides() 결과
    items : list
        인식된 항목 목록 (구독 카테고리에서 서비스명 매칭에 사용)

    Returns
    -------
    str
        해당 섹션 가이드 텍스트
    """
    if items is None:
        items = []

    disposal    = guides.get("disposal", "")
    account     = guides.get("account", "")
    inheritance = guides.get("inheritance", "")

    # ── 구독: 인식된 서비스명 기준으로 동적 추출 ──
    # 서비스명 키워드 → account_guide.txt 섹션명 매핑
    SUBSCRIPTION_SECTION_MAP = {
        "netflix":  "Netflix 계정 해지",
        "넷플릭스":  "Netflix 계정 해지",
        "youtube":  "YouTube Premium 해지",
        "유튜브":    "YouTube Premium 해지",
        "멜론":     "멜론 계정 및 구독 해지",
        "쿠팡":     "쿠팡 와우 해지",
    }

    if category == "구독":
        extracted = []
        for item in items:
            item_lower = item.lower()
            for keyword, section_name in SUBSCRIPTION_SECTION_MAP.items():
                if keyword in item_lower:
                    text = extract_section(account, section_name)
                    if text and text not in extracted:
                        extracted.append(text)
                    break
        return "\n\n".join(extracted)

    # ── 나머지 카테고리: 고정 섹션 매핑 ──────────
    CATEGORY_SECTION_MAP = {
        "사망신고":  [(inheritance, "사망 신고 절차")],
        "안심상속":  [(inheritance, "안심 상속 원스톱서비스 조회"),
                     (inheritance, "금융 자산 및 보험 정리")],
        "귀중품":    [(disposal, "귀중품")],
        "추억물품":  [(disposal, "추억물품")],
        "가전":      [(disposal, "가전")],
        "폐기물":    [(disposal, "폐기물")],
        "서류":      [(disposal, "서류")],
        "보험":      [(inheritance, "금융 자산 및 보험 정리")],
        "계정":      [(account, "Google 계정 정리"),
                     (account, "카카오톡 계정 정리"),
                     (account, "네이버 계정 정리")],
    }

    sections = CATEGORY_SECTION_MAP.get(category, [])
    extracted = []
    for guide_text, section_name in sections:
        text = extract_section(guide_text, section_name)
        if text:
            extracted.append(text)

    return "\n\n".join(extracted)


# ─────────────────────────────────────────────
# CV 결과 파싱
# ─────────────────────────────────────────────

# CV 모듈(YOLO)이 넘겨주는 JSON 형태 — CV 담당자 확인 후 수정 예정
# 현재 가정:
# {
#   "items": [
#     {"label": "냉장고", "confidence": 0.92},
#     {"label": "반지",   "confidence": 0.85}
#   ]
# }

PHYSICAL_CATEGORY_MAP = {
    "귀중품":   ["gold", "ring", "bankbook"],
    "추억물품": ["photo", "album"],
    "가전":     ["TV", "laptop", "fridge", "air_conditioning"],
    "폐기물":   ["glass_bottle", "pet_bottle", "styrofoam"],
    "서류":     ["paper_document", "paper"],
    "가구":     ["bed", "chair", "desk", "dining_table", "drawer", "nightstand", "sofa", "storage_cabinet", "vanity", "wardrobe"],
}


def classify_physical_items(cv_result: dict) -> dict:
    """
    CV 결과 JSON을 받아 물리적 유품을 카테고리별로 분류.

    Returns
    -------
    dict
        {"귀중품": ["반지"], "가전": ["냉장고"], ...}
        해당 항목이 있는 카테고리만 포함됨.
    """
    items = cv_result.get("items", [])
    labels = [item.get("label", "").strip() for item in items]

    result = {}
    for category, keywords in PHYSICAL_CATEGORY_MAP.items():
        matched = [label for label in labels if any(kw in label for kw in keywords)]
        if matched:
            result[category] = matched
    return result


# ─────────────────────────────────────────────
# LLM 결과 파싱
# ─────────────────────────────────────────────

# LLM 모듈(run_llm_pipeline) 반환값:
# {
#   "subscription": {
#     "미해지_구독_목록": [
#       {"서비스명": "Netflix", "월결제금액": 17000, "해지방법": "앱에서 해지"}
#     ]
#   },
#   "insurance": {
#     "보험_목록": [
#       {"보험사": "삼성생명", "보험종류": "종신보험", "고객센터": "1588-3114", "청구가능여부": true}
#     ]
#   }
# }


def classify_digital_assets(llm_result: dict) -> dict:
    """
    LLM run_llm_pipeline() 결과를 받아 유족이 정리해야 할
    디지털 자산을 카테고리별로 분류.

    의료(복약) / 카드 지출 내역은 유품 정리 대상이 아니므로 제외.

    Returns
    -------
    dict
        {
          "보험": ["삼성생명 종신보험 (청구가능)"],
          "구독": ["Netflix (월 17,000원)", "멜론 (월 10,900원)"],
          "계정": ["네이버", "카카오톡"]
        }
        해당 항목이 있는 카테고리만 포함됨.
    """
    result = {}

    # ── 보험 ─────────────────────────────────────
    insurance = llm_result.get("insurance", {})
    ins_list = insurance.get("보험_목록", [])
    if ins_list:
        items = []
        for ins in ins_list:
            company   = ins.get("보험사", "")
            kind      = ins.get("보험종류", "")
            claimable = ins.get("청구가능여부", None)
            label = f"{company} {kind}".strip()
            if claimable is True:
                label += " (청구가능)"
            if label:
                items.append(label)
        if items:
            result["보험"] = items

    # ── 구독 서비스 ──────────────────────────────
    subscription = llm_result.get("subscription", {})
    sub_list = subscription.get("미해지_구독_목록", [])
    if sub_list:
        items = []
        for s in sub_list:
            name  = s.get("서비스명", "")
            price = s.get("월결제금액", "")
            if name:
                label = f"{name} (월 {price:,}원)" if isinstance(price, int) and price else name
                items.append(label)
        if items:
            result["구독"] = items

    # ── 계정 ─────────────────────────────────────
    # LLM이 계정 분석 결과를 넘겨줄 경우 대비
    account = llm_result.get("account", {})
    acc_list = account.get("계정_목록", [])
    if acc_list:
        items = [a.get("서비스명", "") for a in acc_list if a.get("서비스명")]
        if items:
            result["계정"] = items

    return result


# ─────────────────────────────────────────────
# Gemini 컨텍스트 구성
# ─────────────────────────────────────────────

def build_context_for_gemini(
    physical_classified: dict,
    digital_classified: dict,
    guides: dict
) -> dict:
    """
    카테고리별로 해당 가이드 섹션만 추출하여 반환.

    Returns
    -------
    dict
        {
          "사망신고":  {"items": [], "raw_guide": "..."},
          "가전":      {"items": ["냉장고"], "raw_guide": "..."},
          ...
        }
    """
    context = {}

    # 항상 포함: 사망신고 · 안심상속
    for cat in ["사망신고", "안심상속"]:
        context[cat] = {
            "items": [],
            "raw_guide": extract_sections_for_category(cat, guides)
        }

    # 물리적 유품 (CV 결과)
    for cat, items in physical_classified.items():
        context[cat] = {
            "items": items,
            "raw_guide": extract_sections_for_category(cat, guides)
        }

    # 디지털 자산 (LLM 결과) — 구독은 items 넘겨서 해당 서비스만 추출
    for cat, items in digital_classified.items():
        context[cat] = {
            "items": items,
            "raw_guide": extract_sections_for_category(cat, guides, items)
        }

    return context