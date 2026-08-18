"""Pet-name glossary used to protect terms of endearment from machine translation.

THE PROBLEM
-----------
Google Translate (and every generic MT engine) has no concept of romantic
register. Fed the literal word "baby", it does the dictionary-correct thing
and translates it as a literal child - Amharic ህጻን means "kid/toddler", not
a term of endearment - so a flirty line reads as bizarre or even unsettling
instead of romantic. Same story for "babe" or "honey": technically accurate,
completely wrong register.

THE FIX
-------
This file is the list you asked for: every pet-name phrase we care about,
mapped to a hand-picked, natural equivalent in each target language.
`app/services/pet_name_guard.py` is the mechanism that makes sure Google
Translate never gets a chance to touch these words at all - it swaps them
out for a placeholder before the API call and swaps the correct word back
in afterward, straight from this list, no dictionary lookup involved.

To add a new pet name, just add a PetName entry below - no other code
needs to change.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PetName:
    """One pet-name concept and its natural equivalents in each supported language.

    `english` holds every English surface form that maps to this concept.
    Multi-word forms (e.g. "my love") should be listed alongside the
    single-word one - the matcher tries longer phrases first so they aren't
    shadowed by a shorter overlapping entry.
    """

    english: Tuple[str, ...]
    amharic: str
    oromo: str


# Ordered roughly by specificity - the matcher sorts by phrase length anyway,
# but keeping related entries together makes this easier to extend later.
PET_NAMES: Tuple[PetName, ...] = (
    PetName(("my love", "love"), amharic="ፍቅሬ", oromo="jaalala koo"),
    PetName(("baby", "babe", "bae"), amharic="ውዴ", oromo="jaalalee koo"),
    PetName(("honey",), amharic="ማርዬ", oromo="damma koo"),
    PetName(("dear", "darling"), amharic="ውዴዬ", oromo="michuu koo"),
    PetName(("sweetheart",), amharic="ልቤ", oromo="onnee koo"),
    PetName(("cutie", "cute one"), amharic="ቆንጆዬ", oromo="bareedduu koo"),
    PetName(("gorgeous", "beautiful"), amharic="ውብዬ", oromo="bareedduu koo"),
    PetName(("princess",), amharic="ልዕልቲቱ", oromo="gadaanttii koo"),
    PetName(("prince",), amharic="ልዑሌ", oromo="gadaanticha koo"),
    PetName(("angel",), amharic="መልአኬ", oromo="ergamaa koo"),
    PetName(("hun",), amharic="ውዴ", oromo="jaalalee koo"),
)
