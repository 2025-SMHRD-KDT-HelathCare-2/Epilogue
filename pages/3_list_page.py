"""
=========================================================
페이지 3: 통합 체크리스트 + 비탄 케어 챗봇 + PDF 저장
=========================================================

[이 페이지가 하는 일]
1) 페이지 1(CV)과 페이지 2(LLM)에서 분석한 결과를 가져와
   → list_module.generate_action_list() 로 유족 안내 체크리스트 생성
2) 생성된 체크리스트를 화면에 보기 좋게 표시
3) 깔끔한 한글 PDF 로 저장 (로컬 다운로드)
4) 비탄 케어 챗봇 탭에서 유족 심리 상담 지원

[세션 키 — 페이지 1/2와의 약속]
- "cv_result"        : 페이지 1 에서 저장한 CV 분석 결과 (필수 키: items)
- "llm_result"       : 페이지 2 에서 저장한 LLM 분석 결과
  (구버전 호환: "last_report" 도 함께 확인)
- "checklist_result" : 본 페이지에서 생성한 체크리스트 (PDF 저장 시 재사용)
"""

import os
import re
import sys
import io
from datetime import datetime

import streamlit as st

# 프로젝트 루트를 import 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.list_module import generate_action_list
from modules.chatbot_module import GriefChatbot


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(page_title="통합 체크리스트", page_icon="📋", layout="wide")
st.title("📋 통합 체크리스트 & 비탄 케어")


# =========================================================
# 📌 가독성 향상용 CSS
# (Streamlit 기본 폰트가 작고 한글이 빽빽해 보여서, 가이드 박스를 따로 스타일링)
# =========================================================
st.markdown("""
<style>
.guide-box {
    font-size: 17px;
    line-height: 1.9;
    color: #2c2c2c;
    padding: 12px 16px;
    background-color: #fafafa;
    border-left: 4px solid #4CAF50;
    border-radius: 6px;
    margin-top: 8px;
    word-break: keep-all;
}
.guide-box p { margin: 0 0 10px 0; }
.guide-box ul { margin: 6px 0 10px 20px; padding-left: 0; }
.guide-box li { margin-bottom: 6px; }
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


# =========================================================
# 챗봇 로드 (캐싱)
# — GriefChatbot 은 시스템 프롬프트 빌드 비용이 있으므로
#   페이지를 들락날락해도 한 번만 만들도록 cache_resource 사용
# =========================================================
@st.cache_resource
def load_chatbot():
    return GriefChatbot()


bot = load_chatbot()


# =========================================================
# 📌 가이드 텍스트 포맷터
# LLM 이 마크다운으로 반환한 가이드를 화면용 HTML 로 변환합니다.
# - **굵게**, *기울임* 같은 마크다운을 HTML 태그로 치환
# - '-', '·', '1.' 등으로 시작하는 줄은 <ul><li> 로 묶기
# - 문장 종결부에서 줄바꿈을 추가해 가독성 향상
# =========================================================
def format_guide_text(text: str) -> str:
    if not text:
        return ""

    # '**1.\n신고 의무자**' 처럼 별표 안에 줄바꿈이 낀 경우 합치기
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
            # 문장 종결부 뒤에서 줄바꿈 (한국어/영어 대문자 시작 기준)
            sentence_split = re.sub(r"(?<=[.!?。])\s+(?=[가-힣A-Z])", "<br>", line)
            html_parts.append(f"<p>{sentence_split}</p>")

    if in_ul:
        html_parts.append("</ul>")

    html = "".join(html_parts)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)

    return f'<div class="guide-box">{html}</div>'


# =========================================================
# 📌 PDF 생성 — 한글 안 깨지는 깔끔한 체크리스트 PDF
# =========================================================
# [원리 설명]
# reportlab 은 기본 폰트가 영문 전용이라 한글이 ■■■ 로 깨집니다.
# 따라서 OS 에 설치된 한글 TTF 폰트를 찾아 등록(pdfmetrics.registerFont) 해야 합니다.
# Windows: 맑은 고딕(malgun.ttf) — 거의 100% 설치되어 있음
# macOS  : 애플 SD 산돌고딕 / 나눔고딕
# Linux  : 나눔고딕 (apt install fonts-nanum)
# 폰트를 못 찾으면 사용자에게 안내하고 PDF 생성을 중단합니다.

def _find_korean_font() -> tuple[str | None, str | None]:
    """
    시스템에서 사용 가능한 한글 TTF 폰트 경로를 찾는다.
    Returns: (regular_path, bold_path) — bold 가 없으면 regular 로 대체
    """
    candidates = [
        # (regular, bold)
        (r"C:\Windows\Fonts\malgun.ttf",   r"C:\Windows\Fonts\malgunbd.ttf"),
        (r"C:\Windows\Fonts\NanumGothic.ttf", r"C:\Windows\Fonts\NanumGothicBold.ttf"),
        ("/Library/Fonts/AppleSDGothicNeo.ttc", None),
        ("/System/Library/Fonts/AppleSDGothicNeo.ttc", None),
        ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
         "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
        # 프로젝트 내부에 폰트를 두었을 경우의 폴백
        (os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "fonts", "D2Coding.ttf"),
         os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "fonts", "D2CodingBold.ttf")),
    ]
    for reg, bold in candidates:
        if reg and os.path.exists(reg):
            bold_path = bold if (bold and os.path.exists(bold)) else reg
            return reg, bold_path
    return None, None


def _strip_markdown(text: str) -> str:
    """
    PDF 본문용으로 마크다운 기호를 제거.
    (reportlab Paragraph 는 <b>, <i> 만 인식하므로 ** → <b> 로 변환)
    """
    if not text:
        return ""
    # **굵게** → <b>굵게</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # *기울임* → <i>기울임</i>  (단 ** 와 충돌 방지)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    # HTML 특수문자 escape (단, 우리가 만든 <b>,<i> 는 보존)
    # → Paragraph 는 & < > 를 자동 이스케이프하므로 여기선 그대로 둠
    return text


def build_checklist_pdf(checklist: dict) -> bytes | None:
    """
    체크리스트 dict 를 받아 PDF 바이트를 반환.
    한글 폰트를 찾지 못하면 None 반환.
    """
    # 지연 import — reportlab 미설치 환경에서도 페이지 자체는 열리도록
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
            HRFlowable,
        )
    except ImportError:
        st.error(
            "❌ PDF 생성을 위해 reportlab 이 필요합니다.\n"
            "터미널에서 `pip install reportlab` 을 실행해 주세요."
        )
        return None

    # 1) 한글 폰트 등록
    reg_path, bold_path = _find_korean_font()
    if reg_path is None:
        st.error(
            "❌ 한글 폰트를 찾지 못했습니다.\n\n"
            "다음 중 하나를 시도해 주세요:\n"
            "- Windows: 기본 설치된 맑은 고딕이 자동 사용됩니다.\n"
            "- Linux  : `sudo apt install fonts-nanum`\n"
            "- 또는 프로젝트의 `data/fonts/` 폴더에 `D2Coding.ttf` 를 넣어주세요."
        )
        return None

    # registerFont 는 같은 이름을 두 번 등록해도 문제없음
    pdfmetrics.registerFont(TTFont("KFont", reg_path))
    pdfmetrics.registerFont(TTFont("KFont-Bold", bold_path))

    # 2) 스타일 정의 — 한글 폰트를 모든 스타일에 적용
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "KTitle", parent=styles["Title"],
        fontName="KFont-Bold", fontSize=22, leading=28,
        alignment=TA_LEFT, textColor=colors.HexColor("#2c3e50"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "KSub", parent=styles["Normal"],
        fontName="KFont", fontSize=11, leading=16,
        textColor=colors.HexColor("#7f8c8d"), spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        "KH2", parent=styles["Heading2"],
        fontName="KFont-Bold", fontSize=15, leading=22,
        textColor=colors.HexColor("#1f6feb"),
        spaceBefore=14, spaceAfter=6,
    )
    label_style = ParagraphStyle(
        "KLabel", parent=styles["Normal"],
        fontName="KFont-Bold", fontSize=11, leading=16,
        textColor=colors.HexColor("#34495e"), spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "KBody", parent=styles["Normal"],
        fontName="KFont", fontSize=10.5, leading=17,
        textColor=colors.HexColor("#2c2c2c"),
    )
    item_style = ParagraphStyle(
        "KItem", parent=body_style, leftIndent=10, spaceAfter=2,
    )

    # 3) PDF 빌드 (메모리 버퍼에 작성)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="유족 안내 체크리스트",
        author="Epilogue",
    )

    icons = {
        "사망신고": "■", "안심상속": "■", "귀중품": "■", "서류": "■",
        "추억물품": "■", "가전": "■", "폐기물": "■", "보험": "■",
        "구독": "■", "계정": "■",
    }
    # ↑ 이모지는 reportlab 기본 폰트가 지원하지 않을 수 있어 단순 기호로 통일.
    #   (한글 폰트만으로도 안전하게 렌더링되게 하기 위함)

    story = []
    story.append(Paragraph("🕊️ 유족 안내 체크리스트", title_style))
    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    story.append(Paragraph(
        f"생성일시: {now_str} &nbsp;|&nbsp; Epilogue — 유품 및 디지털 유산 통합 정리 솔루션",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 6))

    # 카테고리별 섹션
    for category, data in checklist.items():
        if not isinstance(data, dict):
            continue
        icon = icons.get(category, "■")
        story.append(Paragraph(f"{icon}  {category}", h2_style))

        # 감지된 항목
        items = data.get("items", [])
        if items:
            story.append(Paragraph("📌 감지된 항목", label_style))
            for it in items:
                story.append(Paragraph(f"• {it}", item_style))
            story.append(Spacer(1, 4))

        # 가이드 본문
        guide = _strip_markdown(data.get("guide", ""))
        # 줄바꿈 처리: reportlab Paragraph 는 <br/> 태그를 인식
        for para in guide.split("\n\n"):
            para = para.replace("\n", "<br/>")
            if para.strip():
                story.append(Paragraph(para, body_style))
                story.append(Spacer(1, 4))

        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.3,
                                color=colors.HexColor("#eeeeee")))

    # 푸터용 메모
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "※ 본 체크리스트는 AI 가 생성한 참고 자료입니다. "
        "정확한 처리를 위해서는 각 안내된 기관에 직접 확인해 주세요.",
        ParagraphStyle("Footer", parent=body_style, fontSize=9,
                       textColor=colors.HexColor("#888888")),
    ))

    doc.build(story)
    return buf.getvalue()


# =========================================================
# 탭 구성
# =========================================================
tab1, tab2 = st.tabs(["📋 통합 체크리스트", "💬 비탄 케어 챗봇"])


# =========================================================
# 탭 1: 통합 체크리스트
# =========================================================
with tab1:
    st.subheader("CV·LLM 분석 결과를 기반으로 유족 안내 체크리스트를 생성합니다.")

    # ─────────────────────────────────────────────────────
    # 🔑 페이지 1/2 와 약속된 세션 키로 결과 가져오기
    #    - cv_result   : 페이지 1 (CV 분석)
    #    - llm_result  : 페이지 2 (LLM 분석)
    #    - last_report : 구버전 호환 (혹시 이 이름으로 저장돼 있다면 함께 인식)
    # ─────────────────────────────────────────────────────
    cv_result = st.session_state.get("cv_result")
    llm_result = (
        st.session_state.get("llm_result")
        or st.session_state.get("last_report")
    )

    # 상태 표시 — 어느 단계가 준비됐는지 한눈에 보이게
    col1, col2 = st.columns(2)
    with col1:
        if cv_result and cv_result.get("items"):
            st.success(f"✅ CV 분석 결과 로드됨 (객체 {len(cv_result['items'])}개)")
        else:
            st.warning("⚠️ CV 분석 결과 없음 (페이지 1에서 먼저 실행)")
    with col2:
        if llm_result:
            st.success("✅ LLM 분석 결과 로드됨")
        else:
            st.warning("⚠️ LLM 분석 결과 없음 (페이지 2에서 먼저 실행)")

    # ── 체크리스트 생성 버튼 ──
    if st.button("📋 체크리스트 생성", type="primary"):
        if not cv_result and not llm_result:
            st.error("CV 또는 LLM 분석 결과가 최소 하나는 필요합니다.")
        else:
            with st.spinner("맞춤형 체크리스트 생성 중... (30~40초)"):
                result = generate_action_list(
                    cv_result or {"items": []},
                    llm_result or {},
                )
            # 다시 그릴 때 사라지지 않도록 세션에 저장
            st.session_state["checklist_result"] = result

    # ── 저장된 결과 표시 ──
    result = st.session_state.get("checklist_result")
    if result:
        if "error" in result:
            st.error(f"❌ 생성 실패: {result['error']}")
        else:
            st.success("✅ 체크리스트 생성 완료!")

            # ── PDF 다운로드 버튼 ──
            # build_checklist_pdf 가 None 을 반환하면(폰트/패키지 문제)
            # 에러 메시지가 이미 표시되었으므로 버튼만 숨김
            st.markdown("### 💾 PDF 로 저장")
            pdf_col1, pdf_col2 = st.columns([1, 3])
            with pdf_col1:
                # 버튼을 누르면 그 시점에 PDF 를 빌드.
                # 매번 빌드 비용을 줄이려면 캐싱할 수도 있지만
                # 결과가 바뀔 수 있어 즉시 생성 방식이 안전합니다.
                if st.button("📄 PDF 생성하기"):
                    with st.spinner("PDF 생성 중..."):
                        pdf_bytes = build_checklist_pdf(result)
                    if pdf_bytes:
                        st.session_state["checklist_pdf"] = pdf_bytes
                        st.success("✅ PDF 준비 완료! 오른쪽 다운로드 버튼을 눌러주세요.")

            with pdf_col2:
                pdf_bytes = st.session_state.get("checklist_pdf")
                if pdf_bytes:
                    file_name = f"epilogue_checklist_{datetime.now():%Y%m%d_%H%M%S}.pdf"
                    st.download_button(
                        label="⬇️ PDF 다운로드",
                        data=pdf_bytes,
                        file_name=file_name,
                        mime="application/pdf",
                        type="primary",
                    )

            st.markdown("---")
            st.markdown("### ✅ 유족 안내 체크리스트")

            icons = {
                "사망신고": "📝", "안심상속": "🏦", "귀중품": "💍",
                "서류":     "📄", "추억물품": "💝", "가전":   "🔌",
                "폐기물":   "🗑️", "보험":     "🏥", "구독":   "📺",
                "계정":     "👤",
            }

            for category, data in result.items():
                icon = icons.get(category, "✔️")
                with st.expander(f"{icon}  {category}", expanded=True):
                    if data.get("items"):
                        st.markdown(
                            '<div class="detected-label">📌 감지된 항목</div>',
                            unsafe_allow_html=True,
                        )
                        items_html = "".join(
                            f'<div class="detected-item">• {item}</div>'
                            for item in data["items"]
                        )
                        st.markdown(items_html, unsafe_allow_html=True)
                        st.markdown("")

                    st.markdown(
                        format_guide_text(data.get("guide", "")),
                        unsafe_allow_html=True,
                    )


# =========================================================
# 탭 2: 비탄 케어 챗봇
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

    # 챗봇 상태 초기화
    # chat_history : Gemini 가 컨텍스트로 사용하는 raw 대화 기록
    # chat_display : 화면에 보여줄 메시지 목록 (인사말 포함)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_display = [
            {"role": "assistant",
             "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
        ]

    # 누적 메시지 렌더링
    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 입력 처리
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

    # 대화 초기화 버튼
    if len(st.session_state.chat_display) > 1:
        if st.button("🔄 대화 다시 시작"):
            st.session_state.chat_history = []
            st.session_state.chat_display = [
                {"role": "assistant",
                 "content": "안녕하세요. 힘드신 마음이 있으시면 편히 이야기해주세요."}
            ]
            st.rerun()
