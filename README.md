# The Billionaire's Hidden Wife — Episode Production

This repository is the **rendering and assembly stage**. Write and approve scripts in ChatGPT, paste the structured episode JSON into `episodes/episode_NNN.json`, and upload the approved scene images. The workflow does not write or rewrite your story.

## Pipeline

1. **Input:** approved episode JSON and one image per scene.
2. **Voice:** dialogue lines are turned into speech using Edge TTS. You can override speaker voices with the GitHub repository variable `VOICE_MAP_JSON` (JSON object mapping exact speaker names to Edge voice names).
3. **Talking-face motion:** dialogue scenes are sent to the public community [SadTalker Hugging Face Space](https://huggingface.co/spaces/kevinwang676/SadTalker) through Gradio. No `FAL_KEY` or paid API key is needed. Community compute can queue, sleep, change its API, or become unavailable; if it fails, the renderer falls back to FFmpeg pan/zoom unless `REQUIRE_LIPSYNC=1`.
4. **Motion fallback:** FFmpeg adds a slow cinematic pan/zoom to each scene image if the public Space fails or is disabled.
5. **Assembly:** scenes are rendered at 1080×1920, 30 fps and joined into a vertical MP4.
6. **Export:** GitHub Actions uploads the MP4s and generated voiceovers as a downloadable artifact (available for 7 days). Large video files are not committed to Git.

## Where to put files

- Script: `episodes/episode_001.json` (repeat for episodes 002–070).
- Scene images: `assets/episodes/episode_001/scene_001.png`, `scene_002.png`, and so on. JPG, JPEG, and WebP are also supported.
- Optional alternate image location: `assets/episode_001/scene_001.png`.
- Optional audio you already have: add an existing file path to the scene's `voiceover_files` array or `audio_file` field.
- Output: `generated/episode_001/episode_001.mp4`, with scene clips and voiceovers beside it.

Use zero-padded episode and scene numbers (for example, `episode_001`, `scene_001.png`) so the pipeline finds the right assets. A scene's `dialogue` may be a list of objects like `{"speaker":"Isabella Hart","line":"I came back for my daughter."}`, or plain text strings. The script should include `duration_seconds` for each scene.

## Render from GitHub on Android

1. Commit the episode JSON and scene images to the repository. Keep each scene image matched to the same scene number.
2. Open the [Actions tab](https://github.com/personalremoteai/Billionaires-hidden-wife/actions).
3. Choose **Render episode MP4s** → **Run workflow**.
4. Enter the first episode number and batch size. Start with episode `1`, count `1`.
5. When the run finishes, open the run, scroll to **Artifacts**, and download `rendered-episodes-1-1`. Extract the ZIP to get the MP4.

## Local run (Codespaces or a computer)

Install FFmpeg, then:

```bash
python -m pip install -r requirements-video.txt
python tools/render_episode.py --episode 1 --dry-run
python tools/render_episode.py --episode 1
```

The dry run checks the JSON and image paths without synthesizing audio or rendering video.

## Important limitations

- SadTalker is open-source, but this workflow calls a shared community-hosted Space, not a private GPU. It is free to try, but not guaranteed unlimited or always online. The `kevinwang676/SadTalker` Space may change or become unavailable; set repository variable `SADTALKER_SPACE` or `SADTALKER_API_NAME` if you use another compatible Space.
- Edge TTS is an online voice service, not an unlimited guaranteed free tier. Run a single test episode first.
- This pipeline renders existing images and scripts. It does not generate story scripts or scene images.
- Upload only images and audio you have the rights to use. Never commit API keys or secrets.

## Story assets

- `story_bible/series_bible.md` — canon and continuity.
- `characters/character_bible.md` — stable character appearance and voice direction.
- `prompts/` — reusable scene, character, voice, and image-to-video prompt templates.
- `tools/validate_episode.py` — checks the episode JSON structure.
