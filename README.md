# 🕊️ Epilogue

> **유품 및 디지털 유산 통합 정리 솔루션**
> TensorFlow와 Gemini 2.5 Flash를 활용한 AI 기반 사후 정리 헬스케어 플랫폼

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/TensorFlow-2.x-orange.svg" alt="TensorFlow">
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4.svg" alt="Gemini">
  <img src="https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

---

## 📌 프로젝트 소개

**Epilogue**는 1인 가구와 고독사 증가에 따른 **사후 정리 공백 문제**를 해결하기 위해 개발된 AI 기반 통합 솔루션입니다.

떠난 이가 남긴 **오프라인 유품**(가구·가전·문서·귀중품·추억물품)과 **온라인 디지털 유산**(SNS·이메일·구독·결제 내역), 그리고 **고인의 의료 기록**까지 — AI가 한 번에 정리해 유족에게 안내합니다.

> *"떠난 이의 마지막 페이지를, 남은 이가 덜 외롭게 넘길 수 있도록"*

### 🌏 왜 이 서비스가 필요한가?

| 지표 | 수치 |
|---|---|
| 1인 가구 비율 (통계청, 2024) | **34.5%** |
| 연간 고독사 사망자 | **3,000명 이상** |
| 1인당 평균 디지털 계정 수 | **100개 이상** |
| 유족 행정 처리 평균 소요 기간 | **3~6개월** |

유품 정리 업체는 "치우는 것"에만 집중하고, 상속 자문은 "돈"만 다룹니다.
**"무엇이 남았고, 무엇을 해지·청구·보존해야 하는지"** 를 통합적으로 안내하는 서비스는 비어 있는 영역이었습니다.
Epilogue는 이 공백을 AI로 채웁니다.

---

## ✨ 주요 기능

### 📦 1. 스마트 유품 카탈로그
- TensorFlow EfficientNetV2S 기반 이미지 분류 + EasyOCR 텍스트 인식
- 사진 한 장으로 **귀중품/추억물품/가전/가구/서류/폐기물** 자동 카테고리화
- 보증서·라벨·문서 OCR 통합

### 💼 2. 디지털 자산 보고서
- Gemini 2.5 Flash 기반 4개 도메인 동시 분석 (구독·보험·의료·카드)
- 미해지 구독 / 청구 가능 보험 / 복약 이력 / 카드 지출 패턴 자동 추출
- 마크다운 형식의 종합 보고서 자동 생성

### 📋 3. 통합 체크리스트 + 비탄 케어 챗봇
- 10개 카테고리별 맞춤 안내문 일괄 생성
  *(사망신고·안심상속·귀중품·서류·추억물품·가전·폐기물·보험·구독·계정)*
- **국가트라우마센터 애도상담 매뉴얼** 기반 챗봇
- 위기 키워드(자해·자살 표현) 감지 시 **LLM 호출 이전**에 1393·1577-0199 등 전문기관 즉시 안내

---

## 🏗️ 시스템 아키텍처

┌─────────────────────────────────────────────────────────────┐ │ 🖥️ Streamlit Web UI │ └─────────────────────────────────────────────────────────────┘ │ ┌─────────────────────┼─────────────────────┐ ▼ ▼ ▼ ┌───────────┐ ┌──────────┐ ┌───────────┐ │ CV Page │ │ LLM Page │ │ List Page │ └─────┬─────┘ └─────┬────┘ └─────┬─────┘ │ │ │ ▼ ▼ ▼ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ cv_module │ │ llm_module │ │ list_module │ │ EfficientNet │ │ Gemini 2.5 │ │ + chatbot │ │ + EasyOCR │ │ Flash │ │ (Grief Care) │ └──────────────┘ └──────────────┘ └──────────────┘ │ │ │ └─────────────────────┼─────────────────────┘ ▼ ┌─────────────────────┐ │ 통합 체크리스트 + │ │ 비탄 케어 챗봇 출력 │ └─────────────────────┘

**파이프라인 처리 시간**: 사진 1장 + 디지털 기록 1세트 기준 **약 15초** 내 완료

---

## 📂 프로젝트 구조

Epilogue/ ├── app.py # Streamlit 메인 진입점 ├── pages/ # 멀티페이지 UI │ ├── 1_cv_page.py # 유품 사진 분석 │ ├── 2_llm_page.py # 디지털 자산 분석 │ └── 3_list_page.py # 통합 체크리스트 + 챗봇 ├── modules/ # 비즈니스 로직 │ ├── cv_module.py # YOLODetector + OCRReader │ ├── llm_module.py # Gemini 4개 도메인 분석 │ ├── list_module.py # CV+LLM → 체크리스트 │ └── chatbot_module.py # 비탄 케어 챗봇 ├── utils/ # 전처리 / 유틸 │ ├── cv_preprocessing.py │ ├── llm_preprocessing.py │ └── list_preprocessing.py ├── notebooks/ # 모델 학습·실험 │ ├── 1_eda.ipynb # 탐색적 데이터 분석 │ ├── 2CNN_train.ipynb # EfficientNetV2S 학습 │ ├── 3_experiments.ipynb # YOLO vs EfficientNet 비교 │ ├── 4_error_analysis.ipynb # 오류 사례 분석 │ └── llm_modeling.ipynb # LLM 프롬프트 실험 ├── data/ │ ├── cv_model/best_final.keras # 학습 완료 모델 │ └── processed/grief_care/ # 비탄 케어 가이드 ├── requirements.txt └── README.md

---

## 🛠️ 기술 스택

| 영역 | 사용 기술 |
|---|---|
| **언어/프레임워크** | Python 3.10+, Streamlit |
| **컴퓨터 비전** | TensorFlow (EfficientNetV2S), EasyOCR, OpenCV, Pillow |
| **LLM** | Google Gemini 2.5 Flash, LangChain, ChromaDB |
| **데이터 처리** | NumPy, Pandas, scikit-learn |
| **시각화** | Matplotlib, Seaborn |
| **문서 생성** | ReportLab (PDF), Pydantic (스키마 검증) |
| **환경 관리** | python-dotenv |

---

## 📊 모델 성능

### 🖼️ CV 모델 비교 실험

| Model | Top-1 Acc | Params | 비고 |
|---|---|---|---|
| 초기 YOLO Object Detection | 32.1% | — | ❌ 태스크 불일치로 폐기 |
| YOLO11n-cls | 55.0% | 1.5M | 경량이나 정확도 부족 |
| **EfficientNetV2S** ⭐ | **70.5%** | 20.3M | **최종 채택** |

> **선택 근거**: 사후 정리는 정확성이 중요한 민감 도메인이므로, 파라미터 크기보다 **정확도 우선**으로 EfficientNetV2S 채택. 초기 YOLO Detection의 실패에서 배워 두 모델을 모두 분류 모드로 통일해 공정 비교 수행.

### 🤖 LLM 모듈 성능

| 지표 | 측정값 |
|---|---|
| JSON 파싱 성공률 | **98%** |
| 도메인당 평균 응답 시간 | 약 1.8초 |
| 4개 도메인 + 종합 보고서 총 처리 시간 | 약 9초 |
| 위기 키워드 감지 정확도 | **100%** |

### 🔍 오류 사례 분석 (Top 5)

| 원인 | 대표 케이스 | 개선안 |
|---|---|---|
| top_k=3 오분류 | TV → laptop 1위 | top_k=1 적용 ✅ |
| 저신뢰도 오분류 | 페트병 → nightstand (22.3%) | 신뢰도 임계값 도입 |
| 형태 유사 혼동 | 사진(photo) → TV (82.6%) | OCR 결합으로 해결 (v1.1) |
| 유사 카테고리 | 소파 → bed (34.0%) | 가구 세부 클래스 추가 |
| 색상·형태 결합 오류 | 반지 ↔ 천장형 에어컨 | 어그멘테이션 강화 |

---

## 🚀 설치 및 실행 방법

### 1️⃣ 저장소 클론
```bash
git clone https://github.com/2025-SMHRD-KDT-HelathCare-2/Epilogue.git
cd Epilogue

2️⃣ 가상환경 생성 및 활성화
  Windows
  python -m venv venv
  venv\Scripts\activate

  macOS / Linux
  python -m venv venv
  source venv/bin/activate

3️⃣ 의존성 설치
  pip install -r requirements.txt

4️⃣ 환경 변수 설정
  프로젝트 루트에 .env 파일을 생성하고 Gemini API 키를 입력하세요.
  GEMINI_API_KEY=your_actual_api_key_here

  💡 Google AI Studio에서 무료로 API 키를 발급받을 수 있습니다.

5️⃣ Streamlit 실행
  streamlit run app.py

  브라우저에서 http://localhost:8501이 자동으로 열리며, 좌측 사이드바에서 3개 페이지(CV / LLM / List)에 접근할 수 있습니다.

🛡️ 윤리적 설계 — Responsible AI
  Epilogue는 사망과 애도라는 민감 도메인을 다루는 만큼, 다음 안전장치를 적용했습니다.

🔐 개인정보 보호
  정규표현식 기반 비식별화 (이름·주민번호·전화·계좌·병원명·진료번호 마스킹)
  실증 단계에서 실제 고인의 데이터 일체 미사용 (공개 데이터셋 + GPT 합성 데이터)

💬 위기 키워드 사전 필터링
  사용자 입력에서 다음 표현이 감지되면 LLM 호출 이전에 차단되며, 전문기관 안내가 우선 출력됩니다.
  "죽고 싶", "사라지고 싶", "없어지고 싶", "자해", "자살",
  "따라가고 싶", "살기 싫", "끝내고 싶", "스스로 목숨"

전문기관	연락처
  자살예방상담전화	1393 (24시간)
  정신건강위기상담전화	1577-0199 (24시간)
  보건복지상담센터	129
  국가트라우마센터	02-2204-0001

🩹 임상 가이드라인 기반 응답
  국가트라우마센터 애도상담 매뉴얼을 시스템 프롬프트로 주입하여 다음을 강제합니다.

🚫 금지 표현
  "곧 괜찮아질 거예요"
  "시간이 약이에요"
  "극복해야 해요"
  "다른 가족 생각해서라도 정신 차려"

✅ 권장 표현
  "지금 느끼시는 감정은 자연스러운 반응입니다."
  "천천히 감당 가능한 만큼만 해도 괜찮습니다."

🧘 안정화 기법 안내
  복식호흡 (4-3-5-3)
  착지기법 (5-4-3-2-1)
  나비포옹법

🎯 환각(Hallucination) 통제
  가이드 텍스트를 LLM에 컨텍스트로 주입하여 RAG처럼 활용
  가이드에 있는 연락처·전화번호는 그대로 포함 강제
  가이드 외 내용에는 자동으로 AI 면책 문구 부착
  JSON 파싱 방어 코드 + 3회 재시도 로직

🗺️ 개발 로드맵
버전	계획	                                                     상태
v1.0	CV + LLM + 챗봇 통합 프로토타입	                          ✅ 완료
v1.1	OCR 결합으로 paper/photo 혼동 해결	                      🔄 진행 중
v1.2	신뢰도 임계값 + "분류 불가" 처리 도입	                     📋 계획
v2.0	YOLO Detection 재도입(다중 객체) + 온프레미스 sLLM 전환	   📋 계획
v2.1	실제 한국 가정 데이터 수집 + 24개 클래스 확장              📋 계획
v3.0	지자체·복지센터 연계 공공 서비스화 +                       💭 구상 
      유전 가족력 기반 건강 모니터링	

👥 팀 소개 — 디딤돌
이름          역할 담당                 파일
주양덕	      🎯 PM · UI · 발표	      app.py, 
                                      pages/1_cv_page.py, 
                                      pages/2_llm_page.py, 
                                      pages/3_list_page.py
문정인        👁️ CV 담당	             modules/cv_module.py, 
                                      utils/cv_preprocessing.py, 
                                      notebooks/cv_modeling
김동건	      🤖 LLM 담당,시연영상     modules/llm_module.py,
                                      utils/llm_preprocessing.py,
                                      notebooks/llm_modeling
신예은	      📊 통합List·성능 향상·   modules/list_module.py,
              비교분석 시각화	         modules/cv_module.py, 
                                      notebooks/모델 업그레이드 및 비교분석, 
                                      utils/list_preprocessing.py

📚 데이터 출처
  CV 데이터셋: Roboflow Public Datasets — 8개 클래스 1,254장 (Train 922 / Valid 220 / Test 112)

  비탄 케어 가이드: 국가트라우마센터 애도상담 매뉴얼
  행정 절차 가이드: 정부24 사망신고 안내, 보건복지부 안심상속 원스톱 서비스
  LLM 분석용 데이터: GPT 기반 합성 데이터 (수기 검수)

⚠️ 주의사항 및 한계점
  본 프로젝트는 K-Digital Training 해커톤 프로토타입으로, 실서비스 배포 전 추가 검증이 필요합니다.

  Roboflow 공개 데이터셋 기반 학습으로, 실제 한국 가정 유품과 시각적 차이가 있을 수 있습니다.

  외부 LLM API(Gemini)에 의존하므로, 민감 의료·금융 정보 처리에는 온프레미스 sLLM 전환(v2.0) 후 사용을 권장합니다.

  챗봇은 전문 의료·심리 치료를 대체하지 않으며, 보조 역할에 한정됩니다.

  AI가 생성한 행정·법률·의료 안내는 반드시 해당 기관(주민센터, 정부24, 금융감독원 1332 등)에 직접 확인하시기 바랍니다.

📜 라이선스
  본 프로젝트는 K-Digital Training 교육 과정의 일환으로 개발되었으며, 비상업적 학습·연구 목적으로 자유롭게 활용하실 수 있습니다.

🙏 감사의 글
  본 프로젝트는 광주 스마트인재개발원(SMHRD) K-Digital Training AI활용 헬스케어 서비스 개발자과정 2회차 CV+LLM 해커톤(2025.04.20 ~ 2025.05.20)에서 개발되었습니다.

  지도해 주신 강사진과 운영진, 그리고 사회의 그늘진 곳을 비추는 데 영감을 주신 모든 분들께 감사드립니다.

🕊️ 누군가의 인생이 끝났을 때, 기술이 위로가 될 수 있다고 믿습니다.

© 2025 DiDimDol Team | K-Digital Training
```