from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from .io import read_json, write_json
from .paths import ROOT, ensure_data_dirs


@dataclass(frozen=True)
class MirrorResult:
    mirrored: int
    skipped: int
    manifest_path: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mirror_external_sources(paths: list[str]) -> MirrorResult:
    """Copy external sources into `data/mirrors/` and emit a manifest.

    This is an *unlocked mirror tree*: it copies bytes for deterministic ingestion
    without changing the external source.
    """
    ensure_data_dirs()
    lock_path = ROOT / "data" / "setup" / "root_lock.json"
    lock = read_json(lock_path, {})
    mirror_root_rel = (lock.get("policy") or {}).get("external_mirror_root") if isinstance(lock, dict) else None
    mirror_root = ROOT / (mirror_root_rel or "data/mirrors")
    mirror_root.mkdir(parents=True, exist_ok=True)

    allow_suffixes = set()
    policy = lock.get("policy") if isinstance(lock, dict) else None
    if isinstance(policy, dict):
        for s in policy.get("mirror_allow_suffixes", []) or []:
            if isinstance(s, str):
                allow_suffixes.add(s.lower())

    mirrored = 0
    skipped = 0
    entries: list[dict[str, object]] = []

    for raw in paths:
        src = Path(raw).expanduser().resolve()
        if not src.exists() or not src.is_file():
            skipped += 1
            entries.append({"source": str(src), "status": "missing"})
            continue
        if allow_suffixes and src.suffix.lower() not in allow_suffixes:
            skipped += 1
            entries.append({"source": str(src), "status": "suffix_blocked"})
            continue

        # stable destination name keyed by sha256 + basename to avoid collisions
        digest = _sha256(src)[:16]
        dest = mirror_root / f"{src.stem}__{digest}{src.suffix}"
        shutil.copyfile(src, dest)
        mirrored += 1
        entries.append(
            {
                "source": str(src),
                "dest": str(dest.relative_to(ROOT)),
                "sha256": _sha256(src),
                "bytes": src.stat().st_size,
                "status": "mirrored",
            }
        )

    manifest = {
        "id": "mirror_manifest_v1",
        "root": str(ROOT),
        "mirror_root": str(mirror_root.relative_to(ROOT)),
        "entries": entries,
        "mirrored": mirrored,
        "skipped": skipped,
    }
    manifest_path = mirror_root / "mirror_manifest.json"
    write_json(manifest_path, manifest)
    return MirrorResult(mirrored=mirrored, skipped=skipped, manifest_path=str(manifest_path.relative_to(ROOT)))

