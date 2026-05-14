"""
=========================================================
modules/list_module.py
=========================================================

[역할]
CV / LLM 결과 JSON을 받아 카테고리별 가이드 섹션을 추출하고
Gemini를 한 번만 호출하여 유족 안내 체크리스트를 반환.

pages/ 담당자가 generate_action_list()를 호출하면 됨.

[사용 예시]
    from modules.list_module import generate_action_list

    cv_result  = {"items": [{"label": "냉장고"}, {"label": "반지"}]}
    llm_result = {
        "subscription": {"미해지_구독_목록": [{"서비스명": "Netflix", "월결제금액": 17000}]},
        "insurance":    {"보험_목록": [{"보험사": "삼성생명", "보험종류": "종신보험", "청구가능여부": True}]},
    }

    result = generate_action_list(cv_result, llm_result)
    # result: {
    #   "사망신고": {"items": [], "guide": "..."},
    #   "안심상속": {"items": [], "guide": "..."},
    #   "귀중품":   {"items": ["반지"], "guide": "..."},
    #   "가전":     {"items": ["냉장고"], "guide": "폐가전 무상방문수거(1599-0903)..."},
    #   "보험":     {"items": ["삼성생명 종신보험 (청구가능)"], "guide": "..."},
    #   "구독":     {"items": ["Netflix (월 17,000원)"], "guide": "..."},
    # }
"""

import os
import json
import time
from google import genai
from dotenv import load_dotenv

from utils.list_preprocessing import (
    load_all_guides,
    classify_physical_items,
    classify_digital_assets,
    build_context_for_gemini,
)

load_dotenv()
_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

# 체크리스트 출력 순서
CATEGORY_ORDER = ["사망신고", "안심상속", "귀중품", "서류", "추억물품", "가전", "폐기물", "보험", "구독", "계정"]


# ─────────────────────────────────────────────
# 프롬프트 구성
# ─────────────────────────────────────────────

def _build_prompt(context: dict) -> str:
    """
    모든 카테고리를 한 번에 처리하는 프롬프트 생성.
    카테고리별 가이드 섹션을 명확히 구분하여 전달.
    """
    lines = []
    lines.append("""
당신은 사망한 분의 유족을 위한 유품 및 디지털 유산 정리 안내 시스템입니다.
아래에 카테고리별로 [인식된 항목]과 [가이드]가 주어집니다.
각 카테고리에 대해 가이드 내용을 반드시 기반으로 유족 안내 문구를 작성하세요.

[작성 원칙]
- 가이드에 있는 절차, 구비서류, 연락처, 주의사항을 빠짐없이 포함하세요.
- 가이드에 있는 연락처와 전화번호는 반드시 그대로 포함하세요.
- 가이드에 없는 내용을 추가할 경우 끝에 "※ 위 내용 중 일부는 AI가 생성한 참고 정보로 정확하지 않을 수 있습니다. 반드시 해당 기관에 직접 확인하세요." 문구를 추가하세요.
- 사망신고, 안심상속 카테고리는 가이드 내용이 충분하므로 AI 경고 문구를 붙이지 마세요.
- 추억물품 카테고리는 따뜻한 위로 중심으로만 작성하고, 연락처와 AI 경고 문구는 절대 포함하지 마세요.
- 유족의 심리적 부담을 고려해 따뜻하고 명확한 문체로 작성하세요.

[출력 형식 - 반드시 JSON만 출력, 다른 텍스트 없음]
{
  "카테고리명": {
    "guide": "안내 문구"
  },
  ...
}
""")

    for category, data in context.items():
        items     = data["items"]
        raw_guide = data["raw_guide"]
        items_str = ", ".join(items) if items else "해당 없음"

        lines.append(f"{'='*50}")
        lines.append(f"## 카테고리: {category}")
        lines.append(f"[인식된 항목] {items_str}")
        lines.append(f"[가이드]\n{raw_guide}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 메인 함수
# ─────────────────────────────────────────────

def generate_action_list(cv_result: dict, llm_result: dict) -> dict:
    """
    CV·LLM 결과를 받아 유족 안내 체크리스트를 반환.

    Parameters
    ----------
    cv_result : dict
        YOLO CV 모듈 결과.
    llm_result : dict
        run_llm_pipeline() 반환값.

    Returns
    -------
    dict
        순서 고정된 카테고리별 안내 체크리스트.
        {
          "사망신고": {"items": [], "guide": "..."},
          "안심상속": {"items": [], "guide": "..."},
          "가전":     {"items": ["냉장고"], "guide": "..."},
          ...
        }
        오류 발생 시 {"error": "메시지"} 반환.
    """
    # 1. 분류
    physical = classify_physical_items(cv_result)
    digital  = classify_digital_assets(llm_result)

    # 2. 가이드 로드 + 카테고리별 섹션 추출
    guides  = load_all_guides()
    context = build_context_for_gemini(physical, digital, guides)

    # 3. Gemini 단일 호출
    prompt = _build_prompt(context)

    gemini_result = {}
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(5)
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw_text = response.text.strip()

            # JSON 펜스 제거
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            gemini_result = json.loads(raw_text)
            break
        except json.JSONDecodeError:
            gemini_result = {"error": f"JSON 파싱 실패: {raw_text[:200]}"}
            break
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}

    # 4. 순서 고정하여 결과 조합
    result = {}
    for category in CATEGORY_ORDER:
        if category not in context:
            continue
        guide_text = gemini_result.get(category, {}).get("guide", "안내 생성 실패")
        result[category] = {
            "items": context[category]["items"],
            "guide": guide_text,
        }

    return result


# ─────────────────────────────────────────────
# 단독 실행 테스트
# ─────────────────────────────────────────────

if __name__ == "__main__":
    sample_cv = {
        "items": [
            {"label": "냉장고",   "confidence": 0.92},
            {"label": "반지",     "confidence": 0.85},
            {"label": "사진앨범", "confidence": 0.78},
            {"label": "이불",     "confidence": 0.70},
        ]
    }
    sample_llm = {
        "subscription": {
            "미해지_구독_목록": [
                {"서비스명": "Netflix", "월결제금액": 17000},
                {"서비스명": "멜론",    "월결제금액": 10900},
            ]
        },
        "insurance": {
            "보험_목록": [
                {"보험사": "삼성생명", "보험종류": "종신보험", "고객센터": "1588-3114", "청구가능여부": True},
            ]
        }
    }

    import pprint
    result = generate_action_list(sample_cv, sample_llm)
    pprint.pprint(result)