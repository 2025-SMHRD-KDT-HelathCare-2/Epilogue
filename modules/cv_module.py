"""
cv_module.py
YOLODetector / OCRReader / create_item_catalog
cv_processing.py의 함수를 조립하는 모듈화 레이어
"""


import os
import sys
import easyocr
import tensorflow as tf

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cv_preprocessing import (
    load_image,
    parse_predictions,
    filter_ocr_results,
    CLASS_NAMES,
    CLASS_TO_CATEGORY,
)

# =========================================================
# 모델 클래스
# =========================================================

class YOLODetector:
    """best_final.keras 기반 이미지 분류기"""

    def __init__(self, model_path: str = ""):
        keras_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "cv_model", "best_final.keras"
        )
        self.model = tf.keras.models.load_model(keras_path)
        self.idx_to_class = {i: name for i, name in enumerate(CLASS_NAMES)}

    def predict(self, image_path: str) -> list:
        arr   = load_image(image_path)
        preds = self.model.predict(arr, verbose=0)[0]
        return parse_predictions(preds, self.idx_to_class)


class OCRReader:
    """EasyOCR 기반 텍스트 추출기"""

    def __init__(self):
        self.reader = easyocr.Reader(["ko", "en"], gpu=False)

    def read(self, image_path: str) -> list:
        raw = self.reader.readtext(image_path)
        return filter_ocr_results(raw)


# =========================================================
# 카탈로그 생성
# =========================================================

def create_item_catalog(image_path: str, detector: YOLODetector, ocr: OCRReader) -> dict:
    """
    반환 형식:
    {
        "category":        str,
        "objects":         [{"class": str, "confidence": float}, ...],
        "extracted_texts": [{"text": str, "confidence": float}, ...],
    }
    """
    objects   = detector.predict(image_path)
    texts     = ocr.read(image_path)
    top_class = objects[0]["class"] if objects else "unknown"

    return {
        "category":        CLASS_TO_CATEGORY.get(top_class, "기타"),
        "objects":         objects,
        "extracted_texts": texts,
    }