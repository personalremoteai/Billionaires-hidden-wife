import json
import sys
from pathlib import Path

REQUIRED = ("episode_number", "title", "status", "scenes", "cliffhanger")

def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/validate_episode.py episodes/episode_001.json")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Could not read valid JSON: {exc}")
        raise SystemExit(1)

    errors = [f"Missing required field: {key}" for key in REQUIRED if key not in data]
    if not isinstance(data.get("scenes"), list):
        errors.append("'scenes' must be a list")

    for i, scene in enumerate(data.get("scenes", []), start=1):
        for key in ("scene_number", "location", "characters", "action"):
            if key not in scene:
                errors.append(f"Scene {i}: missing '{key}'")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    print(f"OK: {path} — episode {data['episode_number']} has {len(data['scenes'])} scene(s).")

if __name__ == "__main__":
    main()
