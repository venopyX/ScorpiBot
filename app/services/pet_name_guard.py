"""Segment-splitting logic that keeps pet names away from machine translation
entirely, instead of trying to smuggle them through it.

See app.core.glossary for the "why" and for the actual word list.

FIRST ATTEMPT (superseded): placeholder tokens
------------------------------------------------
The original version of this module replaced each pet name with a fake
Latin word (e.g. "zzptzz0zzptzz") and translated the whole sentence in one
call, betting that Google Translate would leave an unrecognized token
untouched. It doesn't. For a Latin->Ge'ez pair especially, Google's NMT
treats unknown Latin tokens as foreign words to be *transliterated* into
the target script by sound, so "zzptzz0zzptzz" came back as mangled
Ge'ez-script noise (e.g. "\u12CB\u134D\u1355\u1275\u12CB0\u12CB\u134D\u1355\u1275\u12CB") instead of surviving
untouched. Never send anything pet-name-related to the translator - that's
this version's whole design.

CURRENT APPROACH: split, translate the rest, splice the glossary word in
--------------------------------------------------------------------------
`split()` breaks the sentence into an ordered list of plain-text chunks and
pet-name matches. Only the plain-text chunks are ever handed to Google
Translate, each as its own small call. The pet-name chunks are never
translated at all - they're replaced directly with the natural glossary
term for the target language and spliced back into place. Google Translate
never sees the pet name, so it has nothing to mistranslate or mangle.
"""
import re
from typing import List, Tuple

from app.core.glossary import PET_NAMES, PetName

Segment = Tuple[str, object]  # ("text", str) or ("pet", PetName)


def _build_lookup() -> List[Tuple[re.Pattern, PetName]]:
    """Build (regex, PetName) pairs, longest phrase first so multi-word
    entries like "my love" are preferred over the single word "love"."""
    entries = []
    for pet_name in PET_NAMES:
        for phrase in pet_name.english:
            pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            entries.append((pattern, pet_name))
    entries.sort(key=lambda pair: len(pair[0].pattern), reverse=True)
    return entries


_LOOKUP = _build_lookup()


class PetNameGuard:
    """Splits text into translatable chunks and pet-name chunks, and knows
    how to render a pet name naturally for a given target language."""

    def split(self, text: str) -> List[Segment]:
        """Break `text` into an ordered list of ("text", str) and
        ("pet", PetName) segments. Longer phrases win over shorter
        overlapping ones (e.g. "my love" over bare "love")."""
        if not text:
            return [("text", text)]

        occupied = bytearray(len(text))
        matches: List[Tuple[int, int, PetName]] = []

        for pattern, pet_name in _LOOKUP:
            for m in pattern.finditer(text):
                start, end = m.start(), m.end()
                if any(occupied[start:end]):
                    continue
                matches.append((start, end, pet_name))
                for i in range(start, end):
                    occupied[i] = 1

        if not matches:
            return [("text", text)]

        matches.sort(key=lambda m: m[0])

        segments: List[Segment] = []
        cursor = 0
        for start, end, pet_name in matches:
            if start > cursor:
                segments.append(("text", text[cursor:start]))
            segments.append(("pet", pet_name))
            cursor = end
        if cursor < len(text):
            segments.append(("text", text[cursor:]))

        return segments

    def render(self, pet_name: PetName, target_lang: str) -> str:
        """Return the natural equivalent for `pet_name` in `target_lang`
        ("am", "om", or anything else -> plain English)."""
        if target_lang == "am":
            return pet_name.amharic
        if target_lang == "om":
            return pet_name.oromo
        return pet_name.english[0]

    def has_pet_names(self, text: str) -> bool:
        return any(kind == "pet" for kind, _ in self.split(text))
