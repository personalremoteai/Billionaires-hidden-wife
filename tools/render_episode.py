def render_fal_talking_scene(image, audio, target, duration):
    """Optional paid talking-image animation via fal.ai Sync Lipsync v3."""
    import urllib.request
    import fal_client
    target.parent.mkdir(parents=True, exist_ok=True)
    image_url = fal_client.upload_file(str(image))
    audio_url = fal_client.upload_file(str(audio))
    result = fal_client.subscribe(
        "fal-ai/sync-lipsync/v3/image-to-video",
        arguments={"image_url": image_url, "audio_url": audio_url},
    )
    video_url = (result.get("video") or {}).get("url")
    if not video_url:
        raise RuntimeError(f"fal.ai lipsync returned no video URL: {result}")
    raw = target.with_name(target.stem + ".provider.mp4")
    try:
        urllib.request.urlretrieve(video_url, raw)
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration={max(0.0, duration):.3f}"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",raw,"-i",audio,
             "-map","0:v:0","-map","1:a:0","-vf",vf,"-af","apad","-t",f"{duration:.3f}",
             "-r","30","-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","128k","-ar","44100","-ac","2","-movflags","+faststart",target])
    finally:
        if raw.exists(): raw.unlink()
    print(f"  scene {target.stem}: lip-synced with fal.ai")
    return target

def render_scene(image, audio, scene, n, number, outdir, dry_run=False):
    planned = float(scene.get('duration_seconds') or 8)
    if audio and audio.exists(): duration = max(planned, probe_duration(audio))
    else: duration = planned
    duration = max(2.0, min(duration, 180.0))
    target = outdir / 'scenes' / f'scene_{number:03d}.mp4'
    target.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        provider = "fal.ai lip-sync" if audio and os.getenv("FAL_KEY") else "FFmpeg pan/zoom"
        print(f'  scene {number}: image={image.name}; audio={audio.name if audio else "silent"}; duration={duration:.1f}s; motion={provider}')
        return target
    if audio and os.getenv("FAL_KEY"):
        try:
            return render_fal_talking_scene(image, audio, target, duration)
        except Exception as exc:
            if os.getenv("REQUIRE_LIPSYNC", "").strip().lower() in ("1", "true", "yes"):
                raise
            print(f"  WARNING: lip-sync provider failed ({exc}); falling back to FFmpeg pan/zoom.", file=sys.stderr)
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.00055,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,setsar=1,format=yuv420p"
    cmd = ['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','30','-i',image]
    if audio and audio.exists(): cmd += ['-i', audio]
    else: cmd += ['-f','lavfi','-i','anullsrc=r=44100:cl=stereo']
    cmd += ['-vf',vf,'-t',f'{duration:.3f}','-r','30','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-af','apad','-c:a','aac','-b:a','128k','-ar','44100','-ac','2','-movflags','+faststart',target]
    run(cmd)
    return target

def render_episode(n, dry_run=False):
    path = episode_file(n)
    if not path.is_file(): raise FileNotFoundError(f'Missing {path.relative_to(ROOT)}; paste the approved script JSON into episodes/episode_{n:03d}.json first.')
    data = json.loads(path.read_text(encoding='utf-8'))
    errors = validate_episode(data, n)
    if errors: raise ValueError('; '.join(errors))
    outdir = episode_dir(n); outdir.mkdir(parents=True, exist_ok=True)
    print(f"Episode {n:03d}: {data.get('title') or '(untitled)'} — {len(data['scenes'])} scene(s)")
    scenes = []
    for idx, scene in enumerate(data['scenes'], 1):
        number = int(scene.get('scene_number') or idx)
        image = image_for(scene, n, number)
        if not image: raise FileNotFoundError(f'No image found for episode {n:03d}, scene {number:03d}. Add assets/episodes/episode_{n:03d}/scene_{number:03d}.png (or jpg/jpeg/webp).')
        audio = build_scene_audio(scene, n, number, outdir, dry_run=dry_run)
        scenes.append(render_scene(image, audio, scene, n, number, outdir, dry_run=dry_run))
    if dry_run:
        print('DRY RUN complete: no audio/video generated.')
        return None
    final = outdir / f'episode_{n:03d}.mp4'
    listing = outdir / 'scenes' / 'concat.txt'
    listing.write_text('\n'.join(f"file '{p.as_posix()}'" for p in scenes)+'\n', encoding='utf-8')
    run(['ffmpeg','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',listing,'-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','44100','-ac','2','-movflags','+faststart','-y',final])
    print(f'EXPORTED {final.relative_to(ROOT)} ({probe_duration(final):.1f}s)')
    return final

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--episode', type=int, help='Render one episode number (1–70)')
    p.add_argument('--start', type=int, default=1, help='First episode number')
    p.add_argument('--count', type=int, default=1, help='Number of sequential episodes')
    p.add_argument('--dry-run', action='store_true', help='Validate scripts and scene image paths without generating audio/video')
    a=p.parse_args()
    if a.episode is not None: start,count=a.episode,1
    else: start,count=a.start,a.count
    if start<1 or count<1 or start+count-1>70: p.error('episode range must stay within 1–70')
    missing=[]
    for n in range(start,start+count):
        try: render_episode(n,dry_run=a.dry_run)
        except Exception as exc:
            print(f'ERROR episode {n:03d}: {exc}', file=sys.stderr); missing.append(n)
    if missing: print('Failed episodes:', ', '.join(f'{n:03d}' for n in missing), file=sys.stderr); return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
