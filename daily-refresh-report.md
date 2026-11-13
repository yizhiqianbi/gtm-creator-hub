# Daily refresh 2026-11-13

- Creators: **33341 → 33538** (net **+197**)
  - Platforms: tiktok 13613 · instagram 6442 · bilibili 6382 · douyin 4463 · xiaohongshu 1466 · x 972 · wechat_store 200
- Channels: **862 → 908** (net **+46**)
- Brand content sources: **497 → 543** (net **+46**)

## Sources
- bilibili_daily_api: 176
- channels_curated_daily: 46
- brand_curated_daily: 46
- x_mcp_public: 21

## Blockers
- Feedspot soft-empty/404 (3057 pages); only large dumps parsed
- Apify: skipped (quota unused; free Bilibili+X lists yielded net-new creators)
- Feedspot: homepage leftover slugs were mostly adult/gambling (skipped); 3057 unused guessed TikTok geo/city/product slugs and Instagram counterparts probed, 0 large dumps (2975 404, 82 403/405)
- AfterShip: skipped (scale6b/Nov-6 already ingested the standard TTS category slugs; no unused categories remain)
- Douyin/XHS/WeChat: no new free public list dumps today (prior CN weekly already absorbed)
- Bilibili: popular p1-12 + ranking/v2 (some rids -400) + working newlist rids 1/3/4/5/11/13/36/129/155/160/167/177/181/188/202/211; 2083 unique mids, 407 not already in hub, 176 with fans>=1000

## Notes
- Bilibili daily API (popular p1-12, precious, ranking/v2, rotating newlist rids) + X public handles (HVAC / wine / pet / home appliance), verified followers >=1000.
- Feedspot: no net-new dumps (homepage professional slugs already ingested; leftover homepage lists were adult/gambling; guessed slugs 404/403).
- AfterShip skipped (no unused TTS category slugs remaining after Nov-6).
- Channel expansion: public dealers/wholesalers in JP/KR/SG/PH, MX/BR, ZA, AE, IT/AT/CH/PT/CZ/RO/HU, and NZ for portable AC / HVAC / heaters / pet / home appliances / wine.
- Free public lists preferred; Apify paid actors skipped.
- Rules: followers_num ≥ 1000; unknown dropped; dedupe platform+handle.
- merchants.json untouched (separate routine).
