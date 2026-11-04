#!/usr/bin/env python3
"""Expand B2B merchants with NON-China overseas factories / OEM / ODM / private-label.

Sources (public only):
  - curated_seeds.json          — hand-curated overseas OEM/factories
  - crustdata_merged_strict.json — Crustdata company_search product-filtered overseas
  - portable-ac-eu-us-brand-channel-expanded.csv — EU/US PAC brand/OEM notes
  - Europages / directory HTML snapshots under overseas_oem/ when parseable

Tags: oem, odm, private_label, overseas, region:XX, source:overseas_oem (+linkedin/directory)
Daily reuse: called from expand_merchants_multisource.main() and standalone.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/workspace")
HUB = ROOT / "gtm-creator-hub"
HUB_PUSH = ROOT / "gtm-creator-hub-push"
_RAW_CANDIDATES = [
    ROOT / "raw_lists_merchants" / "overseas_oem",
    HUB_PUSH / "raw_lists_merchants" / "overseas_oem",
    Path(__file__).resolve().parent.parent / "raw_lists_merchants" / "overseas_oem",
]
RAW = next((p for p in _RAW_CANDIDATES if p.exists()), _RAW_CANDIDATES[0])

# Reuse helpers from multisource when available
sys.path.insert(0, str(HUB_PUSH / "scripts"))
sys.path.insert(0, str(ROOT))

try:
    from expand_merchants_multisource import (  # type: ignore
        MerchantDB,
        cats_from_text,
        clean_public_contact,
        dedupe_key,
        domain_of,
        infer_type,
        is_marketplace,
        name_key,
        norm_space,
        platforms_from,
        write_merchants,
        source_counts,
    )
except Exception:
    # Minimal fallbacks if import path differs
    raise

CN_COUNTRY = {"CHN", "CN", "HKG", "HK", "MAC", "MO", "PRC"}
CN_WORDS = re.compile(
    r"\b(china|chinese|hong\s*kong|shenzhen|guangzhou|dongguan|foshan|ningbo|"
    r"hangzhou|shanghai|beijing|suzhou|zhongshan|yiwu|jiangsu|zhejiang|"
    r"guangdong|fujian|shandong|anhui|hebei|sichuan|chongqing|tianjin|"
    r"mainland china|prc)\b",
    re.I,
)

COUNTRY_MAP = {
    "VNM": ("Vietnam", "vn"), "VN": ("Vietnam", "vn"), "VIET NAM": ("Vietnam", "vn"), "VIETNAM": ("Vietnam", "vn"),
    "THA": ("Thailand", "th"), "TH": ("Thailand", "th"), "THAILAND": ("Thailand", "th"),
    "MYS": ("Malaysia", "my"), "MY": ("Malaysia", "my"), "MALAYSIA": ("Malaysia", "my"),
    "IDN": ("Indonesia", "id"), "ID": ("Indonesia", "id"), "INDONESIA": ("Indonesia", "id"),
    "IND": ("India", "in"), "IN": ("India", "in"), "INDIA": ("India", "in"),
    "TUR": ("Turkey", "tr"), "TR": ("Turkey", "tr"), "TURKEY": ("Turkey", "tr"), "TÜRKIYE": ("Turkey", "tr"),
    "MEX": ("Mexico", "mx"), "MX": ("Mexico", "mx"), "MEXICO": ("Mexico", "mx"),
    "USA": ("United States", "us"), "US": ("United States", "us"), "UNITED STATES": ("United States", "us"),
    "CAN": ("Canada", "ca"), "CA": ("Canada", "ca"), "CANADA": ("Canada", "ca"),
    "GBR": ("United Kingdom", "gb"), "GB": ("United Kingdom", "gb"), "UK": ("United Kingdom", "gb"),
    "UNITED KINGDOM": ("United Kingdom", "gb"),
    "DEU": ("Germany", "de"), "DE": ("Germany", "de"), "GERMANY": ("Germany", "de"),
    "ITA": ("Italy", "it"), "IT": ("Italy", "it"), "ITALY": ("Italy", "it"),
    "FRA": ("France", "fr"), "FR": ("France", "fr"), "FRANCE": ("France", "fr"),
    "ESP": ("Spain", "es"), "ES": ("Spain", "es"), "SPAIN": ("Spain", "es"),
    "POL": ("Poland", "pl"), "PL": ("Poland", "pl"), "POLAND": ("Poland", "pl"),
    "CZE": ("Czechia", "cz"), "CZ": ("Czechia", "cz"), "CZECHIA": ("Czechia", "cz"), "CZECH REPUBLIC": ("Czechia", "cz"),
    "SVK": ("Slovakia", "sk"), "SK": ("Slovakia", "sk"),
    "SVN": ("Slovenia", "si"), "SI": ("Slovenia", "si"), "SLOVENIA": ("Slovenia", "si"),
    "HUN": ("Hungary", "hu"), "HU": ("Hungary", "hu"),
    "ROU": ("Romania", "ro"), "RO": ("Romania", "ro"),
    "BGR": ("Bulgaria", "bg"), "BG": ("Bulgaria", "bg"),
    "PRT": ("Portugal", "pt"), "PT": ("Portugal", "pt"),
    "NLD": ("Netherlands", "nl"), "NL": ("Netherlands", "nl"), "NETHERLANDS": ("Netherlands", "nl"),
    "BEL": ("Belgium", "be"), "BE": ("Belgium", "be"), "BELGIUM": ("Belgium", "be"),
    "AUT": ("Austria", "at"), "AT": ("Austria", "at"), "AUSTRIA": ("Austria", "at"),
    "CHE": ("Switzerland", "ch"), "CH": ("Switzerland", "ch"),
    "SWE": ("Sweden", "se"), "SE": ("Sweden", "se"), "SWEDEN": ("Sweden", "se"),
    "DNK": ("Denmark", "dk"), "DK": ("Denmark", "dk"), "DENMARK": ("Denmark", "dk"),
    "NOR": ("Norway", "no"), "NO": ("Norway", "no"),
    "FIN": ("Finland", "fi"), "FI": ("Finland", "fi"),
    "IRL": ("Ireland", "ie"), "IE": ("Ireland", "ie"), "IRELAND": ("Ireland", "ie"),
    "PRT": ("Portugal", "pt"),
    "GRC": ("Greece", "gr"), "GR": ("Greece", "gr"),
    "KOR": ("South Korea", "kr"), "KR": ("South Korea", "kr"), "SOUTH KOREA": ("South Korea", "kr"), "KOREA": ("South Korea", "kr"),
    "TWN": ("Taiwan", "tw"), "TW": ("Taiwan", "tw"), "TAIWAN": ("Taiwan", "tw"),
    "JPN": ("Japan", "jp"), "JP": ("Japan", "jp"), "JAPAN": ("Japan", "jp"),
    "PHL": ("Philippines", "ph"), "PH": ("Philippines", "ph"), "PHILIPPINES": ("Philippines", "ph"),
    "SGP": ("Singapore", "sg"), "SG": ("Singapore", "sg"), "SINGAPORE": ("Singapore", "sg"),
    "BRA": ("Brazil", "br"), "BR": ("Brazil", "br"), "BRAZIL": ("Brazil", "br"),
    "EGY": ("Egypt", "eg"), "EG": ("Egypt", "eg"), "EGYPT": ("Egypt", "eg"),
    "ZAF": ("South Africa", "za"), "ZA": ("South Africa", "za"),
    "AUS": ("Australia", "au"), "AU": ("Australia", "au"), "AUSTRALIA": ("Australia", "au"),
    "NZL": ("New Zealand", "nz"), "NZ": ("New Zealand", "nz"),
    "ARE": ("United Arab Emirates", "ae"), "AE": ("United Arab Emirates", "ae"), "UAE": ("United Arab Emirates", "ae"),
    "SAU": ("Saudi Arabia", "sa"), "SA": ("Saudi Arabia", "sa"),
    "ISR": ("Israel", "il"), "IL": ("Israel", "il"),
    "EU": ("European Union", "eu"), "EUROPE": ("European Union", "eu"),
}

PRODUCT_HINTS = re.compile(
    r"(air.?cond|hvac|heat.?pump|portable.?ac|wine.?cool|wine.?cab|beverage.?cool|"
    r"heater|boiler|thermostat|refrigerat|appliance|pet\b|grooming|dehumidifier|"
    r"fan\b|cooler|chiller|ptac|pumps?\b|white.?goods|cooker.?hood|mini.?bar)",
    re.I,
)
OEM_HINTS = re.compile(r"\b(oem|odm|private[\s\-]?label|contract\s+manufactur|white[\s\-]?label|own[\s\-]?brand)\b", re.I)
FACTORY_HINTS = re.compile(r"\b(factory|manufacturer|manufacturing|plant|production)\b", re.I)


def is_china(country: str, headquarters: str = "", name: str = "", website: str = "") -> bool:
    c = (country or "").strip().upper()
    if c in CN_COUNTRY:
        return True
    blob = f"{country} {headquarters} {name}"
    if CN_WORDS.search(blob):
        # Taiwan/Hong Kong as manufacturing base: still skip mainland China; Taiwan allowed via TWN
        if re.search(r"\b(taiwan|taipei|kaohsiung)\b", blob, re.I) and not re.search(
            r"\b(china|shenzhen|guangzhou|dongguan|foshan|ningbo|hangzhou|shanghai)\b", blob, re.I
        ):
            return False
        if re.search(r"\bhong\s*kong\b", blob, re.I) and not re.search(
            r"\b(shenzhen|guangzhou|dongguan|foshan|ningbo|hangzhou|shanghai|mainland)\b", blob, re.I
        ):
            # HK trading shell often China-linked; skip for overseas factory goal
            return True
        return True
    host = domain_of(website)
    if host.endswith(".cn") or host.endswith(".com.cn"):
        return True
    return False


def region_tags(country_code: str, region_text: str) -> list[str]:
    tags = ["overseas"]
    code = (country_code or "").lower()
    if code:
        tags.append(f"region:{code}")
    # also try parse from region_text
    rt = (region_text or "").upper()
    for key, (label, cc) in COUNTRY_MAP.items():
        if key in rt or label.upper() in rt:
            tags.append(f"region:{cc}")
            break
    # dedupe preserve order
    out, seen = [], set()
    for t in tags:
        if t not in seen:
            seen.add(t); out.append(t)
    return out


def resolve_country(country: str, headquarters: str = "", region: str = "") -> tuple[str, str]:
    """Return (region_display, iso2_lower)."""
    for raw in (country, headquarters, region):
        if not raw:
            continue
        key = raw.strip().upper()
        if key in COUNTRY_MAP:
            label, cc = COUNTRY_MAP[key]
            # Prefer HQ city if available
            if headquarters and len(headquarters) > 3:
                return headquarters.strip(), cc
            return label, cc
        # try last token
        last = key.split(",")[-1].strip()
        if last in COUNTRY_MAP:
            label, cc = COUNTRY_MAP[last]
            return (headquarters or region or label).strip(), cc
        # substring match on known labels
        for k, (label, cc) in COUNTRY_MAP.items():
            if len(k) >= 3 and (k in key or label.upper() in key):
                return (headquarters or region or label).strip(), cc
    return (headquarters or region or country or "Unknown").strip(), ""


def oem_tags_from_text(*parts) -> list[str]:
    blob = " ".join(p or "" for p in parts)
    tags = []
    if re.search(r"\boem\b", blob, re.I):
        tags.append("oem")
    if re.search(r"\bodm\b", blob, re.I):
        tags.append("odm")
    if re.search(r"private[\s\-]?label|white[\s\-]?label|own[\s\-]?brand", blob, re.I):
        tags.append("private_label")
    # default oem if factory/manufacturer and product relevant without explicit tag
    if not tags and FACTORY_HINTS.search(blob):
        tags.append("oem")
    return tags


def infer_mtype(text: str, default: str = "manufacturer") -> str:
    t = (text or "").lower()
    if any(x in t for x in ["factory", "manufacturing plant", "production plant", "manufacturing co"]):
        return "factory"
    if "brand" in t and "oem" not in t and "odm" not in t and "factory" not in t:
        return "brand"
    return infer_type(text, default)


def ingest_curated(db: MerchantDB) -> int:
    path = RAW / "curated_seeds.json"
    if not path.exists():
        print("missing curated_seeds", path)
        return 0
    rows = json.loads(path.read_text())
    n = 0
    for s in rows:
        name = s.get("name") or ""
        region = s.get("region") or ""
        website = s.get("website") or ""
        if is_china("", region, name, website):
            db.stats["skipped_china"] += 1
            continue
        _, cc = resolve_country("", region, region)
        tags = list(s.get("tags") or [])
        tags.extend(region_tags(cc, region))
        tags.append("source:overseas_oem")
        tags.append("curated_overseas")
        for t in oem_tags_from_text(name, s.get("notes", ""), " ".join(tags)):
            if t not in tags:
                tags.append(t)
        ok = db.add(
            name=name,
            type_=s.get("type") or "manufacturer",
            region=region,
            website=website,
            public_contact=s.get("public_contact") or "",
            categories=s.get("categories") or cats_from_text(name, s.get("notes", "")),
            platforms=platforms_from(website, s.get("source_url") or ""),
            source_url=s.get("source_url") or website,
            tags=tags,
            notes=s.get("notes") or "Overseas factory/OEM curated seed",
            source_tag="overseas_oem",
        )
        if ok:
            n += 1
    return n


def ingest_crustdata(db: MerchantDB) -> int:
    path = RAW / "crustdata_merged_strict.json"
    if not path.exists():
        # fall back to noncn dump
        path = RAW / "crustdata_overseas_noncn.json"
    if not path.exists():
        print("missing crustdata", path)
        return 0
    rows = json.loads(path.read_text())
    n = 0
    for s in rows:
        name = s.get("name") or ""
        country = s.get("country") or ""
        hq = s.get("headquarters") or ""
        website = s.get("website") or ""
        desc = s.get("description") or ""
        industries = " ".join(s.get("industries") or []) if isinstance(s.get("industries"), list) else str(s.get("industries") or "")
        query = s.get("query") or ""
        linkedin = s.get("linkedin") or ""
        if is_china(country, hq, name, website):
            db.stats["skipped_china"] += 1
            continue
        blob = f"{name} {desc} {industries} {query}"
        # keep product-relevant or OEM-ish
        if not (PRODUCT_HINTS.search(blob) or OEM_HINTS.search(blob) or FACTORY_HINTS.search(blob)):
            db.stats["skipped_irrelevant"] += 1
            continue
        region, cc = resolve_country(country, hq, hq)
        tags = region_tags(cc, region)
        tags.append("source:overseas_oem")
        tags.append("source:linkedin")
        tags.extend(oem_tags_from_text(name, desc, query, industries))
        if not any(t in tags for t in ("oem", "odm", "private_label")):
            tags.append("oem")
        mtype = infer_mtype(f"{name} {desc} {s.get('company_type','')}")
        notes = (desc or query or "Crustdata overseas manufacturer")[:300]
        source_url = linkedin or website
        plats = platforms_from(website, source_url, ["linkedin"] if linkedin else None)
        ok = db.add(
            name=name,
            type_=mtype,
            region=region,
            website=website if website and not is_marketplace(domain_of(website)) else "",
            public_contact="",
            categories=cats_from_text(name, desc, query, industries),
            platforms=plats,
            source_url=source_url,
            tags=tags,
            notes=notes,
            source_tag="overseas_oem",
        )
        if ok:
            n += 1
    return n


def ingest_portable_csv(db: MerchantDB) -> int:
    path = ROOT / "portable-ac-eu-us-brand-channel-expanded.csv"
    if not path.exists():
        return 0
    n = 0
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            name = row.get("company") or ""
            country = row.get("country") or ""
            website = row.get("website") or ""
            notes = row.get("notes") or ""
            typ = (row.get("type") or "").lower()
            if is_china(country, "", name, website):
                db.stats["skipped_china"] += 1
                continue
            # prefer manufacturers/factories/OEMs; still take brands that claim OEM
            blob = f"{typ} {notes}"
            if typ in {"retailer", "distributor", "dealer", "importer"} and not OEM_HINTS.search(blob):
                continue
            region, cc = resolve_country(country, "", country)
            tags = region_tags(cc, region)
            tags.append("source:overseas_oem")
            tags.append("source:channel")
            tags.extend(oem_tags_from_text(name, notes, typ))
            if "oem" in notes.lower() or "odm" in notes.lower() or typ in {"manufacturer", "factory", "oem"}:
                if "oem" not in tags:
                    tags.append("oem")
            mtype = "factory" if "factory" in typ else ("manufacturer" if typ in {"manufacturer", "oem", "odm"} else infer_mtype(blob, "manufacturer"))
            if typ == "brand" and not OEM_HINTS.search(notes):
                mtype = "brand"
            ok = db.add(
                name=name,
                type_=mtype,
                region=region,
                website=website,
                public_contact=clean_public_contact(row.get("contact_hint") or ""),
                categories=cats_from_text(name, notes, "portable ac"),
                platforms=platforms_from(website, row.get("source_url") or ""),
                source_url=row.get("source_url") or website,
                tags=tags,
                notes=(notes or "EU/US portable AC brand/OEM public list")[:300],
                source_tag="overseas_oem",
            )
            if ok:
                n += 1
    return n


def ingest_europages_html(db: MerchantDB) -> int:
    """Best-effort scrape of saved Europages / directory HTML snapshots."""
    n = 0
    for path in sorted(RAW.glob("src_*.html")) + sorted(RAW.glob("*.html")):
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if len(html) < 500:
            continue
        # company cards: common europages patterns
        # data-company-name / company-name / <a ... class="...company...">
        names = set()
        for m in re.finditer(
            r'(?:data-company-name|companyName|company-name)=["\']([^"\']{2,120})["\']',
            html, re.I,
        ):
            names.add(norm_space(m.group(1)))
        for m in re.finditer(
            r'<a[^>]+href="https?://www\.europages[^"]*/([^"/]+)/[^"]*"[^>]*>([^<]{2,120})</a>',
            html, re.I,
        ):
            names.add(norm_space(m.group(2)))
        # Generic directory company-name anchors (ExportersIndia / TradeIndia / similar)
        for m in re.finditer(
            r'>([^<]{3,90}(?:Pvt\.?\s*Ltd\.?|Private Limited|Ltd\.?|Limited|Inc\.?|LLC|GmbH|S\.A\.?))<',
            html, re.I,
        ):
            cand = norm_space(m.group(1))
            if 3 <= len(cand) <= 90:
                names.add(cand)
        # JSON-LD
        for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
            try:
                data = json.loads(m.group(1))
            except Exception:
                continue
            items = data if isinstance(data, list) else [data]
            for it in items:
                if isinstance(it, dict) and it.get("@type") in {"Organization", "LocalBusiness", "Corporation"}:
                    if it.get("name"):
                        names.add(norm_space(it["name"]))
        for name in names:
            if len(name) < 3 or name.lower() in {"europages", "companies", "suppliers", "manufacturers"}:
                continue
            if is_china("", "", name, ""):
                continue
            if not PRODUCT_HINTS.search(name) and "wine" not in name.lower() and "air" not in name.lower():
                # still accept if page is wine/hvac themed
                if "wine" not in path.name and "air" not in path.name and "hvac" not in path.name:
                    # keep generic europages wine cabinet pages
                    if "wine" not in html[:2000].lower() and "air condition" not in html[:2000].lower():
                        continue
            tags = ["overseas", "source:overseas_oem", "source:directory", "oem"]
            cats = cats_from_text(name, path.name, "wine cooler" if "wine" in path.name or "wine" in html[:1500].lower() else "hvac")
            ok = db.add(
                name=name,
                type_="manufacturer",
                region="Europe",
                website="",
                public_contact="",
                categories=cats,
                platforms=["directory"],
                source_url=f"file://{path.name}",
                tags=tags + region_tags("eu", "Europe"),
                notes=f"Directory snapshot {path.name}",
                source_tag="overseas_oem",
            )
            if ok:
                n += 1
    return n


def retag_overseas_existing(db: MerchantDB) -> int:
    """Mark existing non-China factory/manufacturer rows as overseas when region clear."""
    n = 0
    for r in db.rows:
        region = r.get("region") or ""
        website = r.get("website") or ""
        name = r.get("name") or ""
        if is_china("", region, name, website):
            continue
        # must look non-China
        _, cc = resolve_country("", region, region)
        if not cc:
            # try country words
            if not re.search(
                r"\b(vietnam|thailand|malaysia|indonesia|india|turkey|mexico|united states|usa|"
                r"germany|italy|france|poland|spain|uk|united kingdom|korea|taiwan|japan|"
                r"philippines|brazil|egypt|canada|netherlands|belgium|sweden|denmark|"
                r"ireland|slovenia|czech|austria|portugal|australia|uae|singapore)\b",
                region, re.I,
            ):
                continue
            _, cc = resolve_country(region, region, region)
        tags = set(r.get("tags") or [])
        if "overseas" not in tags:
            tags.add("overseas")
            n += 1
        if cc:
            tags.add(f"region:{cc}")
        # factory/manufacturer get oem lean tag if missing
        if r.get("type") in {"factory", "manufacturer"} and not ({"oem", "odm", "private_label"} & tags):
            if any(c in (r.get("categories") or []) for c in (
                "hvac", "portable_ac", "wine_cooler", "heater", "pet_products", "home_appliance", "export_supply"
            )):
                tags.add("oem")
        tags.add("source:overseas_oem") if "curated_overseas" in tags or "oem" in tags else None
        r["tags"] = sorted(tags)
    return n


def expand_into(db: MerchantDB) -> dict:
    """Mutate MerchantDB with overseas OEM sources. Returns stats dict."""
    before = len(db.rows)
    c1 = ingest_curated(db)
    c2 = ingest_crustdata(db)
    c3 = ingest_portable_csv(db)
    c4 = ingest_europages_html(db)
    enriched = retag_overseas_existing(db)
    return {
        "before": before,
        "after": len(db.rows),
        "added_curated": c1,
        "added_crustdata": c2,
        "added_portable_csv": c3,
        "added_europages": c4,
        "retag_touched": enriched,
        "skipped_china": db.stats.get("skipped_china", 0),
        "skipped_irrelevant": db.stats.get("skipped_irrelevant", 0),
        "net_new": len(db.rows) - before,
    }


def count_flags(rows):
    overseas = sum(1 for r in rows if "overseas" in (r.get("tags") or []))
    oem = sum(1 for r in rows if "oem" in (r.get("tags") or []))
    odm = sum(1 for r in rows if "odm" in (r.get("tags") or []))
    pl = sum(1 for r in rows if "private_label" in (r.get("tags") or []))
    factory = sum(1 for r in rows if r.get("type") in {"factory", "manufacturer"} and "overseas" in (r.get("tags") or []))
    return {"overseas": overseas, "oem": oem, "odm": odm, "private_label": pl, "overseas_factory_or_mfr": factory}


def main():
    src = HUB_PUSH / "data" / "merchants.json"
    if not src.exists():
        src = ROOT / "merchants.json"
    before_rows = json.loads(src.read_text())
    before_n = len(before_rows)
    before_flags = count_flags(before_rows)

    db = MerchantDB(before_rows)
    stats = expand_into(db)

    type_rank = {
        "factory": 0, "manufacturer": 1, "exporter": 2, "importer": 3,
        "brand": 4, "wholesaler": 5, "b2b_store": 6,
    }
    db.rows.sort(key=lambda r: (type_rank.get(r.get("type"), 9), (r.get("name") or "").lower()))

    for base in [HUB_PUSH / "data", HUB / "data", ROOT]:
        if base.parent.exists() or base == ROOT:
            try:
                write_merchants(db.rows, base / "merchants.json", base / "merchants.csv")
            except Exception as e:
                print("write skip", base, e)

    # sync this script into hub-push
    scripts_dir = HUB_PUSH / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    here = Path(__file__).resolve() if "__file__" in dir() else ROOT / "expand_merchants_overseas_oem.py"
    for target_root in [HUB_PUSH, HUB]:
        tdir = target_root / "scripts"
        tdir.mkdir(parents=True, exist_ok=True)
        src_script = ROOT / "expand_merchants_overseas_oem.py"
        if src_script.exists():
            (tdir / "expand_merchants_overseas_oem.py").write_text(src_script.read_text())

    after_flags = count_flags(db.rows)
    report = {
        "before": before_n,
        "after": len(db.rows),
        "net_new": len(db.rows) - before_n,
        "expand_stats": stats,
        "before_flags": before_flags,
        "after_flags": after_flags,
        "by_type": dict(Counter(r.get("type") for r in db.rows)),
        "region_tag_top": dict(Counter(
            t for r in db.rows for t in (r.get("tags") or []) if t.startswith("region:")
        ).most_common(25)),
        "blockers": [
            "Alibaba / GlobalSources / TradeKey / Kompass OEM directory pages mostly JS-shell or blocked",
            "Crustdata HVAC industry search hit out_of_credits mid-run; used prior merged_strict dump",
            "Industrystock 403; some association directories login-walled",
            "Mainland China deliberately excluded for this overseas OEM pass",
        ],
    }
    (ROOT / "merchants-overseas-oem-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (HUB_PUSH / "merchants-overseas-oem-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
