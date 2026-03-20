"""FormattingAgent — converts internal subtitle format to SRT/WebVTT/EBU-STL.

Pure Python agent (no AI API calls). Converts TranslationSegment or
TranscriptionSegment objects to formatted subtitle file content.
"""

import structlog

from app.agents.schemas import (
    FormattingInput,
    FormattingOutput,
    TranscriptionSegment,
    TranslationSegment,
)
from app.exceptions import ValidationError
from app.formats.ebu_stl import EBUSTLCue
from app.formats.ebu_stl import generate as generate_ebu_stl
from app.formats.srt import SRTCue
from app.formats.srt import generate as generate_srt
from app.formats.webvtt import WebVTTCue
from app.formats.webvtt import generate as generate_webvtt

logger = structlog.get_logger(__name__)

SUPPORTED_FORMATS = {"srt", "webvtt", "ebu_stl"}


class FormattingAgent:
    """Converts subtitle data to SRT, WebVTT, or EBU-STL format.

    Pure Python — no AI API calls, no cost. Takes input,
    returns formatted output.
    """

    def __init__(self) -> None:
        self._logger = logger.bind(agent="formatting")

    async def process(self, input: FormattingInput) -> FormattingOutput:
        """Convert segments to the requested subtitle format.

        Args:
            input: Formatting input with segments and target format.

        Returns:
            FormattingOutput with formatted file content. For ``ebu_stl``,
            ``content`` is the binary payload encoded as a latin-1 string
            so it can be transported through the ``str`` field; callers must
            decode it back with ``content.encode("latin-1")`` to recover bytes.

        Raises:
            ValidationError: If format is unsupported.
        """
        if input.format not in SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported format: {input.format}. "
                f"Supported: {SUPPORTED_FORMATS}"
            )

        self._logger.info(
            "formatting_started",
            job_id=str(input.job_id),
            language=input.language,
            format=input.format,
            segment_count=len(input.segments),
        )

        # Extract text from either TranslationSegment or TranscriptionSegment
        texts = []
        for seg in input.segments:
            if isinstance(seg, TranslationSegment):
                texts.append(
                    (seg.index, seg.start_ms, seg.end_ms, seg.translated_text)
                )
            elif isinstance(seg, TranscriptionSegment):
                texts.append(
                    (seg.index, seg.start_ms, seg.end_ms, seg.text)
                )
            else:
                # Handle dict-like objects from Pydantic model_dump
                texts.append((
                    seg.index,
                    seg.start_ms,
                    seg.end_ms,
                    getattr(seg, "translated_text", None)
                    or getattr(seg, "text", ""),
                ))

        if input.format == "srt":
            content = self._generate_srt(texts)
        elif input.format == "webvtt":
            content = self._generate_webvtt(texts)
        else:
            content = self._generate_ebu_stl(texts, language=input.language)

        self._logger.info(
            "formatting_completed",
            job_id=str(input.job_id),
            language=input.language,
            format=input.format,
            content_length=len(content),
        )

        return FormattingOutput(
            job_id=input.job_id,
            language=input.language,
            format=input.format,
            content=content,
        )

    def _generate_srt(
        self, texts: list[tuple[int, int, int, str]]
    ) -> str:
        """Generate SRT content from segment data.

        Args:
            texts: List of (index, start_ms, end_ms, text) tuples.

        Returns:
            SRT file content.
        """
        cues = [
            SRTCue(index=idx, start_ms=start, end_ms=end, text=text)
            for idx, start, end, text in texts
        ]
        return generate_srt(cues)

    def _generate_webvtt(
        self, texts: list[tuple[int, int, int, str]]
    ) -> str:
        """Generate WebVTT content from segment data.

        Args:
            texts: List of (index, start_ms, end_ms, text) tuples.

        Returns:
            WebVTT file content.
        """
        cues = [
            WebVTTCue(index=idx, start_ms=start, end_ms=end, text=text)
            for idx, start, end, text in texts
        ]
        return generate_webvtt(cues)

    def _generate_ebu_stl(
        self,
        texts: list[tuple[int, int, int, str]],
        language: str = "en",
    ) -> str:
        """Generate EBU-STL content from segment data.

        The binary payload is encoded as a latin-1 string so it can be
        stored in the ``FormattingOutput.content`` str field without loss.
        The export endpoint decodes it back to bytes with
        ``content.encode("latin-1")`` before sending the HTTP response.

        Args:
            texts: List of (index, start_ms, end_ms, text) tuples.
            language: ISO 639-1 language code passed through to the GSI block.

        Returns:
            EBU-STL binary payload as a latin-1 encoded str.
        """
        cues = [
            EBUSTLCue(index=idx, start_ms=start, end_ms=end, text=text)
            for idx, start, end, text in texts
        ]
        binary = generate_ebu_stl(cues, metadata={"language": language})
        # Round-trip through latin-1: every byte 0x00–0xFF maps 1-to-1.
        return binary.decode("latin-1")
