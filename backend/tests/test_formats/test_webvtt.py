"""Tests for WebVTT format generation and parsing."""

from pathlib import Path

import pytest

from app.formats.webvtt import (
    WebVTTCue,
    generate,
    ms_to_vtt_timecode,
    parse,
    vtt_timecode_to_ms,
)
from app.exceptions import ValidationError

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_subtitles"


class TestMsToVttTimecode:
    """Tests for millisecond to WebVTT timecode conversion."""

    def test_zero(self):
        assert ms_to_vtt_timecode(0) == "00:00:00.000"

    def test_simple(self):
        assert ms_to_vtt_timecode(4200) == "00:00:04.200"

    def test_uses_dot_separator(self):
        """WebVTT uses dots, not commas (unlike SRT)."""
        result = ms_to_vtt_timecode(1234)
        assert "." in result
        assert "," not in result


class TestVttTimecodeToMs:
    """Tests for WebVTT timecode to millisecond conversion."""

    def test_zero(self):
        assert vtt_timecode_to_ms("00:00:00.000") == 0

    def test_simple(self):
        assert vtt_timecode_to_ms("00:00:04.200") == 4200

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            vtt_timecode_to_ms("bad")


class TestWebvttGenerate:
    """Tests for WebVTT file generation."""

    def test_generate_has_header(self):
        cues = [WebVTTCue(index=1, start_ms=0, end_ms=4200, text="Hello.")]
        result = generate(cues)

        assert result.startswith("WEBVTT")

    def test_generate_uses_dot_timecodes(self):
        cues = [WebVTTCue(index=1, start_ms=0, end_ms=4200, text="Hello.")]
        result = generate(cues)

        assert "00:00:00.000 --> 00:00:04.200" in result

    def test_generate_multiple_cues(self):
        cues = [
            WebVTTCue(index=1, start_ms=0, end_ms=4200, text="First."),
            WebVTTCue(index=2, start_ms=4500, end_ms=9800, text="Second."),
        ]
        result = generate(cues)

        assert result.count("-->") == 2

    def test_roundtrip(self):
        """Generate WebVTT then parse — cues should match."""
        original = [
            WebVTTCue(index=1, start_ms=0, end_ms=4200, text="Hello."),
            WebVTTCue(index=2, start_ms=4500, end_ms=9800, text="World."),
        ]
        content = generate(original)
        parsed = parse(content)

        assert len(parsed) == len(original)
        for orig, pars in zip(original, parsed):
            assert orig.index == pars.index
            assert orig.start_ms == pars.start_ms
            assert orig.end_ms == pars.end_ms
            assert orig.text == pars.text


class TestWebvttParse:
    """Tests for WebVTT file parsing."""

    def test_parse_fixture_file(self):
        """Parse the sample WebVTT fixture and validate structure."""
        content = (FIXTURES_DIR / "sample.vtt").read_text()
        cues = parse(content)

        assert len(cues) == 5
        assert cues[0].index == 1
        assert cues[0].start_ms == 0
        assert cues[0].end_ms == 4200

    def test_parse_fixture_all_cues_present(self):
        """No cues dropped during parsing."""
        content = (FIXTURES_DIR / "sample.vtt").read_text()
        cues = parse(content)

        indices = [c.index for c in cues]
        assert indices == [1, 2, 3, 4, 5]

    def test_parse_missing_header_raises(self):
        with pytest.raises(ValidationError, match="WEBVTT"):
            parse("1\n00:00:00.000 --> 00:00:01.000\nHello")

    def test_parse_empty_content_raises(self):
        with pytest.raises(ValidationError):
            parse("")
