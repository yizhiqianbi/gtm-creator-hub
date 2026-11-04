# Daily refresh 2026-11-04

- Creators: **30735 → 30823** (net **+88**)
  - Platforms: tiktok 12154 · instagram 6442 · bilibili 5349 · douyin 4463 · xiaohongshu 1466 · x 749 · wechat_store 200
- Channels: **626 → 657** (net **+31**)
- Brand content sources: **259 → 290** (net **+31**)

## Sources
- feedspot_tiktok_mom: 155
- feedspot_tiktok_pet: 128
- bilibili_daily_api: 115
- feedspot_tiktok_home_decor: 81
- feedspot_tiktok_gardening: 69
- feedspot_tiktok_whiskey: 51
- feedspot_tiktok_tiny_house: 37
- channels_curated_daily: 31
- brand_curated_daily: 31
- feedspot_tiktok_hvac: 28
- feedspot_tiktok_contractor: 21
- aftership6b_baby-maternity: 20
- aftership6b_beauty: 20
- aftership6b_electronics: 20
- aftership6b_fashion: 20
- aftership6b_food-beverages: 20
- aftership6b_jewelry-accessories: 20
- aftership6b_kitchen-dining: 20
- aftership6b_sports-outdoor: 20
- aftership6b_toys-hobbies: 20
- aftership6b_health: 19
- aftership6b_tools-home-improvement: 19
- x_mcp_public: 16

## Blockers
- Feedspot soft-empty (52 pages); only large dumps parsed
- Apify: skipped (prefer free public lists; Feedspot+AfterShip+Bili+X used)
- Most Instagram Feedspot pages soft-empty / anti-bot (<40KB)
- CN Chanmama/Feigua open pages fetched but not parsed as creator lists (login walls / no public handles)
- CN weekly CSV skipped (already absorbed 2026-11-03)

## Notes
- New Feedspot niches (whiskey/tiny_house/home_decor/mom/gardening/pet/hvac/contractor) + AfterShip TTS categories + Bilibili daily API + X public handles.
- Free public lists preferred; Apify paid actors skipped.
- Rules: followers_num ≥ 1000; unknown dropped; dedupe platform+handle.
- merchants.json untouched (separate routine).
