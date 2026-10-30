# Scale4 Report — 2026-10-30 (Asia/Shanghai)

## Totals
- Before: 22588
- After: 24623
- Net new (approx): 2035
- Raw candidate rows this wave: 12846

## Per-platform
| Platform | Before | After | Delta |
|----------|-------:|------:|------:|
| tiktok | 9160 | 10297 | +1137 |
| bilibili | 4331 | 4983 | +652 |
| instagram | 4306 | 4306 | +0 |
| douyin | 2741 | 2831 | +90 |
| xiaohongshu | 1288 | 1288 | +0 |
| x | 562 | 718 | +156 |
| wechat_store | 200 | 200 | +0 |

## Top sources (raw parsed counts)
- bilibili_scale4: 661
- chanmama_综合: 586
- chanmama_jiajujiafang: 200
- chanmama_meizhuanghufu: 200
- chanmama_yundonghuwai: 200
- chanmama_xianhuahuizhi: 196
- chanmama_fushineiyi: 195
- chanmama_wanjuyueqi: 195
- chanmama_yaopinbaojiian: 195
- chanmama_jiajubuilding: 194
- chanmama_shengxianshuguo: 194
- chanmama_riyongbaihuo: 193
- chanmama_3cshuma: 188
- chanmama_chongwuyongpin: 186
- chanmama_zhongbiaopeishi: 184
- chanmama_chuweijiadian: 183
- chanmama_lipinwenchuang: 182
- chanmama_shechipin: 179
- chanmama_muyingyongpin: 174
- chanmama_shipinyinliao: 150
- chanmama_hufu: 146
- chanmama_jiancai: 135
- chanmama_jiajuqingjie: 134
- chanmama_shuma: 133
- chanmama_muyingwanju: 125
- chanmama_yinliao: 125
- chanmama_jujia: 124
- chanmama_meizhuang: 123
- chanmama_shouji: 122
- chanmama_jiankang: 115
- chanmama_shipin: 115
- chanmama_xiexuexiangbao: 110
- feedspot_tiktok_black: 100
- feedspot_tiktok_cat: 100
- feedspot_tiktok_dating: 100
- feedspot_tiktok_digital_art: 100
- feedspot_tiktok_latin: 100
- feedspot_tiktok_latina: 100
- feedspot_tiktok_senior: 100
- feedspot_tiktok_south_african: 96

## QA
- Hard filter: followers_num >= 1000; unknown/未知 dropped
- Dedupe: (platform, handle.lower())
- Sources: Feedspot new niches, Bilibili popular/newlist/precious + relation/stat,
  Chanmama open rank reparse, Influencers.club (when fans present), Modash if unblocked
- Apify not used

## Files
- /workspace/creators.json, creators.csv
- /workspace/gtm-creator-hub/data/
- /workspace/creators-scaled4-2026-10-30.xlsx
- /workspace/scale4-report.md
- Hub: https://yizhiqianbi.github.io/gtm-creator-hub/
