"""Tests for the pet-name splitting logic.

No network calls here - GoogleTranslator itself is exercised indirectly
via test_translator.py using a fake translator, since the sandbox this
was built in can't reach translate.google.com. These tests cover the part
that matters most: pet names are correctly identified and separated from
translatable text, so they can be spliced in directly and never touch the
translator at all.
"""
from app.services.pet_name_guard import PetNameGuard


def test_split_isolates_known_pet_names():
    guard = PetNameGuard()
    segments = guard.split("Hey baby, I love you honey")

    kinds = [kind for kind, _ in segments]
    assert "pet" in kinds
    pet_values = [value.english for kind, value in segments if kind == "pet"]
    assert ("baby", "babe", "bae") in pet_values
    assert ("my love", "love") in pet_values
    assert ("honey",) in pet_values


def test_split_is_case_insensitive_and_word_bounded():
    guard = PetNameGuard()
    # "Babysitter" contains "baby" but must NOT be split out - word
    # boundaries matter, or we'd mangle unrelated words.
    segments = guard.split("The Babysitter is here, BABE")
    text_segments = [value for kind, value in segments if kind == "text"]
    assert any("Babysitter" in t for t in text_segments)
    pet_segments = [value for kind, value in segments if kind == "pet"]
    assert len(pet_segments) == 1


def test_split_preserves_surrounding_text_around_pet_name():
    guard = PetNameGuard()
    segments = guard.split("Good morning honey, how are you")
    assert segments[0] == ("text", "Good morning ")
    assert segments[1][0] == "pet"
    assert segments[1][1].english == ("honey",)
    assert segments[2] == ("text", ", how are you")


def test_no_pet_names_returns_single_text_segment():
    guard = PetNameGuard()
    text = "How is your day going so far"
    segments = guard.split(text)
    assert segments == [("text", text)]


def test_render_uses_amharic_equivalent_not_literal_translation():
    guard = PetNameGuard()
    segments = guard.split("I miss you baby")
    pet = next(value for kind, value in segments if kind == "pet")
    rendered = guard.render(pet, "am")

    # The whole point of this feature: "baby" renders as the natural
    # Amharic pet name (\u12CD\u12F4 / "wude"), not Google's literal,
    # non-flirty dictionary translation ("child/kid") - and it never even
    # gets sent to Google Translate to find out.
    assert rendered == "\u12CD\u12F4"


def test_render_uses_oromo_equivalent():
    guard = PetNameGuard()
    segments = guard.split("Good morning honey")
    pet = next(value for kind, value in segments if kind == "pet")
    assert guard.render(pet, "om") == "damma koo"


def test_has_pet_names():
    guard = PetNameGuard()
    assert guard.has_pet_names("I love you baby") is True
    assert guard.has_pet_names("What time is the meeting") is False


def test_multiword_phrase_wins_over_overlapping_single_word():
    guard = PetNameGuard()
    segments = guard.split("You are my love")
    pet_segments = [value for kind, value in segments if kind == "pet"]
    assert len(pet_segments) == 1
    assert pet_segments[0].english == ("my love", "love")
