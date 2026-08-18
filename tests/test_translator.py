"""Tests for TranslationService._translate_guarded using a fake translator
in place of GoogleTranslator, so we can prove pet names never reach it -
without needing network access to translate.google.com.
"""
from app.services.translator import TranslationService


class RecordingFakeTranslator:
    """Stands in for deep_translator.GoogleTranslator. Records every string
    it's asked to translate and returns an obviously-fake uppercase version,
    so tests can assert both on the output and on exactly what was sent in.
    """

    def __init__(self):
        self.calls = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        return f"[TRANSLATED:{text.upper()}]"


def _service_with_fake():
    service = TranslationService()
    fake = RecordingFakeTranslator()
    return service, fake


def test_pet_name_never_sent_to_translator():
    service, fake = _service_with_fake()
    result = service._translate_guarded("I miss you baby", fake, "am")

    # "baby" must never appear in any string handed to the fake translator.
    for call in fake.calls:
        assert "baby" not in call.lower()

    # The glossary term must appear in the final output, spliced in directly.
    assert "\u12CD\u12F4" in result  # ውዴ


def test_surrounding_text_is_still_translated():
    service, fake = _service_with_fake()
    result = service._translate_guarded("Good morning honey, sleep well", fake, "am")

    # The non-pet-name chunks did go through the (fake) translator.
    assert any("Good morning" in call for call in fake.calls)
    assert any("sleep well" in call for call in fake.calls)
    assert "[TRANSLATED:" in result


def test_plain_text_with_no_pet_names_is_one_call():
    service, fake = _service_with_fake()
    service._translate_guarded("What time is it", fake, "am")
    assert len(fake.calls) == 1
    assert fake.calls[0] == "What time is it"


def test_multiple_pet_names_all_rendered_correctly():
    service, fake = _service_with_fake()
    result = service._translate_guarded("Hey baby, love you honey", fake, "om")

    assert "jaalalee koo" in result  # baby
    assert "jaalala koo" in result  # love
    assert "damma koo" in result  # honey
    for call in fake.calls:
        assert "baby" not in call.lower()
        assert "honey" not in call.lower()


def test_translator_failure_on_one_chunk_falls_back_to_original_text():
    class FlakyTranslator:
        def translate(self, text):
            raise RuntimeError("simulated network failure")

    service = TranslationService()
    result = service._translate_guarded("Good morning baby", FlakyTranslator(), "am")

    # Chunk translation failed, so the original English text for that
    # chunk is used instead of crashing - and the pet name still renders.
    assert "Good morning" in result
    assert "\u12CD\u12F4" in result


def test_translator_returning_none_does_not_crash_join():
    """Regression test: deep_translator's GoogleTranslator can return None
    instead of raising on some inputs (rate limiting, odd chunk length,
    transient hiccups). That used to end up inside the parts list handed
    to "".join(), crashing with "sequence item N: expected str instance,
    NoneType found". Must fall back to the original chunk text instead."""

    class SilentlyFailingTranslator:
        def __init__(self):
            self.call_count = 0

        def translate(self, text):
            self.call_count += 1
            # Simulate Google returning None on, say, the second chunk.
            if self.call_count == 2:
                return None
            return f"[OK:{text}]"

    service = TranslationService()
    # Two pet names guarantee at least two separate text chunks get sent
    # to the translator, so the second call is exercised.
    result = service._translate_guarded("Hey baby, love you honey", SilentlyFailingTranslator(), "am")

    assert isinstance(result, str)
    assert "\u12CD\u12F4" in result  # ውዴ (baby)
    assert "\u134D\u1245\u122C" in result  # ፍቅሬ (love)
    assert "\u121B\u122D\u12EC" in result  # ማርዬ (honey)


def test_translator_returning_empty_string_falls_back_to_original_text():
    class EmptyStringTranslator:
        def translate(self, text):
            return ""

    service = TranslationService()
    result = service._translate_guarded("Good morning", EmptyStringTranslator(), "am")
    assert result == "Good morning"
