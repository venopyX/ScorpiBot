"""Script detection and translation, with pet names spliced in directly
instead of ever being sent through Google Translate. See
app.services.pet_name_guard for the full explanation."""
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

    Pet names (see app.core.glossary) never reach the translator at all -
    the sentence is split into plain-text chunks and pet-name chunks, only
    the plain-text chunks get sent to Google Translate, and the pet-name
    chunks are spliced in directly from the glossary. See
    app.services.pet_name_guard for why an earlier placeholder-token
    approach didn't work for this language pair.
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
        """Translate `text`, splicing in glossary pet-name terms directly
        instead of ever sending them to the translator.

        Each plain-text segment is translated with its own API call so a
        pet name never shares a translator call with surrounding words
        (which is what let Google's NMT mangle the earlier placeholder
        approach). Segments are rejoined in original order.
        """
        segments = self.pet_guard.split(text)

        # Common case: no pet names in this text at all - one call, no
        # extra overhead, identical behavior to before this feature existed.
        if len(segments) == 1 and segments[0][0] == "text":
            return self._translate_chunk(segments[0][1], translator)

        parts = []
        for kind, value in segments:
            if kind == "pet":
                parts.append(self.pet_guard.render(value, target_lang))
            elif value.strip():
                parts.append(self._translate_chunk(value, translator))
            else:
                # Whitespace/punctuation-only chunk - nothing to translate.
                parts.append(value)

        return "".join(parts)

    def _translate_chunk(self, text: str, translator: GoogleTranslator) -> str:
        try:
            return translator.translate(text)
        except Exception as exc:
            logger.error("Translation failed for chunk, returning original text: %s", exc)
            return text
