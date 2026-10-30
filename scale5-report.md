# Scale5 Report — 2026-10-31 (Asia/Shanghai)

## Totals
- Before (scale4 ae6bda7): 24623
- After: 28390
- Net new: 3767

## Per-platform
| Platform | Before | After | Delta |
|----------|-------:|------:|------:|
| tiktok | 10297 | 10297 | +0 |
| instagram | 4306 | 6442 | +2136 |
| bilibili | 4983 | 5109 | +126 |
| douyin | 2831 | 4333 | +1502 |
| xiaohongshu | 1288 | 1291 | +3 |
| x | 718 | 718 | +0 |
| wechat_store | 200 | 200 | +0 |

## Sources
- Feedspot Instagram niches via headless Chrome (public lists): beauty, tech, home_decor, pet, fitness, food, fashion, sports, retail finds, etc.
- Feedspot TikTok niches (mostly already in DB → low net new)
- Feedspot X fitness/marketing (already covered)
- Chanmama Douyin open ranks → +1502
- Bilibili popular/newlist + relation/stat API → +126
- TooBigData XHS Excel name-matched to public UIDs → +3
- Wikipedia most-followed X (already in DB)

## QA
- followers_num >= 1000; 未知/unknown dropped
- Deduped by (platform, handle.lower())
- Public sources only; Apify skipped (hard monthly limit)
- X / TikTok net growth limited this wave (high overlap with scale2–4)
- XHS Excels lack UIDs; only UID-matched rows kept

## Hub
- https://yizhiqianbi.github.io/gtm-creator-hub/
