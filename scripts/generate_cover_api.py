#!/usr/bin/env python3
"""
generate_cover_api.py — generate TEXT-FREE cover artwork via the OpenAI Images API
(gpt-image-1). The reliable replacement for scripting chatgpt.com (which is not
automatable). Output is artwork only; title/series/author are added afterward by
scripts/overlay-cover-text.py (deterministic, correctly-spelled typography).

Key handling (never printed): reads OPENAI_API_KEY from the environment, else from
--key-file, else from ./.openai_key or ~/.openai_key.

Usage:
  generate_cover_api.py <output.png> --prompt "<text-free artwork prompt>"
                        [--size 1024x1536] [--quality high] [--key-file PATH]
Exit: 0 ok, 2 usage/IO, 3 API/auth error.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.openai.com/v1/images/generations"


def load_key(key_file: str | None) -> str | None:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"].strip()
    candidates = [key_file] if key_file else []
    candidates += [str(Path.cwd() / ".openai_key"), str(Path.home() / ".openai_key")]
    for c in candidates:
        if c and Path(c).is_file():
            v = Path(c).read_text().strip()
            if v:
                return v
    return None


def generate(prompt: str, out: Path, size: str, quality: str, key: str) -> None:
    body = json.dumps({
        "model": "gpt-image-1", "prompt": prompt,
        "size": size, "quality": quality, "n": 1,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    b64 = data["data"][0]["b64_json"]
    out.write_bytes(base64.b64decode(b64))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Generate text-free cover artwork via gpt-image-1.")
    ap.add_argument("output")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--size", default="1024x1536",
                    help="gpt-image-1 portrait default; overlay resizes to 1600x2560")
    ap.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    ap.add_argument("--key-file")
    args = ap.parse_args(argv)

    key = load_key(args.key_file)
    if not key:
        print("error: no API key. Set OPENAI_API_KEY, or put it in ./.openai_key or ~/.openai_key",
              file=sys.stderr)
        return 3
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        generate(args.prompt, out, args.size, args.quality, key)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        print(f"API error {e.code}: {detail}", file=sys.stderr)
        return 3
    except Exception as e:  # noqa: BLE001 - surface any transport/parse failure, never crash silently
        print(f"error: {e}", file=sys.stderr)
        return 3
    print(f"artwork written: {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
