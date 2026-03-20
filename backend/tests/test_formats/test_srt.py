"""Tests for SRT format generation and parsing."""

from pathlib import Path

import pytest

from app.formats.srt import SRTCue, generate, ms_to_srt_timecode, parse, srt_timecode_to_ms
from app.exceptions import ValidationError

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_subtitles"


class TestMsToSrtTimecode:
    """Tests for millisecond to SRT timecode conversion."""

    def test_zero(self):
        assert ms_to_srt_timecode(0) == "00:00:00,000"

    def test_simple(self):
        assert ms_to_srt_timecode(4200) == "00:00:04,200"

    def test_minutes(self):
        assert ms_to_srt_timecode(65_500) == "00:01:05,500"

    def test_hours(self):
        assert ms_to_srt_timecode(3_661_123) == "01:01:01,123"

    def test_negative_clamps_to_zero(self):
        assert ms_to_srt_timecode(-100) == "00:00:00,000"

    def test_large_value(self):
        # 99:59:59,999
        ms = 99 * 3_600_000 + 59 * 60_000 + 59 * 1_000 + 999
        assert ms_to_srt_timecode(ms) == "99:59:59,999"


class TestSrtTimecodeToMs:
    """Tests for SRT timecode to millisecond conversion."""

    def test_zero(self):
        assert srt_timecode_to_ms("00:00:00,000") == 0

    def test_simple(self):
        assert srt_timecode_to_ms("00:00:04,200") == 4200

    def test_with_dot_separator(self):
        """Some SRT files use dots instead of commas."""
        assert srt_timecode_to_ms("00:00:04.200") == 4200

    def test_hours(self):
        assert srt_timecode_to_ms("01:01:01,123") == 3_661_123

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            srt_timecode_to_ms("invalid")

    def test_partial_format_raises(self):
        with pytest.raises(ValidationError):
            srt_timecode_to_ms("00:00:04")


class TestSrtGenerate:
    """Tests for SRT file generation."""

    def test_generate_single_cue(self):
        cues = [SRTCue(index=1, start_ms=0, end_ms=4200, text="Hello world.")]
        result = generate(cues)

        assert "1\n" in result
        assert "00:00:00,000 --> 00:00:04,200" in result
        assert "Hello world." in result

    def test_generate_multiple_cues(self):
        cues = [
            SRTCue(index=1, start_ms=0, end_ms=4200, text="First line."),
            SRTCue(index=2, start_ms=4500, end_ms=9800, text="Second line."),
        ]
        result = generate(cues)

        assert result.count("-->") == 2
        assert "First line." in result
        assert "Second line." in result

    def test_generate_multiline_text(self):
        cues = [
            SRTCue(
                index=1, start_ms=0, end_ms=4200,
                text="Line one\nLine two",
            ),
        ]
        result = generate(cues)

        assert "Line one\nLine two" in result

    def test_generate_empty_list(self):
        result = generate([])
        assert result.strip() == ""

    def test_roundtrip(self):
        """Generate SRT then parse it — cues should match."""
        original = [
            SRTCue(index=1, start_ms=0, end_ms=4200, text="Hello."),
            SRTCue(index=2, start_ms=4500, end_ms=9800, text="World."),
        ]
        srt_content = generate(original)
        parsed = parse(srt_content)

        assert len(parsed) == len(original)
        for orig, pars in zip(original, parsed):
            assert orig.index == pars.index
            assert orig.start_ms == pars.start_ms
            assert orig.end_ms == pars.end_ms
            assert orig.text == pars.text


class TestSrtParse:
    """Tests for SRT file parsing."""

    def test_parse_fixture_file(self):
        """Parse the sample SRT fixture and validate structure."""
        content = (FIXTURES_DIR / "sample.srt").read_text()
        cues = parse(content)

        assert len(cues) == 5
        assert cues[0].index == 1
        assert cues[0].start_ms == 0
        assert cues[0].end_ms == 4200
        assert "Hello and welcome" in cues[0].text

    def test_parse_fixture_timing(self):
        """Fixture cue timings are correctly parsed."""
        content = (FIXTURES_DIR / "sample.srt").read_text()
        cues = parse(content)

        assert cues[1].start_ms == 4500
        assert cues[1].end_ms == 9800
        assert cues[4].start_ms == 25800
        assert cues[4].end_ms == 30500

    def test_parse_fixture_all_cues_present(self):
        """No cues dropped during parsing."""
        content = (FIXTURES_DIR / "sample.srt").read_text()
        cues = parse(content)

        indices = [c.index for c in cues]
        assert indices == [1, 2, 3, 4, 5]

    def test_parse_empty_content(self):
        cues = parse("")
        assert cues == []

    def test_parse_invalid_index_raises(self):
        content = "abc\n00:00:00,000 --> 00:00:01,000\nHello"
        with pytest.raises(ValidationError):
            parse(content)
