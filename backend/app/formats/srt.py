"""SRT (SubRip) format generator and parser.

SRT format specification:
- Cue index (1-based integer)
- Timecode: HH:MM:SS,mmm --> HH:MM:SS,mmm
- Text (max 2 lines, max 42 chars per line)
- Blank line separator between cues
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.exceptions import ValidationError


@dataclass
class SRTCue:
    """A single SRT subtitle cue."""

    index: int
    start_ms: int
    end_ms: int
    text: str


def ms_to_srt_timecode(ms: int) -> str:
    """Convert milliseconds to SRT timecode format HH:MM:SS,mmm.

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
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def srt_timecode_to_ms(timecode: str) -> int:
    """Convert SRT timecode HH:MM:SS,mmm to milliseconds.

    Args:
        timecode: SRT timecode string.

    Returns:
        Time in milliseconds.

    Raises:
        ValidationError: If timecode format is invalid.
    """
    match = re.match(
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", timecode.strip()
    )
    if not match:
        raise ValidationError(f"Invalid SRT timecode: {timecode}")

    hours, minutes, seconds, millis = (int(g) for g in match.groups())
    return (hours * 3_600_000) + (minutes * 60_000) + (seconds * 1_000) + millis


def generate(cues: list[SRTCue]) -> str:
    """Generate SRT file content from a list of cues.

    Args:
        cues: List of SRTCue objects.

    Returns:
        SRT file content as a string.
    """
    blocks: list[str] = []

    for cue in cues:
        start = ms_to_srt_timecode(cue.start_ms)
        end = ms_to_srt_timecode(cue.end_ms)
        block = f"{cue.index}\n{start} --> {end}\n{cue.text}"
        blocks.append(block)

    return "\n\n".join(blocks) + "\n"


def parse(content: str) -> list[SRTCue]:
    """Parse SRT file content into a list of cues.

    Args:
        content: SRT file content string.

    Returns:
        List of SRTCue objects.

    Raises:
        ValidationError: If content is malformed.
    """
    cues: list[SRTCue] = []
    blocks = re.split(r"\n\n+", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        try:
            index = int(lines[0].strip())
        except ValueError:
            raise ValidationError(f"Invalid cue index: {lines[0]}")

        timecode_match = re.match(
            r"(.+?)\s*-->\s*(.+)", lines[1].strip()
        )
        if not timecode_match:
            raise ValidationError(f"Invalid timecode line: {lines[1]}")

        start_ms = srt_timecode_to_ms(timecode_match.group(1))
        end_ms = srt_timecode_to_ms(timecode_match.group(2))
        text = "\n".join(lines[2:])

        cues.append(SRTCue(index=index, start_ms=start_ms, end_ms=end_ms, text=text))

    return cues
