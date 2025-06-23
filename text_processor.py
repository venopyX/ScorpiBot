"""Text processing and translation utilities."""
import re
from typing import Tuple
from fidel import Transliterate
from langdetect import detect, LangDetectError
from deep_translator import GoogleTranslator

class TextProcessor:
    """Handles script detection and conversion between Latin and Ge'ez."""
    
    def __init__(self):
        self.geez_range = re.compile(r'[\u1200-\u137F]')
        self.latin_range = re.compile(r'[a-zA-Z]')
    
    def detect_script(self, text: str) -> str:
        """Detect script type of input text."""
        if self.geez_range.search(text):
            return "Amharic (Ge'ez)"
        elif self.latin_range.search(text):
            detected_lang = self._detect_language(text)
            return "Amharic (Latin script)" if detected_lang == "Latin script (Other)" else detected_lang
        return "Unknown"
    
    def _detect_language(self, text: str) -> str:
        """Detect language with error handling."""
        try:
            language = detect(text)
            lang_map = {"en": "English", "om": "Afan Oromo"}
            return lang_map.get(language, "Latin script (Other)")
        except LangDetectError:
            return "Latin script (Other)"
    
    def am_lat_to_geez(self, text: str) -> str:
        """Convert Amharic Latin script to Ge'ez script."""
        script = self.detect_script(text)
        if script in ["Amharic (Latin script)", "Unknown"]:
            return Transliterate(text, symbol=True, auto_correct=True).transliterate()
        return text
    
    def geez_to_am_lat(self, text: str) -> str:
        """Convert Ge'ez script to Amharic Latin script."""
        if self.detect_script(text) == "Amharic (Ge'ez)":
            return Transliterate(text, symbol=True).reverse_transliterate()
        return text

class TextManager:
    """Manages translation between different languages and scripts."""
    
    def __init__(self):
        self.translators = {
            'geez_to_en': GoogleTranslator(source='am', target='en'),
            'en_to_geez': GoogleTranslator(source='en', target='am'),
            'oromo_to_en': GoogleTranslator(source='om', target='en'),
            'en_to_oromo': GoogleTranslator(source='en', target='om')
        }
        self.text_processor = TextProcessor()
    
    def detect_language(self, text: str) -> str:
        """Detect language and return language code."""
        script = self.text_processor.detect_script(text)
        lang_map = {
            'Amharic (Ge\'ez)': 'am',
            'English': 'en',
            'Afan Oromo': 'om',
            'Amharic (Latin script)': 'am_lat'
        }
        return lang_map.get(script, 'other')
    
    def detect_and_translate_to_english(self, text: str) -> Tuple[str, str]:
        """Detect language and translate to English."""
        detected_lang = self.detect_language(text)
        
        translation_map = {
            'am': lambda t: self.translators['geez_to_en'].translate(t),
            'om': lambda t: self.translators['oromo_to_en'].translate(t),
            'en': lambda t: t,
            'am_lat': lambda t: self.translators['geez_to_en'].translate(
                self.text_processor.am_lat_to_geez(t)
            )
        }
        
        translator = translation_map.get(detected_lang, self._translate_other_to_english)
        translated_text = translator(text)
        return translated_text, detected_lang
    
    def translate_from_english(self, text: str, target_language: str) -> str:
        """Translate from English to target language."""
        translation_map = {
            'am': lambda t: self.translators['en_to_geez'].translate(t),
            'om': lambda t: self.translators['en_to_oromo'].translate(t),
            'en': lambda t: t,
            'am_lat': lambda t: self.text_processor.geez_to_am_lat(
                self.translators['en_to_geez'].translate(t)
            )
        }
        
        translator = translation_map.get(target_language, self._translate_english_to_other)
        return translator(text)
    
    def _translate_other_to_english(self, text: str) -> str:
        """Handle translation for 'other' language detection."""
        amharic_geez_text = self.text_processor.am_lat_to_geez(text)
        return self.translators['geez_to_en'].translate(amharic_geez_text)
    
    def _translate_english_to_other(self, text: str) -> str:
        """Handle translation to 'other' language."""
        amharic_geez_text = self.translators['en_to_geez'].translate(text)
        return self.text_processor.geez_to_am_lat(amharic_geez_text)