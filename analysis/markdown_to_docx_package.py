#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}
W = "{%s}" % W_NS


def parse_markdown(md_text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            items.append(("blank", ""))
            continue
        if line.startswith("#### "):
            items.append(("h4", line[5:]))
            continue
        if line.startswith("### "):
            items.append(("h3", line[4:]))
            continue
        if line.startswith("## "):
            items.append(("h2", line[3:]))
            continue
        if line.startswith("# "):
            items.append(("h1", line[2:]))
            continue
        items.append(("p", line))
    return items


def make_paragraph(kind: str, text: str) -> ET.Element:
    paragraph = ET.Element(f"{W}p")

    if kind != "blank":
        ppr = ET.SubElement(paragraph, f"{W}pPr")
        style_id = {
            "h1": "1",
            "h2": "2",
            "h3": "3",
            "h4": "4",
        }.get(kind)
        if style_id:
            pstyle = ET.SubElement(ppr, f"{W}pStyle")
            pstyle.set(f"{W}val", style_id)

        run = ET.SubElement(paragraph, f"{W}r")
        t = ET.SubElement(run, f"{W}t")
        if text.startswith(" ") or text.endswith(" ") or "  " in text:
            t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = text

    return paragraph


def build_body(markdown_text: str, sect_pr: ET.Element) -> list[ET.Element]:
    body_elements: list[ET.Element] = []
    for kind, text in parse_markdown(markdown_text):
        body_elements.append(make_paragraph(kind, text))
    body_elements.append(copy.deepcopy(sect_pr))
    return body_elements


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template_docx", type=Path)
    parser.add_argument("markdown_file", type=Path)
    parser.add_argument("output_docx", type=Path)
    args = parser.parse_args()

    markdown_text = args.markdown_file.read_text(encoding="utf-8")

    with ZipFile(args.template_docx) as archive:
        document_root = ET.fromstring(archive.read("word/document.xml"))
        sect_pr = document_root.find(".//w:body/w:sectPr", NS)
        if sect_pr is None:
            raise SystemExit("Cannot locate sectPr in template docx.")

        body = document_root.find(".//w:body", NS)
        if body is None:
            raise SystemExit("Cannot locate body in template docx.")

        for child in list(body):
            body.remove(child)
        for element in build_body(markdown_text, sect_pr):
            body.append(element)

        document_xml = ET.tostring(document_root, encoding="utf-8", xml_declaration=True)

        with ZipFile(args.output_docx, "w", ZIP_DEFLATED) as out_zip:
            for info in archive.infolist():
                data = archive.read(info.filename)
                if info.filename == "word/document.xml":
                    data = document_xml
                out_zip.writestr(info, data)


if __name__ == "__main__":
    main()
