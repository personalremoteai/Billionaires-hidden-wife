# Full-body motion clips with free/open tools

## What each tool does

- **LTX-Video image-to-video** (open weights, run in Google Colab when a GPU is available): turns one of your approved storyboard images into a short clip with generated body/camera/environment motion.
- **SadTalker community Space** (existing pipeline): optional talking-head/lip-sync attempt. It is not a full-body animation engine and the public Space may be unavailable.
- **FFmpeg** (existing GitHub Actions pipeline): joins scenes, adds the script-generated voiceover, and exports a vertical MP4.
- **Remotion** is optional for advanced title cards/overlays, but it does not generate character motion itself. It is not required for this first test.

## Start with one scene

1. Open the notebook: [Open in Google Colab](https://colab.research.google.com/github/personalremoteai/Billionaires-hidden-wife/blob/main/notebooks/colab_ltx_image_to_video.ipynb).
2. In Colab, choose **Runtime → Change runtime type → T4 GPU** if available. Free GPU availability is not guaranteed; do not buy compute just to run this test.
3. Run the cells in order. Upload only the approved scene image from this repository or your phone. The notebook does not download any reference/storyboard images from the internet. It downloads model weights and software only.
4. Start with one scene, a short clip, and a simple motion prompt. Review the MP4 before generating more scenes.
5. Download the generated MP4 and add it to the repository at:
   `assets/episodes/episode_001/motion/scene_001.mp4`
   Use the matching scene number for each clip. Keep the original approved still image too.
6. Run the existing **Render Episodes** GitHub Actions workflow for that episode. The renderer now prefers a matching motion clip and combines it with the scene's script-generated voiceover. If no motion clip exists, the prior SadTalker/FFmpeg path remains available.

## Important limitations

- Image-to-video can create visible body, clothing, hair, background, and camera motion, but it does **not** guarantee accurate full-body acting, stable faces, two-person interaction, or lip-sync to the dialogue.
- A single image of a face/upper body cannot reliably produce a convincing full-body shot. For body movement, choose an approved storyboard image that already shows the character's body and pose.
- Generate one clip first and inspect for face drift, extra fingers/limbs, unwanted scene changes, and continuity errors. Keep a clip only if it preserves Isabella and Alexander well enough.
- Free Colab sessions can disconnect, run out of GPU memory, or have no GPU available. Model downloads and generation can be slow. This is not a guaranteed 5-episodes-per-day free service.
- Do not commit Hugging Face tokens, API keys, or other secrets into the notebook or repository.
