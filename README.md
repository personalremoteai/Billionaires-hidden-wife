# The Billionaire's Hidden Wife — Production Starter

This is a starter workspace for planning 70 connected short-drama episodes. It does **not** contain 70 finished scripts or an automatic video generator yet. It gives us a clean structure to build those safely in stages.

## Recommended first workflow

1. Fill in `story_bible/series_bible.md`.
2. Approve the reference sheets in `characters/character_bible.md`.
3. Draft and review episodes in `episodes/episode_001.json` through `episode_070.json`.
4. Generate character/scene images with Gemini using the approved references.
5. Generate dialogue audio with a selected TTS engine.
6. Test image-to-video on a few high-value shots; use pan/zoom motion for the rest.
7. Download assets to your Android phone and assemble in CapCut, YouCut, or Kwai Cut.

## Project structure

- `story_bible/` — canon, timeline, relationship rules, and continuity notes.
- `characters/` — character descriptions and approved reference image manifest.
- `episodes/` — episode-by-episode structured script and production instructions.
- `prompts/` — reusable image, motion, and voice prompts.
- `assets/` — approved reusable images, props, and locations.
- `generated/` — generated scene images, voiceovers, and clips (do not commit large files unnecessarily).
- `tools/` — lightweight validation and packaging utilities.

## API key safety

Never paste your Gemini API key into a script, README, chat, or GitHub repository. Keep it private in an environment variable named `GEMINI_API_KEY` or in GitHub Actions Secrets if you later add automation. `.env` is ignored by Git.

## Cost and quota guardrails

- Start with one character sheet and one test scene.
- Set usage limits/alerts where the provider supports them.
- Do not run a full 70-episode batch until the test output, image consistency, audio quality, and actual costs/quotas are checked.
- A Gemini API key does not imply unlimited free image generation. Check the current model pricing and free-tier availability before production.

## Current milestone

**Milestone 1: build the story bible and approve character references.**
After that, we will add a Gemini image-generation script that uses your chosen model and saves images to the correct episode folders.
