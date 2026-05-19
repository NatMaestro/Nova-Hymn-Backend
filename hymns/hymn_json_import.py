"""
Parse and import denomination hymns from JSON (or plain text converted to JSON).

Canonical JSON shape (single hymn or array of hymns):

{
  "number": 1,
  "prefix": "NCH",
  "title": "Behold! Behold! He cometh",
  "language": "English",
  "verses": [
    {
      "verse_number": 1,
      "text": "Behold! Behold! He cometh,\\nWho doth salvation bring;",
      "is_chorus": false
    }
  ]
}

Verses may also be plain strings (auto-numbered from 1).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction

from .models import Author, Category, Denomination, DenominationHymn, Hymn, Verse


class HymnJsonImportError(Exception):
    pass


@dataclass
class ImportResult:
    created_count: int = 0
    updated_count: int = 0
    error_count: int = 0
    messages: list[tuple[str, str]] = field(default_factory=list)  # (level, text)

    def add(self, level: str, text: str) -> None:
        self.messages.append((level, text))


def parse_json_payload(raw: str) -> list[dict[str, Any]]:
    """Parse JSON string; if not JSON, treat as plain hymn text."""
    raw = (raw or "").strip()
    if not raw:
        raise HymnJsonImportError("No hymn data provided")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return parse_plaintext_to_hymns(raw)

    return normalize_hymn_list(data)


def normalize_hymn_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "hymns" in data:
        data = data["hymns"]
    if isinstance(data, dict):
        return [normalize_hymn_dict(data)]
    if isinstance(data, list):
        if not data:
            raise HymnJsonImportError("Hymns array is empty")
        return [normalize_hymn_dict(item) for item in data]
    raise HymnJsonImportError("JSON must be a hymn object, { \"hymns\": [...] }, or an array")


def normalize_hymn_dict(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise HymnJsonImportError("Each hymn must be a JSON object")
    verses = normalize_verses(item.get("verses") or [])
    title = (item.get("title") or "").strip()
    if not title:
        title = derive_title_from_verses(verses)
    if not title:
        raise HymnJsonImportError("Each hymn needs a title or at least one verse")
    if not verses:
        raise HymnJsonImportError(f'Hymn "{title}" has no verses')

    number = item.get("number")
    if number is not None:
        try:
            number = int(number)
        except (TypeError, ValueError) as e:
            raise HymnJsonImportError(f'Invalid number for "{title}"') from e

    prefix = item.get("prefix")
    if prefix:
        prefix = str(prefix).strip().upper()

    return {
        "number": number,
        "prefix": prefix,
        "title": title,
        "language": item.get("language") or "English",
        "verses": verses,
    }


def normalize_verses(verses: list[Any]) -> list[dict[str, Any]]:
    if not isinstance(verses, list):
        raise HymnJsonImportError("verses must be an array")
    out: list[dict[str, Any]] = []
    for idx, verse_item in enumerate(verses, start=1):
        if isinstance(verse_item, str):
            text = verse_item.strip()
            if not text:
                continue
            out.append(
                {
                    "verse_number": idx,
                    "text": text,
                    "is_chorus": False,
                    "order": idx,
                }
            )
        elif isinstance(verse_item, dict):
            text = (verse_item.get("text") or "").strip()
            if not text:
                continue
            verse_number = verse_item.get("verse_number", idx)
            try:
                verse_number = int(verse_number)
            except (TypeError, ValueError) as e:
                raise HymnJsonImportError("verse_number must be an integer") from e
            is_chorus = bool(verse_item.get("is_chorus", False))
            order = verse_item.get("order", verse_number + (100 if is_chorus else 0))
            out.append(
                {
                    "verse_number": verse_number,
                    "text": text,
                    "is_chorus": is_chorus,
                    "order": int(order),
                }
            )
        else:
            raise HymnJsonImportError("Each verse must be a string or object")
    return out


def derive_title_from_verses(verses: list[dict[str, Any]]) -> str:
    for v in verses:
        if v.get("is_chorus"):
            continue
        first_line = (v.get("text") or "").split("\n")[0].strip()
        if first_line:
            return first_line[:80] + ("..." if len(first_line) > 80 else "")
    if verses:
        first_line = (verses[0].get("text") or "").split("\n")[0].strip()
        return first_line[:80] + ("..." if len(first_line) > 80 else "")
    return "Untitled Hymn"


def parse_plaintext_to_hymns(content: str) -> list[dict[str, Any]]:
    """
    Convert plain text to hymn dicts.

    Supports:
      NCH 1
      1. First line…
      2. Second verse…
      Chorus: …
      101. Amazing Grace
    """
    lines = content.replace("\r\n", "\n").split("\n")
    all_hymns: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_verse: dict[str, Any] | None = None

    def flush_verse() -> None:
        nonlocal current_verse
        if current and current_verse:
            current["verses"].append(current_verse)
            current_verse = None

    def flush_hymn() -> None:
        nonlocal current
        flush_verse()
        if current and current.get("verses"):
            all_hymns.append(normalize_hymn_dict(current))
        current = None

    for raw_line in lines:
        text = raw_line.strip()
        if not text:
            flush_verse()
            continue

        if re.match(r"^THE\s+NEW\s+CATHOLIC\s+HYMNAL", text, re.IGNORECASE):
            continue

        prefix_m = re.match(r"^([A-Z]{2,})\s+(\d+)$", text)
        if prefix_m:
            flush_hymn()
            current = {
                "number": int(prefix_m.group(2)),
                "prefix": prefix_m.group(1).upper(),
                "title": "",
                "language": "English",
                "verses": [],
            }
            current_verse = None
            continue

        number_only = re.match(r"^(\d+)$", text)
        if number_only and (not current or current.get("verses")):
            flush_hymn()
            current = {
                "number": int(number_only.group(1)),
                "prefix": None,
                "title": "",
                "language": "English",
                "verses": [],
            }
            current_verse = None
            continue

        header_m = re.match(r"^(\d+)\.\s+(.+)$", text)
        if header_m and not current:
            flush_hymn()
            current = {
                "number": int(header_m.group(1)),
                "prefix": None,
                "title": header_m.group(2).strip(),
                "language": "English",
                "verses": [],
            }
            current_verse = None
            continue

        verse_m = re.match(r"^(\d+)\.\s*(.*)$", text)
        chorus_m = re.match(r"^(Chorus|Refrain):?\s*(.*)$", text, re.IGNORECASE)

        if not current:
            current = {
                "number": None,
                "prefix": None,
                "title": "",
                "language": "English",
                "verses": [],
            }

        if verse_m:
            flush_verse()
            vn = int(verse_m.group(1))
            vtext = verse_m.group(2) or ""
            current_verse = {
                "verse_number": vn,
                "text": vtext,
                "is_chorus": False,
                "order": vn,
            }
            if not current.get("title"):
                first = vtext.split("\n")[0].strip() or vtext
                current["title"] = first[:80] + ("..." if len(first) > 80 else "")
            continue

        if chorus_m:
            flush_verse()
            vtext = chorus_m.group(2) or ""
            vn = (
                current["verses"][-1]["verse_number"]
                if current["verses"]
                else 1
            )
            current["verses"].append(
                {
                    "verse_number": vn,
                    "text": vtext,
                    "is_chorus": True,
                    "order": vn + 100,
                }
            )
            continue

        if current_verse:
            current_verse["text"] = (
                f"{current_verse['text']}\n{text}"
                if current_verse["text"]
                else text
            )
        elif not current.get("title"):
            current["title"] = text

    flush_hymn()

    if not all_hymns:
        raise HymnJsonImportError("Could not parse any hymns from text")
    return all_hymns


def import_hymns_for_denomination(
    *,
    hymns_data: list[dict[str, Any]],
    denomination: Denomination,
    hymn_period: str | None,
    category: Category | None,
    author: Author | None,
    is_premium: bool,
    start_number: int | None,
    message_collector: list[tuple[str, str]] | None = None,
) -> ImportResult:
    """Create or update denomination hymns and verses from normalized hymn dicts."""
    result = ImportResult()

    def emit(level: str, text: str) -> None:
        result.messages.append((level, text))
        if message_collector is not None:
            message_collector.append((level, text))

    if denomination.slug == "catholic" and not hymn_period:
        raise HymnJsonImportError("Catholic hymns require hymn_period (new or old)")
    if denomination.slug != "catholic" and hymn_period:
        raise HymnJsonImportError("hymn_period is only valid for Catholic hymns")

    if start_number is not None:
        current_number = start_number
    else:
        last_dh = (
            DenominationHymn.objects.filter(
                denomination=denomination, hymn_period=hymn_period
            )
            .order_by("-number")
            .first()
        )
        current_number = (last_dh.number + 1) if last_dh else 1

    with transaction.atomic():
        for hymn_data in hymns_data:
            try:
                title = hymn_data["title"]
                verses_data = hymn_data["verses"]
                hymn_number = hymn_data.get("number") or current_number

                existing_dh = DenominationHymn.objects.filter(
                    denomination=denomination,
                    hymn_period=hymn_period,
                    number=hymn_number,
                ).first()
                if existing_dh and existing_dh.hymn.title != title:
                    emit(
                        "warning",
                        f'Number {hymn_number} in use; using {current_number} for "{title}"',
                    )
                    hymn_number = current_number

                hymn, _ = Hymn.objects.get_or_create(
                    title=title,
                    defaults={
                        "category": category,
                        "author": author,
                        "language": hymn_data.get("language", "English"),
                        "is_premium": is_premium,
                    },
                )

                denomination_hymn, dh_created = DenominationHymn.objects.get_or_create(
                    hymn=hymn,
                    denomination=denomination,
                    hymn_period=hymn_period,
                    defaults={"number": hymn_number},
                )

                if not dh_created and denomination_hymn.number != hymn_number:
                    conflict = DenominationHymn.objects.filter(
                        denomination=denomination,
                        hymn_period=hymn_period,
                        number=hymn_number,
                    ).exclude(id=denomination_hymn.id).exists()
                    if not conflict:
                        denomination_hymn.number = hymn_number
                        denomination_hymn.save(update_fields=["number"])

                verses_added = 0
                verses_updated = 0
                for verse_data in verses_data:
                    verse, verse_created = Verse.objects.get_or_create(
                        denomination_hymn=denomination_hymn,
                        verse_number=verse_data["verse_number"],
                        is_chorus=verse_data.get("is_chorus", False),
                        defaults={
                            "text": verse_data["text"],
                            "order": verse_data.get(
                                "order", verse_data["verse_number"]
                            ),
                        },
                    )
                    if not verse_created:
                        if verse.text != verse_data["text"]:
                            verse.text = verse_data["text"]
                            verse.order = verse_data.get(
                                "order", verse_data["verse_number"]
                            )
                            verse.save()
                            verses_updated += 1
                    else:
                        verses_added += 1

                prefix = hymn_data.get("prefix")
                label = f"{prefix} {hymn_number}" if prefix else f"#{hymn_number}"

                if dh_created:
                    result.created_count += 1
                    emit(
                        "success",
                        f'Created "{title}" ({label}) with {verses_added} verses',
                    )
                    current_number = hymn_number + 1
                else:
                    result.updated_count += 1
                    if verses_added:
                        emit(
                            "info",
                            f'"{title}" ({label}) exists; added {verses_added} verses',
                        )
                    elif verses_updated:
                        emit(
                            "info",
                            f'"{title}" ({label}) exists; updated {verses_updated} verses',
                        )
                    else:
                        emit(
                            "warning",
                            f'"{title}" ({label}) unchanged (all verses present)',
                        )
                    current_number = max(current_number, hymn_number + 1)

            except Exception as e:
                result.error_count += 1
                emit("error", f'Error importing "{hymn_data.get("title", "?")}": {e}')

    return result


def example_hymn_nch_1() -> dict[str, Any]:
    """Reference example matching NCH 1 from the hymnal."""
    return {
        "number": 1,
        "prefix": "NCH",
        "title": "Behold! Behold! He cometh",
        "verses": [
            {
                "verse_number": 1,
                "text": (
                    "Behold! Behold! He cometh,\n"
                    "Who doth salvation bring;\n"
                    "Lift up your heads rejoicing,\n"
                    "And welcome Zion's King;\n"
                    "With hymns of joy we praise the Lord.\n"
                    "Hosanna to th'Incarnate Word."
                ),
            },
            {
                "verse_number": 2,
                "text": (
                    "Hosanna to the Saviour,\n"
                    "Who came on Christmas morn;\n"
                    "And, of a lowly Virgin,\n"
                    "Was in a stable born;\n"
                    "Emmanuel! Dear Jesus, come\n"
                    "Within thy children make thy home."
                ),
            },
            {
                "verse_number": 3,
                "text": (
                    "Yea, come in love and meekness,\n"
                    "Our Saviour now to be;\n"
                    "Come to be formed in us,\n"
                    "And make us like to thee,\n"
                    "Before the Day of Wrath draw near,\n"
                    "When as our Judge thou shalt appear."
                ),
            },
            {
                "verse_number": 4,
                "text": (
                    "Soon shalt thou sit in glory\n"
                    "Upon the great White Throne,\n"
                    "And-punish all the wicked,\n"
                    "And recompense thine own;\n"
                    "When ev'ry word and deed and thought\n"
                    "To righteous judgement shall be brought."
                ),
            },
            {
                "verse_number": 5,
                "text": (
                    "Here, good and bad are mingled,\n"
                    "But on that Judgement Day\n"
                    "The angels shall divide them,\n"
                    "And take the bad away\n"
                    "Grant, Lord, that we be faithful found\n"
                    "When the last trumpet-call shall sound."
                ),
            },
        ],
    }
