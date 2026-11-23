# Daily refresh 2026-11-23

- Creators: **34620 → 34846** (net **+226**)
  - Platforms: tiktok 13720 · instagram 6442 · x 1096 · douyin 4463 · bilibili 7459 · xiaohongshu 1466 · wechat_store 200
- Channels: **969 → 982** (net **+13**)
- Brand content sources: **604 → 617** (net **+13**)

## Sources
- bilibili_daily_api: 209
- x_mcp_public: 17
- channels_curated_daily: 13
- brand_curated_daily: 13

## Blockers
- Apify: skipped (not used; free Bilibili + verified public X lists yielded net-new creators)
- Feedspot: homepage http=200, 235 official list links, unused_clean=0; no mass guessed-slug probe today
- AfterShip: skipped (standard TTS category slugs already ingested on earlier runs; no unused official categories remain)
- Douyin/XHS/WeChat: no new free public list dumps today (prior CN weekly already absorbed)
- Bilibili: popular p1-20 + precious + weekly series + ranking/v2 (some rids/dyn -400 or empty) + newlist p1-3 on working rids 1/3/4/5/11/13/36/119/129/155/160/167/177/181/188/202/211; 2580 unique mids, 619 not already in hub, 209 with fans>=1000
- GitHub push not performed in this collection run: repository writes go through a CloudAgent. Live Pages still serve the 2026-11-16 main dataset until the open data PR is merged.
- Open PR #1 (cursor/data-refresh-2026-11-22-9ea2) already contains the 2026-11-22 validated increment and was not merged to main; today's increment is based on that branch, not stale main.

## Notes
- Bilibili daily public API + 17 verified public X handles (wine / HVAC / pet / home appliance), followers >=1000.
- Feedspot homepage discovery found no previously unused official slugs today.
- Channel expansion: 13 official dealer/specialty websites verified in thin markets (KW, AE, EC, HN, RS, CY, KZ, UZ, NP, DE, UK). Sites that returned 403/timeout/TLS errors were not retried or bypassed.
- Rules: followers_num >= 1000; unknown dropped; dedupe platform+handle; all new rows have profile_url and multi tags.
- merchants.json was not changed in this creator-hub routine.
- Today's increment is based on the validated 2026-11-22 dataset (PR #1 / branch cursor/data-refresh-2026-11-22-9ea2), not stale main (11/16).
