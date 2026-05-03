from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import fitz
import mammoth
from bs4 import BeautifulSoup, Tag
from weasyprint import HTML


REPO_ROOT = Path("/home/afetz/work/clean/NEWWAY")
DOCX_PATH = REPO_ROOT / "output/doc/Fizulin_AV_VKR_final_gost_7_32.docx"
PDF_DIR = REPO_ROOT / "output/pdf"
HTML_PATH = PDF_DIR / "Fizulin_AV_VKR_final_gost_7_32.html"
PDF_PATH = PDF_DIR / "Fizulin_AV_VKR_final_gost_7_32.pdf"
TEMP_PDF_PATH = PDF_DIR / "Fizulin_AV_VKR_final_gost_7_32.tmp.pdf"
STATS_PATH = PDF_DIR / "Fizulin_AV_VKR_final_gost_7_32.stats.json"
PREVIEW_DIR = PDF_DIR / "previews"


def ensure_dirs() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "section"


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def visible_text(tag: Tag) -> str:
    text = normalize_text(tag.get_text(" ", strip=True))
    text = re.sub(r"\[\[[^\]]+\]\]", "", text)
    return normalize_text(text)


def convert_docx_fragment() -> str:
    with DOCX_PATH.open("rb") as handle:
        result = mammoth.convert_to_html(handle)
    return result.value


def build_soup(raw_fragment: str) -> BeautifulSoup:
    html = f"<html><body>{raw_fragment}</body></html>"
    return BeautifulSoup(html, "html.parser")


def extract_headings(soup: BeautifulSoup) -> list[dict[str, str | int]]:
    headings: list[dict[str, str | int]] = []
    seen: dict[str, int] = {}
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = normalize_text(tag.get_text(" ", strip=True))
        if not text:
            continue
        base = slugify(text)
        seen[base] = seen.get(base, 0) + 1
        anchor = base if seen[base] == 1 else f"{base}-{seen[base]}"
        tag["id"] = anchor
        marker = f"[[{anchor}]]"
        marker_tag = soup.new_tag("span", attrs={"class": "marker"})
        marker_tag.string = marker
        tag.append(marker_tag)
        level = int(tag.name[1])
        headings.append({"level": level, "text": text, "anchor": anchor, "marker": marker})
    return headings


def wrap_title_page(soup: BeautifulSoup) -> Tag:
    body = soup.body
    first_heading = body.find(["h1", "h2", "h3"])
    title_nodes = []
    current = body.contents[0] if body.contents else None
    while current and current is not first_heading:
        nxt = current.next_sibling
        title_nodes.append(current.extract())
        current = nxt

    section = soup.new_tag("section", attrs={"class": "title-page"})
    for node in title_nodes:
        if isinstance(node, Tag) and normalize_text(node.get_text(" ", strip=True)):
            section.append(node)
    body.insert(0, section)
    return section


def add_section_classes(soup: BeautifulSoup) -> None:
    current_h1 = None
    for node in soup.body.find_all(["h1", "p", "table", "ul", "ol", "pre"], recursive=False):
        if node.name == "h1":
            current_h1 = visible_text(node).lower()
            continue
        if node.name == "p":
            text = normalize_text(node.get_text(" ", strip=True))
            if text.startswith("Рисунок "):
                node["class"] = node.get("class", []) + ["caption"]
            if text.startswith("Таблица "):
                node["class"] = node.get("class", []) + ["caption", "table-caption"]
            if current_h1 and (
                current_h1.startswith("перечень сокращений")
                or current_h1.startswith("термины")
                or current_h1.startswith("список использованных")
            ):
                node["class"] = node.get("class", []) + ["no-indent"]


def toc_level_from_text(text: str) -> int:
    if re.match(r"^\d+\.\d+\.\d+", text):
        return 3
    if re.match(r"^\d+\.\d+", text):
        return 2
    return 1


def format_toc_section(soup: BeautifulSoup) -> None:
    toc_heading = None
    for heading in soup.find_all("h1"):
        if visible_text(heading) == "Содержание":
            toc_heading = heading
            break
    if toc_heading is None:
        return

    current = toc_heading.next_sibling
    while current is not None:
        nxt = current.next_sibling
        if isinstance(current, Tag) and current.name == "h1":
            break
        if isinstance(current, Tag) and current.name == "p":
            text = normalize_text(current.get_text(" ", strip=True))
            match = re.match(r"^(.*?)(\d+)$", text)
            if match:
                label_text = match.group(1).strip()
                page_text = match.group(2)
                entry = soup.new_tag(
                    "div",
                    attrs={"class": f"toc-entry level-{toc_level_from_text(label_text)}"},
                )
                label = soup.new_tag("span", attrs={"class": "label"})
                label.string = label_text
                page = soup.new_tag("span", attrs={"class": "page"})
                page.string = page_text
                entry.append(label)
                entry.append(page)
                current.replace_with(entry)
        current = nxt


def sectionize_body(soup: BeautifulSoup) -> None:
    body = soup.body
    children = list(body.contents)
    new_children = []
    current_section: Tag | None = None

    for child in children:
        if not isinstance(child, Tag):
            continue
        if child.name == "section" and child.get("class") == ["title-page"]:
            if current_section is not None:
                new_children.append(current_section)
                current_section = None
            new_children.append(child.extract())
            continue
        if child.name == "h1":
            if current_section is not None:
                new_children.append(current_section)
            heading_text = visible_text(child)
            classes = ["chapter"]
            if heading_text == "Содержание":
                classes.append("toc-section")
            current_section = soup.new_tag("section", attrs={"class": classes})
            current_section.append(child.extract())
            continue
        if current_section is None:
            current_section = soup.new_tag("section", attrs={"class": "chapter"})
        current_section.append(child.extract())

    if current_section is not None:
        new_children.append(current_section)

    body.clear()
    for node in new_children:
        body.append(node)


def compose_html(soup: BeautifulSoup) -> str:
    css = """
    @page {
      size: A4;
      margin: 2cm 1.5cm 2cm 3cm;
      @bottom-center {
        content: counter(page);
        font-family: "Times New Roman", "Liberation Serif", serif;
        font-size: 12pt;
      }
    }
    @page title {
      @bottom-center { content: ""; }
    }
    html {
      font-family: "Times New Roman", "Liberation Serif", serif;
      font-size: 14pt;
      line-height: 1.5;
      color: #000;
    }
    body {
      margin: 0;
    }
    p {
      margin: 0 0 0.35em 0;
      text-align: justify;
      text-indent: 1.25cm;
      hyphens: auto;
      orphans: 2;
      widows: 2;
    }
    .no-indent {
      text-indent: 0;
    }
    h1, h2, h3 {
      page-break-after: avoid;
      break-after: avoid;
      break-inside: avoid;
      font-size: 14pt;
      margin: 0 0 0.8em 0;
      font-weight: 700;
    }
    h1 {
      text-align: center;
      page-break-before: always;
      break-before: page;
    }
    h2, h3 {
      text-align: left;
    }
    h2 {
      margin-top: 1em;
    }
    h3 {
      margin-top: 0.8em;
    }
    .title-page {
      page: title;
      break-after: page;
      min-height: 25cm;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
    }
    .title-page p {
      text-indent: 0;
      text-align: center;
      margin: 0 0 0.15em 0;
    }
    .title-page p:nth-child(5) { margin-top: 1.6cm; }
    .title-page p:nth-child(6) { margin-top: 0.4cm; }
    .title-page p:nth-child(13) { margin-top: 3.8cm; text-align: left; }
    .title-page p:nth-child(14),
    .title-page p:nth-child(15) { text-align: left; }
    .title-page p:last-child { margin-top: auto; }
    .chapter {
      break-before: page;
    }
    .chapter:first-of-type {
      break-before: auto;
    }
    .toc-section h1 {
      break-before: auto;
      page-break-before: auto;
    }
    .toc-section p {
      text-indent: 0;
      text-align: left;
    }
    .toc-entry {
      display: flex;
      align-items: flex-end;
      gap: 0.35em;
      margin: 0.12em 0;
      text-indent: 0;
      font-size: 14pt;
    }
    .toc-entry.level-1 { font-weight: 700; }
    .toc-entry.level-2 { padding-left: 1.25cm; font-size: 13pt; font-weight: 400; }
    .toc-entry.level-3 { padding-left: 2.5cm; font-size: 12pt; font-weight: 400; }
    .toc-entry .label {
      display: flex;
      flex: 1 1 auto;
      align-items: flex-end;
      min-width: 0;
    }
    .toc-entry .label::after {
      content: "";
      flex: 1 1 auto;
      border-bottom: 1px dotted #000;
      margin: 0 0 0.25em 0.4em;
    }
    .toc-entry .page {
      flex: 0 0 auto;
      min-width: 1.4cm;
      text-align: right;
      font-weight: 400;
    }
    .marker {
      font-size: 1pt;
      color: rgba(255, 255, 255, 0.01);
      margin-left: 0.1em;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      margin: 0.45em 0 0.7em 0;
      font-size: 11.5pt;
    }
    th, td {
      border: 1px solid #000;
      padding: 0.14cm 0.12cm;
      vertical-align: top;
    }
    img {
      display: block;
      margin: 0.35em auto;
      max-width: 100%;
      max-height: 20cm;
      object-fit: contain;
    }
    .caption {
      text-align: center;
      text-indent: 0;
      margin: 0.2em 0 0.55em 0;
    }
    ul, ol {
      margin: 0.3em 0 0.5em 1.25cm;
      padding: 0;
    }
    li {
      margin: 0.15em 0;
    }
    pre, code {
      font-family: "Liberation Mono", monospace;
      font-size: 10.5pt;
      white-space: pre-wrap;
      word-break: break-word;
    }
    """
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Fizulin AV VKR</title>"
        f"<style>{css}</style>"
        "</head><body>"
        f"{soup.body.decode_contents()}"
        "</body></html>"
    )


def render_pdf(html: str, pdf_path: Path) -> None:
    HTML(string=html, base_url=str(REPO_ROOT)).write_pdf(str(pdf_path))


def find_heading_pages(pdf_path: Path, headings: list[dict[str, str | int]]) -> dict[str, int]:
    pdf = fitz.open(pdf_path)
    page_texts = [normalize_text(page.get_text("text")) for page in pdf]
    page_map: dict[str, int] = {}

    for heading in headings:
        marker = normalize_text(str(heading["marker"]))
        for index, page_text in enumerate(page_texts, start=1):
            if marker and marker in page_text:
                page_map[str(heading["anchor"])] = index
                break

    return page_map


def write_previews(pdf_path: Path) -> None:
    pdf = fitz.open(pdf_path)
    if pdf.page_count == 0:
        return

    requested = [0, 1, 2, max(pdf.page_count - 3, 0), max(pdf.page_count - 2, 0), pdf.page_count - 1]
    seen = set()
    for page_index in requested:
        if page_index in seen or page_index < 0 or page_index >= pdf.page_count:
            continue
        seen.add(page_index)
        page = pdf.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        pix.save(PREVIEW_DIR / f"page_{page_index + 1:03d}.png")


def write_stats(pdf_path: Path, page_map: dict[str, int], headings: list[dict[str, str | int]]) -> None:
    pdf = fitz.open(pdf_path)
    payload = {
        "docx": str(DOCX_PATH),
        "pdf": str(pdf_path),
        "page_count": pdf.page_count,
        "headings": [
            {
                "level": heading["level"],
                "text": heading["text"],
                "anchor": heading["anchor"],
                "page": page_map.get(str(heading["anchor"])),
            }
            for heading in headings
        ],
    }
    STATS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_html() -> tuple[str, list[dict[str, str | int]]]:
    raw_fragment = convert_docx_fragment()
    soup = build_soup(raw_fragment)
    headings = extract_headings(soup)
    wrap_title_page(soup)
    add_section_classes(soup)
    format_toc_section(soup)
    sectionize_body(soup)
    html = compose_html(soup)
    return html, headings


def main() -> None:
    ensure_dirs()

    html, headings = build_html()
    render_pdf(html, PDF_PATH)
    final_page_map = find_heading_pages(PDF_PATH, headings)

    HTML_PATH.write_text(html, encoding="utf-8")
    write_previews(PDF_PATH)
    write_stats(PDF_PATH, final_page_map, headings)


if __name__ == "__main__":
    main()
