#!/usr/bin/env python3
"""Incremental B2B merchant expansion from PUBLIC customs / trade directory pages.

Sources (public HTML only, no login bypass):
- ImportYeti HS code pages (supplier links)
- ImportDoor HS product pages (top importers / suppliers tables + FAQ lists)
- Zauba public exporter snippets when company names are visible without sign-in

Attaches: hs_codes, trade_role, tags customs_source / hs:XXXXXX / trade_role:*
Designed to be callable from build_merchants.py daily routine.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/workspace")
RAW = ROOT / "raw_lists_merchants" / "customs"
HUB = ROOT / "gtm-creator-hub"
HUB_PUSH = ROOT / "gtm-creator-hub-push"

COUNTRY_WORDS = {
    "CHINA", "THAILAND", "INDONESIA", "MEXICO", "INDIA", "ITALY", "GERMANY",
    "VIETNAM", "VIET NAM", "JAPAN", "MALAYSIA", "HONG KONG", "NETHERLANDS",
    "REPUBLIC OF KOREA", "KOREA", "TAIWAN", "UNITED STATES", "CANADA", "N/A",
    "SPAIN", "FRANCE", "BRAZIL", "TURKEY", "PHILIPPINES", "UNITED KINGDOM",
    "KOREA, DEMOCRATIC PEOPLES REPUBLIC OF", "SINGAPORE", "POLAND", "BELGIUM",
}

LOGISTICS_RE = re.compile(
    r"\b(logistics|shipping|freight|forwarder|forwarding|express|ocean|"
    r"vessel|seaway|cargo|transport|truck|warehouse|bank|wells fargo|"
    r"notify party|carrier)\b",
    re.I,
)

HS_NICHE = {
    "8415": ["portable_ac", "hvac"],
    "841510": ["portable_ac", "hvac"],
    "841581": ["hvac", "portable_ac"],
    "841582": ["portable_ac", "hvac"],
    "841583": ["hvac"],
    "841520": ["hvac"],
    "841590": ["hvac"],
    "8418": ["wine_cooler", "home_appliance"],
    "841810": ["home_appliance", "wine_cooler"],
    "841829": ["wine_cooler", "home_appliance"],
    "841850": ["wine_cooler", "home_appliance"],
    "841861": ["hvac"],
    "841869": ["wine_cooler", "home_appliance"],
    "841899": ["home_appliance"],
    "847960": ["home_appliance", "portable_ac"],
    "8516": ["heater", "space_heater"],
    "851610": ["heater"],
    "851621": ["heater", "space_heater"],
    "851629": ["heater", "space_heater"],
    "851660": ["home_appliance", "heater"],
    "851680": ["heater"],
    "8508": ["home_appliance"],
    "850811": ["home_appliance"],
    "850819": ["home_appliance"],
    "850870": ["home_appliance"],
    "8509": ["home_appliance"],
    "850980": ["home_appliance"],
    "2309": ["pet_products"],
    "230910": ["pet_products"],
    "4201": ["pet_products"],
    "420100": ["pet_products"],
    "841459": ["home_appliance", "hvac"],
    "841490": ["hvac"],
    "842139": ["hvac", "home_appliance"],
    "732190": ["heater", "home_appliance"],
    "732111": ["heater", "home_appliance"],
    "392690": ["pet_products", "home_appliance"],
    "630790": ["pet_products"],
    "940180": ["home_appliance"],
    "940171": ["home_appliance"],
}

VALID_TYPES = {
    "manufacturer", "factory", "wholesaler", "brand", "exporter", "b2b_store", "importer",
}


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).replace("&amp;", "&")


def name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def domain_of(url: str) -> str:
    if not url:
        return ""
    u = url.strip()
    if not u.startswith("http"):
        u = "https://" + u
    try:
        host = urlparse(u).netloc.lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def dedupe_key(name: str, website: str) -> str:
    d = domain_of(website)
    n = name_key(name)
    return d or n


def cats_for_hs(hs_codes) -> list[str]:
    cats = set()
    for hs in hs_codes or []:
        hs = str(hs)
        if hs in HS_NICHE:
            cats.update(HS_NICHE[hs])
        elif len(hs) >= 4 and hs[:4] in HS_NICHE:
            cats.update(HS_NICHE[hs[:4]])
    if not cats:
        cats.add("home_appliance")
    return sorted(cats)


def region_guess(name: str, role: str, hs_blob: str = "") -> str:
    n = name.lower()
    if any(x in n for x in ("thailand", "thai ")):
        return "Thailand"
    if "hong kong" in n or " hk " in f" {n} " or n.endswith(" hk"):
        return "Hong Kong"
    if any(x in n for x in ("vietnam", "viet nam")):
        return "Vietnam"
    if "indonesia" in n or n.startswith("pt "):
        return "Indonesia"
    if any(x in n for x in ("mexico", " sa de", "s de rl")):
        return "Mexico"
    if any(x in n for x in ("gmbh", "germany")):
        return "Germany"
    if any(x in n for x in (" co ltd", "co., ltd", "limited", "ningbo", "shenzhen", "guangdong", "shanghai", "zhejiang", "jiangsu", "wuhu", "qingdao", "hangzhou", "foshan", "dongguan", "xiamen", "hefei")):
        return "China"
    if role == "importer" or any(x in n for x in (" llc", " inc", " corp", "usa", " america")):
        return "USA"
    return "Unknown"


def infer_type(role: str, name: str) -> str:
    n = name.lower()
    if role == "importer":
        if any(x in n for x in ("home depot", "wal mart", "walmart", "costco", "target", "tractor supply")):
            return "wholesaler"
        return "importer"
    if any(x in n for x in ("manufactur", "factory", "mfg", "industrial", "electric", "appliance", "equipment")):
        return "manufacturer"
    if any(x in n for x in ("trading", "trade", "import", "export", "intl", "international")):
        return "exporter"
    if role == "exporter":
        return "exporter"
    return "manufacturer"


def parse_customs_dir(raw: Path) -> dict:
    """Return name_key -> aggregate company dict from saved public HTML."""
    companies = {}

    def add(name, role, hs, source, url=""):
        name = norm_space(name)
        if len(name) < 3:
            return
        up = name.upper()
        if up in COUNTRY_WORDS or re.fullmatch(r"[\d,]+", name):
            return
        if name.lower() in {"importer", "supplier", "shipments", "country", "product", "origin countries"}:
            return
        if LOGISTICS_RE.search(name):
            return
        # drop obvious person-only short names without company marker when role exporter from yeti noise
        key = name_key(name)
        if len(key) < 4:
            return
        c = companies.get(key)
        if not c:
            c = {
                "name": name,
                "roles": set(),
                "hs": set(),
                "sources": set(),
                "urls": set(),
            }
            companies[key] = c
        # prefer longer display name
        if len(name) > len(c["name"]):
            c["name"] = name
        if role:
            c["roles"].add(role)
        if hs:
            c["hs"].add(str(hs))
        c["sources"].add(source)
        if url:
            c["urls"].add(url)

    if not raw.exists():
        return companies

    # ImportYeti HS / supplier pages
    for p in sorted(raw.glob("yeti-*.html")):
        m = re.search(r"yeti-(\d{4,10})", p.name)
        hs = m.group(1) if m else ""
        t = p.read_text(encoding="utf-8", errors="replace")
        for href, name in re.findall(r'href="(/supplier/[^"]+)"[^>]*>([^<]{2,100})', t):
            add(name, "exporter", hs, "importyeti", f"https://www.importyeti.com{href}")
        for href, name in re.findall(r'href="(/company/[^"]+)"[^>]*>([^<]{2,100})', t):
            add(name, "importer", hs, "importyeti", f"https://www.importyeti.com{href}")

    # ImportDoor product / heading pages
    for p in sorted(list(raw.glob("products_*.html")) + list(raw.glob("id-*.html"))):
        t = p.read_text(encoding="utf-8", errors="replace")
        hm = re.search(r"(?:products_|HS |hs[_ ]?code[^0-9]{0,12}|heading/)(\d{4,10})", p.name + " " + t[:2500], re.I)
        hs = hm.group(1) if hm else ""
        # HTML table rows
        for name, _num in re.findall(r"<td[^>]*>\s*([^<]{2,90})\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*</td>", t):
            name = norm_space(name)
            if name.upper() in COUNTRY_WORDS:
                continue
            if not re.search(r"[A-Za-z]", name):
                continue
            add(name, "", hs, "importdoor", f"https://www.importdoor.com/")
        for m in re.finditer(r"top U\.S\. importers[^\.]{0,100}include ([^\.]{10,500})\.", t, re.I):
            for part in re.split(r",| and ", m.group(1)):
                part = part.strip(" .")
                if part:
                    add(part, "importer", hs, "importdoor")
        for m in re.finditer(
            r"(?:leading suppliers|top suppliers)[^\.]{0,100}include ([^\.]{10,500})\.",
            t,
            re.I,
        ):
            for part in re.split(r",| and ", m.group(1)):
                part = part.strip(" .")
                if part:
                    add(part, "exporter", hs, "importdoor")
        # markdown-style tables if present
        for name, _num in re.findall(r"\|\s*([A-Z][A-Z0-9 &.,'/\-]{2,70})\s*\|\s*([\d,]+)\s*\|", t):
            if name.upper() in COUNTRY_WORDS:
                continue
            add(name, "", hs, "importdoor")

    # Zauba public snippets
    zp = raw / "zauba-pac-exp.html"
    if zp.exists():
        t = zp.read_text(encoding="utf-8", errors="replace")
        for name in re.findall(r">([A-Z][A-Z0-9 &.,\-]{3,80}(?:CO LTD|LIMITED|INC|LLC|CORP))<", t):
            add(name, "exporter", "8415", "zauba", "https://www.zauba.com/portable-air-conditioner-exporters")

    return companies


def load_merchants(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def write_merchants(rows: list[dict], json_path: Path, csv_path: Path):
    fields = [
        "name", "type", "region", "website", "public_contact",
        "categories", "platforms", "source_url", "tags", "notes",
        "related_channel", "hs_codes", "trade_role",
    ]
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, "") for k in fields}
            for list_key in ("categories", "platforms", "tags", "hs_codes"):
                val = r.get(list_key) or []
                row[list_key] = "|".join(val) if isinstance(val, list) else val
            w.writerow(row)


def merge_customs(existing: list[dict], customs: dict) -> tuple[list[dict], dict]:
    by_name = {}
    by_domain = {}
    rows = []
    for r in existing:
        r = dict(r)
        r.setdefault("hs_codes", [])
        r.setdefault("trade_role", "")
        rows.append(r)
        by_name[name_key(r.get("name", ""))] = r
        d = domain_of(r.get("website") or "")
        if d:
            by_domain[d] = r

    added = 0
    enriched = 0
    skipped_logistics = 0

    for key, c in customs.items():
        name = c["name"]
        roles = c["roles"]
        hs_codes = sorted(c["hs"])
        sources = sorted(c["sources"])
        url = sorted(c["urls"])[0] if c["urls"] else ""
        if LOGISTICS_RE.search(name):
            skipped_logistics += 1
            continue

        trade_role = ""
        if "importer" in roles and "exporter" in roles:
            trade_role = "both"
        elif "importer" in roles:
            trade_role = "importer"
        elif "exporter" in roles:
            trade_role = "exporter"
        else:
            # ImportDoor table rows without section — treat as trade participant
            trade_role = "exporter" if any(x in name.lower() for x in ("co ltd", "limited", "manufactur")) else "importer"

        hit = by_name.get(key)
        if not hit and url:
            hit = by_domain.get(domain_of(url))

        cats = cats_for_hs(hs_codes)
        tags = {
            "route:b2b_merchant",
            "customs_source",
            f"trade_role:{trade_role}" if trade_role else "trade_role:unknown",
        }
        for s in sources:
            tags.add(f"customs:{s}")
        for hs in hs_codes:
            tags.add(f"hs:{hs}")
        tags.update(cats)

        if hit:
            # enrich existing
            ht = set(hit.get("tags") or [])
            ht.update(tags)
            hit["tags"] = sorted(ht)
            hs_set = set(hit.get("hs_codes") or [])
            hs_set.update(hs_codes)
            hit["hs_codes"] = sorted(hs_set)
            if trade_role:
                prev = hit.get("trade_role") or ""
                if prev and prev != trade_role and {prev, trade_role} == {"importer", "exporter"}:
                    hit["trade_role"] = "both"
                elif not prev:
                    hit["trade_role"] = trade_role
            # merge categories
            cset = set(hit.get("categories") or [])
            cset.update(cats)
            hit["categories"] = sorted(cset)
            note_bits = []
            if hs_codes:
                note_bits.append("HS " + "/".join(hs_codes[:4]))
            if sources:
                note_bits.append("customs:" + ",".join(sources))
            extra = "; ".join(note_bits)
            if extra and extra not in (hit.get("notes") or ""):
                hit["notes"] = norm_space(((hit.get("notes") or "") + " | " + extra).strip(" |"))[:320]
            enriched += 1
            continue

        type_ = infer_type(trade_role if trade_role != "both" else "exporter", name)
        if type_ not in VALID_TYPES:
            type_ = "manufacturer"
        tags.add(type_)
        region = region_guess(name, trade_role)
        source_url = url or (
            "https://www.importdoor.com/" if "importdoor" in sources else
            "https://www.importyeti.com/" if "importyeti" in sources else
            "https://www.zauba.com/"
        )
        platforms = ["customs_directory"]
        if "importyeti" in sources:
            platforms.append("importyeti")
        if "importdoor" in sources:
            platforms.append("importdoor")
        if "zauba" in sources:
            platforms.append("zauba")

        row = {
            "name": name,
            "type": type_,
            "region": region,
            "website": "",
            "public_contact": "",
            "categories": cats,
            "platforms": sorted(set(platforms)),
            "source_url": source_url,
            "tags": sorted(tags),
            "notes": norm_space(
                f"Public customs/trade directory · role={trade_role or 'n/a'} · HS {('/'.join(hs_codes[:4]) or 'n/a')}"
            )[:320],
            "related_channel": "",
            "hs_codes": hs_codes,
            "trade_role": trade_role,
        }
        rows.append(row)
        by_name[key] = row
        added += 1

    type_rank = {
        "factory": 0, "manufacturer": 1, "exporter": 2, "importer": 3,
        "brand": 4, "wholesaler": 5, "b2b_store": 6,
    }
    rows.sort(key=lambda r: (type_rank.get(r.get("type"), 9), (r.get("name") or "").lower()))

    report = {
        "customs_candidates": len(customs),
        "added": added,
        "enriched_existing": enriched,
        "skipped_logistics": skipped_logistics,
        "total_after": len(rows),
        "by_type": dict(Counter(r.get("type") for r in rows)),
        "with_hs": sum(1 for r in rows if r.get("hs_codes")),
        "by_trade_role": dict(Counter(r.get("trade_role") or "unset" for r in rows)),
        "sources_used": sorted({
            s for c in customs.values() for s in c["sources"]
        }),
    }
    return rows, report


def main():
    # Prefer push copy as canonical current dataset
    src = HUB_PUSH / "data" / "merchants.json"
    if not src.exists():
        src = ROOT / "merchants.json"
    before = load_merchants(src)
    before_n = len(before)
    customs = parse_customs_dir(RAW)
    rows, report = merge_customs(before, customs)
    report["before"] = before_n
    report["net_new"] = report["total_after"] - before_n

    for base in [HUB_PUSH / "data", HUB / "data", ROOT]:
        write_merchants(rows, base / "merchants.json", base / "merchants.csv")

    (ROOT / "merchants-customs-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
