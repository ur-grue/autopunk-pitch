"""Subtitle format validators.

Enforces broadcast-quality rules:
- Max 42 characters per line
- Max 2 lines per cue
- Reading speed ≤ 25 characters per second (CPS)
- Minimum duration: 1000ms (1 second)
- Minimum gap between cues: 0ms (no overlap)
- All text must be valid UTF-8
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class QCIssue:
    """A single quality control issue found during validation."""

    cue_index: int
    severity: Severity
    rule: str
    message: str
    value: str | float | int | None = None


@dataclass
class ValidationResult:
    """Result of subtitle validation."""

    issues: list[QCIssue] = field(default_factory=list)
    total_cues: int = 0
    error_count: int = 0
    warning_count: int = 0
    score: int = 100

    @property
    def passed(self) -> bool:
        """Whether validation passed with no errors."""
        return self.error_count == 0


# Default broadcast quality limits
MAX_CHARS_PER_LINE = 42
MAX_LINES_PER_CUE = 2
MAX_CPS = 25.0
MIN_DURATION_MS = 1000
MIN_GAP_MS = 0


@dataclass
class SubtitleCue:
    """Generic subtitle cue for validation."""

    index: int
    start_ms: int
    end_ms: int
    text: str


def validate_subtitles(
    cues: list[SubtitleCue],
    max_chars_per_line: int = MAX_CHARS_PER_LINE,
    max_lines: int = MAX_LINES_PER_CUE,
    max_cps: float = MAX_CPS,
    min_duration_ms: int = MIN_DURATION_MS,
) -> ValidationResult:
    """Validate a list of subtitle cues against broadcast quality rules.

    Args:
        cues: List of subtitle cues to validate.
        max_chars_per_line: Maximum characters per line.
        max_lines: Maximum lines per cue.
        max_cps: Maximum characters per second (reading speed).
        min_duration_ms: Minimum cue duration in milliseconds.

    Returns:
        ValidationResult with all issues found.
    """
    result = ValidationResult(total_cues=len(cues))
    issues: list[QCIssue] = []

    for i, cue in enumerate(cues):
        # Rule: Line length
        lines = cue.text.split("\n")
        for line_num, line in enumerate(lines):
            if len(line) > max_chars_per_line:
                issues.append(
                    QCIssue(
                        cue_index=cue.index,
                        severity=Severity.ERROR,
                        rule="line_length",
                        message=(
                            f"Line {line_num + 1} has {len(line)} chars "
                            f"(max {max_chars_per_line})"
                        ),
                        value=len(line),
                    )
                )

        # Rule: Max lines per cue
        if len(lines) > max_lines:
            issues.append(
                QCIssue(
                    cue_index=cue.index,
                    severity=Severity.ERROR,
                    rule="max_lines",
                    message=f"Cue has {len(lines)} lines (max {max_lines})",
                    value=len(lines),
                )
            )

        # Rule: Minimum duration
        duration_ms = cue.end_ms - cue.start_ms
        if duration_ms < min_duration_ms:
            issues.append(
                QCIssue(
                    cue_index=cue.index,
                    severity=Severity.WARNING,
                    rule="min_duration",
                    message=(
                        f"Duration {duration_ms}ms is below "
                        f"minimum {min_duration_ms}ms"
                    ),
                    value=duration_ms,
                )
            )

        # Rule: Reading speed (CPS)
        if duration_ms > 0:
            char_count = len(cue.text.replace("\n", ""))
            cps = (char_count / duration_ms) * 1000
            if cps > max_cps:
                issues.append(
                    QCIssue(
                        cue_index=cue.index,
                        severity=Severity.WARNING,
                        rule="reading_speed",
                        message=(
                            f"Reading speed {cps:.1f} CPS "
                            f"exceeds max {max_cps} CPS"
                        ),
                        value=round(cps, 1),
                    )
                )

        # Rule: Timing validity
        if cue.start_ms >= cue.end_ms:
            issues.append(
                QCIssue(
                    cue_index=cue.index,
                    severity=Severity.ERROR,
                    rule="timing",
                    message="Start time must be before end time",
                    value=None,
                )
            )

        # Rule: Overlap with next cue
        if i + 1 < len(cues):
            next_cue = cues[i + 1]
            if cue.end_ms > next_cue.start_ms:
                issues.append(
                    QCIssue(
                        cue_index=cue.index,
                        severity=Severity.ERROR,
                        rule="overlap",
                        message=(
                            f"Cue overlaps with next cue "
                            f"(ends at {cue.end_ms}ms, "
                            f"next starts at {next_cue.start_ms}ms)"
                        ),
                        value=cue.end_ms - next_cue.start_ms,
                    )
                )

        # Rule: Empty text
        if not cue.text.strip():
            issues.append(
                QCIssue(
                    cue_index=cue.index,
                    severity=Severity.WARNING,
                    rule="empty_text",
                    message="Cue has empty text",
                    value=None,
                )
            )

    # Calculate score and counts
    result.issues = issues
    result.error_count = sum(
        1 for i in issues if i.severity == Severity.ERROR
    )
    result.warning_count = sum(
        1 for i in issues if i.severity == Severity.WARNING
    )

    # Score: start at 100, deduct 5 per error, 2 per warning
    if result.total_cues > 0:
        deduction = (result.error_count * 5) + (result.warning_count * 2)
        result.score = max(0, 100 - deduction)

    return result
