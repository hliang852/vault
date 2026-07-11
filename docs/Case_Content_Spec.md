# Case Content Spec — plugging summaries & links into case dossiers

**Status: spec only — no content exists yet, and none is auto-generated.** Executive summaries and source links are being produced separately from the site build (maintainer decision, 2026-07-07). This document defines the contract so that when that content is ready, it mounts into the case dossier pages (Part 3) without touching site code.

## Where content lives

One file per case:

```
content/cases/JP-001.md
content/cases/JP-002.md
...
```

- Filename must be `<deal_id>.md`, matching a `deal_id` in `data/Japan.csv` exactly.
- A case with no file is normal — the dossier page renders designed "pending" placeholders (see *Rendering rules* below). Files are added incrementally as dossiers are researched; there is no requirement to cover all 62 before shipping any.

## File format

Markdown with YAML frontmatter:

```markdown
---
deal_id: JP-026
status: draft            # draft | verified
last_verified: 2026-07-15
links:
  - label: "Tender offer registration statement (公開買付届出書)"
    url: "https://disclosure2.edinet-fsa.go.jp/..."
    source: filing        # filing | exchange | news | company | regulator | other
    date: 2024-08-09      # date of the document itself
    language: ja
  - label: "KKR press release announcing the tender offer"
    url: "https://..."
    source: company
    date: 2024-08-08
    language: en
testimonies:              # scraped context/commentary quotes — shown two at a time at the foot of the dossier
  - quote: "..."          # verbatim excerpt
    source: "Nikkei"      # publication / speaker
    date: 2024-09-02
    url: "https://..."    # optional, back to the source
---

## Executive summary

Two to five paragraphs of written narrative...
```

### Frontmatter fields

| Field | Required | Rules |
|---|---|---|
| `deal_id` | yes | Must equal the filename stem and exist in `data/Japan.csv`. Build fails loudly on mismatch — never silently skips. |
| `status` | yes | `draft` renders with a visible "draft — not yet verified" tag on the page; `verified` renders clean. There is no third state. |
| `last_verified` | when `status: verified` | ISO date of the most recent verification pass against primary sources. |
| `links` | no | May be empty/omitted while only the summary exists — the links slot then stays in its "pending" state. |
| `links[].label` | yes | Human-readable, specific ("FY2024 tender offer statement"), not "link" or a bare domain. |
| `links[].url` | yes | Absolute `https://` URL. |
| `links[].source` | yes | One of `filing` (EDINET etc.), `exchange` (TDnet/TSE), `news`, `company` (IR/press releases), `regulator` (METI/JFTC/CFIUS materials), `other`. Drives the grouping/icon on the page. |
| `links[].date` | recommended | Date of the underlying document, not of link collection. |
| `links[].language` | recommended | `ja` / `en` — shown as a tag so readers know before clicking. |
| `testimonies` | no | Scraped context quotes/press excerpts. Rendered as the dossier's final section, two cards at a time as the reader scrolls. Each needs `quote` + `source`; `date`/`url` optional. Empty/omitted → the testimonies slot stays in its "pending" state, same as the others. |

**Filenames use `deal_id`, but the UI never shows it.** Content files are keyed by `deal_id` (`JP-026.md`) because that is the dataset's stable primary key, but every user-facing surface displays the case by **name + ticker** in the format `9749 JP Equity` (from `target_ticker_code`); the `JP-###` id is internal only. Foreign/unlisted targets with no JP ticker fall back to name alone.

### Body

Everything after the frontmatter is the executive summary, standard Markdown. Conventions:

- Open with `## Executive summary`. Optional further sections: `## Timeline`, `## Why it matters`, `## Aftermath`.
- **No new unverified facts.** Every claim must be traceable to (a) fields already in `data/Japan_Master.csv`, or (b) a source listed in `links` — this is the same discipline as the rest of the project (see `Claude.md`), and the advisor-pilot experience (a summarized web result reported Toshiba's advisors backwards; only reading the primary filing caught it) is the standing reason summaries should not be written from search-result summaries.
- Numbers flagged `TBV`/`_is_estimate` in the dataset must stay hedged in prose ("approximately", "reportedly") unless the verification pass resolved them — in which case update the dataset too, per `Claude.md`'s audit-trail rule.

## Rendering rules (for the Part 3 build)

1. At build time, the site generator scans `content/cases/*.md`, validates per the table above, converts the body to HTML, and embeds the result into the viewer data as `node.content = { summary_html, links[], status, last_verified }`.
2. **Missing file** → both dossier slots render the designed placeholder state (dashed panel, "pending" tag) exactly as shown in `viewer/design/mockup_japanese_minimal.html`. Placeholders are honest: they say the dossier hasn't been written, never "coming soon" implying imminence.
3. **Summary present, no links** (or vice versa) → render the slot that exists, placeholder for the other. The two slots are independent.
4. `status: draft` → summary renders with a visible draft tag; links render normally (a link is either verified enough to list or shouldn't be in the file).
5. The generator must fail the build (not warn) on: filename/`deal_id` mismatch, unknown `deal_id`, malformed frontmatter, non-https URL, or unknown `source` value. Content errors should be impossible to ship silently.

## Explicitly out of scope for this spec

- Who writes the summaries and how links are researched/verified — tracked separately (see `docs/To-do.md`).
- Auto-generation of any summary text from dataset fields — ruled out; the slot stays empty until a human-produced file exists.
- Translation/localization of summaries.
