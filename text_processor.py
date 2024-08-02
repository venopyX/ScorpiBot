import re
from fidel import Translate, Reverse
from langdetect import detect

from deep_translator import GoogleTranslator


class TextProcessor:
    def __init__(self):
        self.geez_range = re.compile(r'[\u1200-\u137F]')
        self.latin_range = re.compile(r'[a-zA-Z]')
        
    def detect_script(self, text):
        """Detect if the text is English, Amharic (Latin script), or Amharic (Ge'ez script)."""
        if self.geez_range.search(text):
            return "Amharic (Ge'ez)"
        elif self.latin_range.search(text):
            detected_lang = self._detect_language(text)
            if detected_lang == "Latin script (Other)":
                return "Amharic (Latin script)"
            return detected_lang
        else:
            return "Unknown"
    
    def _detect_language(self, text):
        """Detect the language of the text and handle Latin script and other cases."""
        try:
            language = detect(text)
            if language == "en":
                return "English"
            elif language == "om":
                return "Afan Oromo"
            else:
                return "Latin script (Other)"
        except:
            return "Latin script (Other)"
    
    def am_lat_to_geez(self, text):
        """Translate Amharic (Latin script) to Amharic (Ge'ez script)."""
        if self.detect_script(text) == "Amharic (Latin script)" or self.detect_script(text) == "Unknown":
            return Translate(text).translate()
        return text

    def geez_to_am_lat(self, text):
        """Reverse translate Amharic (Ge'ez script) to Amharic (Latin script)."""
        if self.detect_script(text) == "Amharic (Ge'ez)":
            try:
                reverse_translated = Reverse(text, symbol=True).translate()
                return reverse_translated
            except Exception as e:
                print(f"Reverse translation error: {e}")
                return text
        return text




class DeepTranslator:
    def __init__(self):
        self.translator = GoogleTranslator()

    def translate(self, text, target_language):
        return self.translator.translate(text, target=target_language)


class TextManager:
    def __init__(self):
        self.geez_to_english = GoogleTranslator(source='am', target='en')
        self.english_to_geez = GoogleTranslator(source='en', target='am')
        self.oromo_to_english = GoogleTranslator(source='om', target='en')
        self.english_to_oromo = GoogleTranslator(source='en', target='om')

    def detect_language(self, text):
        if self.is_amharic_geez(text):
            return 'am'
        elif self.is_amharic_latin(text):
            return 'am_lat'
        elif self.is_oromo(text):
            return 'om'
        elif self.is_english(text):
            return 'en'
        else:
            return 'other'

    def is_amharic_geez(self, text):
        return any('\u1200' <= char <= '\u137F' for char in text)

    def is_amharic_latin(self, text):
        return all(char.isalpha() or char.isspace() for char in text) and not self.is_english(text)

    def is_oromo(self, text):
        return all(char.isalpha() or char.isspace() for char in text) and not (self.is_english(text) or self.is_amharic_latin(text))

    def is_english(self, text):
        return all('A' <= char <= 'Z' or 'a' <= char <= 'z' or char.isspace() for char in text)

    def detect_and_translate_to_english(self, text):
        detected_language = self.detect_language(text)
        if detected_language == 'am':
            translated_text = self.geez_to_english.translate(text)
        elif detected_language == 'am_lat':
            amharic_geez_text = TextProcessor.am_lat_to_geez(text)
            translated_text = self.geez_to_english.translate(amharic_geez_text)
        elif detected_language == 'om':
            translated_text = self.oromo_to_english.translate(text)
        else:
            amharic_geez_text = TextProcessor.am_lat_to_geez(text)
            translated_text = self.geez_to_english.translate(amharic_geez_text)
        return translated_text, detected_language

    def translate_from_english(self, text, target_language):
        if target_language == 'am':
            return self.english_to_geez.translate(text)
        elif target_language == 'am_lat':
            amharic_geez_text = self.english_to_geez.translate(text)
            return TextProcessor.geez_to_am_lat(amharic_geez_text)
        elif target_language == 'om':
            return self.english_to_oromo.translate(text)
        else:
            amharic_geez_text = self.english_to_geez.translate(text)
            return TextProcessor.geez_to_am_lat(amharic_geez_text)
