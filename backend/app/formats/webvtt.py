"""WebVTT format generator and parser.

WebVTT specification:
- File starts with "WEBVTT" header
- Timecode: HH:MM:SS.mmm --> HH:MM:SS.mmm
- Optional cue identifiers
- Text (max 2 lines, max 42 chars per line)
- Blank line separator between cues
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.exceptions import ValidationError


@dataclass
class WebVTTCue:
    """A single WebVTT subtitle cue."""

    index: int
    start_ms: int
    end_ms: int
    text: str


def ms_to_vtt_timecode(ms: int) -> str:
    """Convert milliseconds to WebVTT timecode format HH:MM:SS.mmm.

    Args:
        ms: Time in milliseconds.

    Returns:
        Formatted timecode string.
    """
    if ms < 0:
        ms = 0
    hours = ms // 3_600_000
    minutes = (ms % 3_600_000) // 60_000
    seconds = (ms % 60_000) // 1_000
    millis = ms % 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def vtt_timecode_to_ms(timecode: str) -> int:
    """Convert WebVTT timecode HH:MM:SS.mmm to milliseconds.

    Args:
        timecode: WebVTT timecode string.

    Returns:
        Time in milliseconds.

    Raises:
        ValidationError: If timecode format is invalid.
    """
    match = re.match(
        r"(\d{2}):(\d{2}):(\d{2})[.](\d{3})", timecode.strip()
    )
    if not match:
        raise ValidationError(f"Invalid WebVTT timecode: {timecode}")

    hours, minutes, seconds, millis = (int(g) for g in match.groups())
    return (hours * 3_600_000) + (minutes * 60_000) + (seconds * 1_000) + millis


def generate(cues: list[WebVTTCue]) -> str:
    """Generate WebVTT file content from a list of cues.

    Args:
        cues: List of WebVTTCue objects.

    Returns:
        WebVTT file content as a string.
    """
    lines: list[str] = ["WEBVTT", ""]

    for cue in cues:
        start = ms_to_vtt_timecode(cue.start_ms)
        end = ms_to_vtt_timecode(cue.end_ms)
        lines.append(str(cue.index))
        lines.append(f"{start} --> {end}")
        lines.append(cue.text)
        lines.append("")

    return "\n".join(lines)


def parse(content: str) -> list[WebVTTCue]:
    """Parse WebVTT file content into a list of cues.

    Args:
        content: WebVTT file content string.

    Returns:
        List of WebVTTCue objects.

    Raises:
        ValidationError: If content is malformed or missing WEBVTT header.
    """
    lines = content.strip().split("\n")

    if not lines or not lines[0].strip().startswith("WEBVTT"):
        raise ValidationError("Missing WEBVTT header")

    cues: list[WebVTTCue] = []
    # Split into blocks after the header
    body = "\n".join(lines[1:])
    blocks = re.split(r"\n\n+", body.strip())

    for block in blocks:
        block_lines = block.strip().split("\n")
        if not block_lines:
            continue

        # Find the timecode line
        timecode_idx = None
        for i, line in enumerate(block_lines):
            if "-->" in line:
                timecode_idx = i
                break

        if timecode_idx is None:
            continue

        # Cue identifier is the line before timecode (if any)
        index = 0
        if timecode_idx > 0:
            try:
                index = int(block_lines[timecode_idx - 1].strip())
            except ValueError:
                pass

        timecode_match = re.match(
            r"(.+?)\s*-->\s*(.+)", block_lines[timecode_idx].strip()
        )
        if not timecode_match:
            continue

        start_ms = vtt_timecode_to_ms(timecode_match.group(1).strip())
        end_ms = vtt_timecode_to_ms(timecode_match.group(2).strip())
        text = "\n".join(block_lines[timecode_idx + 1:])

        if not index:
            index = len(cues) + 1

        cues.append(
            WebVTTCue(index=index, start_ms=start_ms, end_ms=end_ms, text=text)
        )

    return cues
