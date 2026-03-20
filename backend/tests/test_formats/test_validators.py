"""Tests for subtitle format validators."""

import pytest

from app.formats.validators import (
    Severity,
    SubtitleCue,
    ValidationResult,
    validate_subtitles,
)


def _make_cue(
    index: int = 1,
    start_ms: int = 0,
    end_ms: int = 4000,
    text: str = "Hello world.",
) -> SubtitleCue:
    return SubtitleCue(index=index, start_ms=start_ms, end_ms=end_ms, text=text)


class TestValidateSubtitles:
    """Tests for the validate_subtitles function."""

    def test_valid_cues_pass(self):
        """Well-formed cues produce no issues."""
        cues = [
            _make_cue(1, 0, 4000, "Hello world."),
            _make_cue(2, 4500, 9000, "The ocean is vast."),
        ]
        result = validate_subtitles(cues)

        assert result.passed
        assert result.score == 100
        assert result.error_count == 0

    def test_line_length_violation(self):
        """Line exceeding 42 chars is flagged as error."""
        long_text = "A" * 50  # 50 chars, exceeds 42
        cues = [_make_cue(text=long_text)]
        result = validate_subtitles(cues)

        assert not result.passed
        assert result.error_count >= 1
        line_issues = [i for i in result.issues if i.rule == "line_length"]
        assert len(line_issues) == 1
        assert line_issues[0].severity == Severity.ERROR

    def test_max_lines_violation(self):
        """Cue with 3+ lines is flagged as error."""
        cues = [_make_cue(text="Line 1\nLine 2\nLine 3")]
        result = validate_subtitles(cues)

        max_line_issues = [i for i in result.issues if i.rule == "max_lines"]
        assert len(max_line_issues) == 1

    def test_two_lines_is_valid(self):
        """Cue with exactly 2 lines is OK."""
        cues = [_make_cue(text="Line 1\nLine 2")]
        result = validate_subtitles(cues)

        max_line_issues = [i for i in result.issues if i.rule == "max_lines"]
        assert len(max_line_issues) == 0

    def test_min_duration_warning(self):
        """Cue shorter than 1s is flagged as warning."""
        cues = [_make_cue(start_ms=0, end_ms=500)]
        result = validate_subtitles(cues)

        duration_issues = [i for i in result.issues if i.rule == "min_duration"]
        assert len(duration_issues) == 1
        assert duration_issues[0].severity == Severity.WARNING

    def test_reading_speed_warning(self):
        """High reading speed (>25 CPS) is flagged as warning."""
        # 80 chars in 2 seconds = 40 CPS
        fast_text = "A" * 40 + "\n" + "B" * 40
        cues = [_make_cue(start_ms=0, end_ms=2000, text=fast_text)]
        result = validate_subtitles(cues)

        speed_issues = [i for i in result.issues if i.rule == "reading_speed"]
        assert len(speed_issues) == 1

    def test_normal_reading_speed_passes(self):
        """20 CPS is within limits."""
        # 20 chars in 2 seconds = 10 CPS
        cues = [_make_cue(start_ms=0, end_ms=2000, text="Hello, this is fine.")]
        result = validate_subtitles(cues)

        speed_issues = [i for i in result.issues if i.rule == "reading_speed"]
        assert len(speed_issues) == 0

    def test_timing_error(self):
        """Start >= end is flagged as error."""
        cues = [_make_cue(start_ms=5000, end_ms=3000)]
        result = validate_subtitles(cues)

        timing_issues = [i for i in result.issues if i.rule == "timing"]
        assert len(timing_issues) == 1
        assert timing_issues[0].severity == Severity.ERROR

    def test_overlap_error(self):
        """Overlapping cues are flagged as error."""
        cues = [
            _make_cue(1, 0, 5000, "First."),
            _make_cue(2, 4000, 8000, "Second."),
        ]
        result = validate_subtitles(cues)

        overlap_issues = [i for i in result.issues if i.rule == "overlap"]
        assert len(overlap_issues) == 1

    def test_empty_text_warning(self):
        """Empty text is flagged as warning."""
        cues = [_make_cue(text="  ")]
        result = validate_subtitles(cues)

        empty_issues = [i for i in result.issues if i.rule == "empty_text"]
        assert len(empty_issues) == 1

    def test_score_calculation(self):
        """Score deducts 5 per error, 2 per warning."""
        cues = [
            _make_cue(1, 0, 500, "A" * 50),  # line_length error + min_duration warning
        ]
        result = validate_subtitles(cues)

        # At least 1 error (line length) and 1 warning (min duration)
        assert result.score < 100
        assert result.score == max(
            0, 100 - (result.error_count * 5) - (result.warning_count * 2)
        )

    def test_empty_input(self):
        """Empty cue list returns perfect score."""
        result = validate_subtitles([])
        assert result.passed
        assert result.score == 100
        assert result.total_cues == 0

    def test_52_min_documentary_fixture(self):
        """Validate a realistic set of well-formed cues (no issues)."""
        cues = [
            _make_cue(
                index=i + 1,
                start_ms=i * 5000,
                end_ms=i * 5000 + 4000,
                text=f"Subtitle cue number {i + 1}.",
            )
            for i in range(100)
        ]
        result = validate_subtitles(cues)

        assert result.passed
        assert result.total_cues == 100
        assert result.score == 100
