# Hymn bulk upload — JSON format

Bulk upload in Django admin (**Denomination Hymns → Bulk upload (JSON)**) accepts JSON only. Plain text (e.g. `NCH 1` with numbered verses) is auto-converted on import if it is not valid JSON.

## Single hymn (NCH 1)

```json
{
  "number": 1,
  "prefix": "NCH",
  "title": "Behold! Behold! He cometh",
  "language": "English",
  "verses": [
    {
      "verse_number": 1,
      "text": "Behold! Behold! He cometh,\nWho doth salvation bring;\nLift up your heads rejoicing,\nAnd welcome Zion's King;\nWith hymns of joy we praise the Lord.\nHosanna to th'Incarnate Word."
    },
    {
      "verse_number": 2,
      "text": "Hosanna to the Saviour,\nWho came on Christmas morn;\nAnd, of a lowly Virgin,\nWas in a stable born;\nEmmanuel! Dear Jesus, come\nWithin thy children make thy home."
    },
    {
      "verse_number": 3,
      "text": "Yea, come in love and meekness,\nOur Saviour now to be;\nCome to be formed in us,\nAnd make us like to thee,\nBefore the Day of Wrath draw near,\nWhen as our Judge thou shalt appear."
    },
    {
      "verse_number": 4,
      "text": "Soon shalt thou sit in glory\nUpon the great White Throne,\nAnd-punish all the wicked,\nAnd recompense thine own;\nWhen ev'ry word and deed and thought\nTo righteous judgement shall be brought."
    },
    {
      "verse_number": 5,
      "text": "Here, good and bad are mingled,\nBut on that Judgement Day\nThe angels shall divide them,\nAnd take the bad away\nGrant, Lord, that we be faithful found\nWhen the last trumpet-call shall sound."
    }
  ]
}
```

## Multiple hymns

**Array:**

```json
[
  { "number": 1, "title": "…", "verses": ["…", "…"] },
  { "number": 2, "title": "…", "verses": ["…"] }
]
```

**Or wrapped:**

```json
{
  "hymns": [
    { "number": 1, "title": "…", "verses": ["…"] }
  ]
}
```

## Verse formats

**Detailed (recommended):**

```json
{ "verse_number": 1, "text": "Line one\nLine two", "is_chorus": false }
```

**Simple strings** (auto-numbered 1, 2, 3…):

```json
"verses": [
  "First verse lines…",
  "Second verse lines…"
]
```

**Chorus:**

```json
{ "verse_number": 1, "text": "Amazing grace…", "is_chorus": true }
```

## Fields

| Field | Required | Notes |
|--------|----------|--------|
| `title` | Yes* | *Omitted → first line of verse 1 |
| `verses` | Yes | At least one verse |
| `number` | No | Hymn number in denomination; auto-increment if omitted |
| `prefix` | No | e.g. `NCH` (reference only, not stored in DB) |
| `language` | No | Default `English` |

## Plain text (legacy)

Still supported on import (not as `.docx`/`.txt` files):

```
NCH 1

1. Behold! Behold! He cometh,
Who doth salvation bring;

2. Hosanna to the Saviour,
…
```

## Admin steps

1. **Denomination Hymns** → **Bulk upload (JSON)**
2. Select denomination (and **period** for Catholic)
3. Paste JSON or plain text
4. **Import hymns**

Optional: category, author, premium flag, starting number.
