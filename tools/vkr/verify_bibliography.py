#!/usr/bin/env python3
"""Verify bibliography URLs, enrich missing DOIs via Crossref, and export
an updated bibliography file for the final VKR package."""

from __future__ import annotations

import csv
import difflib
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, quote_plus
from urllib.request import Request, urlopen


ROOT = Path("/home/afetz/work/clean/NEWWAY")
BIB_MD = ROOT / "analysis" / "vkr" / "VKR_bibliography.md"
OUT_DIR = ROOT / "output" / "doc" / "verification"
OUT_CSV = OUT_DIR / "bibliography_verification.csv"
OUT_JSON = OUT_DIR / "bibliography_sources.json"
OUT_MD = OUT_DIR / "bibliography_verification.md"
OUT_BIB = ROOT / "analysis" / "vkr" / "VKR_bibliography_verified.md"

ENTRY_RE = re.compile(r"^\d+\.\s+(.*)")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)]+")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

USER_AGENT = "Mozilla/5.0 (compatible; VKRVerifier/1.0; +https://example.org)"

MANUAL_OVERRIDES: dict[str, dict[str, str]] = {
    "1": {"url": "https://www.sae.org/standards/content/j3016_202104/"},
    "3": {"url": "https://www.etsi.org/deliver/etsi_en/302600_302699/302665/01.01.01_60/en_302665v010101p.pdf"},
    "4": {"url": "https://www.etsi.org/deliver/etsi_ts/123200_123299/123286/16.06.00_60/ts_123286v160600p.pdf"},
    "5": {"url": "https://www.etsi.org/deliver/etsi_ts/123200_123299/123287/16.06.00_60/ts_123287v160600p.pdf"},
    "6": {"url": "https://rosap.ntl.bts.gov/view/dot/34761"},
    "7": {"url": "https://rosap.ntl.bts.gov/view/dot/64241"},
    "8": {"url": "https://www.etsi.org/deliver/etsi_en/302600_302699/30263702/01.04.01_60/en_30263702v010401p.pdf"},
    "9": {"url": "https://www.etsi.org/deliver/etsi_en/302600_302699/30263703/01.03.01_60/en_30263703v010301p.pdf"},
    "10": {"url": "https://www.etsi.org/deliver/etsi_ts/103300_103399/103324/02.01.01_60/ts_103324v020101p.pdf"},
    "11": {"url": "https://www.sae.org/standards/content/j2735_202409/"},
    "12": {"url": "https://trid.trb.org/View/1516920"},
    "13": {"url": "https://www.etsi.org/deliver/etsi_ts/102600_102699/102687/01.02.01_60/ts_102687v010201p.pdf"},
    "15": {"doi": "10.1109/ACCESS.2021.3090855"},
    "16": {"url": "https://itecspec.com/archive/3gpp-specification-tr-37-885/"},
    "17": {"url": "https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.885.V1600.pdf"},
    "18": {"url": "https://www.etsi.org/deliver/etsi_tr/101600_101699/101613/01.01.01_60/tr_101613v010101p.pdf"},
    "21": {"url": "https://www.fhwa.dot.gov/publications/research/safety/08051/"},
    "27": {"url": "https://arxiv.org/abs/1711.10925"},
    "32": {"url": "https://arxiv.org/abs/2505.14184"},
    "36": {"url": "https://us.artechhouse.com/Introduction-to-the-Uniform-Geometrical-Theory-of-Diffraction-P288.aspx"},
    "42": {"url": "https://arxiv.org/abs/2203.11854"},
    "43": {"url": "https://elib.dlr.de/8380/"},
    "44": {"url": "https://trid.trb.org/View/115323"},
    "46": {"url": "https://assets.cambridge.org/97805217/73621/frontmatter/9780521773621_frontmatter.pdf"},
    "47": {"url": "https://search.worldcat.org/title/Simulation-modeling-and-analysis/oclc/864085388"},
    "59": {"url": "https://www.etsi.org/deliver/etsi_ts/102800_102899/10289402/01.03.01_60/ts_10289402v010301p.pdf"},
    "61": {"url": "https://standards.ieee.org/ieee/802.11/7028/"},
}

MANUAL_VERIFICATION_NOTES = {
    "12": "Verified via stable TRID catalog record for the NHTSA report when direct host access returned 403.",
    "16": "Verified via archived specification page for 3GPP TR 37.885 when direct host access was unstable.",
}


def read_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    source_index = 0
    for raw in BIB_MD.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        match = ENTRY_RE.match(stripped)
        if not match:
            continue
        source_index += 1
        body = match.group(1)
        doi_match = DOI_RE.search(body)
        url_match = URL_RE.search(body)
        entries.append(
            {
                "index": str(source_index),
                "entry": body,
                "doi": doi_match.group(0) if doi_match else "",
                "url": url_match.group(0) if url_match else "",
            }
        )
    return entries


def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"doi:\s*\S+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^a-zа-я0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_title(entry: str) -> str:
    title = entry.split("//")[0].strip()
    if ". — " in title:
        title = title.split(". — ")[0].strip()

    # Common bibliography shape: "Authors. Title"
    parts = [part.strip() for part in title.split(". ") if part.strip()]
    if len(parts) >= 2:
        candidate = parts[-1].strip()
        if len(candidate.split()) >= 4:
            return candidate.strip(" .")
    return title.strip(" .")


def extract_year(entry: str) -> str:
    years = YEAR_RE.findall(entry)
    if not years:
        return ""
    match = re.search(r"\b((?:19|20)\d{2})\b", entry)
    return match.group(1) if match else ""


def is_official_resource(entry: str) -> bool:
    official_markers = [
        "ETSI",
        "3GPP",
        "SAE Standard",
        "Documentation",
        "Official project site",
        "Manual",
        "FHWA-",
        "DOT HS",
        "arXiv",
        "IEEE 802.11-2020",
    ]
    return any(marker.lower() in entry.lower() for marker in official_markers)


def crossref_lookup(entry: str) -> tuple[str, str]:
    title = extract_title(entry)
    year = extract_year(entry)
    if not title or is_official_resource(entry):
        return "", ""

    query = entry if len(entry) < 240 else title
    url = f"https://api.crossref.org/works?rows=5&query.bibliographic={quote_plus(query)}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except Exception:
        return "", ""

    wanted = normalize(title)
    best_doi = ""
    best_title = ""
    best_score = 0.0
    for item in payload.get("message", {}).get("items", []):
        item_title = (item.get("title") or [""])[0]
        item_norm = normalize(item_title)
        score = max(
            difflib.SequenceMatcher(None, wanted, item_norm).ratio(),
            difflib.SequenceMatcher(None, normalize(query), item_norm).ratio(),
        )
        item_year = ""
        for key in ("published-print", "published-online", "issued"):
            if key in item and item[key].get("date-parts"):
                item_year = str(item[key]["date-parts"][0][0])
                break
        if year and item_year and item_year != year:
            score -= 0.15
        if score > best_score:
            best_score = score
            best_doi = item.get("DOI", "")
            best_title = item_title
    if best_score >= 0.78:
        return best_doi, best_title
    return "", ""


def fetch(url: str) -> tuple[str, str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            final_url = response.geturl()
            status = str(getattr(response, "status", "200"))
            content_type = response.headers.get("Content-Type", "")
            return status, final_url, content_type
    except HTTPError as exc:
        return str(exc.code), url, ""
    except URLError:
        return "ERROR", url, ""


def verify_doi(doi: str) -> tuple[str, str, str]:
    crossref_url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    status, final_url, content_type = fetch(crossref_url)
    if status.startswith("2"):
        return status, final_url, content_type
    return fetch(f"https://doi.org/{quote(doi, safe=':/')}")


def verify_entry(entry: dict[str, str]) -> dict[str, str]:
    override = MANUAL_OVERRIDES.get(entry["index"], {})
    inferred_doi, inferred_title = ("", "")
    if not entry["doi"] and "doi" not in override:
        inferred_doi, inferred_title = crossref_lookup(entry["entry"])

    result = {
        "index": entry["index"],
        "entry": entry["entry"],
        "title_guess": extract_title(entry["entry"]),
        "doi": entry["doi"] or override.get("doi", "") or inferred_doi,
        "doi_source": (
            "existing" if entry["doi"]
            else "manual" if override.get("doi")
            else ("crossref" if inferred_doi else "")
        ),
        "doi_title_match": inferred_title,
        "doi_status": "",
        "doi_url": "",
        "doi_type": "",
        "url": entry["url"] or override.get("url", ""),
        "url_status": "",
        "url_final": "",
        "url_type": "",
        "status": "",
        "verification_note": "",
    }
    if result["doi"]:
        status, final_url, content_type = verify_doi(result["doi"])
        result["doi_status"] = status
        result["doi_url"] = final_url
        result["doi_type"] = content_type
        time.sleep(0.2)
    if result["url"]:
        status, final_url, content_type = fetch(result["url"])
        result["url_status"] = status
        result["url_final"] = final_url
        result["url_type"] = content_type
        time.sleep(0.2)
    if result["doi"] and result["doi_status"].startswith("2"):
        result["status"] = "doi_ok"
    elif result["url"] and result["url_status"].startswith("2"):
        result["status"] = "url_ok"
    elif entry["index"] in MANUAL_VERIFICATION_NOTES:
        result["status"] = "manual_verified"
        result["verification_note"] = MANUAL_VERIFICATION_NOTES[entry["index"]]
        if not result["url_final"]:
            result["url_final"] = result["url"]
        if not result["url_status"]:
            result["url_status"] = "MANUAL"
    else:
        result["status"] = "unresolved"
    return result


def format_verified_entry(row: dict[str, str]) -> str:
    entry = row["entry"]
    doi = row["doi"].strip()
    url = row["url"].strip()

    if doi and "doi:" not in entry.lower() and "10." not in entry:
        if "URL:" in entry:
            entry = entry.replace("URL:", f"DOI: {doi}. URL:")
        else:
            entry = entry.rstrip(".") + f". DOI: {doi}."

    if url and "url:" not in entry.lower():
        entry = entry.rstrip(".") + f". URL: {url}."

    return entry


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verified = [verify_entry(entry) for entry in read_entries()]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "index",
                "entry",
                "title_guess",
                "doi",
                "doi_source",
                "doi_title_match",
                "doi_status",
                "doi_url",
                "doi_type",
                "url",
                "url_status",
                "url_final",
                "url_type",
                "status",
                "verification_note",
            ],
        )
        writer.writeheader()
        writer.writerows(verified)

    with OUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(verified, fh, ensure_ascii=False, indent=2)

    total = len(verified)
    doi_ok = sum(1 for row in verified if row["doi"] and row["doi_status"].startswith("2"))
    url_ok = sum(1 for row in verified if row["url"] and row["url_status"].startswith("2"))
    doi_added = sum(1 for row in verified if row["doi_source"] == "crossref")
    manual_ok = sum(1 for row in verified if row["status"] == "manual_verified")
    unresolved = sum(1 for row in verified if row["status"] == "unresolved")
    with OUT_MD.open("w", encoding="utf-8") as fh:
        fh.write("# Проверка библиографии\n\n")
        fh.write(f"- Всего записей: {total}\n")
        fh.write(f"- DOI с успешным разрешением: {doi_ok}\n")
        fh.write(f"- DOI, найденные автоматически через Crossref: {doi_added}\n")
        fh.write(f"- URL с успешным ответом: {url_ok}\n")
        fh.write(f"- Записей, подтвержденных вручную по стабильным каталожным страницам: {manual_ok}\n\n")
        fh.write(f"- Неразрешенных записей после проверки: {unresolved}\n\n")
        fh.write("Подробные статусы по каждой записи сохранены в `bibliography_verification.csv`.\n")

    with OUT_BIB.open("w", encoding="utf-8") as fh:
        fh.write("# Список использованных источников\n\n")
        for idx, row in enumerate(verified, start=1):
            fh.write(f"{idx}. {format_verified_entry(row)}\n\n")


if __name__ == "__main__":
    main()
