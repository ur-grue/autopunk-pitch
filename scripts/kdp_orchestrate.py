#!/usr/bin/env python3
"""
kdp_orchestrate.py — the deterministic spine for the kdp-orchestrator skill.

Manages orchestrator_state.json: walks a title through research -> [GATE 1] ->
generate -> quality -> [GATE 2] -> cover -> prepare -> upload -> [GATE 3], stopping
at each human gate, verifying the real artifact at each stage, and resuming from the
saved state. It NEVER publishes (GATE 3 is the greenlight; default = draft).

Stages run real checks: the quality stage shells out to scripts/quality_gate.py; the
others verify the produced artifacts exist. The browser-driving stages (cover gen,
KDP upload) are exercised by their own skills/scripts; here they are gated + recorded.

Usage:
  kdp_orchestrate.py init   <novel_dir> [--config TOML] [--mode single|series] [--books N]
  kdp_orchestrate.py run    <novel_dir>            # advance until a gate or done
  kdp_orchestrate.py approve <novel_dir> <g1|g2|g3>
  kdp_orchestrate.py status <novel_dir>
Exit: 0 ok, 2 usage/IO, 3 stopped at an unapproved gate.
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Ordered pipeline: ("stage", name) auto-runs; ("gate", key) stops until approved.
PIPELINE = [
    ("stage", "research"),
    ("gate", "g1"),
    ("stage", "generate"),
    ("stage", "quality"),
    ("gate", "g2"),
    ("stage", "cover"),
    ("stage", "prepare"),
    ("stage", "upload"),
    ("gate", "g3"),
    ("stage", "done"),
]
GATE_LABEL = {"g1": "GATE 1 (approve niche/spec)",
              "g2": "GATE 2 (approve manuscript + quality)",
              "g3": "GATE 3 (greenlight — default DRAFT, never auto-publish)"}


def state_path(novel_dir: Path) -> Path:
    return novel_dir / "orchestrator_state.json"


def load(novel_dir: Path) -> dict:
    p = state_path(novel_dir)
    if not p.exists():
        raise FileNotFoundError(f"no orchestrator_state.json in {novel_dir} — run `init` first")
    return json.loads(p.read_text())


def save(novel_dir: Path, st: dict) -> None:
    state_path(novel_dir).write_text(json.dumps(st, indent=2))


# --- stage runners: return (ok: bool, detail: str) -------------------------
def run_research(d: Path, st: dict):
    cfg = st.get("config")
    if cfg and (REPO / cfg).exists():
        return True, f"niche spec: {cfg}"
    return False, "no genre TOML config set (research-niche must emit one)"


def run_generate(d: Path, st: dict):
    chapters = sorted(glob.glob(str(d / "chapter[0-9][0-9].md")))
    docx = (d / "complete_novel.docx").exists()
    if chapters and docx:
        return True, f"{len(chapters)} chapters + complete_novel.docx"
    return False, f"missing output (chapters={len(chapters)}, docx={docx})"


def run_quality(d: Path, st: dict):
    try:
        r = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "quality_gate.py"), str(d), "--json"],
            capture_output=True, text=True, timeout=120)
        rep = json.loads(r.stdout)
        st["quality"] = {"pass": rep["pass"], "failing_chapters": rep["failing_chapters"]}
        n = len(rep["failing_chapters"])
        # Non-blocking at the stage level: the result is surfaced to the human at GATE 2.
        return True, ("quality PASS" if rep["pass"]
                      else f"quality FAIL ({n} ch) -> would auto-regen, then escalate @ GATE 2")
    except Exception as e:  # noqa: BLE001 - record + surface, never crash the spine
        st["quality"] = {"pass": False, "error": str(e)}
        return True, f"quality scorer error (fail-to-human @ GATE 2): {e}"


def run_cover(d: Path, st: dict):
    if (d / "covers" / "cover_final.jpg").exists():
        return True, "covers/cover_final.jpg present (overlay path)"
    return False, "no cover_final.jpg (run cover-generate)"


def run_prepare(d: Path, st: dict):
    if (d / "kdp_upload").is_dir():
        return True, "kdp_upload/ package present"
    return False, "no kdp_upload/ package (run kdp-prepare)"


def run_upload(d: Path, st: dict):
    # The live upload is driven by the kdp-upload skill (browse). Record status;
    # never publish from here. If a prior run/skill saved a draft, reflect it.
    prior = st.get("upload", "none")
    val = prior if prior in ("draft", "published") else "draft"
    st["upload"] = val
    return True, f"upload status: {val} (kdp-upload skill drives the live browser; GATE 3 stays draft)"


def run_done(d: Path, st: dict):
    return True, "pipeline complete — title sits at DRAFT awaiting your explicit publish"


RUNNERS = {"research": run_research, "generate": run_generate, "quality": run_quality,
           "cover": run_cover, "prepare": run_prepare, "upload": run_upload, "done": run_done}


def advance(novel_dir: Path) -> int:
    st = load(novel_dir)
    pos = st.get("pos", 0)
    while pos < len(PIPELINE):
        kind, key = PIPELINE[pos]
        if kind == "gate":
            if not st["gates"].get(key):
                st["pos"] = pos
                st["stage"] = f"awaiting:{key}"
                save(novel_dir, st)
                print(f"⏸  STOP at {GATE_LABEL[key]} — approve with: "
                      f"kdp_orchestrate.py approve {novel_dir} {key}")
                return 3
            print(f"✓  {GATE_LABEL[key]} approved")
            pos += 1
            continue
        ok, detail = RUNNERS[key](novel_dir, st)
        mark = "✓" if ok else "✗"
        print(f"{mark}  stage {key}: {detail}")
        if not ok:
            st["pos"] = pos
            st["stage"] = key
            save(novel_dir, st)
            print(f"⛔ stage '{key}' not satisfied — fix its input, then re-run")
            return 3
        st["pos"] = pos + 1
        st["stage"] = key
        save(novel_dir, st)
        pos += 1
    st["stage"] = "done"
    save(novel_dir, st)
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Deterministic spine for kdp-orchestrator.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init")
    pi.add_argument("novel_dir")
    pi.add_argument("--config")
    pi.add_argument("--mode", default="single")
    pi.add_argument("--books", type=int, default=1)
    for c in ("run", "status"):
        sub.add_parser(c).add_argument("novel_dir")
    pa = sub.add_parser("approve")
    pa.add_argument("novel_dir")
    pa.add_argument("gate")
    args = ap.parse_args(argv)
    d = Path(args.novel_dir)

    if args.cmd == "init":
        if not d.is_dir():
            print(f"error: not a directory: {d}", file=sys.stderr)
            return 2
        st = {"novel_dir": str(d), "mode": args.mode, "books": args.books,
              "config": args.config, "pos": 0, "stage": "init",
              "gates": {"g1": False, "g2": False, "g3": False},
              "upload": "none"}
        save(d, st)
        print(f"initialized orchestrator_state.json ({args.mode}) for {d}")
        return 0
    if args.cmd == "status":
        st = load(d)
        print(json.dumps({k: st[k] for k in ("mode", "stage", "pos", "gates", "config",
              "quality", "upload") if k in st}, indent=2))
        return 0
    if args.cmd == "approve":
        st = load(d)
        if args.gate not in st["gates"]:
            print(f"unknown gate {args.gate} (g1|g2|g3)", file=sys.stderr)
            return 2
        st["gates"][args.gate] = True
        save(d, st)
        print(f"approved {args.gate}")
        return 0
    if args.cmd == "run":
        return advance(d)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
