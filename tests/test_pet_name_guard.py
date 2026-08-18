"""Tests for the pet-name masking/restoring logic (no network calls - the
actual Google Translate call is mocked out since we're only testing that
pet names survive the round trip unmangled)."""
from app.services.pet_name_guard import PetNameGuard


def test_mask_replaces_known_pet_names_with_tokens():
    guard = PetNameGuard()
    masked, mapping = guard.mask("Hey baby, I love you honey")

    assert "baby" not in masked
    assert "honey" not in masked
    # "baby", "love", and "honey" are three separate pet-name matches here.
    assert len(mapping) == 3


def test_mask_is_case_insensitive_and_word_bounded():
    guard = PetNameGuard()
    # "Babysitter" contains "baby" but should NOT be masked - word boundary matters.
    masked, mapping = guard.mask("The Babysitter is here, BABE")
    assert "Babysitter" in masked
    assert len(mapping) == 1


def test_restore_uses_amharic_equivalent_not_literal_translation():
    guard = PetNameGuard()
    masked, mapping = guard.mask("I miss you baby")
    restored = guard.restore(masked, mapping, "am")

    # The whole point of this feature: "baby" comes back as the natural
    # Amharic pet name (\u12CD\u12F4 / "wude"), not Google's literal,
    # non-flirty dictionary translation ("child/kid").
    assert "\u12CD\u12F4" in restored  # ውዴ - the correct romantic term
    assert "baby" not in restored.lower()


def test_restore_uses_oromo_equivalent():
    guard = PetNameGuard()
    masked, mapping = guard.mask("Good morning honey")
    restored = guard.restore(masked, mapping, "om")
    assert "damma koo" in restored


def test_restore_tolerates_whitespace_inserted_by_translator():
    """Simulates a translator inserting a space inside the opaque token,
    which has been observed with some MT engines."""
    guard = PetNameGuard()
    masked, mapping = guard.mask("hello love")
    # Simulate MT mangling: insert a space in the middle of the token.
    mangled = masked.replace("zzptzz", "zz ptzz")
    restored = guard.restore(mangled, mapping, "am")
    assert "\u134D\u1245\u122C" in restored  # ፍቅሬ


def test_no_pet_names_returns_text_unchanged():
    guard = PetNameGuard()
    text = "How is your day going so far"
    masked, mapping = guard.mask(text)
    assert masked == text
    assert mapping == {}
