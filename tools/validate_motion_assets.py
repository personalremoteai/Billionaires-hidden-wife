#!/usr/bin/env python3
"""Fail early unless every scene in the selected episodes has an approved motion MP4."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def motion_path(episode_number: int, scene_number: int) -> Path:
    base = ROOT / "assets" / "episodes" / f"episode_{episode_number:03d}" / "motion"
    candidates = (
        base / f"scene_{scene_number:03d}.mp4",
        base / f"scene_{scene_number:02d}.mp4",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[0])


def video_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def validate_episode(number: int) -> list[str]:
    episode_file = ROOT / "episodes" / f"episode_{number:03d}.json"
    if not episode_file.is_file():
        return [f"Episode {number:03d}: missing {episode_file.relative_to(ROOT)}"]
    try:
        data = json.loads(episode_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Episode {number:03d}: cannot read episode JSON: {exc}"]
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return [f"Episode {number:03d}: JSON has no non-empty scenes list"]

    errors = []
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            errors.append(f"Episode {number:03d} scene {index:03d}: scene must be an object")
            continue
        try:
            scene_number = int(scene.get("scene_number") or index)
        except (TypeError, ValueError):
            errors.append(f"Episode {number:03d} scene {index:03d}: invalid scene_number")
            continue
        path = motion_path(number, scene_number)
        if not path.is_file():
            errors.append(
                f"Episode {number:03d} scene {scene_number:03d}: missing approved motion MP4 "
                f"at {path.relative_to(ROOT)}"
            )
            continue
        try:
            duration = video_duration(path)
            if duration < 0.5:
                errors.append(f"{path.relative_to(ROOT)}: clip is too short ({duration:.2f}s)")
            else:
                print(f"OK {path.relative_to(ROOT)} — {duration:.1f}s")
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: ffprobe could not read this MP4: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()
    if args.start < 1 or args.count < 1 or args.start + args.count - 1 > 70:
        parser.error("episode range must stay within 1–70")
    errors = []
    for number in range(args.start, args.start + args.count):
        errors.extend(validate_episode(number))
    if errors:
        print("Motion asset validation failed:")
        for error in errors:
            print(f" - {error}")
        print("Generate and visually approve a motion MP4 for every scene, then rerun.")
        return 1
    print("Motion asset validation passed. All selected scenes have readable motion MP4s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
