"""
=========================================================
modules/chatbot_module.py
=========================================================

[역할]
grief_guide.txt 기반 유족 멘탈케어 챗봇 로직.
국가트라우마센터 애도상담 매뉴얼을 시스템 프롬프트로 활용.

pages/ 담당자가 chat()을 호출하면 됨.

[사용 예시]
    from modules.chatbot_module import GriefChatbot

    bot = GriefChatbot()

    # 첫 메시지
    response = bot.chat("너무 힘들어요. 아무것도 하기 싫어요.")
    print(response["text"])           # 챗봇 응답
    print(response["is_crisis"])      # True면 위기 상황 → 전문기관 안내 포함
    print(response["history"])        # 전체 대화 기록 (Streamlit session_state에 저장)

    # 이어서 대화
    response = bot.chat("숨이 막히고 불안해요.", history=response["history"])
"""

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─────────────────────────────────────────────
# 위기 표현 키워드 (자해·자살 관련)
# ─────────────────────────────────────────────

_CRISIS_KEYWORDS = [
    "죽고 싶", "사라지고 싶", "없어지고 싶", "자해", "자살",
    "따라가고 싶", "살기 싫", "끝내고 싶", "스스로 목숨",
]

_CRISIS_RESPONSE = """
지금 많이 힘드신 마음이 느껴져서 걱정됩니다.
혼자 감당하기 너무 힘드실 때는 아래 전문기관에 연락해 주세요.
전문 상담사가 24시간 함께해 드립니다.

📞 자살예방상담전화: **1393** (24시간)
📞 정신건강위기상담전화: **1577-0199** (24시간)
📞 보건복지상담센터: **129**
📞 국가트라우마센터: **02-2204-0001**

지금 이 순간의 감정은 영원하지 않습니다.
곁에 있어 드리고 싶습니다. 천천히 이야기해 주세요.
"""


# ─────────────────────────────────────────────
# 시스템 프롬프트 구성
# ─────────────────────────────────────────────

def _build_system_prompt() -> str:
    grief_path = os.path.join(
        BASE_DIR, "data", "processed", "grief_care", "grief_guide.txt"
    )
    grief_guide = ""
    if os.path.exists(grief_path):
        with open(grief_path, encoding="utf-8") as f:
            grief_guide = f.read()

    system = f"""
당신은 사랑하는 사람을 잃은 유족을 위한 심리 케어 챗봇입니다.
국가트라우마센터 애도상담 매뉴얼을 바탕으로 응답합니다.

【역할과 한계】
- 감정 공감과 안정화 보조 역할을 합니다.
- 전문 의료·심리 치료를 대체하지 않습니다.
- 위기 신호 발견 시 전문기관 안내를 최우선으로 합니다.

【응답 원칙】
1. 사용자의 감정을 먼저 공감합니다. 해결책을 성급히 제시하지 않습니다.
2. 슬픔·죄책감·분노·무기력감은 사별 후 자연스러운 반응임을 안내합니다.
3. 사용자의 속도를 존중합니다. 반복되는 감정 표현도 자연스럽게 수용합니다.
4. 필요 시 복식호흡(4-3-5-3), 나비포옹법, 착지기법(5-4-3-2-1)을 제안합니다.
5. 응답은 따뜻하고 간결하게, 3~5문장 내외로 작성합니다.

【사용하면 안 되는 표현】
- "곧 괜찮아질 거예요"
- "시간이 약이에요"
- "극복해야 해요"
- "네 탓이 아니야" (일방적 단정)
- "다른 가족 생각해서라도 정신 차려"

【권장 표현】
- "지금 느끼시는 감정은 자연스러운 반응입니다."
- "지금은 스스로를 너무 몰아붙이지 않아도 괜찮습니다."
- "천천히 감당 가능한 만큼만 해도 괜찮습니다."

【안정화 기법 안내 방법】
복식호흡(4-3-5-3):
  4초 들이마시기 → 3초 멈추기 → 5초 천천히 내쉬기 → 3초 멈추기 (4회 반복)

착지기법(5-4-3-2-1):
  보이는 것 5가지 → 들리는 것 4가지 → 만져지는 것 3가지 →
  냄새 2가지 → 맛 1가지 순서로 인식하기

나비포옹법:
  양팔을 가슴 앞 X자로 교차 → 어깨를 좌우 번갈아 가볍게 두드리며
  "지금 나는 안전하다" 속으로 되뇌기 (1~2분)

【참고 가이드 외 내용 처리】
- 가이드에 명확한 정보가 없는 행정·법률·의료 관련 질문은 AI 생성 내용임을 밝히고
  "정확하지 않을 수 있으니 아래 기관에 직접 확인하시길 권장합니다"라고 안내하세요.
- 확인 기관 예시:
  · 사망신고·행정 절차: 관할 주민센터 또는 정부24 (www.gov.kr)
  · 보험·금융: 금융감독원 1332
  · 상속·법률: 대한법률구조공단 132
  · 정신건강: 정신건강위기상담전화 1577-0199

【참고 가이드】
{grief_guide}
"""
    return system.strip()


# ─────────────────────────────────────────────
# 챗봇 클래스
# ─────────────────────────────────────────────

class GriefChatbot:
    """
    유족 멘탈케어 챗봇.

    Streamlit에서는 session_state에 history를 저장하고
    매 턴마다 chat()에 넘기는 방식으로 사용.
    """

    def __init__(self):
        self._system_prompt = _build_system_prompt()

    def _is_crisis(self, text: str) -> bool:
        """위기 표현 포함 여부 확인."""
        return any(kw in text for kw in _CRISIS_KEYWORDS)

    def chat(
        self,
        user_message: str,
        history: list | None = None
    ) -> dict:
        """
        사용자 메시지를 받아 챗봇 응답을 반환.

        Parameters
        ----------
        user_message : str
            사용자 입력 메시지.

        history : list | None
            이전 대화 기록.
            형식: [{"role": "user"|"model", "parts": ["..."]}]
            None이면 새 대화 시작.

        Returns
        -------
        dict
            {
              "text":       str,   # 챗봇 응답 텍스트
              "is_crisis":  bool,  # 위기 표현 감지 여부
              "history":    list   # 업데이트된 대화 기록 (session_state에 저장)
            }
        """
        if history is None:
            history = []

        # 위기 표현 감지 → 전문기관 안내 우선 출력
        if self._is_crisis(user_message):
            updated_history = history + [
                {"role": "user",  "parts": [user_message]},
                {"role": "model", "parts": [_CRISIS_RESPONSE]},
            ]
            return {
                "text":      _CRISIS_RESPONSE,
                "is_crisis": True,
                "history":   updated_history,
            }

        # 일반 대화: Gemini 호출
        try:
            conversation = f"{self._system_prompt}\n\n"
            for turn in history:
                role  = "사용자" if turn["role"] == "user" else "상담사"
                parts = turn["parts"][0] if turn["parts"] else ""
                conversation += f"{role}: {parts}\n"
            full_prompt = conversation + f"사용자: {user_message}\n상담사:"

            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            reply = response.text.strip()

            updated_history = history + [
                {"role": "user",  "parts": [user_message]},
                {"role": "model", "parts": [reply]},
            ]

            return {
                "text":      reply,
                "is_crisis": False,
                "history":   updated_history,
            }

        except Exception as e:
            error_msg = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            return {
                "text":      error_msg,
                "is_crisis": False,
                "history":   history,
            }


# ─────────────────────────────────────────────
# 단독 실행 테스트
# ─────────────────────────────────────────────

if __name__ == "__main__":
    bot = GriefChatbot()
    history = None

    test_messages = [
        "너무 힘들어요. 아무것도 하기 싫어요.",
        "제가 더 잘했어야 했는데 자꾸 후회돼요.",
        "숨이 막히고 불안해요.",
    ]

    for msg in test_messages:
        print(f"\n[사용자] {msg}")
        result = bot.chat(msg, history=history)
        print(f"[챗봇] {result['text']}")
        print(f"위기감지: {result['is_crisis']}")
        history = result["history"]