# GTM Creator Hub

Internal shortlist of creators for GTM outreach (GitHub Pages). **Multi-platform** (TikTok, Instagram, X) with **multi-tag** filtering (product, format, audience, geo, commerce).

**Dataset:** 13814 unique creators — TikTok 8946 · Instagram 4306 · X 562 (all `followers_num >= 1000`).

## Live site

https://yizhiqianbi.github.io/gtm-creator-hub/

## Update data

Replace `data/creators.json` (and optionally `data/creators.csv`) then commit to `main`.

### Schema

JSON array of objects:

| field | type | notes |
|---|---|---|
| `platform` | string | `tiktok` \| `instagram` \| `x` |
| `handle` | string | username without `@` |
| `display_name` | string\|null | |
| `profile_url` | string | platform-correct profile link |
| `followers` | string\|null | display band e.g. `255.4K` |
| `followers_num` | number | numeric; **required ≥ 1000** |
| `country_or_language` | string\|null | |
| `bio_snippet` | string\|null | |
| `email_or_contact` | string\|null | only if publicly known — never invent |
| `source_url` | string | list/page provenance |
| `notes` | string\|null | |
| `primary_niche` | string | one best product/category tag |
| `tags` | string[] | all applicable snake_case tags |

Profile URL rules:

- TikTok: `https://www.tiktok.com/@handle`
- Instagram: `https://www.instagram.com/handle/`
- X: `https://x.com/handle`

CSV uses the same columns; `tags` is pipe-separated (`a|b|c`). Same person on two platforms = two rows.

### UI filters

- Platform chips (OR within platforms; empty = all)
- Free-text search across handle, name, bio, notes, tags, platform
- Multi-select tag chips (AND: creator must have every selected tag)
- Optional `primary_niche` dropdown and follower-band filter
- Platform badge column

## Sources

Public web lists only (Feedspot Instagram lists, Influencers.club Twitter niche lists, Wikipedia most-followed X, prior TikTok Feedspot/EcomRide/blog lists). No invented follower counts.

## Pages

Settings → Pages → Deploy from branch `main` / root `/`.
