"""English voiceover generation via edge-tts (Task 21).

Primary voice: en-IN-PrabhatNeural (Indian English male).
Fallback: en-US-GuyNeural. Rate -5% for clarity.
"""

import asyncio
from pathlib import Path

PRIMARY_VOICE = "en-IN-PrabhatNeural"
FALLBACK_VOICE = "en-US-GuyNeural"
VOICE_RATE = "-5%"

BRAND_SCRIPTS = {
    "portfolio": Path(__file__).resolve().parent / "scripts" / "portfolio.txt",
    "gymos": Path(__file__).resolve().parent / "scripts" / "gymos.txt",
    "webscraper": Path(__file__).resolve().parent / "scripts" / "webscraper.txt",
}


async def _synthesize(text: str, output: Path, voice: str, rate: str) -> Path:
    import edge_tts

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(output))
    return output


async def generate_voiceover_async(
    text: str,
    output: Path,
    voice: str = PRIMARY_VOICE,
    rate: str = VOICE_RATE,
) -> Path:
    """Synthesize `text` to mp3. Falls back to en-US-GuyNeural on primary failure."""
    try:
        return await _synthesize(text, output, voice, rate)
    except Exception:
        if voice != FALLBACK_VOICE:
            return await _synthesize(text, output, FALLBACK_VOICE, rate)
        raise


def generate_voiceover(
    text: str,
    output: Path,
    voice: str = PRIMARY_VOICE,
    rate: str = VOICE_RATE,
) -> Path:
    """Sync wrapper around generate_voiceover_async."""
    return asyncio.run(generate_voiceover_async(text, output, voice, rate))


def voiceover_for_brand(brand: str, output: Path) -> Path:
    """Load videos/scripts/<brand>.txt and synthesize. Raises KeyError/FileNotFound."""
    key = (brand or "").strip().lower()
    if key not in BRAND_SCRIPTS:
        raise KeyError(f"Unknown brand: {brand!r} (expected one of {sorted(BRAND_SCRIPTS)})")
    script_path = BRAND_SCRIPTS[key]
    text = script_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Empty voiceover script: {script_path}")
    return generate_voiceover(text, output)
