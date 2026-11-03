#!/usr/bin/env python3
"""Zip each skill for upload in chat (Customize > Skills). Run:  python tools/package.py

Creates dist/<skill-name>.zip with the folder name at the top, as the upload requires.
Runs the skill lint first and stops if it fails.
"""
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if subprocess.run([sys.executable, str(ROOT / "tools/lint_skills.py")]).returncode != 0:
    sys.exit("Fix the lint problems first.")

dist = ROOT / "dist"
dist.mkdir(exist_ok=True)
for folder in sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()):
    out = dist / f"{folder.name}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                full = Path(root) / f
                z.write(full, Path(folder.name) / full.relative_to(folder))
    print(f"{out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB)")
