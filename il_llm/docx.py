from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def extract_docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", WORD_NS):
        parts: list[str] = []
        for node in para.iter():
            tag = node.tag.rsplit("}", 1)[-1]
            if tag == "t" and node.text:
                parts.append(node.text)
            elif tag == "tab":
                parts.append(" ")
            elif tag == "br":
                parts.append("\n")
        text = re.sub(r"[ \t]+", " ", "".join(parts)).strip()
        if text:
            paragraphs.append(html.unescape(text))
    return paragraphs


def count_docx_tables(path: Path) -> int:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    return len(root.findall(".//w:tbl", WORD_NS))


def count_docx_media(path: Path) -> int:
    with zipfile.ZipFile(path) as zf:
        return sum(1 for name in zf.namelist() if name.startswith("word/media/"))

