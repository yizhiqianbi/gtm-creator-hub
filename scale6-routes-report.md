# Scale 6 — Three GTM routes crawl (2026-11-01)

## A) 第三方内容合作 (creators)
- Before (pre-scale6): **28,390** → After: **30,213** (net **+1,823**)
- Tagged `route:third_party_content` + `sample_ready`: **23,601**
- Platforms: TikTok 12120 · Instagram 6442 · Bilibili 5109 · Douyin 4333 · 小红书 1291 · X 718 · 微信小店 200
- Sources: Feedspot (scale6+legacy), EcomRide TTS Sep2026, AfterShip TTS categories, Crowdcreate Amazon finds
- Filters unchanged: ≥1000 followers, known counts, platform+handle dedupe

## B) 渠道合作 (channels)
- Records: **589** → `data/channels.json` + `data/channels.csv`
- Types: distributor 257 · dealer 191 · mod_shop 56 · brand 41 · wholesaler 38 · importer 4 · channel 2
- Niches: portable_ac / hvac / wine_cooler / space_heater / pet_products
- Sources: maps leads CSVs, PIDA, Breezaire, Transtherm, La Fraîcheur, ThomasNet, WLW, Wine Guardian, curated public directories & associations

## C) 公司品牌与专业内容 (brand content sources)
- Records: **225** → `data/brand_content_sources.json` + csv
- asset_types: site 90 · brochure 56 · faq 43 · case 36
- Links + short notes only (no copyrighted full-text dumps)

## Blockers
- Apify monthly hard limit — skipped paid actors
- Feedspot anti-bot on many niche URLs (curl shells); only large HTML dumps parsed
- AfterShip: display names + follower ranges (midpoint); handles approximated when not handle-like
- Hub UI still creators-first — channels/brand data committed; UI follow-up recommended
