from __future__ import annotations

import hashlib
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .docx import count_docx_media, count_docx_tables, extract_docx_paragraphs
from .io import read_json, write_json
from .paths import SOURCE_MANIFEST_PATH, SOURCES_DIR, ensure_data_dirs, project_relative


TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".yml", ".yaml"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_source_text(path: Path) -> tuple[str, dict[str, int]]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        paragraphs = extract_docx_paragraphs(path)
        return "\n\n".join(paragraphs), {
            "paragraph_count": len(paragraphs),
            "table_count": count_docx_tables(path),
            "media_count": count_docx_media(path),
        }
    if suffix in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text, {
            "paragraph_count": len([p for p in re.split(r"\n\s*\n", text) if p.strip()]),
            "table_count": 0,
            "media_count": 0,
        }
    raise ValueError(f"unsupported source type: {path}")


def source_id(path: Path) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", path.stem).strip("_").lower()
    return clean[:80] or "source"


def ingest_source(path: Path, *, attribution: str = "A. Keddeh") -> dict[str, object]:
    ensure_data_dirs()
    path = path.expanduser().resolve()
    text, counts = read_source_text(path)
    sid = source_id(path)
    text_path = SOURCES_DIR / f"{sid}.txt"
    text_path.write_text(text + "\n", encoding="utf-8")
    if path.suffix.lower() == ".docx":
        copy_path = SOURCES_DIR / path.name
        if copy_path.resolve() != path:
            shutil.copyfile(path, copy_path)
    words = re.findall(r"\b[\w-]+\b", text)
    record = {
        "id": sid,
        "source_path": str(path),
        "source_copy": project_relative(SOURCES_DIR / path.name) if path.suffix.lower() == ".docx" else None,
        "extracted_text_path": project_relative(text_path),
        "attribution": attribution,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "word_count": len(words),
        "line_count": len(text.splitlines()),
        "ingested_utc": datetime.now(timezone.utc).isoformat(),
        **counts,
    }
    manifest = read_json(SOURCE_MANIFEST_PATH, [])
    manifest = [item for item in manifest if item.get("id") != sid]
    manifest.append(record)
    manifest.sort(key=lambda item: item["id"])
    write_json(SOURCE_MANIFEST_PATH, manifest)
    return record


def ingest_many(paths: list[Path], *, attribution: str = "A. Keddeh") -> list[dict[str, object]]:
    return [ingest_source(path, attribution=attribution) for path in paths]

