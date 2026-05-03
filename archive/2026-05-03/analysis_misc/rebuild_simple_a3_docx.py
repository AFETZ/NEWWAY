#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}
W = "{%s}" % W_NS


def make_paragraph(text: str, style_id: str) -> ET.Element:
    p = ET.Element(f"{W}p")
    ppr = ET.SubElement(p, f"{W}pPr")
    pstyle = ET.SubElement(ppr, f"{W}pStyle")
    pstyle.set(f"{W}val", style_id)
    if text:
        run = ET.SubElement(p, f"{W}r")
        t = ET.SubElement(run, f"{W}t")
        if text.startswith(" ") or text.endswith(" ") or "  " in text:
            t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = text
    return p


def read_paragraphs(text_path: Path) -> list[str]:
    lines = text_path.read_text(encoding="utf-8").splitlines()
    return [line.rstrip() for line in lines]


def rebuild(template_docx: Path, text_path: Path, output_docx: Path) -> None:
    paragraphs = read_paragraphs(text_path)
    with ZipFile(template_docx) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        body = root.find(".//w:body", NS)
        if body is None:
            raise SystemExit("Cannot locate body in docx.")
        sect_pr = body.find("w:sectPr", NS)
        if sect_pr is None:
            raise SystemExit("Cannot locate sectPr in docx.")
        sect_pr = ET.fromstring(ET.tostring(sect_pr, encoding="utf-8"))

        for child in list(body):
            body.remove(child)

        for line in paragraphs:
            body.append(make_paragraph(line, "a3"))
        body.append(sect_pr)

        document_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with ZipFile(output_docx, "w", ZIP_DEFLATED) as out_zip:
            for info in archive.infolist():
                data = archive.read(info.filename)
                if info.filename == "word/document.xml":
                    data = document_xml
                out_zip.writestr(info, data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template_docx", type=Path)
    parser.add_argument("text_path", type=Path)
    parser.add_argument("output_docx", type=Path)
    args = parser.parse_args()
    rebuild(args.template_docx, args.text_path, args.output_docx)


if __name__ == "__main__":
    main()
