"""FFmpeg composition helpers (Task 21).

compose(): video + voiceover -> 1920x1080 MP4 (H.264, AAC 128k) with
brand watermark top-left at 15% opacity, 0.5s fade in/out, -shortest trim.

Also: audio probing + fit_audio_to_max() to enforce the 60s hard cap.
"""

import json
import subprocess
from pathlib import Path

WIDTH = 1920
HEIGHT = 1080
FADE_DUR = 0.5
WATERMARK_OPACITY = 0.15
MAX_DURATION = 58.0  # safety margin under the 60s hard cap
AUDIO_BITRATE = "128k"


def audio_duration(path: Path) -> float:
    """Return audio duration in seconds via ffprobe."""
    return _media_duration(path)


def video_duration(path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    return _media_duration(path)


def _media_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def leading_blank_seconds(
    path: Path, fps: int = 2, max_check: float = 10.0, std_thresh: float = 5.0
) -> float:
    """Timestamp of the first non-blank frame.

    Blank = flat AND bright (white about:blank / page loader). Flat dark
    frames count as content: dark heroes have low std (~3) at thumbnail
    size, so std alone cannot separate them from a white loader.
    Returns 0.0 if no blank leader is found. Tolerant of extraction
    failure (returns 0.0).
    """
    import tempfile

    from PIL import Image

    path = Path(path)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(path),
                 "-vf", f"fps={fps}", "-t", str(max_check),
                 f"{tmp}/f_%03d.png"],
                check=True,
            )
            frames = sorted(Path(tmp).glob("f_*.png"))
            for i, frame in enumerate(frames):
                px = list(Image.open(frame).convert("L").resize((160, 90))
                          .get_flattened_data())
                mean = sum(px) / len(px)
                var = sum((v - mean) ** 2 for v in px) / len(px)
                if not (var ** 0.5 < std_thresh and mean > 200):
                    return round(i / fps, 2)
            return 0.0
    except Exception:
        return 0.0


def stretch_audio_to(src: Path, dst: Path, target_dur: float) -> Path:
    """Time-stretch (pitch-preserving atempo) src to exactly target_dur."""
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tempo = audio_duration(src) / target_dur
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-filter:a", f"atempo={tempo:.4f}", "-c:a", "libmp3lame", str(dst)],
        check=True,
    )
    return dst


def fit_audio_to_max(src: Path, dst: Path, max_dur: float = MAX_DURATION) -> Path:
    """Copy src to dst; if longer than max_dur, speed up with atempo to fit.

    Returns dst. Single atempo filter (ratio always < 2x here).
    """
    src, dst = Path(src), Path(dst)
    dur = audio_duration(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dur <= max_dur:
        if src.resolve() != dst.resolve():
            dst.write_bytes(src.read_bytes())
        return dst
    tempo = dur / max_dur
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-filter:a", f"atempo={tempo:.4f}", "-c:a", "libmp3lame", str(dst)],
        check=True,
    )
    return dst


def build_ffmpeg_args(
    video_in: Path,
    audio_in: Path,
    logo_png: Path,
    output: Path,
    total_dur: float,
    ss: float = 0.0,
) -> list:
    """Build the final compose argv (testable without running ffmpeg).

    `ss` seeks past a blank recording leader (input seeking, frame-accurate
    after re-encode); total_dur is the post-seek output length.
    """
    fade_out_start = max(total_dur - FADE_DUR, 0.0)
    filter_complex = (
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"fade=t=in:st=0:d={FADE_DUR},"
        f"fade=t=out:st={fade_out_start:.2f}:d={FADE_DUR},format=yuv420p[v1];"
        f"[2:v]format=rgba,colorchannelmixer=aa={WATERMARK_OPACITY},scale=-2:64[wm];"
        f"[v1][wm]overlay=30:30[v]"
    )
    pre = ["-ss", f"{ss:.2f}"] if ss > 0 else []
    return [
        "ffmpeg", "-y", "-v", "error",
        *pre, "-i", str(video_in),
        "-i", str(audio_in),
        "-i", str(logo_png),
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-t", f"{total_dur:.2f}",
        str(output),
    ]


def compose_video(
    video_in: Path,
    audio_in: Path,
    logo_png: Path,
    output: Path,
    total_dur: float | None = None,
    ss: float = 0.0,
) -> Path:
    """Mux video + voiceover with watermark + fades.

    Final length = min(video - ss, audio, total_dur) so fades always land
    inside the actual output (no dangling fade-out past a trim cut).
    Returns output Path.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    bounds = [max(video_duration(video_in) - ss, 1.0), audio_duration(audio_in)]
    if total_dur is not None:
        bounds.append(float(total_dur))
    final = min(bounds)
    args = build_ffmpeg_args(video_in, audio_in, logo_png, output, final, ss=ss)
    subprocess.run(args, check=True)
    return output
