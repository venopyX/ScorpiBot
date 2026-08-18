"""Mask/restore logic that shields pet names from machine translation.

See app.core.glossary for the "why" and for the actual word list. This
module is the "how": it finds pet-name phrases in a string, replaces them
with placeholder tokens that survive a round-trip through Google Translate
untouched, and later swaps those tokens for the correct natural term in the
target language - so Google Translate never sees "baby" and never gets a
chance to hand back the Amharic word for a literal child.
"""
import re
from typing import Dict, List, Tuple

from app.core.glossary import PET_NAMES, PetName

# Placeholder tokens deliberately look like meaningless alphanumeric junk so
# translation engines have nothing to "helpfully" translate. Digits keep each
# token unique; the "zzptzz" wrapper keeps it from colliding with real words.
_TOKEN_TEMPLATE = "zzptzz{index}zzptzz"
# Lenient on purpose: translators occasionally insert spaces or flip case
# around opaque tokens, so we match loosely and rebuild the canonical form
# from whatever digits we find between the "zzptzz" markers.
_TOKEN_PATTERN = re.compile(r"zz\s*pt\s*zz\s*(\d+)\s*zz\s*pt\s*zz", re.IGNORECASE)


def _build_lookup() -> List[Tuple[re.Pattern, PetName]]:
    """Build (regex, PetName) pairs, longest phrase first so multi-word
    entries like "my love" are matched before the single word "love"."""
    entries = []
    for pet_name in PET_NAMES:
        for phrase in pet_name.english:
            pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            entries.append((pattern, pet_name))
    # Longest phrase (by character length) first.
    entries.sort(key=lambda pair: len(pair[0].pattern), reverse=True)
    return entries


_LOOKUP = _build_lookup()


class PetNameGuard:
    """Masks English pet names before translation and restores natural
    target-language equivalents afterward."""

    def mask(self, text: str) -> Tuple[str, Dict[str, PetName]]:
        """Replace known pet-name phrases with placeholder tokens.

        Returns the masked text and a mapping of token -> PetName so the
        caller can restore the right word later.
        """
        mapping: Dict[str, PetName] = {}
        masked = text
        index = 0

        for pattern, pet_name in _LOOKUP:
            def _replace(match: "re.Match", pet_name: PetName = pet_name) -> str:
                nonlocal index
                token = _TOKEN_TEMPLATE.format(index=index)
                mapping[token] = pet_name
                index += 1
                return token

            masked = pattern.sub(_replace, masked)

        return masked, mapping

    def restore(self, text: str, mapping: Dict[str, PetName], language: str) -> str:
        """Swap placeholder tokens back in as natural target-language terms.

        `language` should be one of "am" (Amharic), "om" (Afaan Oromo), or
        "en" (plain English, e.g. when translation was skipped).
        """
        if not mapping:
            return text

        def _restore_match(match: "re.Match") -> str:
            token = _TOKEN_TEMPLATE.format(index=match.group(1))
            pet_name = mapping.get(token)
            if pet_name is None:
                return token
            if language == "am":
                return pet_name.amharic
            if language == "om":
                return pet_name.oromo
            # English (or unknown target) - just use the first canonical form.
            return pet_name.english[0]

        return _TOKEN_PATTERN.sub(_restore_match, text)
