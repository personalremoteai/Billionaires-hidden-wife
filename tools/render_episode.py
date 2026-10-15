#!/usr/bin/env python3
"""Render user-authored episode JSON and scene images into a vertical MP4."""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".ppm")
DEFAULT_VOICES = {
    "isabella": "en-US-JennyNeural",
    "alexander": "en-US-GuyNeural",
    "lily": "en-US-AnaNeural",
    "victoria": "en-US-AriaNeural",
}

def run(cmd):
    subprocess.run([str(x) for x in cmd], check=True, cwd=ROOT)

def episode_file(n):
    return ROOT / "episodes" / f"episode_{n:03d}.json"

def episode_dir(n):
    return ROOT / "generated" / f"episode_{n:03d}"

def image_for(scene, n, number):
    candidates = []
    for key in ("image_file", "image_path", "scene_image", "image"):
        value = scene.get(key)
        if isinstance(value, str) and value.strip():
            p = Path(value)
            candidates.append(p if p.is_absolute() else ROOT / p)
    for base in (
        ROOT / "assets" / "episodes" / f"episode_{n:03d}",
        ROOT / "assets" / f"episode_{n:03d}",
        ROOT / "generated" / f"episode_{n:03d}" / "images",
    ):
        for ext in IMAGE_EXTS:
            candidates.append(base / f"scene_{number:03d}{ext}")
            candidates.append(base / f"scene_{number:02d}{ext}")
    for item in scene.get("images", []) if isinstance(scene.get("images"), list) else []:
        if isinstance(item, str):
            p = Path(item)
            candidates.append(p if p.is_absolute() else ROOT / p)
    for p in candidates:
        if p.is_file():
            return p.resolve()
    return None

def dialogue_lines(scene):
    data = scene.get("dialogue", [])
    if isinstance(data, str):
        return [{"speaker": "Narrator", "line": data}] if data.strip() else []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if isinstance(item, str) and item.strip():
            out.append({"speaker": "Narrator", "line": item.strip()})
        elif isinstance(item, dict):
            line = item.get("line") or item.get("text") or item.get("dialogue") or ""
            if isinstance(line, str) and line.strip():
                out.append({
                    "speaker": str(item.get("speaker") or item.get("character") or "Narrator"),
                    "line": line.strip(),
                    "emotion": item.get("emotion", ""),
                })
    narration = scene.get("narration")
    if isinstance(narration, str) and narration.strip():
        out.append({"speaker": "Narrator", "line": narration.strip()})
    return out

def validate_episode(data, n):
    errors = []
    if not isinstance(data, dict):
        return ["episode JSON must be an object"]
    for key in ("episode_number", "scenes"):
        if key not in data:
            errors.append(f"missing required field: {key}")
    if data.get("episode_number") != n:
        errors.append(f"episode_number must equal {n}")
    if not isinstance(data.get("scenes"), list) or not data.get("scenes"):
        errors.append("scenes must be a non-empty list")
    else:
        for i, scene in enumerate(data["scenes"], 1):
            if not isinstance(scene, dict):
                errors.append(f"scene {i} must be an object")
                continue
            if not scene.get("scene_number"):
                scene["scene_number"] = i
    return errors

def voice_for(speaker):
    try:
        custom = json.loads(os.getenv("VOICE_MAP_JSON", "{}"))
    except json.JSONDecodeError:
        custom = {}
    if isinstance(custom, dict):
        for name, voice in custom.items():
            if str(name).casefold() == speaker.casefold() and isinstance(voice, str) and voice:
                return voice
    low = speaker.casefold()
    for character, voice in DEFAULT_VOICES.items():
        if character in low:
            return voice
    if any(word in low for word in ("he ", "man", "father", "husband", "alex")):
        return "en-US-GuyNeural"
    if "narrat" in low:
        return "en-US-AriaNeural"
    return "en-US-JennyNeural"

async def make_tts(text, voice, target):
    import edge_tts
    await edge_tts.Communicate(text=text, voice=voice).save(str(target))

def probe_duration(path):
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip()
    return float(raw)

def build_scene_audio(scene, n, number, outdir, dry_run=False):
    values = scene.get("voiceover_files", [])
    if isinstance(values, str):
        values = [values]
    for value in values if isinstance(values, list) else []:
        if isinstance(value, str):
            p = Path(value)
            p = p if p.is_absolute() else ROOT / p
            if p.is_file():
                return p.resolve()
    explicit = scene.get("audio_file") or scene.get("voiceover_file")
    if isinstance(explicit, str) and explicit:
        p = Path(explicit)
        p = p if p.is_absolute() else ROOT / p
        if p.is_file():
            return p.resolve()
    lines = dialogue_lines(scene)
    if not lines:
        return None
    audio_dir = outdir / "voiceovers"
    audio_dir.mkdir(parents=True, exist_ok=True)
    scene_dir = audio_dir / f"scene_{number:03d}"
    scene_dir.mkdir(parents=True, exist_ok=True)
    line_files = []
    for i, line in enumerate(lines, 1):
        target = scene_dir / f"line_{i:02d}.mp3"
        if not target.exists():
            if dry_run:
                continue
            asyncio.run(make_tts(line["line"], voice_for(line["speaker"]), target))
        line_files.append(target)
    if dry_run or not line_files:
        return None
    silence = scene_dir / "pause.mp3"
    if not silence.exists():
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "anullsrc=r=24000:cl=mono", "-t", "0.28",
             "-c:a", "libmp3lame", "-q:a", "6", "-y", silence])
    concat_list = scene_dir / "concat.txt"
    entries = []
    for i, f in enumerate(line_files):
        entries.append(f"file '{f.as_posix()}'")
        if i < len(line_files) - 1:
            entries.append(f"file '{silence.as_posix()}'")
    concat_list.write_text("\n".join(entries) + "\n", encoding="utf-8")
    combined = audio_dir / f"scene_{number:03d}.mp3"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "concat",
         "-safe", "0", "-i", concat_list, "-c:a", "libmp3lame", "-q:a", "4",
         "-y", combined])
    return combined

def render_sadtalker_space(image, audio, target, duration):
    """Use a public community SadTalker Space; no paid API key is required."""
    import urllib.request
    from gradio_client import Client, handle_file
    space = os.getenv("SADTALKER_SPACE", "kevinwang676/SadTalker")
    client = Client(space, verbose=False)
    # The current community Space exposes one unnamed endpoint (fn_index=0),
    # with eight inputs. Inspect the API and use the documented unnamed endpoint.
    # Older Space versions may expose named endpoints, so try those only if needed.
    api_info = client.view_api(return_format="dict")
    unnamed = api_info.get("unnamed_endpoints", {})
    if "0" in unnamed:
        result = client.predict(
            handle_file(str(image)), handle_file(str(audio)),
            "crop", True, False, 1, "256", 0,
            fn_index=0,
        )
        print("  SadTalker endpoint accepted: unnamed fn_index=0")
    else:
        configured = os.getenv("SADTALKER_API_NAME", "").strip()
        named = api_info.get("named_endpoints", {})
        candidates = [configured] if configured else []
        candidates += [name for name in ("/generate", "/gen_video", "/predict", "/run", "/test") if name not in candidates]
        result = None
        errors = []
        for api_name in candidates:
            if api_name not in named:
                continue
            try:
                result = client.predict(
                    handle_file(str(image)), handle_file(str(audio)),
                    "crop", True, False, 1, "256", 0,
                    api_name=api_name,
                )
                print(f"  SadTalker endpoint accepted: {api_name}")
                break
            except Exception as exc:
                errors.append(f"{api_name}: {exc}")
        if result is None:
            raise RuntimeError(
                "No compatible SadTalker endpoint found. "
                f"Named endpoints: {list(named.keys())}; errors: {errors}"
            )
    if isinstance(result, (list, tuple)):
        result = next((v for v in result if isinstance(v, (str, dict)) and v), None)
    if isinstance(result, dict):
        video_value = result.get("video") or result.get("path") or result.get("url")
        if isinstance(video_value, dict):
            video_value = video_value.get("url") or video_value.get("path")
    else:
        video_value = result
    if not isinstance(video_value, str) or not video_value:
        raise RuntimeError(f"SadTalker Space returned no video path: {result!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = target.with_name(target.stem + ".provider.mp4")
    try:
        if video_value.startswith(("http://", "https://")):
            urllib.request.urlretrieve(video_value, raw)
        else:
            source = Path(video_value)
            if not source.is_file():
                raise RuntimeError(f"SadTalker returned an inaccessible video path: {video_value}")
            shutil.copy2(source, raw)
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration={max(0.0, duration):.3f}"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", raw, "-i", audio,
             "-map", "0:v:0", "-map", "1:a:0", "-vf", vf, "-af", "apad",
             "-t", f"{duration:.3f}", "-r", "30", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
             "-movflags", "+faststart", target])
    finally:
        if raw.exists():
            raw.unlink()
    print(f"  scene {target.stem}: lip-synced with free community Space {space}")
    return target

def render_scene(image, audio, scene, n, number, outdir, dry_run=False):
    planned = float(scene.get("duration_seconds") or 8)
    if audio and audio.exists():
        duration = max(planned, probe_duration(audio))
    else:
        duration = planned
    duration = max(2.0, min(duration, 180.0))
    target = outdir / "scenes" / f"scene_{number:03d}.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        provider = "SadTalker community Space" if audio and os.getenv("SADTALKER_SPACE", "kevinwang676/SadTalker") else "FFmpeg pan/zoom"
        print(f"  scene {number}: image={image.name}; audio={audio.name if audio else 'silent'}; duration={duration:.1f}s; motion={provider}")
        return target
    if audio and os.getenv("SADTALKER_SPACE", "kevinwang676/SadTalker"):
        try:
            return render_sadtalker_space(image, audio, target, duration)
        except Exception as exc:
            if os.getenv("REQUIRE_LIPSYNC", "").strip().lower() in ("1", "true", "yes"):
                raise
            print(f"  WARNING: lip-sync provider failed ({exc}); falling back to FFmpeg pan/zoom.", file=sys.stderr)
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.00055,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,setsar=1,format=yuv420p"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1",
           "-framerate", "30", "-i", image]
    if audio and audio.exists():
        cmd += ["-i", audio]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-vf", vf, "-t", f"{duration:.3f}", "-r", "30", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-af", "apad",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", target]
    run(cmd)
    return target

def render_episode(n, dry_run=False):
    path = episode_file(n)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path.relative_to(ROOT)}; paste the approved script JSON into episodes/episode_{n:03d}.json first.")
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_episode(data, n)
    if errors:
        raise ValueError("; ".join(errors))
    outdir = episode_dir(n)
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Episode {n:03d}: {data.get('title') or '(untitled)'} — {len(data['scenes'])} scene(s)")
    scenes = []
    for idx, scene in enumerate(data["scenes"], 1):
        number = int(scene.get("scene_number") or idx)
        image = image_for(scene, n, number)
        if not image:
            raise FileNotFoundError(f"No image found for episode {n:03d}, scene {number:03d}. Add assets/episodes/episode_{n:03d}/scene_{number:03d}.png (or jpg/jpeg/webp).")
        audio = build_scene_audio(scene, n, number, outdir, dry_run=dry_run)
        scenes.append(render_scene(image, audio, scene, n, number, outdir, dry_run=dry_run))
    if dry_run:
        print("DRY RUN complete: no audio/video generated.")
        return None
    final = outdir / f"episode_{n:03d}.mp4"
    listing = outdir / "scenes" / "concat.txt"
    listing.write_text("\n".join(f"file '{p.as_posix()}'" for p in scenes) + "\n", encoding="utf-8")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", listing, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
         "-ac", "2", "-movflags", "+faststart", "-y", final])
    print(f"EXPORTED {final.relative_to(ROOT)} ({probe_duration(final):.1f}s)")
    return final

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--episode", type=int, help="Render one episode number (1–70)")
    p.add_argument("--start", type=int, default=1, help="First episode number")
    p.add_argument("--count", type=int, default=1, help="Number of sequential episodes")
    p.add_argument("--dry-run", action="store_true", help="Validate scripts and scene image paths without generating audio/video")
    a = p.parse_args()
    if a.episode is not None:
        start, count = a.episode, 1
    else:
        start, count = a.start, a.count
    if start < 1 or count < 1 or start + count - 1 > 70:
        p.error("episode range must stay within 1–70")
    failed = []
    for n in range(start, start + count):
        try:
            render_episode(n, dry_run=a.dry_run)
        except Exception as exc:
            print(f"ERROR episode {n:03d}: {exc}", file=sys.stderr)
            failed.append(n)
    if failed:
        print("Failed episodes: " + ", ".join(f"{n:03d}" for n in failed), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
