#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{%s}" % NS["w"]
CITATION_RE = re.compile(r"\[(\d+)\](?:\s*[–-]\s*\[(\d+)\])?")
REF_ENTRY_RE = re.compile(r"^\s*(\d+)\.\s*(.+)")


@dataclass
class Paragraph:
    index: int
    style_id: str
    text: str
    citations: list[int]


def iter_paragraphs(docx_path: Path) -> Iterable[Paragraph]:
    with ZipFile(docx_path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    for index, paragraph in enumerate(root.findall(".//w:body/w:p", NS), start=1):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()
        if not text:
            continue

        style_id = ""
        props = paragraph.find("w:pPr", NS)
        if props is not None:
            style = props.find("w:pStyle", NS)
            if style is not None:
                style_id = style.get(f"{W}val", "")

        citations: list[int] = []
        for first, last in CITATION_RE.findall(text):
            start = int(first)
            end = int(last) if last else start
            citations.extend(range(start, end + 1))

        yield Paragraph(index=index, style_id=style_id, text=text, citations=citations)


def extract_references(paragraphs: list[Paragraph]) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    started = False
    for paragraph in paragraphs:
        if paragraph.text == "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ":
            started = True
            continue
        if not started:
            continue
        match = REF_ENTRY_RE.match(paragraph.text)
        if not match:
            continue
        refs.append(
            {
                "paragraph_index": paragraph.index,
                "number": int(match.group(1)),
                "text": match.group(2).strip(),
            }
        )
    return refs


def extract_first_chapter(paragraphs: list[Paragraph]) -> list[Paragraph]:
    start = None
    end = None
    for pos, paragraph in enumerate(paragraphs):
        if paragraph.text == "1 Обзор предметной области и анализ существующих подходов":
            start = pos
        elif paragraph.text == "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ":
            end = pos
            break

    if start is None or end is None or start >= end:
        raise SystemExit("Cannot locate chapter 1 or bibliography in document.")

    return paragraphs[start:end]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx_path", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--section",
        choices=["chapter1", "references", "all"],
        default="all",
    )
    args = parser.parse_args()

    paragraphs = list(iter_paragraphs(args.docx_path))
    payload: dict[str, object] = {}

    if args.section in {"chapter1", "all"}:
        payload["chapter1"] = [
            {
                "index": p.index,
                "style_id": p.style_id,
                "text": p.text,
                "citations": p.citations,
            }
            for p in extract_first_chapter(paragraphs)
        ]

    if args.section in {"references", "all"}:
        payload["references"] = extract_references(paragraphs)

    indent = 2 if args.pretty else None
    print(json.dumps(payload, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
