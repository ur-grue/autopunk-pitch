#!/usr/bin/env bash
# assemble-docx.sh — Assembles chapter markdown files into a KDP-ready DOCX
# Usage: ./assemble-docx.sh <novel_directory> [title] [author]
#
# Requires: pandoc (brew install pandoc)

set -euo pipefail

NOVEL_DIR="${1:?Usage: assemble-docx.sh <novel_directory> [title] [author]}"
TITLE="${2:-Untitled Novel}"
AUTHOR="${3:-Anonymous}"
YEAR=$(date +%Y)

# Verify pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "ERROR: pandoc is required but not installed."
    echo "Install with: brew install pandoc (macOS) or apt install pandoc (Linux)"
    exit 1
fi

# Collect chapter files in order
CHAPTERS=()
for f in "$NOVEL_DIR"/chapter[0-9][0-9].md; do
    [ -f "$f" ] && CHAPTERS+=("$f")
done

if [ ${#CHAPTERS[@]} -eq 0 ]; then
    echo "ERROR: No chapter files found in $NOVEL_DIR"
    exit 1
fi

echo "Found ${#CHAPTERS[@]} chapters"

# Build combined markdown
COMBINED="$NOVEL_DIR/complete_novel.md"
{
    # Title page
    echo "# $TITLE"
    echo ""
    echo "*by $AUTHOR*"
    echo ""
    echo "\\newpage"
    echo ""
    # Copyright page
    echo "Copyright $YEAR $AUTHOR"
    echo ""
    echo "All rights reserved. No part of this publication may be reproduced,"
    echo "distributed, or transmitted in any form or by any means without the"
    echo "prior written permission of the author."
    echo ""
    echo "This is a work of fiction. Names, characters, places, and incidents"
    echo "are the product of the author's imagination or are used fictitiously."
    echo ""
    echo "\\newpage"
    echo ""

    # Chapters
    TOTAL_WORDS=0
    CH_NUM=0
    for chapter in "${CHAPTERS[@]}"; do
        CH_NUM=$((CH_NUM + 1))
        echo ""
        # Extract chapter title if first line is a heading, otherwise use default
        FIRST_LINE=$(head -1 "$chapter")
        if [[ "$FIRST_LINE" == \#* ]]; then
            # Use existing heading
            cat "$chapter"
        else
            echo "## Chapter $CH_NUM"
            echo ""
            cat "$chapter"
        fi
        echo ""
        echo "\\newpage"
        echo ""

        # Count words
        WC=$(wc -w < "$chapter" | tr -d ' ')
        TOTAL_WORDS=$((TOTAL_WORDS + WC))
        echo "  Chapter $CH_NUM: $WC words" >&2
    done

    # Back matter — About the Author placeholder
    echo ""
    echo "## About the Author"
    echo ""
    echo "*$AUTHOR writes [genre] fiction. This is their [first/latest] novel.*"
    echo ""

    echo "Total words: $TOTAL_WORDS" >&2

} > "$COMBINED"

echo "Combined markdown: $COMBINED"

# Convert to DOCX
DOCX="$NOVEL_DIR/complete_novel.docx"

# Check for reference doc
REF_DOC=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/reference.docx" ]; then
    REF_DOC="--reference-doc=$SCRIPT_DIR/reference.docx"
fi

pandoc "$COMBINED" \
    -o "$DOCX" \
    --from markdown \
    --to docx \
    --toc \
    --toc-depth=1 \
    --metadata title="$TITLE" \
    --metadata author="$AUTHOR" \
    $REF_DOC

DOCX_SIZE=$(ls -lh "$DOCX" | awk '{print $5}')
echo ""
echo "DOCX created: $DOCX ($DOCX_SIZE)"
echo "Chapters: ${#CHAPTERS[@]}"
echo "Total words: $TOTAL_WORDS"
echo ""
echo "Ready for KDP upload."
