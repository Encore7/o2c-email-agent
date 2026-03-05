import re
from datetime import datetime


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.strip()
        if not key:
            continue
        low = key.lower()
        if low in seen:
            continue
        seen.add(low)
        result.append(key)
    return result


def to_float_amounts(values: list[str]) -> list[float]:
    result: list[float] = []
    seen: set[float] = set()
    for raw in values:
        cleaned = re.sub(r"[^0-9.\-]", "", str(raw))
        if not cleaned:
            continue
        try:
            val = round(float(cleaned), 2)
        except ValueError:
            continue
        if val in seen:
            continue
        seen.add(val)
        result.append(val)
    return result


def to_iso_dates(values: list[str]) -> list[str]:
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d/%m/%y",
        "%m/%d/%y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%B %d %Y",
    ]
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        val = str(raw).strip()
        if not val:
            continue
        parsed: datetime | None = None
        for fmt in formats:
            try:
                parsed = datetime.strptime(val, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", val):
                iso = val
            else:
                continue
        else:
            iso = parsed.date().isoformat()
        if iso in seen:
            continue
        seen.add(iso)
        result.append(iso)
    return result


def limit_detail(text: str, max_len: int = 140) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 3].rstrip() + "..."


def derive_detail_from_text(subject: str, body: str) -> str:
    snippet = body.strip().splitlines()[0] if body.strip() else subject.strip()
    return snippet or subject.strip() or "Customer sent AR email requiring review."

