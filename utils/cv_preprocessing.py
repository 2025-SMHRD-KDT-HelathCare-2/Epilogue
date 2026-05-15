"""
cv_processing.py
이미지 전처리 / 예측 후처리 / 카테고리 매핑 데이터
"""

import numpy as np
from PIL import Image

# =========================================================
# 상수
# =========================================================

IMG_SIZE = (224, 224)

CLASS_NAMES = [
    "TV", "air_conditioning", "album", "bankbook", "bed", "chair",
    "desk", "dining_table", "drawer", "fridge", "glass_bottle", "gold",
    "laptop", "nightstand", "paper", "paper_document", "pet_bottle", "photo",
    "ring", "sofa", "storage_cabinet", "styrofoam", "vanity", "wardrobe"
]

CLASS_TO_CATEGORY = {
    "gold":             "귀중품",
    "ring":             "귀중품",
    "bankbook":         "귀중품",
    "photo":            "추억물품",
    "album":            "추억물품",
    "TV":               "가전",
    "laptop":           "가전",
    "fridge":           "가전",
    "air_conditioning": "가전",
    "paper_document":   "의료문서",
    "paper":            "의료문서",
    "bed":              "가구",
    "chair":            "가구",
    "desk":             "가구",
    "dining_table":     "가구",
    "drawer":           "가구",
    "nightstand":       "가구",
    "sofa":             "가구",
    "storage_cabinet":  "가구",
    "vanity":           "가구",
    "wardrobe":         "가구",
    "glass_bottle":     "폐기물",
    "pet_bottle":       "폐기물",
    "styrofoam":        "폐기물",
}

# =========================================================
# 전처리
# =========================================================

def load_image(image_path: str) -> np.ndarray:
    """이미지 파일 → 모델 입력 배열 (1, 224, 224, 3)"""
    img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)

# =========================================================
# 후처리
# =========================================================

def parse_predictions(preds: np.ndarray, idx_to_class: dict, top_k: int = 3) -> list:
    """모델 출력 확률 배열 → 상위 k개 클래스 + 신뢰도 리스트"""
    top_indices = np.argsort(preds)[::-1][:top_k]
    return [
        {
            "class":      idx_to_class[int(i)],
            "confidence": float(preds[i])
        }
        for i in top_indices
    ]

def filter_ocr_results(raw_results: list, min_confidence: float = 0.3) -> list:
    """EasyOCR 원본 결과 → 신뢰도 필터링된 텍스트 리스트"""
    return [
        {
            "text":       text,
            "confidence": float(conf)
        }
        for (_, text, conf) in raw_results
        if conf >= min_confidence
    ]