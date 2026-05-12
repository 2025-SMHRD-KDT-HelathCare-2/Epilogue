## Epilogue
YOLO와 Gemini 2.5 flash를 활용한 유품 및 디지털 유산 통합 정리


## 🕊️ 유품 및 디지털 유산 통합 정리 솔루션

## 팀명 : 디딤돌

## 프로젝트명 : Epilogue

## 팀원 & 역할 담당
주양덕 : PM, 데이터 담당, UI, 발표
  - pages/1_유품_카탈로그.py
  - pages/2_디지털_자산_보고서.py
  - pages/3_통합_체크리스트.py
  - data/raw

문정인 : CV 담당
  - modules/cv_module.py
  - notebooks/cv_modeling

김동건 : LLM 담당
  - modules/llm_module.py
  - notebooks/llm_modeling

신예은 : 통합/성능 향상 담당
  - utils/preprocessing.py, 
  - notebooks/모델 업그레이드


## 실행 방법
```bash

> git clone https://github.com/2025-SMHRD-KDT-HelathCare-2/Epilogue.git

> cd Epilogue

> python -m venv venv

> venv\Scripts\activate

> pip install -r requirements.txt

> streamlit run app.py
