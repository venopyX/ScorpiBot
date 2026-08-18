"""Script detection and translation, with pet names shielded from mistranslation."""
import logging
import re
from typing import Tuple

from deep_translator import GoogleTranslator
from fidel import Transliterate
from langdetect import DetectorFactory, detect

from app.services.pet_name_guard import PetNameGuard

# Deterministic language detection.
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

_GEEZ_RANGE = re.compile(r"[\u1200-\u137F]")
_LATIN_RANGE = re.compile(r"[a-zA-Z]")

_LANG_NAME_MAP = {"en": "English", "om": "Afan Oromo"}


class ScriptDetector:
    """Detects whether text is Ge'ez script, Latin-script Amharic, English, or Oromo."""

    def detect_script(self, text: str) -> str:
        if _GEEZ_RANGE.search(text):
            return "Amharic (Ge'ez)"
        if _LATIN_RANGE.search(text):
            detected = self._detect_language(text)
            return "Amharic (Latin script)" if detected == "Latin script (Other)" else detected
        return "Unknown"

    def _detect_language(self, text: str) -> str:
        try:
            code = detect(text)
            return _LANG_NAME_MAP.get(code, "Latin script (Other)")
        except Exception:
            return "Latin script (Other)"

    def latin_to_geez(self, text: str) -> str:
        """Convert Latin-script Amharic ("selam") to Ge'ez script."""
        if self.detect_script(text) in ("Amharic (Latin script)", "Unknown"):
            return Transliterate(text, symbol=True, auto_correct=True).transliterate()
        return text

    def geez_to_latin(self, text: str) -> str:
        """Convert Ge'ez script back to Latin-script Amharic."""
        if self.detect_script(text) == "Amharic (Ge'ez)":
            return Transliterate(text, symbol=True).reverse_transliterate()
        return text


class TranslationService:
    """Translates between English, Amharic, and Afaan Oromo.

    Pet names (see app.core.glossary) are masked before every translation
    call and restored with their natural target-language equivalent
    afterward, so "baby" never becomes a literal infant in Amharic.
    """

    def __init__(self) -> None:
        self._translators = {
            "geez_to_en": GoogleTranslator(source="am", target="en"),
            "en_to_geez": GoogleTranslator(source="en", target="am"),
            "oromo_to_en": GoogleTranslator(source="om", target="en"),
            "en_to_oromo": GoogleTranslator(source="en", target="om"),
        }
        self.scripts = ScriptDetector()
        self.pet_guard = PetNameGuard()

    def detect_language_code(self, text: str) -> str:
        """Return a short code: 'am', 'en', 'om', 'am_lat', or 'other'."""
        script = self.scripts.detect_script(text)
        return {
            "Amharic (Ge'ez)": "am",
            "English": "en",
            "Afan Oromo": "om",
            "Amharic (Latin script)": "am_lat",
        }.get(script, "other")

    def to_english(self, text: str) -> Tuple[str, str]:
        """Detect the language of `text` and translate it to English.

        Returns (translated_text, detected_language_code).
        """
        lang = self.detect_language_code(text)

        if lang == "en":
            return text, lang
        if lang == "am":
            return self._translate_guarded(text, self._translators["geez_to_en"], "en"), lang
        if lang == "om":
            return self._translate_guarded(text, self._translators["oromo_to_en"], "en"), lang
        if lang == "am_lat":
            geez_text = self.scripts.latin_to_geez(text)
            return self._translate_guarded(geez_text, self._translators["geez_to_en"], "en"), lang

        # Unknown script - best effort via the Amharic path.
        geez_text = self.scripts.latin_to_geez(text)
        return self._translate_guarded(geez_text, self._translators["geez_to_en"], "en"), "other"

    def from_english(self, text: str, target_language: str) -> str:
        """Translate English text into `target_language` ('am', 'om', 'en', 'am_lat')."""
        if target_language == "en":
            return text
        if target_language == "am":
            return self._translate_guarded(text, self._translators["en_to_geez"], "am")
        if target_language == "om":
            return self._translate_guarded(text, self._translators["en_to_oromo"], "om")
        if target_language == "am_lat":
            geez = self._translate_guarded(text, self._translators["en_to_geez"], "am")
            return self.scripts.geez_to_latin(geez)

        # Unknown target - fall back to Amharic Latin script.
        geez = self._translate_guarded(text, self._translators["en_to_geez"], "am")
        return self.scripts.geez_to_latin(geez)

    def _translate_guarded(self, text: str, translator: GoogleTranslator, target_lang: str) -> str:
        """Mask pet names, translate the rest, then restore natural equivalents."""
        masked_text, mapping = self.pet_guard.mask(text)
        try:
            translated = translator.translate(masked_text)
        except Exception as exc:
            logger.error("Translation failed, returning masked source text: %s", exc)
            translated = masked_text
        return self.pet_guard.restore(translated, mapping, target_lang)
