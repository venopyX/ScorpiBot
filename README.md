# ScorpiBot / Princess Selene

**Creator:** @venopyx

A flirty, multilingual (English / Amharic / Afaan Oromo) Telegram companion bot.

## What's new in this version

- **Restructured codebase** - a proper `app/` package split into `core`
  (constants, personality, glossary), `services` (AI client, translation,
  history, stickers, reactions), `handlers` (Telegram-facing logic), and
  `health` (monitoring endpoints). No more duplicate/dead handler files.
- **Sticker replies** - send Selene a sticker and she'll pull a random one
  back from the same pack.
- **AI-suggested reactions** - the AI itself decides, from the full
  conversation, whether the moment is emotional enough to react to, and
  which of a small curated emoji set fits (`❤️‍🔥 💋 🤣 🥰 😍 🔥 😭 💔 😡`).
  It's sparing on purpose - most replies get no reaction at all.
- **Pet-name glossary** - fixes the bug where English terms of endearment
  ("baby", "honey", "babe"...) were coming out of Google Translate as
  literal, non-flirty Amharic/Oromo words. See "How the pet-name fix works"
  below.

## Project layout

```
app/
  config.py              settings loaded from environment variables
  main.py                entrypoint: builds the bot, registers handlers
  core/
    constants.py          trigger keywords, limits, allowed reaction emoji
    instruction.py         personality prompt + reaction directive
    glossary.py            pet-name -> Amharic/Oromo equivalents
  services/
    ai_client.py            AI completion client (retries, error handling)
    translator.py           script detection + translation (glossary-aware)
    pet_name_guard.py       masks/restores pet names around translation
    history.py              per-user short-term chat memory
    stickers.py             sticker pack lookup + random pick, with caching
    reaction.py              parses the AI's REACT: tag out of its reply
  handlers/
    commands.py              /start /help
    messages.py               text message pipeline
    stickers.py               sticker message handler
  health/
    api.py                    FastAPI health/status endpoints
tests/                        pytest suite for the tricky bits
run.py                        `python run.py` entrypoint
```

## How the pet-name fix works

Google Translate has no idea "baby" is a term of endearment - translated
literally into Amharic it comes back as the word for a literal child, which
reads as bizarre instead of flirty. The fix is `app/core/glossary.py` (the
list of pet names you can extend) plus `app/services/pet_name_guard.py`
(the mechanism).

**An earlier version of this masked pet names with a fake placeholder word
(e.g. `baby` -> `zzptzz0zzptzz`) and translated the whole sentence in one
call, betting the placeholder would survive untouched. It didn't** - Google's
NMT engine transliterates unrecognized Latin tokens into Ge'ez script by
sound instead of leaving them alone, so the placeholder came back as
mangled Ge'ez noise instead of the pet name.

The current approach never lets Google Translate see anything related to
the pet name at all:

1. The sentence is split into an ordered list of plain-text chunks and
   pet-name chunks (`PetNameGuard.split`).
2. Only the plain-text chunks are sent to Google Translate, each as its own
   small call.
3. The pet-name chunks are never translated - they're replaced directly
   with the natural glossary term for the target language and spliced back
   into place in order.

Nothing pet-name-related ever touches the translator, so there's nothing
for it to mangle. To add a new pet name, add one `PetName(...)` entry to
`app/core/glossary.py` - nothing else needs to change.

## How AI-driven reactions work

Rather than a fixed keyword list guessing the mood, the AI is asked (see
`Instruction.reaction_directive()` in `app/core/instruction.py`) to end
every reply with a hidden control line:

```
REACT: 🔥
```
or
```
REACT: NONE
```

It's told to pick a reaction only for genuinely strong, obvious moments -
something that made it laugh, something heartbreaking, something that makes
it swoon - and to default to `NONE` for ordinary chit-chat. The directive
also drills the exact two-line shape with worked examples, since a
described format is much less reliable than a shown one for smaller
models. `app/services/reaction.py` strips that line out before the reply
is translated and shown to the user, validates the emoji against the fixed
allow-list, and uses it to fire a native Telegram reaction via
`set_message_reaction`. If the tag is missing or malformed, it fails safe
to no reaction rather than guessing - but if the model wraps a valid emoji
in extra punctuation or words (`REACT: 🔥.` or `REACT: I'll go with 🔥`),
that emoji is still found and used rather than being thrown away, since an
earlier exact-match-only version of this check was silently killing
reactions on almost any formatting deviation.

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token |
| `API_BASE_URL` | Base URL for the AI completion API |
| `API_TOKEN` | AI API auth token |
| `STICKERS_ENABLED` | `true`/`false`, default `true` |
| `REACTIONS_ENABLED` | `true`/`false`, default `true` |
| `LOG_LEVEL` | default `INFO` |
| `PORT` | health API port, default `8000` |

## Running

```bash
pip install -r requirements.txt
python run.py
```

Or with Docker:

```bash
docker compose up --build
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```
