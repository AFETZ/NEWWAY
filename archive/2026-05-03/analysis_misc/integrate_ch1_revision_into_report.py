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


def normalize_inline_math(text: str) -> str:
    text = text.replace(r"\(", "").replace(r"\)", "")
    text = text.replace(r"\Delta", "Δ")
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def set_paragraph_text(paragraph: ET.Element, text: str) -> ET.Element:
    ppr = paragraph.find(f"{W}pPr")
    for child in list(paragraph):
        if child is not ppr:
            paragraph.remove(child)
    run = ET.SubElement(paragraph, f"{W}r")
    t = ET.SubElement(run, f"{W}t")
    if text.startswith(" ") or text.endswith(" ") or "  " in text:
        t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return paragraph


def make_paragraph(text: str, style_id: str | None = None, center: bool = False) -> ET.Element:
    paragraph = ET.Element(f"{W}p")
    if style_id or center:
        ppr = ET.SubElement(paragraph, f"{W}pPr")
        if style_id:
            pstyle = ET.SubElement(ppr, f"{W}pStyle")
            pstyle.set(f"{W}val", style_id)
        if center:
            jc = ET.SubElement(ppr, f"{W}jc")
            jc.set(f"{W}val", "center")
    return set_paragraph_text(paragraph, text)


def clear_cell(cell: ET.Element) -> None:
    tcpr = cell.find(f"{W}tcPr")
    for child in list(cell):
        if child is not tcpr:
            cell.remove(child)


def fill_table(table: ET.Element, rows: list[list[str]]) -> ET.Element:
    trs = table.findall(f"{W}tr")
    if len(trs) != len(rows):
        raise ValueError(f"Table row count mismatch: expected {len(trs)}, got {len(rows)}")
    for tr, row_texts in zip(trs, rows):
        cells = tr.findall(f"{W}tc")
        if len(cells) != len(row_texts):
            raise ValueError(f"Table column count mismatch: expected {len(cells)}, got {len(row_texts)}")
        for cell, text in zip(cells, row_texts):
            clear_cell(cell)
            cell.append(make_paragraph(text))
    return table


def extract_section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def parse_markdown_table(lines: list[str], index: int) -> tuple[list[list[str]], int]:
    table_lines: list[str] = []
    while index < len(lines) and lines[index].strip().startswith("|"):
        table_lines.append(lines[index].strip())
        index += 1
    rows: list[list[str]] = []
    for line_no, line in enumerate(table_lines):
        parts = [part.strip() for part in line.strip("|").split("|")]
        if line_no == 1 and all(re.fullmatch(r"-+", part.replace(" ", "")) for part in parts):
            continue
        rows.append(parts)
    return rows, index


def parse_blocks(section_text: str) -> list[dict[str, object]]:
    lines = section_text.splitlines()
    blocks: list[dict[str, object]] = []
    paragraph_buf: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_buf
        if paragraph_buf:
            blocks.append({"type": "paragraph", "text": normalize_inline_math(" ".join(paragraph_buf).strip())})
            paragraph_buf = []

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped.startswith(r"\["):
            flush_paragraph()
            eq_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(r"\]"):
                eq_lines.append(lines[i].strip())
                i += 1
            eq_text = normalize_inline_math(" ".join(eq_lines)).replace(" ", "")
            blocks.append({"type": "equation", "text": eq_text})
            i += 1
            continue
        if stripped.startswith("**Таблица"):
            flush_paragraph()
            caption = stripped.strip("*")
            blocks.append({"type": "caption", "text": caption})
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            rows, i = parse_markdown_table(lines, i)
            blocks.append({"type": "table", "rows": rows})
            continue
        if stripped.startswith("**Рисунок"):
            flush_paragraph()
            blocks.append({"type": "figure_caption", "text": stripped.strip("*")})
            i += 1
            continue
        if stripped.startswith("#### "):
            flush_paragraph()
            blocks.append({"type": "heading", "level": 3, "text": stripped[5:]})
            i += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            blocks.append({"type": "heading", "level": 2, "text": stripped[4:]})
            i += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            blocks.append({"type": "heading", "level": 1, "text": stripped[3:]})
            i += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            i += 1
            continue
        if re.match(r"^\d+\.\s", stripped):
            flush_paragraph()
            blocks.append({"type": "paragraph", "text": normalize_inline_math(stripped)})
            i += 1
            continue
        paragraph_buf.append(stripped)
        i += 1

    flush_paragraph()
    return blocks


def parse_bibliography(section_text: str) -> list[str]:
    entries: list[str] = []
    for line in section_text.splitlines():
        match = re.match(r"^\s*(\d+)\.\s+(.+)$", line)
        if match:
            entries.append(f"{match.group(1)}. {match.group(2).strip()}")
    return entries


def locate_body_parts(body: ET.Element) -> dict[str, object]:
    children = list(body)
    para_no = 0
    chapter_start_idx = None
    bibliography_idx = None
    figure_caption_idx = None
    for idx, child in enumerate(children):
        tag = child.tag.split("}", 1)[1]
        if tag != "p":
            continue
        para_no += 1
        text = "".join(t.text or "" for t in child.findall(".//w:t", NS)).strip()
        if text == "1 Обзор предметной области и анализ существующих подходов":
            chapter_start_idx = idx
        if text == "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ":
            bibliography_idx = idx
        if text.startswith("Рисунок 1.1"):
            figure_caption_idx = idx

    if chapter_start_idx is None or bibliography_idx is None or figure_caption_idx is None:
        raise SystemExit("Failed to locate chapter start, figure caption, or bibliography in report.")

    table_templates = [copy.deepcopy(child) for child in children if child.tag == f"{W}tbl"]
    if len(table_templates) < 2:
        raise SystemExit("Expected two tables in report body.")

    figure_drawing_idx = figure_caption_idx - 1
    figure_drawing = copy.deepcopy(children[figure_drawing_idx])
    figure_caption = copy.deepcopy(children[figure_caption_idx])
    sect_pr = copy.deepcopy(body.find("w:sectPr", NS))
    if sect_pr is None:
        raise SystemExit("Failed to locate sectPr in report.")

    intro_children = [copy.deepcopy(child) for child in children[:chapter_start_idx]]
    return {
        "intro_children": intro_children,
        "table_templates": table_templates[:2],
        "figure_drawing": figure_drawing,
        "figure_caption": figure_caption,
        "sect_pr": sect_pr,
    }


def build_new_content(
    blocks: list[dict[str, object]],
    table_templates: list[ET.Element],
    figure_drawing: ET.Element,
    figure_caption_template: ET.Element,
    bibliography_entries: list[str],
) -> list[ET.Element]:
    elements: list[ET.Element] = []
    heading_styles = {1: "1", 2: "2", 3: "3"}
    table_iter = iter(table_templates)

    for block in blocks:
        kind = block["type"]
        if kind == "heading":
            level = int(block["level"])
            elements.append(make_paragraph(str(block["text"]), style_id=heading_styles[level]))
        elif kind == "paragraph":
            elements.append(make_paragraph(str(block["text"])))
        elif kind == "caption":
            elements.append(make_paragraph(str(block["text"])))
        elif kind == "equation":
            elements.append(make_paragraph(str(block["text"]), center=True))
        elif kind == "table":
            template = copy.deepcopy(next(table_iter))
            elements.append(fill_table(template, block["rows"]))
        elif kind == "figure_caption":
            elements.append(copy.deepcopy(figure_drawing))
            caption = copy.deepcopy(figure_caption_template)
            elements.append(set_paragraph_text(caption, str(block["text"])))
        else:
            raise ValueError(f"Unsupported block type: {kind}")

    elements.append(make_paragraph("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", style_id="1"))
    for entry in bibliography_entries:
        elements.append(make_paragraph(entry))
    return elements


def integrate(template_docx: Path, revision_md: Path, output_docx: Path) -> None:
    md_text = revision_md.read_text(encoding="utf-8")
    section_a = extract_section(md_text, "# А. Полностью исправленный текст первой главы", "# Б. Отчёт по правкам")
    section_c = extract_section(md_text, "# В. Очищенный список литературы по первой главе", "# Г. Список проблемных мест")
    blocks = parse_blocks(section_a)
    bibliography_entries = parse_bibliography(section_c)

    with ZipFile(template_docx) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        body = root.find(".//w:body", NS)
        if body is None:
            raise SystemExit("Cannot locate body in report.")

        parts = locate_body_parts(body)
        new_children = parts["intro_children"] + build_new_content(
            blocks,
            parts["table_templates"],
            parts["figure_drawing"],
            parts["figure_caption"],
            bibliography_entries,
        )
        new_children.append(parts["sect_pr"])

        for child in list(body):
            body.remove(child)
        for child in new_children:
            body.append(child)

        document_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with ZipFile(output_docx, "w", ZIP_DEFLATED) as out_zip:
            for info in archive.infolist():
                data = archive.read(info.filename)
                if info.filename == "word/document.xml":
                    data = document_xml
                out_zip.writestr(info, data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_docx", type=Path)
    parser.add_argument("revision_md", type=Path)
    parser.add_argument("output_docx", type=Path)
    args = parser.parse_args()
    integrate(args.report_docx, args.revision_md, args.output_docx)


if __name__ == "__main__":
    main()
