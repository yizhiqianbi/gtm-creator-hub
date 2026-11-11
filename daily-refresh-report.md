# Daily refresh 2026-11-11

- Creators: **31593 → 31981** (net **+388**)
  - Platforms: tiktok 12395 · instagram 6442 · bilibili 6074 · douyin 4463 · xiaohongshu 1466 · x 941 · wechat_store 200
- Channels: **795 → 823** (net **+28**)
- Brand content sources: **430 → 458** (net **+28**)

## Sources
- bilibili_daily_api: 152
- feedspot_tiktok_stem: 133
- x_mcp_public: 77
- feedspot_tiktok_cigar: 73
- feedspot_tiktok_cybersecurity: 71
- feedspot_tiktok_homeschool: 63
- feedspot_tiktok_scuba: 62
- feedspot_tiktok_ai: 61
- feedspot_tiktok_dnd: 60
- feedspot_tiktok_keto: 56
- feedspot_tiktok_classical_music: 54
- feedspot_tiktok_anime: 50
- feedspot_tiktok_chess: 42
- feedspot_tiktok_beard: 30
- channels_curated_daily: 28
- brand_curated_daily: 28
- feedspot_tiktok_opera: 27
- feedspot_tiktok_pizza: 26
- feedspot_tiktok_audiophile: 16
- feedspot_tiktok_jazz: 11
- feedspot_tiktok_electric_vehicle: 10

## Blockers
- Feedspot soft-empty/404 (261 pages); only large dumps parsed
- Apify: skipped (quota unused; free Feedspot+Bili+X lists yielded net-new creators)
- Instagram Feedspot: most new niche URLs 404 or anti-bot; TikTok dumps used instead
- Many Feedspot niche URLs 404; large TikTok dumps parsed where pages existed
- AfterShip: skipped (scale6b/Nov-6 already ingested the standard TTS category slugs; no unused categories remain)
- Douyin/XHS/WeChat: no new free public list dumps today (prior CN weekly already absorbed)
- Bilibili ranking/v2 returned risk-control code -352; used popular p1-12, precious, and rotating newlist rids

## Notes
- New Feedspot TikTok niches + Bilibili daily API (popular p1-12, precious, rotating newlist rids) + X public handles (HVAC / wine / pet / home appliance).
- AfterShip skipped (no unused TTS category slugs remaining after Nov-6).
- Channel expansion: public dealers in AE/SA/KW/EG/NG/ZA/TN/HR/SI/RS/SG/PH/IN/HK/MX/NZ/PT for portable AC / HVAC / heaters / pet.
- Free public lists preferred; Apify paid actors skipped.
- Rules: followers_num ≥ 1000; unknown dropped; dedupe platform+handle.
- merchants.json untouched (separate routine).
