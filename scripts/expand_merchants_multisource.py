#!/usr/bin/env python3
"""Expand B2B merchants from PUBLIC multi-sources for daily reuse.

Sources / tags:
  source:channel     — trade channel / distributor directories (channels.json + brand CSVs)
  source:customs     — customs import/export (expand_merchants_customs)
  source:trade_show  — Canton Fair / Ambiente / Hardware Fair exhibitor lists
  source:linkedin    — Crustdata LinkedIn-indexed company search (public company fields)
  source:maps        — Google Maps public business listings CSVs
  source:alibaba     — Alibaba.com public supplier listing pages
  source:1688        — 1688 public pages when available
  source:association — AHRI / AHAM / other trade association member directories
  source:mic         — Made-in-China public manufacturer directories (kept + retagged)

Public only; no login/paywall bypass.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/workspace")
RAW = ROOT / "raw_lists_merchants"
HUB = ROOT / "gtm-creator-hub"
HUB_PUSH = ROOT / "gtm-creator-hub-push"

VALID_TYPES = {
    "manufacturer", "factory", "wholesaler", "brand", "exporter", "b2b_store", "importer",
}

SOURCE_TAGS = {
    "channel", "customs", "trade_show", "linkedin", "maps", "alibaba", "1688", "association", "mic",
}

MARKETPLACE_DOMAINS = {
    "alibaba.com", "1688.com", "made-in-china.com", "globalsources.com",
    "amazon.com", "business.amazon.com", "google.com", "google.co.uk",
    "google.de", "google.nl", "google.fr", "ec21.com", "cantonfair.co",
    "cantonfair.org.cn", "ahrinet.org", "aham.org", "linkedin.com",
    "eisenwarenmesse.com", "messefrankfurt.com", "importyeti.com",
    "importdoor.com", "zauba.com",
}


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).replace("&amp;", "&").replace("&#39;", "'")


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


def is_marketplace(host: str) -> bool:
    if not host:
        return False
    return any(host == m or host.endswith("." + m) for m in MARKETPLACE_DOMAINS)


def dedupe_key(name: str, website: str) -> str:
    d = domain_of(website)
    n = re.sub(r"[^a-z0-9]+", "", (name or "").lower())
    if is_marketplace(d) or "made-in-china.com" in d or "en.alibaba.com" in d:
        return f"{d}::{n}" if n else d
    return d or n


def name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def cats_from_text(*parts) -> list[str]:
    blob = " ".join(p or "" for p in parts).lower()
    cats = set()
    mapping = [
        ("portable_ac", ["portable ac", "portable air", "mobile air conditioner", "spot cooler", "portable_ac", "pac "]),
        ("hvac", ["hvac", "air conditioner", "air conditioning", "dehumidifier", "heat pump", "vrf", "chiller", "ventilation"]),
        ("wine_cooler", ["wine cooler", "wine cabinet", "wine fridge", "wine refrigerator", "beverage cooler", "wine_cooler", "wine accessory"]),
        ("heater", ["space heater", "oil heater", "ptc heater", "electric heater", "infrared heater", "patio heater", "heater"]),
        ("pet_products", ["pet ", "pet-", "petkit", "pet feeder", "pet dryer", "pet products", "pet_products", "dog dryer", "grooming"]),
        ("home_appliance", ["home appliance", "household", "appliance", "mini fridge", "air cooler", "ice maker", "fridge"]),
        ("export_supply", ["export", "oem", "odm", "private label", "imp.&exp", "imp & exp", "import and export"]),
    ]
    for cat, keys in mapping:
        if any(k in blob for k in keys):
            cats.add(cat)
    if not cats:
        cats.add("home_appliance")
    return sorted(cats)


def infer_type(text: str, default: str = "manufacturer") -> str:
    t = (text or "").lower()
    if any(x in t for x in ["factory", "manufacturing plant", "oem factory"]):
        return "factory"
    if any(x in t for x in ["wholesaler", "wholesale", "distributor", "dealer"]):
        return "wholesaler"
    if any(x in t for x in ["importer", "importing"]):
        return "importer"
    if any(x in t for x in ["exporter", "import and export", "imp and exp", "imp.&exp", "trading company", "i/e"]):
        return "exporter"
    if "brand" in t and "oem" not in t:
        return "brand"
    if any(x in t for x in ["manufacturer", "oem", "odm", "co., ltd", "co ltd"]):
        return "manufacturer"
    return default if default in VALID_TYPES else "manufacturer"


def clean_public_contact(raw: str) -> str:
    raw = norm_space(raw)
    if not raw or raw.lower() in {"unknown", "n/a", "na", "-"}:
        return ""
    emails = re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", raw)
    phones = re.findall(r"\+?\d[\d\-\s()]{6,}\d", raw)
    parts = []
    for e in emails:
        el = e.lower()
        local = el.split("@")[0]
        if local in {"info", "sales", "export", "b2b", "wholesale", "contact", "service",
                     "customerservice", "support", "oem", "odm", "enquiry", "inquiry"} or any(
            x in local for x in ("sales", "export", "info", "b2b", "wholesale", "oem")
        ):
            parts.append(e)
        elif not el.endswith(("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@icloud.com")):
            parts.append(e)
    for ph in phones[:2]:
        parts.append(norm_space(ph))
    out, seen = [], set()
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower()); out.append(p)
    return "; ".join(out)


def platforms_from(website: str, source_url: str, extra=None) -> list[str]:
    plats = set(extra or [])
    for u in (website, source_url):
        d = domain_of(u)
        if "alibaba.com" in d:
            plats.add("alibaba")
        if "1688.com" in d:
            plats.add("1688")
        if "made-in-china.com" in d:
            plats.add("made_in_china")
        if "linkedin.com" in d:
            plats.add("linkedin")
        if "google." in d and "maps" in (u or "").lower():
            plats.add("google_maps")
    if website and domain_of(website) and not is_marketplace(domain_of(website)):
        plats.add("official_site")
    if not plats:
        plats.add("directory")
    return sorted(plats)


class MerchantDB:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.seen = set()
        for r in self.rows:
            self.seen.add(dedupe_key(r.get("name", ""), r.get("website", "")))
        self.stats = Counter()
        self.by_source_added = Counter()

    def add(self, *, name, type_, region, website="", public_contact="", categories=None,
            platforms=None, source_url="", tags=None, notes="", related_channel="",
            hs_codes=None, trade_role="", source_tag=""):
        name = norm_space(name)
        if not name or len(name) < 2:
            return False
        low = name.lower()
        if low in {"n/a", "na", "company", "manufacturer", "suppliers", "firma", "stand",
                   "overview", "exhibitors", "membership", "log in", "search", "tickets"}:
            return False
        # skip chambers / pure orgs without product fit unless association tag
        if "chamber of commerce" in low and source_tag != "association":
            return False
        if type_ not in VALID_TYPES:
            type_ = infer_type(type_ + " " + notes + " " + name, "manufacturer")
        if re.search(r"Imp(?:ort)?\.?\s*&?\s*Exp|Import and Export|Import & Export|I/E Co", name, re.I):
            type_ = "exporter"
        website = norm_space(website)
        if website and not website.startswith("http"):
            website = "https://" + website
        key = dedupe_key(name, website)
        if not key:
            return False
        if key in self.seen:
            # enrich tags on existing
            for r in self.rows:
                if dedupe_key(r.get("name", ""), r.get("website", "")) == key:
                    tset = set(r.get("tags") or [])
                    if source_tag:
                        tset.add(f"source:{source_tag}")
                    for t in (tags or []):
                        tset.add(t)
                    r["tags"] = sorted(tset)
                    if categories:
                        cset = set(r.get("categories") or []); cset.update(categories)
                        r["categories"] = sorted(cset)
                    self.stats["enriched"] += 1
                    return False
            return False
        self.seen.add(key)
        cats = categories or cats_from_text(name, notes, source_url)
        tset = set(tags or [])
        tset.add("route:b2b_merchant")
        tset.add(type_)
        tset.update(cats)
        if source_tag:
            tset.add(f"source:{source_tag}")
        if related_channel:
            tset.add("channel_overlap")
        row = {
            "name": name,
            "type": type_,
            "region": region or "Unknown",
            "website": website,
            "public_contact": clean_public_contact(public_contact),
            "categories": sorted(set(cats)),
            "platforms": platforms or platforms_from(website, source_url),
            "source_url": source_url or website,
            "tags": sorted(tset),
            "notes": notes[:320],
            "related_channel": related_channel or "",
            "hs_codes": list(hs_codes or []),
            "trade_role": trade_role or "",
        }
        self.rows.append(row)
        self.stats["added"] += 1
        if source_tag:
            self.by_source_added[source_tag] += 1
        return True


def retag_existing(db: MerchantDB):
    """Ensure existing rows carry source:* tags where we can infer."""
    for r in db.rows:
        tags = set(r.get("tags") or [])
        plats = set(r.get("platforms") or [])
        src = (r.get("source_url") or "").lower()
        notes = (r.get("notes") or "").lower()
        if "customs_source" in tags or any(p.startswith("customs") for p in plats) or "importyeti" in src or "importdoor" in src or "zauba" in src:
            tags.add("source:customs")
        if "made_in_china" in tags or "made-in-china" in src or "made_in_china" in plats:
            tags.add("source:mic")
        if "google_maps" in tags or "google_maps" in plats or "maps public" in notes:
            tags.add("source:maps")
        if "from_channels" in tags or "channel_overlap" in tags or "brand_channel" in tags:
            tags.add("source:channel")
        if "curated_public" in tags and "source:channel" not in tags and "source:mic" not in tags:
            tags.add("source:channel")  # curated seeds treated as channel/brand seeds
        if "alibaba" in plats or "alibaba.com" in src:
            tags.add("source:alibaba")
        if "1688" in plats or "1688.com" in src:
            tags.add("source:1688")
        if "linkedin" in plats or "linkedin.com" in src:
            tags.add("source:linkedin")
        r["tags"] = sorted(tags)


def ingest_maps(db: MerchantDB):
    paths = [
        ROOT / "portable-ac-maps-leads-uk-de.csv",
        ROOT / "portable-ac-maps-leads-nl-us.csv",
        RAW / "maps" / "portable-ac-maps-leads-uk-de.csv",
        RAW / "maps" / "portable-ac-maps-leads-nl-us.csv",
    ]
    # de-dupe path list while preserving order
    seen_paths, uniq = set(), []
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        uniq.append(path)
    paths = uniq
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                name = r.get("company") or ""
                website = r.get("website") or ""
                country = r.get("country") or ""
                city = r.get("city") or ""
                region = ", ".join(x for x in [city, country] if x)
                cat = r.get("category") or ""
                phone = r.get("phone") or ""
                emails = r.get("emails") or ""
                # keep only generic business emails
                contact = clean_public_contact("; ".join(x for x in [phone, emails] if x))
                notes = norm_space(f"Maps public listing; {cat}; {r.get('fit_note') or ''}")
                t = "wholesaler"
                cl = cat.lower()
                if "manufacturer" in cl or "factory" in cl:
                    t = "manufacturer"
                elif "import" in cl:
                    t = "importer"
                elif "brand" in cl:
                    t = "brand"
                db.add(
                    name=name, type_=t, region=region or country or "Unknown",
                    website=website, public_contact=contact,
                    categories=cats_from_text(cat, name, notes, r.get("search_string") or ""),
                    platforms=platforms_from(website, r.get("maps_url") or "", ["google_maps"]),
                    source_url=r.get("maps_url") or website,
                    tags=["google_maps", "public_listing", "eu_us_trade"],
                    notes=notes[:300],
                    source_tag="maps",
                )


def ingest_channels(db: MerchantDB):
    ch_path = HUB_PUSH / "data" / "channels.json"
    if not ch_path.exists():
        return
    channels = json.loads(ch_path.read_text())
    tmap = {
        "brand": "brand", "wholesaler": "wholesaler", "importer": "importer",
        "distributor": "wholesaler", "dealer": "wholesaler", "mod_shop": "wholesaler",
        "channel": "wholesaler",
    }
    for ch in channels:
        t = tmap.get(ch.get("type"), "wholesaler")
        db.add(
            name=ch.get("name") or "",
            type_=t,
            region=ch.get("region") or "",
            website=ch.get("website") or "",
            public_contact=ch.get("contact_email") or "",
            categories=ch.get("categories") or cats_from_text(ch.get("notes") or "", ch.get("name") or ""),
            platforms=platforms_from(ch.get("website") or "", ch.get("source_url") or ""),
            source_url=ch.get("source_url") or ch.get("website") or "",
            tags=["from_channels", "trade_channel", f"channel_type:{ch.get('type')}"],
            notes=norm_space((ch.get("notes") or "")[:240]),
            related_channel=ch.get("name") or "",
            source_tag="channel",
        )


def parse_mic_html(path: Path, category_hint: str, region_default="China"):
    html = path.read_text(errors="ignore")
    out = []
    for m in re.finditer(
        r'class="company-name-link"[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>',
        html, re.I,
    ):
        href, raw = m.group(1), m.group(2)
        name = norm_space(re.sub(r"<[^>]+>", "", raw))
        if not name:
            continue
        href = href if href.startswith("http") else ("https:" + href if href.startswith("//") else href)
        chunk = html[max(0, m.start() - 500): m.end() + 800]
        region = region_default
        rm = re.search(r"City/Province:\s*([^<\n]+)", chunk)
        if rm:
            region = "China / " + norm_space(rm.group(1))
        btype = "manufacturer"
        if re.search(r"Imp(?:ort)?\.?\s*&?\s*Exp|Import and Export|I/E Co", name, re.I):
            btype = "exporter"
        elif re.search(r"Trading Company", chunk, re.I) and not re.search(r"Manufacturer/Factory", chunk, re.I):
            btype = "exporter"
        notes = f"MIC directory; niche hint={category_hint}"
        if re.search(r"\bOEM\b|\bODM\b", chunk, re.I):
            notes += "; OEM/ODM"
        out.append({
            "name": name, "type": btype, "region": region, "website": href,
            "source_url": f"https://www.made-in-china.com/manufacturers/{category_hint}.html",
            "categories": cats_from_text(category_hint, name, chunk[:500]),
            "platforms": ["made_in_china"],
            "notes": notes,
            "tags": ["made_in_china", "public_directory", category_hint],
        })
    return out


def ingest_mic(db: MerchantDB):
    hint_map = {
        "portable-ac": "portable_ac", "portable-ac-p2": "portable_ac", "portable-ac-p3": "portable_ac",
        "portable-ac-p4": "portable_ac", "portable-ac-p5": "portable_ac",
        "space-heater": "heater", "space-heater-p2": "heater", "space-heater-p3": "heater",
        "space-heater-p4": "heater", "space-heater-p5": "heater",
        "oil-heater": "heater", "ptc-heater": "heater",
        "wine-cooler": "wine_cooler", "wine-cabinet": "wine_cooler", "beverage-cooler": "wine_cooler",
        "beverage-cooler-p2": "wine_cooler", "beverage-cooler-p3": "wine_cooler",
        "beverage-cooler-p4": "wine_cooler", "beverage-cooler-p5": "wine_cooler",
        "pet-dryer": "pet_products", "pet-feeder": "pet_products",
        "dehumidifier": "hvac", "dehumidifier-p2": "hvac", "dehumidifier-p3": "hvac",
        "dehumidifier-p4": "hvac", "dehumidifier-p5": "hvac",
        "air-conditioner": "hvac", "heat-pump": "hvac",
        "mini-fridge": "home_appliance", "ice-maker": "home_appliance",
        "mic-pac": "portable_ac", "mic-pet": "pet_products", "mic-space-heater": "heater", "mic-wine": "wine_cooler",
    }
    # root-level legacy + mic/
    files = list((RAW / "mic").glob("*.html")) + [RAW / f for f in [
        "mic-pac.html", "mic-pet.html", "mic-space-heater.html", "mic-wine.html",
        "extra_1.html", "extra_2.html", "extra_3.html", "extra_4.html", "extra_5.html",
        "extra_6.html", "extra_7.html", "extra_8.html", "extra_9.html", "extra_10.html",
        "extra_11.html", "extra_12.html", "extra_13.html", "extra_14.html", "extra_15.html", "extra_16.html",
    ] if (RAW / f).exists()]
    for path in files:
        if not path.exists() or path.stat().st_size < 5000:
            continue
        stem = path.stem
        hint = hint_map.get(stem, stem.replace("-", "_"))
        for item in parse_mic_html(path, hint):
            db.add(
                name=item["name"], type_=item["type"], region=item["region"],
                website=item["website"], categories=item["categories"],
                platforms=item["platforms"], source_url=item["source_url"],
                tags=item["tags"], notes=item["notes"], source_tag="mic",
            )


def ingest_alibaba(db: MerchantDB):
    # seed JSON
    seed = RAW / "alibaba_md" / "suppliers_seed.json"
    if seed.exists():
        data = json.loads(seed.read_text())
        for niche, names in data.items():
            for name in names:
                db.add(
                    name=name, type_="manufacturer", region="China",
                    website="", categories=cats_from_text(niche, name),
                    platforms=["alibaba"],
                    source_url=f"https://www.alibaba.com/{niche.replace('_','-')}-suppliers.html",
                    tags=["alibaba", "public_directory", niche],
                    notes=f"Alibaba public supplier listing; niche={niche}",
                    source_tag="alibaba",
                )
    # HTML pages under alibaba_md and alibaba/
    niche_from_name = {
        "pac": "portable_ac", "wine": "wine_cooler", "heater": "heater", "pet": "pet_products",
        "dehum": "hvac", "bev": "wine_cooler", "fridge": "home_appliance", "cooler": "home_appliance",
        "heatpump": "hvac",
    }
    for folder in [RAW / "alibaba_md", RAW / "alibaba"]:
        if not folder.exists():
            continue
        for path in folder.glob("*.html"):
            if path.stat().st_size < 10000:
                continue
            stem = path.stem
            niche = "home_appliance"
            for k, v in niche_from_name.items():
                if stem.startswith(k):
                    niche = v
                    break
            html = path.read_text(errors="ignore")
            if "404-Error" in html or "<title>404" in html:
                # still try company pattern
                pass
            names = re.findall(
                r">([A-Z][^<]{5,90}(?:Co\.,?\s*Ltd\.|Limited|Inc\.|Corp\.|Corporation|Factory))<",
                html,
            )
            # also ## markdown-like won't be in html
            for name in names:
                name = norm_space(name)
                if "Supplier" in name or "Alibaba" in name:
                    continue
                db.add(
                    name=name, type_=infer_type(name, "manufacturer"), region="China",
                    website="", categories=cats_from_text(niche, name),
                    platforms=["alibaba"],
                    source_url=f"https://www.alibaba.com/{path.stem}-suppliers.html",
                    tags=["alibaba", "public_directory", niche],
                    notes=f"Alibaba public supplier HTML; file={path.name}",
                    source_tag="alibaba",
                )


def ingest_1688(db: MerchantDB):
    folder = RAW / "ali1688"
    if not folder.exists():
        return
    for path in folder.glob("*.html"):
        if path.stat().st_size < 5000:
            continue
        html = path.read_text(errors="ignore")
        # company names often in Chinese; keep Latin company tokens + 公司
        names = re.findall(r">([^<>]{2,60}(?:公司|厂|有限公司|Co\.,?\s*Ltd\.))<", html)
        for name in names:
            name = norm_space(name)
            if len(name) < 3:
                continue
            db.add(
                name=name, type_="manufacturer", region="China",
                website="", categories=cats_from_text(path.stem, name),
                platforms=["1688"], source_url="https://www.1688.com/",
                tags=["1688", "public_directory"], notes=f"1688 public page snapshot; {path.name}",
                source_tag="1688",
            )


def ingest_associations(db: MerchantDB):
    # AHRI
    for fname, region, niche, src_url in [
        ("ahri.html", "United States", "hvac", "https://www.ahrinet.org/get-involved/ahri-members"),
        ("ahri2.html", "United States", "hvac", "https://www.ahrinet.org/get-involved/ahri-members"),
        ("aham.html", "United States", "home_appliance", "https://aham.org/AHAM/AHAM/AHAM_MemberPortal/Member_Directory/AHAM_Member_Directory_Public.aspx"),
    ]:
        for base in [RAW / "assoc", RAW / "assoc_md"]:
            path = base / fname
            if not path.exists():
                continue
            html = path.read_text(errors="ignore")
            text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
            text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.I)
            text = re.sub(r"<[^>]+>", "\n", text)
            lines = [norm_space(l) for l in text.splitlines() if l.strip()]
            for line in lines:
                if not re.search(r"\b(Inc\.?|LLC|Ltd\.?|Corporation|Company|Co\.|Products|GmbH|PLC|LP)\b", line):
                    continue
                if len(line) < 4 or len(line) > 120:
                    continue
                if any(x in line.lower() for x in ["scholarship", "log in", "advocacy", "certification", "membership", "directory", "privacy", "cookie"]):
                    continue
                t = "manufacturer"
                if "distributor" in line.lower() or "wholesale" in line.lower():
                    t = "wholesaler"
                db.add(
                    name=line, type_=t, region=region,
                    website="", categories=cats_from_text(niche, line),
                    platforms=["association_directory"],
                    source_url=src_url,
                    tags=["association", "public_member_directory", niche],
                    notes=f"Public association member directory ({fname})",
                    source_tag="association",
                )


def pdf_text(path: Path) -> str:
    try:
        r = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, timeout=60)
        return r.stdout or ""
    except Exception:
        return ""


def ingest_trade_shows(db: MerchantDB):
    # Canton Fair PDF
    canton_pdf = RAW / "shows" / "canton_intl_pavilion.pdf"
    if canton_pdf.exists():
        text = pdf_text(canton_pdf)
        # company lines often before booth like 2.1A01
        for line in text.splitlines():
            line = norm_space(line)
            if not line or line.lower().startswith("company name") or "booth" in line.lower() and len(line) < 20:
                continue
            # strip trailing booth numbers
            name = re.sub(r"\s+\d+\.\d+[A-Z]\d+.*$", "", line)
            name = re.sub(r"\s{2,}\S*$", "", name) if re.search(r"\d+\.\d+[A-Z]", line) else name
            # better: remove booth tokens
            name = re.sub(r"\s+\d+\.\d+[A-Z0-9,\-\s]+$", "", line)
            name = norm_space(name)
            if len(name) < 4 or len(name) > 100:
                continue
            if not re.search(r"[A-Za-z]{3,}", name):
                continue
            if name.lower() in {"the list of companies for phase 1 of the 138th canton fair international pavilion"}:
                continue
            db.add(
                name=name, type_=infer_type(name, "manufacturer"), region="International / Canton Fair",
                website="", categories=cats_from_text("home_appliance", "hvac", name),
                platforms=["trade_show"],
                source_url="https://cmsfile.cantonfair.org.cn/",
                tags=["trade_show", "canton_fair", "exhibitor"],
                notes="Canton Fair Phase 1 International Pavilion public exhibitor PDF",
                source_tag="trade_show",
            )

    # Canton HEA names txt / html
    hea_txt = RAW / "shows_md" / "canton_hea_names.txt"
    if hea_txt.exists():
        for line in hea_txt.read_text().splitlines():
            name = norm_space(line)
            if not name:
                continue
            region = "China"
            db.add(
                name=name, type_=infer_type(name, "manufacturer"), region=region,
                website="", categories=cats_from_text("home_appliance", "hvac", "wine_cooler", name),
                platforms=["trade_show"],
                source_url="https://cantonfair.co/139/categories/household-electrical-appliances",
                tags=["trade_show", "canton_fair", "household_electrical"],
                notes="Canton Fair household electrical appliances public exhibitor category",
                source_tag="trade_show",
            )

    # Ambiente PDF
    for pdf_name in ["ambiente2026.pdf", "ambiente2026b.pdf"]:
        pdf = RAW / "shows" / pdf_name
        if not pdf.exists():
            continue
        text = pdf_text(pdf)
        for line in text.splitlines():
            line = norm_space(line)
            if not line or line.lower() in {"firma", "stand", "ambiente", "frankfurt / main"}:
                continue
            if re.match(r"^HALLE\b", line, re.I) or re.match(r"^(INTERIORS|COOK|MODERN|GIFTS|HORECA|TABLE|URBAN)\b", line, re.I):
                continue
            # "Company  StandCode" patterns
            m = re.match(r"^(.+?)\s{1,}([A-Z]\s?\d{1,3})\s*$", line)
            if m:
                name = norm_space(m.group(1))
            else:
                # line may be just company
                if re.search(r"\b(GmbH|AG|Ltd|Inc|NV|Co\.|Collection|Products|Design)\b", line) or (
                    len(line) > 3 and not re.search(r"^\d", line) and "Stand" not in line
                ):
                    name = re.sub(r"\s+[A-Z]\s?\d{1,3}\s*$", "", line)
                    name = norm_space(name)
                else:
                    continue
            if len(name) < 3 or len(name) > 80:
                continue
            if name.lower() in {"firma", "stand"}:
                continue
            db.add(
                name=name, type_="brand", region="Germany / EU · Ambiente",
                website="", categories=cats_from_text("home_appliance", name),
                platforms=["trade_show"],
                source_url="https://ambiente.messefrankfurt.com/",
                tags=["trade_show", "ambiente", "exhibitor"],
                notes="Ambiente Frankfurt public exhibitor press list PDF",
                source_tag="trade_show",
            )

    # Hardware Fair HTML
    hf = RAW / "shows_md" / "hardware_fair.html"
    if hf.exists():
        html = hf.read_text(errors="ignore")
        text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
        text = re.sub(r"<[^>]+>", "\n", text)
        for line in text.splitlines():
            line = norm_space(line)
            m = re.match(r"^(.+?)\s*\|\s*(Taiwan|China|Germany|USA|Italy|Japan|India|.+)$", line)
            if not m:
                continue
            name, region = norm_space(m.group(1)), norm_space(m.group(2))
            if len(name) < 3:
                continue
            db.add(
                name=name, type_="manufacturer", region=region,
                website="", categories=["home_appliance", "export_supply"],
                platforms=["trade_show"],
                source_url="https://www.eisenwarenmesse.com/eisenwarenmesse-exhibitors/",
                tags=["trade_show", "hardware_fair", "exhibitor"],
                notes="International Hardware Fair Cologne public exhibitor list",
                source_tag="trade_show",
            )


def ingest_linkedin(db: MerchantDB):
    path = RAW / "linkedin" / "crustdata_companies.json"
    if not path.exists():
        return
    rows = json.loads(path.read_text())
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = r.get("name") or ""
        website = r.get("website") or ""
        linkedin = r.get("linkedin") or ""
        desc = r.get("description") or ""
        country = r.get("country") or ""
        query = r.get("query") or ""
        # skip pure logistics / exhibition equipment unless niche in desc
        blob = f"{name} {desc} {query}".lower()
        if any(x in blob for x in ["freight forward", "shipping line", "bank ", "law firm"]):
            continue
        t = infer_type(blob, "manufacturer")
        if "distributor" in blob or "wholesaler" in blob:
            t = "wholesaler"
        if "brand" in blob and "oem" not in blob:
            t = "brand"
        db.add(
            name=name, type_=t, region=country or "Unknown",
            website=website,
            public_contact="",
            categories=cats_from_text(desc, query, name),
            platforms=platforms_from(website, linkedin, ["linkedin"] if linkedin else []),
            source_url=linkedin or website or "",
            tags=["linkedin", "crustdata_company_search"],
            notes=norm_space(f"LinkedIn-indexed company · {desc[:200]}")[:320],
            source_tag="linkedin",
        )


def merge_customs(db: MerchantDB):
    try:
        from expand_merchants_customs import parse_customs_dir, merge_customs as mc
    except Exception as e:
        print("customs_import_fail", e)
        return
    customs = parse_customs_dir(RAW / "customs")
    if not customs:
        print("customs_empty")
        return
    before = len(db.rows)
    merged, report = mc(db.rows, customs)
    # ensure source:customs tag
    for r in merged:
        tags = set(r.get("tags") or [])
        if "customs_source" in tags or r.get("hs_codes"):
            tags.add("source:customs")
            r["tags"] = sorted(tags)
    db.rows = merged
    db.seen = {dedupe_key(r.get("name", ""), r.get("website", "")) for r in db.rows}
    added = len(db.rows) - before
    if added > 0:
        db.by_source_added["customs"] += added
    db.stats["customs_report"] = report
    print("customs_merge", report)


def write_merchants(rows, json_path: Path, csv_path: Path):
    fields = [
        "name", "type", "region", "website", "public_contact",
        "categories", "platforms", "source_url", "tags", "notes", "related_channel",
        "hs_codes", "trade_role",
    ]
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, "") for k in fields}
            row["categories"] = "|".join(r.get("categories") or [])
            row["platforms"] = "|".join(r.get("platforms") or [])
            row["tags"] = "|".join(r.get("tags") or [])
            row["hs_codes"] = "|".join(r.get("hs_codes") or [])
            w.writerow(row)


def source_counts(rows):
    c = Counter()
    for r in rows:
        tags = r.get("tags") or []
        hit = False
        for t in tags:
            if t.startswith("source:"):
                c[t] += 1
                hit = True
        if not hit:
            c["source:unset"] += 1
    return dict(c)


def main():
    src = HUB_PUSH / "data" / "merchants.json"
    if not src.exists():
        src = ROOT / "merchants.json"
    before_rows = json.loads(src.read_text())
    before_n = len(before_rows)
    before_by_source = source_counts(before_rows)

    db = MerchantDB(before_rows)
    retag_existing(db)

    ingest_maps(db)
    ingest_channels(db)
    ingest_mic(db)
    ingest_alibaba(db)
    ingest_1688(db)
    ingest_associations(db)
    ingest_trade_shows(db)
    ingest_linkedin(db)
    merge_customs(db)

    type_rank = {
        "factory": 0, "manufacturer": 1, "exporter": 2, "importer": 3,
        "brand": 4, "wholesaler": 5, "b2b_store": 6,
    }
    db.rows.sort(key=lambda r: (type_rank.get(r.get("type"), 9), (r.get("name") or "").lower()))

    for base in [HUB_PUSH / "data", HUB / "data", ROOT]:
        write_merchants(db.rows, base / "merchants.json", base / "merchants.csv")

    # sync scripts into hub-push for daily reuse
    scripts_dir = HUB_PUSH / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    for script in ["expand_merchants_multisource.py", "expand_merchants_customs.py", "build_merchants.py"]:
        src_p = ROOT / script
        if src_p.exists():
            (scripts_dir / script).write_text(src_p.read_text())
            if (HUB / "scripts").exists():
                (HUB / "scripts" / script).write_text(src_p.read_text())

    after_by_source = source_counts(db.rows)
    report = {
        "before": before_n,
        "after": len(db.rows),
        "net_new": len(db.rows) - before_n,
        "stats": dict(db.stats),
        "added_by_source_tag": dict(db.by_source_added),
        "before_by_source_tag": before_by_source,
        "after_by_source_tag": after_by_source,
        "by_type": dict(Counter(r.get("type") for r in db.rows)),
        "with_website": sum(1 for r in db.rows if r.get("website")),
        "with_hs": sum(1 for r in db.rows if r.get("hs_codes")),
        "blockers": [
            "Alibaba supplier pages often 404/JS-shell via plain curl; used WebFetch + HTML regex where available",
            "1688 public search pages thin/blocked in this environment",
            "CES 2026 GitHub raw JSON 404; skipped",
            "Apollo mixed_companies_search skipped (requires per-credit user confirmation)",
            "Apify monthly credits previously exhausted — not used this run",
            "Some association/trade-show pages 403/login-walled (HARDI/ACCA)",
        ],
    }
    (ROOT / "merchants-multisource-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    (HUB_PUSH / "merchants-multisource-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
