import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _normalize_row(row):
    if is_dataclass(row):
        return asdict(row)
    return dict(row)


def write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_normalize_row(r) for r in rows]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {key: row.get(key) for key in fieldnames}
            writer.writerow(out)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\n", "\\n")
    if any(ch in text for ch in [":", "#", "[", "]", "{", "}"]):
        return f'"{text}"'
    return text


def _dump_yaml(obj, indent=0):
    pad = " " * indent
    lines = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(_dump_yaml(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {_yaml_scalar(value)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(_dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
    else:
        lines.append(f"{pad}{_yaml_scalar(obj)}")

    return lines


def write_yaml(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(_dump_yaml(payload)) + "\n"
    with path.open("w", encoding="utf-8") as f:
        f.write(text)
