# Daily refresh 2026-11-16

- Creators: **33538 → 34159** (net **+621**)
  - Platforms: tiktok 13720 · bilibili 6803 · instagram 6442 · douyin 4463 · xiaohongshu 1466 · x 1065 · wechat_store 200
- Channels: **908 → 957** (net **+49**)
- Brand content sources: **543 → 592** (net **+49**)

## Sources
- bilibili_daily_api: 421
- feedspot_tiktok_finance: 154
- feedspot_tiktok_comedy: 147
- feedspot_tiktok_perfume: 141
- feedspot_tiktok_amazon: 137
- feedspot_tiktok_wedding: 131
- feedspot_tiktok_black_female_fitness: 130
- feedspot_tiktok_airbnb: 122
- feedspot_tiktok_music: 119
- feedspot_tiktok_christian: 117
- feedspot_tiktok_book: 109
- feedspot_tiktok_pickleball: 97
- x_mcp_public: 93
- feedspot_tiktok_sexual_health: 89
- feedspot_tiktok_weight_loss: 87
- feedspot_tiktok_sustainability: 84
- feedspot_tiktok_mental_health: 83
- feedspot_tiktok_dance: 82
- feedspot_tiktok_natural_hair: 78
- feedspot_tiktok_australian_fashion: 77
- feedspot_tiktok_golf: 75
- feedspot_tiktok_gaming: 73
- feedspot_tiktok_food: 68
- feedspot_tiktok_cannabis: 66
- feedspot_tiktok_us_food: 65
- feedspot_tiktok_australian_travel: 60
- feedspot_tiktok_uk_food: 60
- feedspot_tiktok_meditation: 54
- channels_curated_daily: 49
- brand_curated_daily: 49
- feedspot_tiktok_tesla: 42
- feedspot_tiktok_bikini: 37
- feedspot_tiktok_gut_health: 35
- feedspot_tiktok_california_mom: 30
- feedspot_tiktok_robotics: 28
- feedspot_tiktok_trail_running: 19
- feedspot_tiktok_australian_camping: 17
- feedspot_tiktok_test: 6
- feedspot_tiktok_recent_created: 0

## Blockers
- Apify: skipped (quota unused; free Feedspot+Bilibili+X lists yielded net-new creators)
- Feedspot: homepage discovery found 35 previously unused official TikTok list slugs, all large dumps; no mass guessed-slug probe today
- AfterShip: skipped (scale6b/Nov-6 already ingested the standard TTS category slugs; no unused categories remain)
- Douyin/XHS/WeChat: no new free public list dumps today (prior CN weekly already absorbed)
- Bilibili: popular p1-20 + precious + weekly series + ranking/v2 (some rids -400) + newlist p1-3 on working rids 1/3/4/5/11/13/36/119/129/155/160/167/177/181/188/202/211; 2613 unique mids, 816 not already in hub, 421 with fans>=1000

## Notes
- Bilibili daily API (popular p1-20, precious, weekly series, ranking/v2, newlist p1-3 on working rids) + X public handles (HVAC / wine / pet / home appliance), verified followers >=1000.
- Feedspot: homepage discovery of previously unused official slugs (large TikTok dumps ingested; no mass guessed-slug probe).
- AfterShip skipped (no unused TTS category slugs remaining after Nov-6).
- Channel expansion: public dealers/wholesalers in underrepresented markets (Nordics/Baltics, Balkans, SEA, LATAM, MEA) for portable AC / HVAC / heaters / pet / home appliances / wine.
- Free public lists preferred; Apify paid actors skipped.
- Rules: followers_num ≥ 1000; unknown dropped; dedupe platform+handle.
- merchants.json untouched (separate routine).
