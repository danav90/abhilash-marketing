"""Tests for Task 21 demo video pipeline (network/browser/subprocess mocked)."""

from pathlib import Path
from unittest import mock

from videos import compose_video as cv_mod
from videos import generate_voiceover as vo_mod
from videos import record_website as rec_mod


class _FakeCommunicate:
    seen = []

    def __init__(self, text, voice=None, rate=None):
        _FakeCommunicate.seen.append({"text": text, "voice": voice, "rate": rate})
        self._voice = voice

    async def save(self, output):
        if self._voice == vo_mod.PRIMARY_VOICE and getattr(self, "_fail_primary", False):
            raise RuntimeError("voice unavailable")
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_bytes(b"fake-mp3")


def test_voiceover_uses_indian_voice_and_falls_back(tmp_path):
    """Primary en-IN-PrabhatNeural at -5%; fallback en-US-GuyNeural on failure."""
    _FakeCommunicate.seen.clear()
    out = tmp_path / "v.mp3"
    with mock.patch("edge_tts.Communicate", _FakeCommunicate):
        vo_mod.generate_voiceover("Hello world", out)
    assert out.exists()
    assert _FakeCommunicate.seen[0]["voice"] == "en-IN-PrabhatNeural"
    assert _FakeCommunicate.seen[0]["rate"] == "-5%"

    # Primary failure -> fallback voice, same output.
    _FakeCommunicate.seen.clear()
    _FakeCommunicate._fail_primary = True
    try:
        with mock.patch("edge_tts.Communicate", _FakeCommunicate):
            vo_mod.generate_voiceover("Hello world", out)
    finally:
        _FakeCommunicate._fail_primary = False
    voices = [c["voice"] for c in _FakeCommunicate.seen]
    assert voices == ["en-IN-PrabhatNeural", "en-US-GuyNeural"]

    # Unknown brand raises.
    try:
        vo_mod.voiceover_for_brand("nope", tmp_path / "x.mp3")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")


class _FakeLocator:
    def __init__(self, page, text):
        self._page = page
        self._text = text
        self.first = self

    async def scroll_into_view_if_needed(self, timeout=None):
        self._page.actions.append(("scroll_to", self._text))

    async def hover(self, timeout=None):
        self._page.actions.append(("hover", self._text))

    async def click(self, timeout=None):
        self._page.actions.append(("click", self._text))


class _FakePage:
    def __init__(self):
        self.actions = []

    async def goto(self, url, wait_until=None, timeout=None):
        self.actions.append(("goto", url))

    async def wait_for_timeout(self, ms):
        self.actions.append(("wait", ms))

    async def evaluate(self, *a, **k):
        return None

    def get_by_text(self, text, exact=None):
        return _FakeLocator(self, text)

    def get_by_role(self, role, name=None):
        return _FakeLocator(self, name or role)

    async def go_back(self, wait_until=None, timeout=None):
        self.actions.append(("back",))


class _FakeContext:
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.page = _FakePage()

    async def new_page(self):
        return self.page

    async def close(self):
        return None


class _FakeBrowser:
    def __init__(self, store):
        self._store = store

    async def new_context(self, **kwargs):
        self._store.append(kwargs)
        return _FakeContext(kwargs)

    async def close(self):
        return None


class _FakePW:
    def __init__(self, store):
        self._store = store

    @property
    def chromium(self):
        store = self._store

        class _Chromium:
            async def launch(self, headless=True):
                return _FakeBrowser(store)

        return _Chromium()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def test_record_website_uses_1920x1080_viewport(tmp_path):
    """Recording context must request 1920x1080 viewport + video size; webm moved."""
    store = []
    out = tmp_path / "rec.webm"

    async def _fake_async(url, actions, duration, output, width=1920, height=1080):
        assert (width, height) == (1920, 1080)
        async with _FakePW(store) as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=str(Path(output).parent / "_record_tmp"),
                record_video_size={"width": width, "height": height},
            )
            page = await context.new_page()
            for action in actions:
                await rec_mod._run_action(page, action, deadline=1e18)
            await context.close()
            await browser.close()
        Path(output).write_bytes(b"fake-webm")
        return Path(output)

    with mock.patch.object(rec_mod, "record_website_async", side_effect=_fake_async):
        result = rec_mod.record_website(
            "https://example.com",
            [{"do": "goto", "url": "https://example.com"}, {"do": "wait", "s": 1.0}],
            5.0, out,
        )
    assert Path(result) == out
    assert out.read_bytes() == b"fake-webm"
    assert store, "browser.new_context was not called"
    ctx = store[0]
    assert ctx["viewport"] == {"width": 1920, "height": 1080}
    assert ctx["record_video_size"] == {"width": 1920, "height": 1080}
    assert "record_video_dir" in ctx


def test_compose_builds_correct_ffmpeg_args(tmp_path):
    """ffmpeg argv: libx264, aac 128k, fades, 15% watermark overlay, shortest."""
    args = cv_mod.build_ffmpeg_args(
        tmp_path / "v.webm", tmp_path / "a.mp3", tmp_path / "logo.png",
        tmp_path / "out.mp4", 56.9,
    )
    blob = " ".join(args)
    assert "-c:v" in args and "libx264" in args
    assert "-c:a" in args and "aac" in args and "128k" in args
    assert "-t" in args and "56.90" in args
    assert "-shortest" not in args
    assert "yuv420p" in blob
    assert "faststart" in blob
    assert "fade=t=in:st=0:d=0.5" in blob
    assert "fade=t=out:st=56.40:d=0.5" in blob
    assert "colorchannelmixer=aa=0.15" in blob
    assert "overlay=30:30" in blob
    assert "scale=1920:1080" in blob

    # compose_video trims to min(video, audio, hint) so fades stay in-frame.
    seen = []
    with mock.patch.object(cv_mod.subprocess, "run") as fake_run, \
         mock.patch.object(cv_mod, "video_duration", return_value=60.0), \
         mock.patch.object(cv_mod, "audio_duration", return_value=56.9):
        cv_mod.compose_video(
            tmp_path / "v.webm", tmp_path / "a.mp3", tmp_path / "logo.png",
            tmp_path / "out.mp4", 58.0,
        )
        seen.append(fake_run.call_args[0][0])
    assert seen[0] == args

    # Blank-leader seek is wired through.
    args_ss = cv_mod.build_ffmpeg_args(
        tmp_path / "v.webm", tmp_path / "a.mp3", tmp_path / "logo.png",
        tmp_path / "out.mp4", 56.9, ss=1.5,
    )
    assert "-ss" in args_ss and "1.50" in args_ss
    src = tmp_path / "short.mp3"
    src.write_bytes(b"x" * 100)
    with mock.patch.object(cv_mod, "audio_duration", return_value=30.0):
        dst = cv_mod.fit_audio_to_max(src, tmp_path / "short_fit.mp3")
    assert Path(dst).read_bytes() == b"x" * 100

    # Long audio gets atempo-compressed.
    with mock.patch.object(cv_mod, "audio_duration", return_value=61.632), \
         mock.patch.object(cv_mod.subprocess, "run") as fake_run:
        cv_mod.fit_audio_to_max(src, tmp_path / "long_fit.mp3")
    ff_args = " ".join(fake_run.call_args[0][0])
    assert "atempo=1.0626" in ff_args
