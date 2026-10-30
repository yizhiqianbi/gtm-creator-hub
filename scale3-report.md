# Scale3 / Scale3b Report — 2026-10-30 (Asia/Shanghai)

## Totals
- Original (session start): 17766
- After scale3: 19801
- **After scale3b: 22588**
- Net new this wave (scale3b): 2787
- Follower updates on existing: 1
- Cumulative vs session start: +4822

## Per-platform
| Platform | Before scale3b | After | Delta |
|----------|---------------:|------:|------:|
| tiktok | 9025 | 9160 | +135 |
| bilibili | 1679 | 4331 | +2652 |
| instagram | 4306 | 4306 | +0 |
| douyin | 2741 | 2741 | +0 |
| xiaohongshu | 1288 | 1288 | +0 |
| x | 562 | 562 | +0 |
| wechat_store | 200 | 200 | +0 |

## Sources (net-new keys this wave)
- bilibili_enriched: 2652
- feedspot_crossfit: 68
- modash_tt: 67

## QA
- Hard filter: followers_num >= 1000; unknown/未知 dropped
- Dedupe: (platform, handle.lower())
- Bilibili fans from public api.bilibili.com/x/relation/stat (search + rank + popular)
- Feedspot: creators.feedspot.com niche lists (36 niches with content)
- Modash: public find-influencers HTML
- Apify not used

## Files
- /workspace/creators.json, creators.csv
- /workspace/gtm-creator-hub/data/creators.json, creators.csv
- /workspace/creators-scaled-2026-10-30.xlsx
- /workspace/scale3-report.md
- Hub: https://yizhiqianbi.github.io/gtm-creator-hub/
