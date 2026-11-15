#!/usr/bin/env python3
"""Build MANIFEST.json for the staged SGLang course.

Records canonical staged paths, per-file SHA-256, the read-only root source,
and prohibited paths.  Usage: python3 make_manifest.py <staging_dir> <source.md> <out.json>
"""
import hashlib
import json
import os
import sys

staging = os.path.realpath(sys.argv[1])
source = os.path.realpath(sys.argv[2])
out_path = sys.argv[3]

ORDER = [
    "01-positioning-and-background.md",
    "02-core-concepts.md",
    "03-core-functionality.md",
    "04-usage.md",
    "05-related-tools.md",
    "06-learning-path.md",
    "07-verification-record.md",
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


files = []
for name in ORDER:
    p = os.path.join(staging, name)
    if not os.path.isfile(p) or os.path.islink(p):
        raise SystemExit(f"missing or non-regular staged file: {p}")
    files.append(
        {
            "path": p,
            "name": name,
            "sha256": sha256(p),
            "bytes": os.path.getsize(p),
            "op": "create",
        }
    )

manifest = {
    "course": "sglang-course",
    "generated": "2026-11-15",
    "root_source": {"path": source, "sha256": sha256(source), "mode": "read-only"},
    "staging_dir": staging,
    "destination": os.path.join(os.path.dirname(staging), "sglang-course"),
    "files": files,
    "prohibited_paths": [
        source,
        os.path.join(os.path.dirname(staging), ".git"),
        "any path outside " + staging,
    ],
}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print(f"MANIFEST written: {out_path}")
print(f"  staged files : {len(files)}")
print(f"  source sha256: {manifest['root_source']['sha256']}")
for x in files:
    print(f"  {x['sha256'][:16]}  {x['bytes']:>7}  {x['name']}")
