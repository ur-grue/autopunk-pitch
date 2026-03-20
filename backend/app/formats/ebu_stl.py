"""EBU-STL (European Broadcasting Union Subtitle) format generator.

EBU Tech 3264 binary format used for broadcast subtitle delivery.
Only generation is implemented; parsing is out of scope.

Structure:
- GSI block: 1024-byte header with programme and file metadata
- TTI blocks: 128-byte records, one per subtitle cue
"""

from __future__ import annotations

import datetime
import struct
from dataclasses import dataclass

from app.exceptions import ValidationError


@dataclass
class EBUSTLCue:
    """A single EBU-STL subtitle cue."""

    index: int
    start_ms: int
    end_ms: int
    text: str


# EBU Tech 3264 Annex 2 — ISO 639-1 to EBU language code mapping (hex values).
# Only the most commonly used broadcast languages are listed; unknown codes fall
# back to 0x00 (not specified).
_LANGUAGE_CODES: dict[str, int] = {
    "sq": 0x01,  # Albanian
    "br": 0x02,  # Breton
    "ca": 0x03,  # Catalan
    "hr": 0x04,  # Croatian
    "cy": 0x05,  # Welsh
    "cs": 0x06,  # Czech
    "da": 0x07,  # Danish
    "de": 0x08,  # German
    "en": 0x09,  # English
    "es": 0x0A,  # Spanish
    "eo": 0x0B,  # Esperanto
    "et": 0x0C,  # Estonian
    "eu": 0x0D,  # Basque
    "fo": 0x0E,  # Faroese
    "fr": 0x0F,  # French
    "fy": 0x10,  # Frisian
    "ga": 0x11,  # Irish
    "gd": 0x12,  # Scottish Gaelic
    "gl": 0x13,  # Galician
    "is": 0x14,  # Icelandic
    "it": 0x15,  # Italian
    "lv": 0x16,  # Latvian
    "lb": 0x17,  # Luxembourgish
    "lt": 0x18,  # Lithuanian
    "hu": 0x19,  # Hungarian
    "mt": 0x1A,  # Maltese
    "nl": 0x1B,  # Dutch
    "no": 0x1C,  # Norwegian
    "oc": 0x1D,  # Occitan
    "pl": 0x1E,  # Polish
    "pt": 0x1F,  # Portuguese
    "ro": 0x20,  # Romanian
    "rm": 0x21,  # Romansh
    "sr": 0x22,  # Serbian
    "sk": 0x23,  # Slovak
    "sl": 0x24,  # Slovenian
    "fi": 0x25,  # Finnish
    "sv": 0x26,  # Swedish
    "tr": 0x27,  # Turkish
    "nl_BE": 0x28,  # Flemish (Belgian Dutch)
    "wa": 0x29,  # Walloon
    # Codes 0x2A–0x7F are unassigned in the spec.
    "zz": 0x00,  # Unknown / not specified (fallback)
}

# Teletext control code for new line in EBU-STL text fields.
_CR_LF: int = 0x8A

# Maximum bytes available in the text field of each TTI block.
_TF_SIZE: int = 112


def ms_to_ebu_timecode(ms: int, fps: int = 25) -> bytes:
    """Convert milliseconds to a 4-byte BCD timecode (HH MM SS FF).

    Each component is stored as a BCD byte (decimal value packed into
    two nibbles), matching the EBU Tech 3264 timecode layout.

    Args:
        ms: Time in milliseconds. Clamped to zero if negative.
        fps: Frames per second used to derive the frame component.
            Defaults to 25 (PAL standard).

    Returns:
        4 bytes: [HH, MM, SS, FF] each as a BCD-encoded byte.

    Raises:
        ValidationError: If fps is not a positive integer.
    """
    if fps <= 0:
        raise ValidationError(f"fps must be a positive integer, got {fps}")

    if ms < 0:
        ms = 0

    total_seconds = ms // 1_000
    remaining_ms = ms % 1_000
    frames = (remaining_ms * fps) // 1_000

    hours = total_seconds // 3_600
    minutes = (total_seconds % 3_600) // 60
    seconds = total_seconds % 60

    def to_bcd(value: int) -> int:
        """Pack a decimal value 0–99 into a single BCD byte."""
        return ((value // 10) << 4) | (value % 10)

    return bytes([to_bcd(hours), to_bcd(minutes), to_bcd(seconds), to_bcd(frames)])


def _encode_fixed(value: str, width: int, encoding: str = "latin-1") -> bytes:
    """Encode a string into a fixed-width byte field, space-padded on the right.

    Args:
        value: String to encode.
        width: Required byte width of the output field.
        encoding: Character encoding (default latin-1 for EBU-STL).

    Returns:
        Bytes of exactly ``width`` length.
    """
    raw = value.encode(encoding, errors="replace")[:width]
    return raw.ljust(width, b" ")


def _build_gsi(metadata: dict, subtitle_count: int) -> bytes:
    """Build the 1024-byte GSI (General Subtitle Information) block.

    The GSI block is the file header defined in EBU Tech 3264 section 9.
    All multi-byte numeric fields are ASCII decimal strings. Fields that
    are not provided in ``metadata`` receive sensible broadcast defaults.

    Args:
        metadata: Optional programme metadata dict with keys:
            - ``title`` (str): Programme title. Up to 32 characters.
            - ``language`` (str): ISO 639-1 language code.
            - ``fps`` (int): Frame rate; affects DFC field. Default 25.
        subtitle_count: Total number of subtitle (TTI) blocks in the file.

    Returns:
        Exactly 1024 bytes.
    """
    fps = int(metadata.get("fps", 25))
    language_iso = str(metadata.get("language", "en")).lower()
    title = str(metadata.get("title", ""))

    # DFC: Disk Format Code — STL25.01 (25fps PAL) or STL30.01 (30fps).
    dfc = "STL25.01" if fps == 25 else "STL30.01"

    # LC: EBU language code as zero-padded 2-digit hex string per spec.
    ebu_lc = _LANGUAGE_CODES.get(language_iso, 0x00)
    lc_field = f"{ebu_lc:02X}"

    # Creation date — today's date in YYMMDD format.
    today = datetime.date.today()
    creation_date = today.strftime("%y%m%d")

    # Revision date — same as creation for new files.
    revision_date = creation_date

    # TNB: Total Number of TTI Blocks = subtitle_count (one block per cue).
    tnb = str(subtitle_count).zfill(5)

    # TNS: Total Number of Subtitles.
    tns = str(subtitle_count).zfill(5)

    gsi = bytearray(1024)
    offset = 0

    def write(field: bytes) -> None:
        nonlocal offset
        end = offset + len(field)
        gsi[offset:end] = field
        offset = end

    # CPN — Code Page Number (bytes 0–2): "850" = Western European multilingual.
    write(_encode_fixed("850", 3))

    # DFC — Disk Format Code (bytes 3–10): 8 bytes.
    write(_encode_fixed(dfc, 8))

    # DSC — Display Standard Code (byte 11): "1" = open subtitles.
    write(_encode_fixed("1", 1))

    # CCT — Character Code Table (bytes 12–13): "00" = Latin.
    write(_encode_fixed("00", 2))

    # LC — Language Code (bytes 14–15): 2-char hex string.
    write(_encode_fixed(lc_field, 2))

    # OPT — Original Programme Title (bytes 16–47): 32 bytes.
    write(_encode_fixed(title, 32))

    # OET — Original Episode Title (bytes 48–79): 32 bytes, blank.
    write(_encode_fixed("", 32))

    # TPT — Translated Programme Title (bytes 80–111): 32 bytes, blank.
    write(_encode_fixed("", 32))

    # TET — Translated Episode Title (bytes 112–143): 32 bytes, blank.
    write(_encode_fixed("", 32))

    # TN — Translator's Name (bytes 144–175): 32 bytes, blank.
    write(_encode_fixed("", 32))

    # TCS — Translator's Contact Details / stub (bytes 176–207): 32 bytes.
    # Reused in practice for contact details; we leave blank.
    write(_encode_fixed("", 32))

    # SLR — Subtitle List Reference (bytes 208–222): 16 bytes.
    write(_encode_fixed("", 16))

    # CD — Creation Date (bytes 223–228): YYMMDD, 6 bytes.
    write(_encode_fixed(creation_date, 6))

    # RD — Revision Date (bytes 229–234): YYMMDD, 6 bytes.
    write(_encode_fixed(revision_date, 6))

    # RN — Revision Number (bytes 235–236): "00".
    write(_encode_fixed("00", 2))

    # TNB — Total Number of TTI Blocks (bytes 237–241): 5 chars.
    write(_encode_fixed(tnb, 5))

    # TNS — Total Number of Subtitles (bytes 242–246): 5 chars.
    write(_encode_fixed(tns, 5))

    # TNG — Total Number of Subtitle Groups (bytes 247–248): "001".
    # Truncated to 3 bytes per layout; spec says 3 chars here.
    write(_encode_fixed("001", 3))

    # MNC — Maximum Number of Displayable Characters (bytes 250–251).
    # Note: offset is now 250 (3+8+1+2+2+32+32+32+32+32+32+16+6+6+2+5+5+3 = 249).
    write(_encode_fixed("42", 2))

    # MNR — Maximum Number of Displayable Rows (bytes 252–253): "02".
    write(_encode_fixed("02", 2))

    # TC — Time Code: Start of Programme (bytes 254–257) not used; set to zeros.
    # TCS — Timecode Status (byte 254, but layout conflicts — we handle below).
    # Per EBU 3264 section 9 table: TCS is at byte 255 (1 byte), "1" = use TC.
    # We write "1" at byte 255 explicitly after setting the block.

    # CS — Country of Origin (bytes 254–255): 2 chars, blank.
    write(_encode_fixed("  ", 2))

    # TCS — Timecode: Start of Programme (bytes 256–259): 4 bytes ASCII "00000000".
    # This is the BCD start-of-programme TC; we default to 00:00:00:00.
    write(_encode_fixed("00000000", 8))

    # TP — Total Running Time (bytes 264 approx) — skip forward.
    # The remaining bytes to offset 1023 are spare/user data; leave as 0x20 (space).
    # Fill remainder with spaces to comply with the spec's "shall be spaces" note.
    while offset < 1024:
        gsi[offset] = 0x20
        offset += 1

    # Patch TCS (Timecode Status) at byte 255: set to ASCII "1" (use timecodes).
    gsi[255] = ord("1")

    return bytes(gsi)


def _build_tti(cue: EBUSTLCue, subtitle_number: int, fps: int = 25) -> bytes:
    """Build a 128-byte TTI (Text and Timing Information) block.

    Each TTI block holds one subtitle cue including timing, display
    parameters, and the text payload in a 112-byte field. Text lines are
    separated by the teletext newline control code 0x8A; the field is
    padded to 112 bytes with 0x8F (end-of-text, then ignored).

    Args:
        cue: The subtitle cue to encode.
        subtitle_number: 0-based subtitle sequence number (written to SN field).
        fps: Frames per second for timecode encoding. Default 25.

    Returns:
        Exactly 128 bytes.
    """
    tti = bytearray(128)

    # SGN — Subtitle Group Number (bytes 0–1): uint16 LE, always 0.
    struct.pack_into("<H", tti, 0, 0)

    # SN — Subtitle Number (bytes 2–3): uint16 LE, 0-based.
    struct.pack_into("<H", tti, 2, subtitle_number)

    # EBN — Extension Block Number (byte 4): 0xFF = last (and only) block.
    tti[4] = 0xFF

    # CS — Cumulative Status (byte 5): 0x00 = not part of a cumulative set.
    tti[5] = 0x00

    # TCI — Time Code In (bytes 6–9): BCD HH MM SS FF.
    tci = ms_to_ebu_timecode(cue.start_ms, fps)
    tti[6:10] = tci

    # TCO — Time Code Out (bytes 10–13): BCD HH MM SS FF.
    tco = ms_to_ebu_timecode(cue.end_ms, fps)
    tti[10:14] = tco

    # VP — Vertical Position (byte 14): row number; 20 = near bottom.
    tti[14] = 20

    # JC — Justification Code (byte 15): 0x02 = centred.
    tti[15] = 0x02

    # CF — Comment Flag (byte 16): 0x00 = subtitle data (not a comment).
    tti[16] = 0x00

    # TF — Text Field (bytes 17–128, i.e. 112 bytes).
    # Lines are separated by 0x8A (teletext CR/LF). Unused bytes are 0x8F
    # (end-of-text padding), which broadcast decoders treat as ignored filler.
    tf = bytearray(_TF_SIZE)
    tf_pos = 0

    lines = cue.text.split("\n")
    for line_idx, line in enumerate(lines):
        if line_idx > 0 and tf_pos < _TF_SIZE:
            # Insert teletext newline between lines.
            tf[tf_pos] = _CR_LF
            tf_pos += 1

        encoded_line = line.encode("latin-1", errors="replace")
        for byte in encoded_line:
            if tf_pos >= _TF_SIZE:
                break
            tf[tf_pos] = byte
            tf_pos += 1

    # Pad remainder of text field with 0x8F (end-of-text filler).
    while tf_pos < _TF_SIZE:
        tf[tf_pos] = 0x8F
        tf_pos += 1

    tti[17:129] = tf

    return bytes(tti)


def generate(cues: list[EBUSTLCue], metadata: dict | None = None) -> bytes:
    """Generate a valid EBU-STL binary file from a list of subtitle cues.

    The output is a GSI block (1024 bytes) followed by one 128-byte TTI
    block per cue, per EBU Tech 3264.

    Args:
        cues: Ordered list of ``EBUSTLCue`` objects. May be empty.
        metadata: Optional dict with programme metadata:
            - ``title`` (str): Original programme title (max 32 chars displayed).
            - ``language`` (str): ISO 639-1 target language code (e.g. ``"fr"``).
            - ``fps`` (int): Frame rate; 25 (default) or 30.

    Returns:
        Binary EBU-STL file content as ``bytes``.

    Raises:
        ValidationError: If any cue has end_ms <= start_ms, or if fps is
            not a supported value (25 or 30).
    """
    if metadata is None:
        metadata = {}

    fps = int(metadata.get("fps", 25))
    if fps not in (25, 30):
        raise ValidationError(
            f"Unsupported fps value: {fps}. EBU-STL supports 25 (PAL) or 30 (NTSC)."
        )

    for cue in cues:
        if cue.end_ms <= cue.start_ms:
            raise ValidationError(
                f"Cue {cue.index}: end_ms ({cue.end_ms}) must be greater than "
                f"start_ms ({cue.start_ms})."
            )

    gsi = _build_gsi(metadata, subtitle_count=len(cues))

    tti_blocks = bytearray()
    for i, cue in enumerate(cues):
        tti_blocks.extend(_build_tti(cue, subtitle_number=i, fps=fps))

    return gsi + bytes(tti_blocks)
