# Episode engine overlay

Adds a Gemini-powered episode batch generator and prompt exporter. This addition does not delete existing files.

## Install
```bash
python -m pip install -r requirements-engine.txt
```
Set `GEMINI_API_KEY` as an environment variable or a GitHub Actions secret. Never put the key in code or commit it.

## Test without API usage
```bash
python tools/production_engine.py --count 3 --dry-run
python -m unittest discover -s tests -v
```

## Generate in small batches first
```bash
python tools/production_engine.py --start 1 --count 1
python tools/production_engine.py --start 2 --count 4
```
Review character names and continuity before scaling. Existing output files are skipped unless `--overwrite` is supplied. Generate in order so each episode can carry forward the previous episode's cliffhanger.

## Validate and prepare prompts
```bash
python tools/production_engine.py --validate-all
python tools/production_engine.py --prepare-prompts
```
Output files go under `production/episode_outputs/`. Prompt preparation creates image prompts and dialogue/narration text per scene. This script does not generate images, audio, or MP4s itself; those require separate provider integrations and cost/quota checks. Model availability may change; set `GEMINI_MODEL` to a model enabled for your API key if the default is unavailable.
