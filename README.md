# GTM Creator Hub

Internal shortlist of TikTok creators for GTM outreach, published as GitHub Pages. Supports **multi-tag** filtering (product, format, audience, geo, commerce).

**Dataset:** 9782 unique creators (multi-tag).

## Live site

https://yizhiqianbi.github.io/gtm-creator-hub/

## Update data

Replace `data/creators.json` (and optionally `data/creators.csv`) then commit to `main`.

### Schema

JSON array of objects:

| field | type | notes |
|---|---|---|
| `handle` | string | TikTok username |
| `display_name` | string\|null | |
| `profile_url` | string | `https://www.tiktok.com/@handle` |
| `followers` | string\|null | display band e.g. `255.4K` |
| `followers_num` | number\|null | numeric for filters; null if unknown |
| `country_or_language` | string\|null | |
| `bio_snippet` | string\|null | |
| `email_or_contact` | string\|null | only if publicly known — never invent |
| `source_url` | string | list/page provenance |
| `notes` | string\|null | |
| `primary_niche` | string | one best product/category tag |
| `tags` | string[] | all applicable snake_case tags |

CSV uses the same columns; `tags` is pipe-separated (`a|b|c`).

### UI filters

- Free-text search across handle, name, bio, notes, tags
- Multi-select tag chips (AND: creator must have every selected tag)
- Optional `primary_niche` dropdown and follower-band filter

## Pages

Settings → Pages → Deploy from branch `main` / root `/`.
