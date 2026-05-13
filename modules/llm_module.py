import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# 환경변수 로드
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


# ── 내부 유틸 ─────────────────────────────────────────────
def _chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content


def _parse_json(text: str) -> dict:
    try:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        print(f"[경고] JSON 파싱 실패: {e}")
        return {"raw_response": text, "error": str(e)}


# ── 1. 구독 서비스 분석 ───────────────────────────────────
def analyze_subscriptions(llm_text: str) -> dict:
    prompt = f"""
아래는 고인의 구독 서비스 결제 알림 내역입니다.
각 구독 서비스별로 정리하여 유족이 해지해야 할 목록을 JSON으로 반환해주세요.
JSON만 반환하고 다른 텍스트는 쓰지 마세요.

[결제 내역]
{llm_text}

[출력 형식]
{{
  "미해지_구독_목록": [
    {{
      "서비스명": "Netflix",
      "월결제금액": 17000,
      "해지방법": "앱 또는 홈페이지에서 해지",
      "우선순위": "높음"
    }}
  ],
  "예상_월간_지출": 0,
  "총_구독수": 0
}}
"""
    return _parse_json(_chat(prompt))


# ── 2. 보험 분석 ──────────────────────────────────────────
def analyze_insurance(llm_text: str) -> dict:
    prompt = f"""
아래는 고인의 보험 관련 이메일 내역입니다.
유족이 청구할 수 있는 보험금과 유지 중인 보험 목록을 JSON으로 반환해주세요.
JSON만 반환하고 다른 텍스트는 쓰지 마세요.

[보험 내역]
{llm_text}

[출력 형식]
{{
  "보험_목록": [
    {{
      "보험사": "삼성생명",
      "보험종류": "종신보험",
      "증권번호": "1234567",
      "월납입료": 50000,
      "청구가능여부": true,
      "고객센터": "1588-0000"
    }}
  ],
  "총_보험수": 0,
  "청구가능_보험수": 0
}}
"""
    return _parse_json(_chat(prompt))


# ── 3. 의료 기록 분석 ─────────────────────────────────────
def analyze_medical(llm_text: str) -> dict:
    prompt = f"""
아래는 고인의 의료 관련 알림 내역입니다.
복약 중이던 약물, 주요 진단 내용, 담당 병원을 JSON으로 정리해주세요.
JSON만 반환하고 다른 텍스트는 쓰지 마세요.

[의료 내역]
{llm_text}

[출력 형식]
{{
  "복약_목록": [
    {{
      "약물명": "암로디핀 5mg",
      "용도": "혈압약",
      "복용시간": "오전 8시"
    }}
  ],
  "주요_진단": ["고혈압", "당뇨"],
  "담당_병원": ["서울아산병원", "우리동네내과"]
}}
"""
    return _parse_json(_chat(prompt))


# ── 4. 카드 결제 분석 ─────────────────────────────────────
def analyze_card(llm_text: str) -> dict:
    prompt = f"""
아래는 고인의 카드 결제 내역입니다.
의료비, 정기 지출, 주요 소비 패턴을 JSON으로 정리해주세요.
JSON만 반환하고 다른 텍스트는 쓰지 마세요.

[카드 결제 내역]
{llm_text}

[출력 형식]
{{
  "의료비_내역": [
    {{
      "병원명": "서울아산병원",
      "금액": 45000,
      "날짜": "2025-01-15"
    }}
  ],
  "카테고리별_지출": {{
    "의료": 0,
    "쇼핑": 0,
    "편의점": 0,
    "건강": 0
  }},
  "총_지출": 0
}}
"""
    return _parse_json(_chat(prompt))


# ── 5. 종합 보고서 생성 ───────────────────────────────────
def generate_report(all_results: dict) -> str:
    prompt = f"""
아래는 고인의 디지털 기록을 분석한 결과입니다.
유족이 이해하기 쉽도록 따뜻하고 명확한 한국어로 정리 보고서를 작성해주세요.

[분석 결과]
{json.dumps(all_results, ensure_ascii=False, indent=2)}

보고서에는 다음 내용을 포함해주세요:
1. 즉시 처리가 필요한 사항 (해지해야 할 구독, 청구 가능한 보험)
2. 의료 관련 정리 사항
3. 재정 정리 요약
4. 유족을 위한 안내 메시지

보고서 형식은 마크다운으로 작성해주세요.
"""
    return _chat(prompt)


# ── 6. 전체 파이프라인 ────────────────────────────────────
def run_llm_pipeline(preprocessed_data: dict) -> dict:
    """
    전처리된 데이터를 받아 전체 LLM 분석을 수행합니다.

    사용법:
        from utils.preprocessing import preprocess_all
        from modules.llm_module import run_llm_pipeline

        data = preprocess_all()
        result = run_llm_pipeline(data)
        print(result["report"])
    """
    llm_input = preprocessed_data.get("llm_input", {})
    results = {}

    print("[LLM 분석 시작]")

    if "subscription" in llm_input:
        print("  → 구독 서비스 분석 중...")
        results["subscription"] = analyze_subscriptions(llm_input["subscription"])

    if "insurance" in llm_input:
        print("  → 보험 분석 중...")
        results["insurance"] = analyze_insurance(llm_input["insurance"])

    if "medical" in llm_input:
        print("  → 의료 기록 분석 중...")
        results["medical"] = analyze_medical(llm_input["medical"])

    if "card" in llm_input:
        print("  → 카드 결제 분석 중...")
        results["card"] = analyze_card(llm_input["card"])

    print("  → 종합 보고서 생성 중...")
    results["report"] = generate_report(results)

    print("[LLM 분석 완료]")
    return results


# ── 테스트 실행 ───────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from utils.preprocessing import preprocess_all

    data = preprocess_all()
    result = run_llm_pipeline(data)

    print("\n[종합 보고서]")
    print(result["report"])