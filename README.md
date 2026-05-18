## Epilogue
Tensorflow와 Gemini 2.5 flash를 활용한 유품 및 디지털 유산 통합 정리


## 🕊️ 유품 및 디지털 유산 통합 정리 솔루션

## 팀명 : 디딤돌

## 프로젝트명 : Epilogue

## 팀원 & 역할 담당
주양덕 : PM, UI, 발표
  - app.py
  - pages/1_cv_page.py
  - pages/2_llm_page.py
  - pages/3_list_page.py

문정인 : CV 담당
  - modules/cv_module.py
  - notebooks/cv_modeling
  - utils/cv_preprocessing.py
  - 

김동건 : LLM 담당
  - modules/llm_module.py
  - notebooks/llm_modeling
  - utils/llm_preprocessing.py
  - 

신예은 : List/성능 향상, 비교분석 시각화 담당
  - modules/list_module.py
  - modules/cv_module.py 
  - notebooks/모델 업그레이드 및 비교분석, 그래프 작업
  - utils/list_processing.py
  - 


## 실행 방법
```bash

> git clone https://github.com/2025-SMHRD-KDT-HelathCare-2/Epilogue.git

> cd Epilogue

> python -m venv venv

> venv\Scripts\activate

> pip install -r requirements.txt

> streamlit run app.py
