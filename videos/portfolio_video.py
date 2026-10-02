"""Portfolio slideshow assembly (Task 21, Part 1).

Still PNGs -> per-slide Ken Burns (slow zoom) segments -> concat ->
mux with voiceover + watermark + fades via compose_video.
"""

import subprocess
from pathlib import Path

from videos.compose_video import audio_duration, compose_video, stretch_audio_to
from videos.portfolio_slides import SLIDE_MIN_DURATIONS

FPS = 30


def slide_durations(audio_dur: float, target_total: float = 55.8) -> list:
    """Stretch minimums proportionally to audio, then pad evenly to target.

    Total lands at min(target_total, audio + 0.4 * n) so short audio never
    over-pads and long audio never exceeds the target.
    """
    mins = list(SLIDE_MIN_DURATIONS)
    base = sum(mins)
    scaled = [max(m, audio_dur * m / base) for m in mins]
    total = sum(scaled)
    cap = min(target_total, audio_dur + 0.5 * len(mins))
    if total < cap:
        pad = (cap - total) / len(scaled)
        scaled = [d + pad for d in scaled]
    return scaled


def _zoompan_filter(frames: int, zoom_in: bool) -> str:
    if zoom_in:
        z = f"1.00+0.08*on/{frames}"
    else:
        z = f"1.08-0.08*on/{frames}"
    return (
        f"scale=3840:2160,"
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:s=1920x1080:fps={FPS}"
    )


def build_slideshow(slide_pngs: list, durations: list, tmp_dir: Path) -> Path:
    """Render one Ken Burns segment per slide, concat to silent slideshow.mp4."""
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    seg_paths = []
    for i, (png, dur) in enumerate(zip(slide_pngs, durations)):
        frames = max(int(round(dur * FPS)), FPS)
        seg = tmp_dir / f"seg_{i:02d}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(png),
             "-vf", _zoompan_filter(frames, zoom_in=(i % 2 == 0)),
             "-frames:v", str(frames),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-pix_fmt", "yuv420p", str(seg)],
            check=True,
        )
        seg_paths.append(seg)
    concat_list = tmp_dir / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in seg_paths), encoding="utf-8"
    )
    out = tmp_dir / "slideshow.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(out)],
        check=True,
    )
    return out


def build_portfolio_video(
    slide_pngs: list,
    audio_mp3: Path,
    logo_png: Path,
    output: Path,
    tmp_dir: Path,
    target_total: float = 55.8,
) -> Path:
    """Full portfolio pipeline: durations -> slideshow -> compose. Returns mp4.

    Voiceover is gently time-stretched (pitch-preserving) to fill the
    slideshow minus a half-second tail, so the final video lands at ~55s
    with the fade-out fully visible.
    """
    audio_dur = audio_duration(audio_mp3)
    durations = slide_durations(audio_dur, target_total)
    total = sum(durations)
    tmp_dir = Path(tmp_dir)
    audio_target = total - 0.5
    if audio_dur < audio_target - 0.2:
        stretched = tmp_dir / "voice_stretched.mp3"
        audio_mp3 = stretch_audio_to(audio_mp3, stretched, audio_target)
    slideshow = build_slideshow(slide_pngs, durations, tmp_dir)
    return compose_video(slideshow, audio_mp3, logo_png, output, total)
