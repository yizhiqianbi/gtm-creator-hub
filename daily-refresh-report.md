# Daily refresh 2026-11-10

- Creators: **31417 → 31593** (net **+176**)
  - Platforms: tiktok 12236 · instagram 6442 · bilibili 5922 · douyin 4463 · xiaohongshu 1466 · x 864 · wechat_store 200
- Channels: **759 → 795** (net **+36**)
- Brand content sources: **390 → 430** (net **+40**)

## Sources
- bilibili_daily_api: 113
- feedspot_tiktok_crossfit: 92
- feedspot_tiktok_lego: 76
- feedspot_tiktok_quilting: 52
- brand_curated_daily: 40
- channels_curated_daily: 36
- x_mcp_public: 34

## Blockers
- Feedspot soft-empty/404 (92 pages); only large dumps parsed
- Apify: skipped (quota unused; free Feedspot+Bili+X lists yielded net-new creators)
- Instagram Feedspot pages 403/anti-bot (tried fishing/photography/cycling/pilates/knitting)
- Many Feedspot niche URLs 404; 3 TikTok niches yielded large dumps (crossfit/lego/quilting)
- AfterShip: skipped (scale6b/Nov-6 already ingested the standard TTS category slugs; no unused categories remain)
- Douyin/XHS/WeChat: no new free public list dumps today (prior CN weekly already absorbed)
- Many unused Bilibili newlist rids returned empty archives; supplemented with popular p1-12 plus known-working rids whose daily lists rotate

## Notes
- New Feedspot TikTok niches (crossfit/lego/quilting) + Bilibili daily API (popular p1-12 + rotating newlist rids) + X public handles (HVAC / wine / pet / home appliance).
- AfterShip skipped (no unused TTS category slugs remaining after Nov-6).
- Channel expansion: CL/CO/AR/PE/BR/UY + CZ/HU/RO/GR/BG + EE/LV/LT + extra CA/AU dealers for portable AC / HVAC / wine coolers / heaters / pet.
- Free public lists preferred; Apify paid actors skipped.
- Rules: followers_num ≥ 1000; unknown dropped; dedupe platform+handle.
- merchants.json untouched (separate routine).
