"""
TCGIS - Language Detector
Detect the language of Telegram groups
"""

import os
import logging
from typing import Tuple, Optional

from langdetect import detect, DetectorFactory

logger = logging.getLogger(__name__)

# ضبط seed للحصول على نتائج متسقة
DetectorFactory.seed = 0


class LanguageDetector:
    """كاشف لغة المجموعات"""
    
    def __init__(self):
        self.language_model = None
        self._load_model()
    
    def _load_model(self):
        """تحميل نموذج fasttext إذا كان متوفراً"""
        model_path = os.getenv('LANGUAGE_MODEL_PATH', '/models/lid.176.bin')
        
        try:
            if os.path.exists(model_path):
                import fasttext
                self.language_model = fasttext.load_model(model_path)
                logger.info("✅ FastText language model loaded")
            else:
                logger.warning("⚠️ FastText model not found, using langdetect fallback")
        except ImportError:
            logger.warning("⚠️ fasttext not installed, using langdetect fallback")
        except Exception as e:
            logger.error(f"❌ Error loading language model: {e}")
    
    def detect(self, text: str) -> Tuple[str, float]:
        """
        كشف لغة النص
        
        Returns:
            (language_code, confidence)
        """
        if not text or not text.strip():
            return 'unknown', 0.0
        
        try:
            # استخدام fasttext
            if self.language_model:
                predictions = self.language_model.predict(text[:1000], k=1)
                lang_code = predictions[0][0].replace('__label__', '')
                confidence = float(predictions[1][0])
                
                # تحويل رموز fasttext
                lang_map = {
                    'ar': 'arabic',
                    'en': 'english',
                    'fr': 'french',
                    'tr': 'turkish',
                    'fa': 'persian',
                    'ur': 'urdu',
                    'id': 'indonesian',
                    'ms': 'malay',
                    'hi': 'hindi',
                    'ru': 'russian',
                    'es': 'spanish',
                    'de': 'german',
                    'it': 'italian',
                }
                
                return lang_map.get(lang_code, lang_code), round(confidence * 100, 2)
            
            # Fallback: langdetect
            detected = detect(text)
            return detected, 70.0
            
        except Exception as e:
            logger.debug(f"⚠️ Language detection failed: {e}")
            return 'unknown', 0.0
    
    def detect_batch(self, texts: list) -> list:
        """كشف لغة مجموعة من النصوص"""
        results = []
        for text in texts:
            results.append(self.detect(text))
        return results
