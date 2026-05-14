import json
import re
from pathlib import Path
from datetime import datetime


# ── 경로 설정 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # project root
DIGITAL_RECORDS_PATH = BASE_DIR / "data/raw/texts/synthetic/digital_records.json"
INSURANCE_DIR        = BASE_DIR / "data/raw/texts/insurance"
ADMIN_PATH           = BASE_DIR / "data/raw/texts/admin/inheritance_guide.txt"
GRIEF_PATH           = BASE_DIR / "data/raw/texts/grief_care/grief_guide.txt"


# ── 1. JSON 디지털 기록 로드 ───────────────────────────────
def load_digital_records(path: Path = DIGITAL_RECORDS_PATH) -> list[dict]:
    """
    digital_records.json을 로드하고 기본 유효성 검사를 수행합니다.
    반환: [{"category": ..., "date": ..., "content": ...}, ...]
    """
    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    required_keys = {"category", "date", "content"}
    valid = []
    for i, r in enumerate(records):
        if not required_keys.issubset(r.keys()):
            print(f"[경고] {i}번 레코드 필드 누락 → 건너뜀")
            continue
        if not r["content"].strip():
            print(f"[경고] {i}번 레코드 content 비어있음 → 건너뜀")
            continue
        valid.append(r)

    print(f"[로드 완료] 총 {len(valid)}건 / 원본 {len(records)}건")
    return valid


# ── 2. 날짜 정규화 ─────────────────────────────────────────
def normalize_date(date_str: str) -> str:
    """
    다양한 날짜 포맷을 YYYY-MM-DD 로 통일합니다.
    파싱 실패 시 원본 문자열 반환.
    """
    formats = ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    print(f"[경고] 날짜 파싱 실패: {date_str!r}")
    return date_str


# ── 3. 텍스트 정제 ────────────────────────────────────────
def clean_text(text: str) -> str:
    """
    - 연속 공백/줄바꿈 정리
    - 특수문자 중 불필요한 것 제거 (괄호·숫자·한글·영문·기본 구두점 유지)
    """
    text = re.sub(r"[ \t]+", " ", text)          # 연속 공백 → 단일 공백
    text = re.sub(r"\n{3,}", "\n\n", text)        # 3줄 이상 빈 줄 → 2줄
    text = re.sub(r"[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?()\[\]:·\-/]", "", text)
    return text.strip()


# ── 4. 카테고리별 분류 ────────────────────────────────────
CATEGORY_MAP = {
    "보험":    "insurance",
    "구독":    "subscription",
    "SNS":     "sns",
    "카드결제": "card",
    "의료":    "medical",
}

def categorize_records(records: list[dict]) -> dict[str, list[dict]]:
    """
    카테고리별로 레코드를 분류합니다.
    반환: {"insurance": [...], "subscription": [...], ...}
    """
    categorized: dict[str, list] = {v: [] for v in CATEGORY_MAP.values()}
    categorized["unknown"] = []

    for r in records:
        key = CATEGORY_MAP.get(r["category"], "unknown")
        categorized[key].append(r)

    for cat, items in categorized.items():
        print(f"  [{cat}] {len(items)}건")

    return categorized


# ── 5. LLM 입력용 포맷 변환 ───────────────────────────────
def format_for_llm(records: list[dict], max_chars: int = 8000) -> str:
    """
    레코드 리스트를 Gemini에 넘길 단일 텍스트 블록으로 변환합니다.
    max_chars 초과 시 잘라냅니다 (Gemini 컨텍스트 대비 여유 확보).
    """
    lines = []
    for i, r in enumerate(records, 1):
        lines.append(f"[{i}] ({r['date']}) {r['category']}: {r['content']}")

    combined = "\n".join(lines)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n...(이하 생략)"
        print(f"[경고] 텍스트가 {max_chars}자 초과 → 잘라냄")

    return combined


# ── 6. 텍스트 파일 로드 (보험약관·행정가이드·비탄케어) ─────
def load_text_file(path: Path) -> str:
    """일반 텍스트 파일을 읽어 정제된 문자열로 반환합니다."""
    if not path.exists():
        print(f"[경고] 파일 없음: {path}")
        return ""
    text = path.read_text(encoding="utf-8")
    return clean_text(text)


# ── 7. 전체 파이프라인 ────────────────────────────────────
def preprocess_all() -> dict:
    """
    모든 데이터를 로드·정제하여 딕셔너리로 반환합니다.
    llm_module.py 에서 이 함수 하나만 import해서 쓰면 됩니다.

    반환 구조:
    {
        "categorized": {카테고리별 레코드},
        "llm_input":   {카테고리별 LLM용 텍스트},
        "insurance_guide": str,
        "inheritance_guide": str,
        "grief_guide": str,
    }
    """
    print("=" * 40)
    print("[전처리 시작]")

    # 1) 디지털 기록 로드
    records = load_digital_records()

    # 2) 날짜 정규화 + 텍스트 정제
    for r in records:
        r["date"]    = normalize_date(r["date"])
        r["content"] = clean_text(r["content"])

    # 3) 카테고리 분류
    print("\n[카테고리 분류]")
    categorized = categorize_records(records)

    # 4) LLM 입력 포맷 변환 (카테고리별)
    llm_input = {
        cat: format_for_llm(items)
        for cat, items in categorized.items()
        if items
    }

    # 5) 텍스트 파일 로드
    insurance_texts = []
    if INSURANCE_DIR.exists():
        for json_file in INSURANCE_DIR.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                insurance_texts.append(json.dumps(data, ensure_ascii=False))
            except Exception as e:
                print(f"[경고] 보험약관 로드 실패: {json_file.name} → {e}")

    result = {
        "categorized":       categorized,
        "llm_input":         llm_input,
        "insurance_guide":   "\n".join(insurance_texts),
        "inheritance_guide": load_text_file(ADMIN_PATH),
        "grief_guide":       load_text_file(GRIEF_PATH),
    }

    print("\n[전처리 완료]")
    print("=" * 40)
    return result


# ── 테스트 실행 ───────────────────────────────────────────
if __name__ == "__main__":
    result = preprocess_all()
    print("\n[LLM 입력 샘플 - 구독 카테고리 앞 200자]")
    print(result["llm_input"].get("subscription", "")[:200])

def mask_personal_info(text: str) -> str:
    import re
    text = re.sub(r'\d{3}-\d{3,4}-\d{4}', '[전화번호]', text)
    text = re.sub(r'\d{6}-\d{7}', '[주민번호]', text)
    text = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[이메일]', text)
    return text

    