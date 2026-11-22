# Daily refresh 2026-11-22

Attachment-only validation of the 2026-11-22 public supplement. No new collection and no paid calls. `origin/main` was still `276ac1bf08976e09dc88100f751141eb279be1ed` (2026-11-16); nothing later was overwritten. No 2026-11-17 through 2026-11-20 history was created.

- Creators: **34159 → 34620** (net **+461**)
  - Platforms: tiktok 13720 · bilibili 7250 · instagram 6442 · douyin 4463 · xiaohongshu 1466 · x 1079 · wechat_store 200
  - bilibili 6803 → 7250 (+447); x 1065 → 1079 (+14); other platforms unchanged
- Channels: **957 → 969** (net **+12**)
- Brand content sources: **592 → 604** (net **+12**)
- Merchants: **7961 → 8422** (net **+461**). The attachment had 8431; 9 Canton Fair category headings were excluded.

## Sources
- bilibili_daily_api: 447 (`https://api.bilibili.com/x/web-interface/popular`, fans via the public stat fields already on the rows)
- x_mcp_public: 14 (public `https://x.com/{handle}` profiles)
- channels_curated_daily: 12 (official retailer sites)
- brand_curated_daily: 12 (same sites, recorded as `asset_type: site`)

## Checks
- JSON and CSV row counts and fields match. Creator `null` emails and bios still serialize as empty CSV cells, same as the 2026-11-16 files.
- Primary keys unique: creator `platform+handle`, channel `name`, brand `url`, merchant `name+website`.
- Every 2026-11-16 row is still present. No existing creator, channel, or brand row was edited.
- New creators: `followers_num >= 1000`, follower label not unknown, `profile_url` present, at least two tags, `source_url` present.

## Exclusions and corrections
- Excluded 9 Canton Fair category titles that the attachment stored as companies: Agricultural Machinery; General Machinery and Mechanical Basic Parts; Home Textiles; Medicines, Health Products and Medical Devices; Power Machinery and Electric Power; Processing Machinery Equipment; Safety Equipment; Toiletries; Weaving, Rattan and Iron Products.
- Removed guessed `heater` / `hvac` labels from 106 real exhibitor names that came from the power-machinery and general-machinery lists. Notes still cite those category pages.
- Removed guessed `heater` or `portable_ac` labels from Do it Center Panama, Novey, Panafoto, Plaza Lama, and Singer Sri Lanka. Their notes only support a retailer / home-appliance site.
- New retailer homepages are `asset_type: site`, not brochures.
- 33 Wikipedia companies with Wikidata official websites were kept. False `region:se` on unresolved "Overseas" rows, `region:de` on the two Denmark rows, and other unauditable extra geo or niche tags were removed. The note no longer claims HVAC or pet-food category lists.

## Anomalies kept visible
- `RiojaWine` has `country_or_language: us` and a `us` tag. The profile URL is the public Rioja Wine account. The row meets the follower, profile, and tag rules, so it was not dropped.
- All 447 new Bilibili rows cite the popular API URL. The note also says 分区榜; no separate ranking URL was in the attachment.
- `Anglepoise lamp` keeps the Wikipedia article title. `Lamps Plus` and `Rejuvenation` are real sites kept under the existing Wikipedia-plus-official-website rule; `manufacturer` / `oem` is that batch's default label, not a separate factory audit.
- Brand-only exhibitor tokens `CERAGEM` and `EVERMAPLE` stay. They are not the category title.
- Baseline already contains Canton headings (including `Industrial Automation and Intelligent Manufacturing`). They were not deleted. The new self-match tag on that heading was reverted.

## Blockers
- This commit does not start a crawl, Apify run, or paid enrichment.
- Attachment merchant file was not ingested at 8431, because 9 of those rows are category headings.
