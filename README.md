# GTM Creator Hub

Internal shortlist of creators for GTM outreach (GitHub Pages). **Multi-platform** (TikTok, Instagram, X, 抖音, 小红书, B站, 微信小店) with **multi-tag** filtering (product, format, audience, geo, commerce).

**Dataset:** 33341 unique creators — tiktok 13613 · instagram 6442 · bilibili 6206 · douyin 4463 · xiaohongshu 1466 · x 951 · wechat_store 200 (all `followers_num >= 1000`).

## Route datasets (Scale 6)

Alongside `data/creators.json`, this repo also ships:

- `data/channels.json` (+ csv) — public **渠道合作** partners (distributors / dealers / wholesalers / mod shops) for portable AC, HVAC, wine coolers, heaters, pet products. **862** rows.
- `data/brand_content_sources.json` (+ csv) — public **公司品牌与专业内容** URLs (FAQ / case / brochure / site) with short notes only; no copyrighted full-text dumps. **497** rows.

See `scale6-routes-report.md` / `daily-refresh-report.md` for counts and blockers. Creator UI: `index.html`. Merchant UI: `merchants.html`. Channel/brand JSON still ship alongside; channel browsing UI is a follow-up.

## Data

<!-- merchants-dataset -->
- **B端商家 / merchants**: `data/merchants.json` + `data/merchants.csv` (5704 rows; manufacturer / factory / wholesaler / brand / exporter / importer / b2b_store; niches: portable AC/HVAC, wine cooler, heaters, pet, home appliances, export/live-commerce supply). Includes public customs/trade directory enrichment (`hs_codes`, `trade_role`, tags `customs_source` / `hs:*`). Cross-tagged with `channels.json` via `merchant_db_overlap` / `related_channel` (no silent merge).
- **商家站 UI**: [`merchants.html`](./merchants.html) (GitHub Pages) — filter by type / region / category / trade role / tags.
