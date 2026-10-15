# Full-body / scene motion — experimental workflow

## Recommended tool stack

- **LTX-Video image-to-video** in Google Colab (when a GPU is available): creates a short moving clip from one of your approved storyboard images.
- **SadTalker community Space**: optional talking-head lip-sync attempt. It is not a full-body animation engine; this repository has recently encountered a Gradio “Unknown protocol: ws” failure, so its compatibility is not yet confirmed.
- **FFmpeg + GitHub Actions**: attaches the script-generated voiceover, assembles scenes, and exports the vertical MP4.
- **Remotion**: optional titles/overlays/editing. It does not generate body motion, so it is not a substitute for LTX-Video.

## Generate and approve one test clip

1. Open the [LTX-Video Colab notebook](https://colab.research.google.com/github/personalremoteai/Billionaires-hidden-wife/blob/main/notebooks/colab_ltx_image_to_video.ipynb).
2. In Colab, choose **Runtime → Change runtime type → GPU** when available. Free GPU access is not guaranteed; do not pay just to test.
3. Run the notebook cells in order and upload **one approved individual scene image** (not the whole nine-panel storyboard). The notebook downloads model weights/software only, not scene/reference images from the web.
4. Inspect the result for face drift, body/hand glitches, flicker, continuity, and unwanted characters. Keep it only if acceptable.
5. Download the MP4 and upload it to **assets/episodes/episode_001/motion/scene_001.mp4**. Preserve the original approved still. Match the filename to the scene number for each additional approved clip.

## Render an episode

Open [GitHub Actions](https://github.com/personalremoteai/Billionaires-hidden-wife/actions) → **Render episode MP4s** → **Run workflow**.

- Choose **talking_head_lipsync** to use the SadTalker attempt for scenes without supplied motion clips. The shared public Space may fail; it is not a guaranteed free service.
- Choose **approved_motion_clips** only after **every scene** in every selected episode has a readable MP4 at **assets/episodes/episode_NNN/motion/scene_NNN.mp4**. The workflow checks this first and fails clearly if any are missing. The renderer uses those clips and replaces their audio with the episode's generated dialogue voiceover.

Start with one episode. The exported artifact is temporary (7 days); download it and review it before scaling.

## Important limits

- LTX-Video may create body, clothing, hair, background, and camera motion, but it does **not** guarantee stable character identity, correct anatomy, lip-sync, walking/contact, or believable two-person dramatic interaction.
- A portrait that only shows a face cannot reliably produce convincing full-body motion. Use a scene image that already shows the body/pose when that movement matters.
- Free Colab GPUs can be unavailable, disconnect, run out of memory, or take a long time. This is not a guaranteed free service for five episodes per day.
- GitHub-hosted Actions runners do not include a standard free GPU. GitHub is used for validation and assembly, not the model's heavy video generation.
- No stock or web-downloaded story images are used. Keep only your approved character/storyboard assets and clips you have reviewed. Never commit access tokens or API keys.
