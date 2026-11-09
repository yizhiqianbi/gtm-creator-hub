# Daily refresh 2026-11-09

- Creators: **31133 → 31417** (net **+284**)
  - Platforms: tiktok 12205 · instagram 6442 · bilibili 5809 · douyin 4463 · xiaohongshu 1466 · x 832 · wechat_store 200
- Channels: **726 → 759** (net **+33**)
- Brand content sources: **355 → 390** (net **+35**)

## Sources
- bilibili_daily_api: 382
- feedspot_tiktok_vegan: 114
- feedspot_tiktok_health_and_fitness: 86
- feedspot_tiktok_agriculture: 82
- feedspot_tiktok_technology: 81
- feedspot_tiktok_uk_dog: 65
- feedspot_tiktok_uk_beauty: 58
- x_mcp_public: 55
- feedspot_tiktok_craft_beer: 46
- feedspot_tiktok_uk_construction: 46
- brand_curated_daily: 35
- channels_curated_daily: 33
- feedspot_tiktok_plumber: 29
- feedspot_tiktok_roofing: 29
- feedspot_tiktok_mens_grooming: 28

## Blockers
- Feedspot soft-empty/404 (122 pages); only large dumps parsed
- Apify: skipped (quota unused; free Feedspot+Bili+X lists yielded net-new creators)
- Instagram Feedspot pages 403/anti-bot (tried wine/cleaning/organization/smart_home/coffee)
- Many Feedspot niche URLs 404; 11 TikTok niches yielded large dumps (vegan/agriculture/health_and_fitness/technology/uk_dog/craft_beer/uk_beauty/uk_construction/roofing/plumber/mens_grooming)
- AfterShip: skipped (scale6b/Nov-6 already ingested the standard TTS category slugs; no unused categories remain)
- Douyin/XHS/WeChat: no new free public list dumps today (prior CN weekly already absorbed)

## Notes
- New Feedspot TikTok niches (vegan/agriculture/health_and_fitness/technology/uk_dog/craft_beer/uk_beauty/uk_construction/roofing/plumber/mens_grooming) + Bilibili daily API + X public handles (HVAC / wine cellar / pet / DeLonghi).
- AfterShip skipped (no unused TTS category slugs remaining after Nov-6).
- Channel expansion: IE/BE/AT/CH/IT/ES/SE/DK/KR/TW/PH/ID/VN/IN/ZA/MX/AE/PT/PL/FI/NO dealers & wholesalers for portable AC / HVAC / wine coolers / heaters / pet.
- Free public lists preferred; Apify paid actors skipped.
- Rules: followers_num ≥ 1000; unknown dropped; dedupe platform+handle.
- merchants.json untouched (separate routine).
