#!/usr/bin/env python3
"""Build initial B2B merchants dataset for gtm-creator-hub."""
from __future__ import annotations
import csv, json, re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/workspace")
HUB = ROOT / "gtm-creator-hub"
HUB_PUSH = ROOT / "gtm-creator-hub-push"
RAW = ROOT / "raw_lists_merchants"
RAW.mkdir(exist_ok=True)

VALID_TYPES = {
    "manufacturer", "factory", "wholesaler", "brand", "exporter", "b2b_store", "importer"
}

def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

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

MARKETPLACE_DOMAINS = {
    "alibaba.com", "1688.com", "made-in-china.com", "globalsources.com",
    "amazon.com", "business.amazon.com", "google.com", "google.co.uk",
    "google.de", "google.nl", "google.fr", "ec21.com",
}

def is_marketplace(host: str) -> bool:
    if not host:
        return False
    return any(host == m or host.endswith("." + m) for m in MARKETPLACE_DOMAINS)

def dedupe_key(name: str, website: str) -> str:
    d = domain_of(website)
    n = re.sub(r"[^a-z0-9]+", "", (name or "").lower())
    # Marketplace / directory hosts often list many sellers on one domain — keep name.
    if is_marketplace(d) or d.endswith(".made-in-china.com") or "en.made-in-china.com" in d:
        return f"{d}::{n}" if n else d
    return d or n

def clean_public_contact(raw: str) -> str:
    """Keep only clearly public business contacts; drop personal enrichment."""
    raw = norm_space(raw)
    if not raw or raw.lower() in {"unknown", "n/a", "na", "-"}:
        return ""
    # drop phrases that look like private CRM enrichment notes
    if "use website contact" in raw.lower() and "@" not in raw:
        return ""
    # Prefer emails / phones / published form hints; strip personal names where possible
    emails = re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", raw)
    phones = re.findall(r"\+?\d[\d\-\s()]{6,}\d", raw)
    parts = []
    for e in emails:
        el = e.lower()
        # skip likely personal Gmail etc unless company domain later; keep generic sales@
        local = el.split("@")[0]
        if local in {"info", "sales", "export", "b2b", "wholesale", "contact", "service",
                     "customerservice", "support", "oem", "odm", "enquiry", "inquiry",
                     "marketing", "biz", "business", "trade", "asst"} or any(
            x in local for x in ("sales", "export", "info", "b2b", "wholesale", "oem")
        ):
            parts.append(e)
        elif not el.endswith(("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@icloud.com")):
            parts.append(e)
    for ph in phones[:2]:
        parts.append(norm_space(ph))
    # keep short published hints without personal names
    if not parts and ("官网" in raw or "contact" in raw.lower() or "directory" in raw.lower()):
        # strip personal-looking "Name: Foo"
        cleaned = re.sub(r"(General Manager|Sales Manager|Mr\.|Ms\.|Contact Person)[:：].*", "", raw, flags=re.I)
        cleaned = norm_space(cleaned)
        if 3 < len(cleaned) < 120:
            parts.append(cleaned)
    # dedupe preserve order
    out, seen = [], set()
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower()); out.append(p)
    return "; ".join(out)

def infer_type(text: str, default: str = "manufacturer") -> str:
    t = (text or "").lower()
    if any(x in t for x in ["factory", "manufacturing plant", "oem factory", "odm factory"]):
        return "factory"
    if any(x in t for x in ["wholesaler", "wholesale", "distributor wholesale", "b2b wholesale"]):
        return "wholesaler"
    if any(x in t for x in ["exporter", "import and export", "imp and exp", "import & export", "imp. and exp", "i/e", "trading company"]):
        if any(x in t for x in ["export", "imp and", "imp.", "import", "trading"]):
            return "exporter"
    if any(x in t for x in ["b2b store", "alibaba store", "1688", "showroom", "marketplace"]):
        return "b2b_store"
    if "brand" in t and "oem" not in t:
        return "brand"
    if any(x in t for x in ["manufacturer", "factory & trading", "manufacturer/factory", "oem", "odm"]):
        return "manufacturer"
    return default if default in VALID_TYPES else "manufacturer"

def cats_from_text(*parts) -> list[str]:
    blob = " ".join(p or "" for p in parts).lower()
    cats = set()
    mapping = [
        ("portable_ac", ["portable ac", "portable air", "mobile air conditioner", "spot cooler", "portable_ac", "pac"]),
        ("hvac", ["hvac", "air conditioner", "air conditioning", "dehumidifier", "heat pump", "vrf", "chiller"]),
        ("wine_cooler", ["wine cooler", "wine cabinet", "wine fridge", "wine refrigerator", "beverage cooler", "wine_cooler"]),
        ("heater", ["space heater", "oil heater", "ptc heater", "electric heater", "infrared heater", "parking heater", "heater"]),
        ("pet_products", ["pet ", "pet-", "petkit", "pet feeder", "pet dryer", "pet products", "pet_products"]),
        ("home_appliance", ["home appliance", "household", "appliance", "mini fridge", "air cooler", "fan "]),
        ("export_supply", ["export", "oem", "odm", "private label", "live commerce", "tiktok shop supply"]),
    ]
    for cat, keys in mapping:
        if any(k in blob for k in keys):
            cats.add(cat)
    if not cats:
        cats.add("home_appliance")
    return sorted(cats)

def platforms_from(website: str, source_url: str, extra=None) -> list[str]:
    plats = set(extra or [])
    for u in (website, source_url):
        d = domain_of(u)
        if "alibaba.com" in d or d.endswith("alibaba.com"):
            plats.add("alibaba")
        if "1688.com" in d:
            plats.add("1688")
        if "made-in-china.com" in d:
            plats.add("made_in_china")
        if "globalsources.com" in d:
            plats.add("global_sources")
        if "amazon." in d:
            plats.add("amazon")
        if "globalspec" in d:
            plats.add("globalspec")
    if website and domain_of(website) and "made-in-china" not in domain_of(website):
        plats.add("official_site")
    if not plats:
        plats.add("directory")
    return sorted(plats)

class MerchantDB:
    def __init__(self):
        self.rows = []
        self.seen = set()

    def add(self, *, name, type_, region, website="", public_contact="", categories=None,
            platforms=None, source_url="", tags=None, notes="", related_channel=""):
        name = norm_space(name)
        if not name or len(name) < 2:
            return False
        # skip obvious non-companies
        low = name.lower()
        if low in {"n/a", "na", "company", "manufacturer", "suppliers"}:
            return False
        if type_ not in VALID_TYPES:
            type_ = infer_type(type_ + " " + notes, "manufacturer")
        # name-based exporter nudge (public I/E trading houses)
        if re.search(r"Imp(?:ort)?\.?\s*&?\s*Exp|Import and Export|Import & Export", name, re.I):
            type_ = "exporter"
        website = norm_space(website)
        if website and not website.startswith("http"):
            website = "https://" + website
        key = dedupe_key(name, website)
        if not key or key in self.seen:
            return False
        self.seen.add(key)
        cats = categories or cats_from_text(name, notes, source_url)
        tags = set(tags or [])
        tags.add("route:b2b_merchant")
        tags.add(type_)
        tags.update(cats)
        if related_channel:
            tags.add("channel_overlap")
        row = {
            "name": name,
            "type": type_,
            "region": region or "Unknown",
            "website": website,
            "public_contact": clean_public_contact(public_contact),
            "categories": sorted(set(cats)),
            "platforms": platforms or platforms_from(website, source_url),
            "source_url": source_url or website,
            "tags": sorted(tags),
            "notes": notes,
            "related_channel": related_channel or "",
            "hs_codes": [],
            "trade_role": "",
        }
        self.rows.append(row)
        return True

def parse_mic_html(path: Path, category_hint: str, region_default="China"):
    html = path.read_text(errors="ignore")
    out = []
    # Primary: company-name blocks with optional storefront href
    for m in re.finditer(
        r'class="company-name-link"[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>',
        html, re.I,
    ):
        href, raw = m.group(1), m.group(2)
        name = norm_space(re.sub(r"<[^>]+>", "", raw))
        if not name:
            continue
        href = href if href.startswith("http") else ("https:" + href if href.startswith("//") else href)
        # region near company card
        chunk = html[max(0, m.start()-500): m.end()+800]
        region = region_default
        rm = re.search(r"City/Province:\s*([^<\n]+)", chunk)
        if rm:
            region = "China / " + norm_space(rm.group(1))
        btype = "manufacturer"
        if re.search(r"Imp(?:ort)?\.?\s*&?\s*Exp|Import and Export|I/E Co", name, re.I):
            btype = "exporter"
        elif re.search(r"Trading Company", chunk, re.I) and not re.search(r"Manufacturer/Factory", chunk, re.I):
            btype = "exporter"
        elif re.search(r"Manufacturer/Factory\s*&\s*Trading", chunk, re.I):
            btype = "manufacturer"
        elif re.search(r"Manufacturer/Factory", chunk, re.I):
            btype = "manufacturer"
        elif re.search(r"Trading Company", chunk, re.I):
            btype = "exporter"
        notes = f"MIC directory; niche hint={category_hint}"
        if re.search(r"\bOEM\b|\bODM\b", chunk, re.I):
            notes += "; OEM/ODM"
            btype = "manufacturer" if btype != "exporter" else btype
        out.append({
            "name": name,
            "type": btype,
            "region": region,
            "website": href,
            "source_url": f"https://www.made-in-china.com/manufacturers/{category_hint}.html",
            "categories": cats_from_text(category_hint, name, chunk[:500]),
            "platforms": ["made_in_china"],
            "notes": notes,
            "tags": ["made_in_china", "public_directory", category_hint],
        })
    # Fallback: alt logos
    if len(out) < 5:
        for alt in re.findall(r'alt="([^"]{5,120})"', html):
            if re.search(r"(Co\.|Ltd|Limited|Inc|Corp|Factory|Technology|Appliance|Electric)", alt, re.I):
                out.append({
                    "name": norm_space(alt),
                    "type": "manufacturer",
                    "region": region_default,
                    "website": "",
                    "source_url": f"https://www.made-in-china.com/manufacturers/{category_hint}.html",
                    "categories": cats_from_text(category_hint, alt),
                    "platforms": ["made_in_china"],
                    "notes": f"MIC alt listing; niche hint={category_hint}",
                    "tags": ["made_in_china", "public_directory", category_hint],
                })
    return out

# ---- curated public seeds (well-known B2B / OEM / brand / exporter / stores) ----
CURATED = [
    # Portable AC / HVAC brands & factories
    ("Midea Group", "brand", "China", "https://www.midea.com/", "", ["portable_ac","hvac","home_appliance"], ["official_site"], "https://www.midea.com/us/air-conditioners/portable-air-conditioners", ["brand","hvac"], "Major home appliance OEM/OBM; portable AC lines"),
    ("Gree Electric", "brand", "China", "https://global.gree.com/", "", ["portable_ac","hvac","home_appliance"], ["official_site"], "https://global.gree.com/", ["brand","hvac"], "Global HVAC brand with portable/window lines"),
    ("Haier / Candy", "brand", "China/Italy", "https://www.haier.com/", "", ["portable_ac","home_appliance","wine_cooler"], ["official_site"], "https://www.haier.com/", ["brand"], "Global appliance group; cooling & wine storage"),
    ("Hisense", "brand", "China", "https://global.hisense.com/", "", ["portable_ac","hvac","home_appliance"], ["official_site"], "https://global.hisense.com/", ["brand"], "Appliance/HVAC brand exporter"),
    ("AUX Group", "brand", "China", "https://www.auxgroup.com/", "", ["portable_ac","hvac"], ["official_site"], "https://www.auxgroup.com/", ["brand","manufacturer"], "HVAC manufacturer/brand"),
    ("TCL", "brand", "China", "https://www.tcl.com/", "", ["portable_ac","home_appliance"], ["official_site"], "https://www.tcl.com/", ["brand"], "Appliance brand with AC lines"),
    ("Chigo / Guangdong Chigo", "manufacturer", "China", "https://www.chigo.cn/", "", ["portable_ac","hvac"], ["official_site"], "https://www.chigo.cn/", ["manufacturer","oem"], "HVAC manufacturer"),
    ("Jiangsu Youao / Shinco", "manufacturer", "China", "http://www.yoau.cn/", "sales@yoau.com.cn; 400-1890-315", ["portable_ac","hvac","export_supply"], ["official_site"], "http://www.yoau.cn/about/", ["oem","exporter"], "Portable AC/dehumidifier specialist OEM/export"),
    ("Dongguan Jinhongsheng (JHS)", "factory", "China", "https://gb.jhs8.com/", "sales10@jhs8.com", ["portable_ac","export_supply"], ["official_site"], "https://gb.jhs8.com/", ["oem","factory"], "Major China portable-AC OEM/export factory"),
    ("Olimpia Splendid", "brand", "Italy", "https://www.olimpiasplendid.com/", "customerservice@olimpiasplendidusa.com", ["portable_ac","hvac"], ["official_site"], "https://www.olimpiasplendid.com/", ["brand","eu"], "EU portable AC brand Dolceclima"),
    ("Argoclima / Argo", "brand", "Italy", "https://www.argoclima.com/", "", ["portable_ac","hvac"], ["official_site"], "https://www.argoclima.com/en/categoria/single-duct-portable-airconditioners/", ["brand","oem"], "IT brand; OEM engineering claimed"),
    ("Toyotomi Europe", "brand", "Japan/Netherlands", "https://www.toyotomi.eu/", "", ["portable_ac","heater","hvac"], ["official_site"], "https://www.toyotomi.eu/about-us/", ["brand"], "Portable AC + heaters EU subsidiaries"),
    ("PVG / Qlima", "brand", "Netherlands", "https://www.qlima.com/", "", ["portable_ac","heater"], ["official_site"], "https://www.pvg.eu/our-brands", ["brand","eu"], "EU mobile climate brand owner"),
    ("UnitedStar", "manufacturer", "China", "https://www.unitedstar.com.cn/", "asst@unitedstar.com.cn", ["portable_ac","home_appliance","export_supply"], ["official_site"], "https://www.unitedstar.com.cn/ifa-ac/", ["oem","odm","factory"], "R290 portable AC OEM/ODM factory Zhongshan"),
    ("Yoozor", "manufacturer", "China", "https://yoozor.com/", "", ["portable_ac","hvac","export_supply"], ["official_site"], "https://yoozor.com/cn/", ["oem","exporter"], "Ningbo portable AC & dehumidifier OEM"),
    ("Foshan Zhenghe / Zhengxi", "factory", "China", "https://zhengheac.en.made-in-china.com/", "", ["portable_ac","export_supply"], ["made_in_china"], "https://zhengheac.en.made-in-china.com/", ["oem","odm","factory"], "Portable/camping AC manufacturer Foshan"),
    ("PortableACManufacturer.com (SZ OEM)", "manufacturer", "China", "https://www.portableacmanufacturer.com/", "sales@portableacmanufacturer.com", ["portable_ac","export_supply"], ["official_site"], "https://www.portableacmanufacturer.com/", ["oem","odm"], "Shenzhen portable AC OEM site"),
    ("Blueway", "manufacturer", "China", "https://www.blueway.com.cn/", "", ["portable_ac","hvac"], ["official_site"], "https://www.blueway.com.cn/", ["oem"], "Climate appliance manufacturer"),
    ("De'Longhi", "brand", "Italy", "https://www.delonghi.com/", "", ["portable_ac","heater","home_appliance"], ["official_site"], "https://www.delonghi.com/", ["brand"], "Portable AC & heaters brand"),
    ("Honeywell Home / Resideo (climate SKUs)", "brand", "United States", "https://www.honeywellhome.com/", "", ["portable_ac","heater"], ["official_site"], "https://www.honeywellhome.com/", ["brand"], "Climate comfort brand umbrella"),
    ("Whynter", "brand", "United States", "https://www.whynter.com/", "", ["portable_ac","wine_cooler"], ["official_site"], "https://www.whynter.com/", ["brand"], "US portable AC & wine cooler brand"),
    ("Black+Decker (appliances license)", "brand", "United States", "https://www.blackanddecker.com/", "", ["portable_ac","home_appliance"], ["official_site"], "https://www.blackanddecker.com/", ["brand"], "Portable AC / appliance brand lines"),
    ("LG Electronics", "brand", "South Korea", "https://www.lg.com/", "", ["portable_ac","hvac","home_appliance","wine_cooler"], ["official_site"], "https://www.lg.com/", ["brand"], "Global appliance/HVAC"),
    ("Samsung Electronics", "brand", "South Korea", "https://www.samsung.com/", "", ["hvac","home_appliance","wine_cooler"], ["official_site"], "https://www.samsung.com/", ["brand"], "Global appliance"),
    ("Daikin", "brand", "Japan", "https://www.daikin.com/", "", ["hvac"], ["official_site"], "https://www.daikin.com/", ["brand"], "HVAC manufacturer/brand"),
    ("Mitsubishi Electric", "brand", "Japan", "https://www.mitsubishielectric.com/", "", ["hvac"], ["official_site"], "https://www.mitsubishielectric.com/", ["brand"], "HVAC manufacturer/brand"),
    ("Carrier / Toshiba Carrier", "brand", "United States", "https://www.carrier.com/", "", ["hvac","portable_ac"], ["official_site"], "https://www.carrier.com/", ["brand"], "HVAC group"),
    ("Electrolux / Frigidaire", "brand", "Sweden/United States", "https://www.electrolux.com/", "", ["portable_ac","home_appliance","wine_cooler"], ["official_site"], "https://www.electrolux.com/", ["brand"], "Appliance brands incl. portable AC"),
    ("Airwell", "brand", "France", "https://www.airwell.com/", "", ["portable_ac","hvac"], ["official_site"], "https://www.airwell.com/fr/maui/", ["brand","eu"], "FR HVAC portable monobloc"),
    ("Aosom / HOMCOM B2B", "brand", "United Kingdom/EU", "https://aosom.eu/", "", ["portable_ac","home_appliance"], ["official_site","b2b_portal"], "https://aosom.eu/pages/business-application", ["brand","wholesale"], "EU B2B wholesale portal"),
    # Wine cooler specialists
    ("Foshan Sunnai Electrical", "manufacturer", "China", "https://www.sunnai.com/", "", ["wine_cooler","export_supply"], ["official_site"], "https://www.ec21.com/companies/wine-refrigerator.html", ["oem","wine"], "Wine/beverage cooler manufacturer"),
    ("Guangdong Candor", "manufacturer", "China", "https://www.candorwinecooler.com/", "", ["wine_cooler","export_supply"], ["official_site"], "https://www.ec21.com/companies/wine-refrigerator.html", ["oem","factory"], "Built-in wine cooler manufacturer"),
    ("SICAO", "manufacturer", "China", "https://www.sicao.com/", "", ["wine_cooler"], ["official_site"], "https://www.sicao.com/", ["oem","thermoelectric"], "Semiconductor wine cooler specialist"),
    ("HONDAR / Unicave", "manufacturer", "China", "https://www.hondar.com.cn/", "", ["wine_cooler","export_supply"], ["official_site"], "https://www.company-listing.org/wine_refrigerators_in_china.html", ["oem","exporter"], "Wine cooler OEM exporter Zhongshan"),
    ("MeiHe / Meihe Appliances", "manufacturer", "China", "https://www.meihecooler.com/", "", ["wine_cooler"], ["official_site"], "https://www.company-listing.org/wine_refrigerators_in_china.html", ["oem"], "Shenzhen wine cooler manufacturer"),
    ("Guangdong Unique Appliance", "manufacturer", "China", "https://unique-appliance.en.made-in-china.com/", "", ["wine_cooler"], ["made_in_china"], "https://www.made-in-china.com/manufacturers/wine-cooler-cabinet.html", ["oem","odm"], "Wine cooler / dry ager OEM Foshan"),
    ("Foshan Shunde Wiki Electrical", "manufacturer", "China", "https://wiki-electrical.en.made-in-china.com/", "", ["wine_cooler"], ["made_in_china"], "https://www.made-in-china.com/manufacturers/wine-cooler.html", ["oem","odm"], "Wine cabinet manufacturer"),
    ("Vinotemp", "brand", "United States", "https://www.vinotemp.com/", "", ["wine_cooler"], ["official_site"], "https://www.vinotemp.com/", ["brand"], "US wine storage brand"),
    ("EuroCave", "brand", "France", "https://www.eurocave.com/", "", ["wine_cooler"], ["official_site"], "https://www.eurocave.com/", ["brand"], "Premium wine cellar brand"),
    ("NewAir", "brand", "United States", "https://www.newair.com/", "", ["wine_cooler","portable_ac","heater"], ["official_site"], "https://www.newair.com/", ["brand"], "Wine coolers + climate appliances"),
    ("EdgeStar", "brand", "United States", "https://www.edgestar.com/", "", ["wine_cooler","home_appliance"], ["official_site"], "https://www.edgestar.com/", ["brand"], "Compact fridge/wine cooler brand"),
    ("Firstcooler / First Industrial", "manufacturer", "China", "https://www.globalsources.com/", "", ["wine_cooler","export_supply"], ["global_sources"], "https://www.globalsources.com/Wine-refrigerator/Dual-zone-wine-and-beverage-cooler-1191667205p.htm", ["exporter","oem"], "Dual-zone wine/beverage cooler supplier listing"),
    ("ARTISTE TECHNOLOGY LTD.", "exporter", "China", "https://www.globalsources.com/", "", ["wine_cooler","export_supply"], ["global_sources"], "https://www.globalsources.com/Wine-refrigerator/Wine-cooler-1201282452p.htm", ["exporter"], "Wine cooler wholesale listing on Global Sources"),
    # Heaters
    ("Sunzone / Jinke", "manufacturer", "China", "https://www.sun-zone.com.cn/", "sunzone@sun-zone.com.cn", ["heater","home_appliance","export_supply"], ["official_site"], "https://www.sun-zone.com.cn/", ["oem","odm","ptc"], "PTC ceramic heater OEM for global brands"),
    ("Calorvanta Electric", "manufacturer", "China", "https://www.space-heater-manufacturers.com/", "", ["heater","export_supply"], ["official_site"], "https://www.space-heater-manufacturers.com/", ["oem","wholesale"], "Cixi space heater OEM/wholesale"),
    ("Cixi Shuangfu Electrical", "factory", "China", "https://www.shuangfuappliance.com/", "info@shuangfuappliance.com", ["heater","export_supply"], ["official_site"], "https://www.shuangfuappliance.com/", ["oem","odm","ptc"], "PTC space heater factory"),
    ("Kinscoter / Chaozhou Tongheng", "manufacturer", "China", "https://www.kinscoter.com/", "", ["heater","home_appliance","export_supply"], ["official_site"], "https://www.kinscoter.com/space-heater", ["oem","odm"], "Small appliance / space heater OEM"),
    ("Lasko", "brand", "United States", "https://www.lasko.com/", "", ["heater","home_appliance"], ["official_site"], "https://www.lasko.com/", ["brand"], "US heater/fan brand"),
    ("Vornado", "brand", "United States", "https://www.vornado.com/", "", ["heater","home_appliance"], ["official_site"], "https://www.vornado.com/", ["brand"], "US heater/fan brand"),
    ("Dyson", "brand", "United Kingdom", "https://www.dyson.com/", "", ["heater","home_appliance"], ["official_site"], "https://www.dyson.com/", ["brand"], "Premium heater/purifier brand"),
    # Pet products
    ("Petkit", "brand", "China", "https://www.petkit.com/", "", ["pet_products","export_supply"], ["official_site"], "https://www.petkit.com/", ["brand","smart_pet"], "Smart pet appliance brand"),
    ("Furbo / Tomofun", "brand", "Taiwan/global", "https://furbo.com/", "", ["pet_products"], ["official_site"], "https://furbo.com/", ["brand"], "Pet camera brand"),
    ("Xiaomi / Smart Pet ecosystem OEMs", "brand", "China", "https://www.mi.com/", "", ["pet_products","home_appliance"], ["official_site"], "https://www.mi.com/", ["brand"], "Smart home + pet device ecosystem"),
    ("Rover / pet retail B2B refs", "brand", "United States", "https://www.chewy.com/", "", ["pet_products"], ["official_site"], "https://www.chewy.com/", ["retail_brand"], "Large pet retail (buyer side reference)"),
    ("Trampolene / pet dryer OEMs cluster note", "manufacturer", "China", "https://www.alibaba.com/showroom/pet-dryer.html", "", ["pet_products","export_supply"], ["alibaba"], "https://www.alibaba.com/showroom/pet-dryer.html", ["b2b_directory"], "Alibaba pet dryer showroom entry point"),
    # B2B stores / wholesale platforms (as merchants of record for sourcing)
    ("Alibaba Portable AC Showroom", "b2b_store", "China/global", "https://www.alibaba.com/showroom/portable-air-conditioner.html", "", ["portable_ac","export_supply"], ["alibaba"], "https://www.alibaba.com/showroom/portable-air-conditioner.html", ["marketplace","sourcing"], "Public B2B showroom for portable AC suppliers"),
    ("Alibaba Wine Cooler Showroom", "b2b_store", "China/global", "https://www.alibaba.com/showroom/wine-cooler.html", "", ["wine_cooler","export_supply"], ["alibaba"], "https://www.alibaba.com/showroom/wine-cooler.html", ["marketplace","sourcing"], "Public B2B showroom"),
    ("Alibaba Space Heater Showroom", "b2b_store", "China/global", "https://www.alibaba.com/showroom/space-heater.html", "", ["heater","export_supply"], ["alibaba"], "https://www.alibaba.com/showroom/space-heater.html", ["marketplace","sourcing"], "Public B2B showroom"),
    ("Alibaba Pet Products Showroom", "b2b_store", "China/global", "https://www.alibaba.com/showroom/pet-products.html", "", ["pet_products","export_supply"], ["alibaba"], "https://www.alibaba.com/showroom/pet-products.html", ["marketplace","sourcing"], "Public B2B showroom"),
    ("1688 Home Appliance Category", "b2b_store", "China", "https://www.1688.com/", "", ["home_appliance","export_supply"], ["1688"], "https://www.1688.com/", ["marketplace","cn_wholesale"], "CN domestic B2B wholesale portal"),
    ("Made-in-China Portable AC Directory", "b2b_store", "China", "https://www.made-in-china.com/manufacturers/portable-air-conditioner.html", "", ["portable_ac"], ["made_in_china"], "https://www.made-in-china.com/manufacturers/portable-air-conditioner.html", ["directory"], "Public manufacturer directory"),
    ("Global Sources Wine Refrigerator", "b2b_store", "Hong Kong/China", "https://www.globalsources.com/", "", ["wine_cooler","export_supply"], ["global_sources"], "https://www.globalsources.com/gsol/I/Wine-refrigerator/b/2000000003844.htm", ["directory","trade_show"], "Trade directory / exhibition ecosystem"),
    ("Amazon Business Home", "b2b_store", "United States/global", "https://business.amazon.com/", "", ["home_appliance","export_supply"], ["amazon"], "https://business.amazon.com/", ["marketplace","b2b"], "B2B marketplace for appliances"),
]

MIC_FILES = [
    ("mic-pac.html", "portable-air-conditioner"),
    ("mic-pet.html", "pet-products"),
    ("mic-space-heater.html", "space-heater"),
    ("extra_3.html", "beverage-cooler"),
    ("extra_4.html", "dehumidifier"),
    ("extra_5.html", "oil-heater"),
    ("extra_6.html", "ptc-heater"),
    ("extra_7.html", "pet-feeder"),
    ("extra_8.html", "pet-dryer"),
    ("extra_9.html", "air-cooler"),
    ("extra_10.html", "home-appliance"),
    ("extra_11.html", "mini-fridge"),
    ("extra_12.html", "electric-heater"),
]

def map_category_to_type(cat: str) -> str:
    c = (cat or "").lower()
    if any(x in c for x in ["manufacturer", "factory"]):
        return "factory" if "factory" in c else "manufacturer"
    if "wholesal" in c or "supplier" in c:
        return "wholesaler"
    if "distributor" in c or "dealer" in c or "retail" in c:
        return "wholesaler"
    if "import" in c or "export" in c:
        return "exporter"
    if "brand" in c:
        return "brand"
    if "heating" in c or "air conditioning" in c or "hvac" in c:
        return "wholesaler"
    return "wholesaler"

def ingest_maps(db: MerchantDB):
    paths = [
        ROOT / "portable-ac-maps-leads-uk-de.csv",
        ROOT / "portable-ac-maps-leads-nl-us.csv",
    ]
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
                # only business phone; ignore enriched personal emails
                public = phone
                notes = norm_space(f"Maps public listing; {cat}; {r.get('fit_note') or ''}")
                db.add(
                    name=name,
                    type_=map_category_to_type(cat),
                    region=region or country or "Unknown",
                    website=website,
                    public_contact=public,
                    categories=cats_from_text(cat, name, notes),
                    platforms=platforms_from(website, r.get("maps_url") or "", ["google_maps"]),
                    source_url=r.get("maps_url") or website,
                    tags=["google_maps", "public_listing", "eu_us_trade"],
                    notes=notes[:300],
                )

def ingest_company_csvs(db: MerchantDB):
    # portable-ac-eu-us-companies.csv
    p = ROOT / "portable-ac-eu-us-companies.csv"
    if p.exists():
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                name = r.get("company_name_en") or ""
                oem = (r.get("oem_private_label") or "").lower()
                t = "manufacturer" if "yes" in oem else "brand"
                if "factory" in (r.get("why_fit") or "").lower():
                    t = "factory"
                db.add(
                    name=name,
                    type_=t,
                    region=r.get("hq_country") or "",
                    website=r.get("website") or "",
                    public_contact=r.get("contact_public") or "",
                    categories=cats_from_text("portable_ac", r.get("why_fit"), r.get("markets")),
                    platforms=platforms_from(r.get("website") or "", r.get("source_urls") or ""),
                    source_url=(r.get("source_urls") or "").split("|")[0].strip() or r.get("website") or "",
                    tags=["portable_ac_research", "prior_seed"],
                    notes=norm_space((r.get("why_fit") or "")[:280]),
                )
    p2 = ROOT / "portable-ac-eu-us-brand-channel-expanded.csv"
    if p2.exists():
        with p2.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                raw_type = (r.get("type") or "brand").lower()
                t = raw_type if raw_type in VALID_TYPES else infer_type(raw_type, "brand")
                db.add(
                    name=r.get("company") or "",
                    type_=t,
                    region=r.get("country") or "",
                    website=r.get("website") or "",
                    public_contact=r.get("contact_hint") or "",
                    categories=cats_from_text("portable_ac", r.get("notes")),
                    platforms=platforms_from(r.get("website") or "", r.get("source_url") or ""),
                    source_url=r.get("source_url") or r.get("website") or "",
                    tags=["brand_channel_expanded", "prior_seed"],
                    notes=norm_space((r.get("notes") or "")[:280]),
                )
    p3 = ROOT / "portable-ac-brand-channel.csv"
    if p3.exists():
        with p3.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                db.add(
                    name=r.get("company_name_en") or "",
                    type_="brand",
                    region=r.get("hq_country") or "",
                    website=(r.get("website") or "").split(";")[0].strip(),
                    public_contact=r.get("contact_public") or "",
                    categories=cats_from_text("portable_ac", r.get("why_fit")),
                    platforms=platforms_from(r.get("website") or "", ""),
                    source_url=(r.get("source_urls") or "").split("|")[0].strip(),
                    tags=["brand_channel", "prior_seed"],
                    notes=norm_space((r.get("why_fit") or "")[:280]),
                )

def cross_link_channels(db: MerchantDB):
    ch_path = HUB_PUSH / "data" / "channels.json"
    channels = json.loads(ch_path.read_text())
    # index merchants by domain/name
    by_domain = {}
    by_name = {}
    for i, m in enumerate(db.rows):
        d = domain_of(m["website"])
        if d:
            by_domain.setdefault(d, []).append(i)
        by_name.setdefault(re.sub(r"[^a-z0-9]+", "", m["name"].lower()), []).append(i)

    overlap = 0
    for ch in channels:
        d = domain_of(ch.get("website") or "")
        nkey = re.sub(r"[^a-z0-9]+", "", (ch.get("name") or "").lower())
        hits = []
        if d and d in by_domain:
            hits.extend(by_domain[d])
        if nkey and nkey in by_name:
            hits.extend(by_name[nkey])
        hits = sorted(set(hits))
        if hits:
            overlap += 1
            tags = set(ch.get("tags") or [])
            tags.add("merchant_db_overlap")
            tags.add("related_merchant")
            ch["tags"] = sorted(tags)
            # annotate first merchant
            m = db.rows[hits[0]]
            if not m.get("related_channel"):
                m["related_channel"] = ch["name"]
            mt = set(m.get("tags") or [])
            mt.add("channel_overlap")
            mt.add(f"channel_type:{ch.get('type')}")
            m["tags"] = sorted(mt)
            # ensure merchant exists for channel brand/wholesaler/importer if missing? already hit
        else:
            # promote clear B2B-ish channel types into merchants without silent merge
            if ch.get("type") in {"brand", "wholesaler", "importer"}:
                tmap = {"brand": "brand", "wholesaler": "wholesaler", "importer": "exporter"}
                added = db.add(
                    name=ch["name"],
                    type_=tmap[ch["type"]],
                    region=ch.get("region") or "",
                    website=ch.get("website") or "",
                    public_contact=ch.get("contact_email") or "",
                    categories=ch.get("categories") or [],
                    platforms=platforms_from(ch.get("website") or "", ch.get("source_url") or ""),
                    source_url=ch.get("source_url") or ch.get("website") or "",
                    tags=["from_channels", "cross_link"],
                    notes=norm_space((ch.get("notes") or "")[:240]),
                    related_channel=ch["name"],
                )
                if added:
                    tags = set(ch.get("tags") or [])
                    tags.add("merchant_db_overlap")
                    ch["tags"] = sorted(tags)
                    overlap += 1
    ch_path.write_text(json.dumps(channels, ensure_ascii=False, indent=2) + "\n")
    # mirror channels csv quickly
    write_channels_csv(channels, HUB_PUSH / "data" / "channels.csv")
    return overlap

def write_channels_csv(channels, path: Path):
    fields = ["name", "type", "region", "website", "contact_email", "categories", "source_url", "tags", "notes"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in channels:
            row = {k: c.get(k, "") for k in fields}
            row["categories"] = "|".join(c.get("categories") or [])
            row["tags"] = "|".join(c.get("tags") or [])
            w.writerow(row)

def write_merchants(rows, json_path: Path, csv_path: Path):
    fields = [
        "name", "type", "region", "website", "public_contact",
        "categories", "platforms", "source_url", "tags", "notes", "related_channel",
        "hs_codes", "trade_role",
    ]
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

def maybe_update_readme():
    readme = HUB_PUSH / "README.md"
    if not readme.exists():
        return
    txt = readme.read_text()
    marker = "<!-- merchants-dataset -->"
    block = (
        f"{marker}\n"
        f"- **B端商家 / merchants**: `data/merchants.json` + `data/merchants.csv` "
        f"(manufacturer / factory / wholesaler / brand / exporter / importer / b2b_store; "
        f"niches: portable AC/HVAC, wine cooler, heaters, pet, home appliances, export/live-commerce supply). "
        f"Cross-tagged with `channels.json` via `merchant_db_overlap` / `related_channel` (no silent merge).\n"
    )
    if marker in txt:
        txt = re.sub(r"<!-- merchants-dataset -->[\s\S]*?(?=\n##|\n#|$)", block, txt, count=1)
    else:
        # append under data section if present
        if "## Data" in txt:
            txt = txt.replace("## Data", "## Data\n\n" + block, 1)
        else:
            txt = txt.rstrip() + "\n\n## Data\n\n" + block + "\n"
    readme.write_text(txt)

def main():
    db = MerchantDB()

    # curated
    for name, type_, region, website, contact, cats, plats, src, tags, notes in CURATED:
        db.add(
            name=name, type_=type_, region=region, website=website,
            public_contact=contact, categories=cats, platforms=plats,
            source_url=src, tags=tags + ["curated_public"], notes=notes,
        )

    # MIC pages
    for fname, hint in MIC_FILES:
        path = RAW / fname
        if not path.exists() or path.stat().st_size < 5000:
            continue
        for item in parse_mic_html(path, hint):
            db.add(
                name=item["name"], type_=item["type"], region=item["region"],
                website=item["website"], categories=item["categories"],
                platforms=item["platforms"], source_url=item["source_url"],
                tags=item["tags"], notes=item["notes"],
            )

    ingest_company_csvs(db)
    ingest_maps(db)

    # sort: manufacturers/factories first-ish then name
    type_rank = {"factory": 0, "manufacturer": 1, "exporter": 2, "importer": 3, "brand": 4, "wholesaler": 5, "b2b_store": 6}
    db.rows.sort(key=lambda r: (type_rank.get(r["type"], 9), r["name"].lower()))

    overlap = cross_link_channels(db)

    # Public customs / trade directories incremental merge (ImportYeti / ImportDoor / Zauba HTML snapshots)
    try:
        from expand_merchants_customs import parse_customs_dir, merge_customs
        customs = parse_customs_dir(RAW / "customs")
        if customs:
            merged, creport = merge_customs(db.rows, customs)
            db.rows = merged
            db.seen = {dedupe_key(r.get("name",""), r.get("website","")) for r in db.rows}
            print("customs_merge", creport)
    except Exception as e:
        print("customs_merge_skipped", type(e).__name__, e)

    # write to push + local hub + workspace copies
    for base in [HUB_PUSH / "data", HUB / "data", ROOT]:
        base.mkdir(parents=True, exist_ok=True)
        write_merchants(db.rows, base / "merchants.json", base / "merchants.csv")
        if base == ROOT:
            # also refresh workspace channels mirror if present
            pass

    # sync channels from push to hub + workspace
    for dest in [HUB / "data", ROOT]:
        (dest / "channels.json").write_text((HUB_PUSH / "data" / "channels.json").read_text())
        (dest / "channels.csv").write_text((HUB_PUSH / "data" / "channels.csv").read_text())

    maybe_update_readme()
    # copy readme to hub
    if (HUB_PUSH / "README.md").exists() and HUB.exists():
        (HUB / "README.md").write_text((HUB_PUSH / "README.md").read_text())

    report = {
        "total": len(db.rows),
        "by_type": dict(Counter(r["type"] for r in db.rows)),
        "by_category": Counter(cat for r in db.rows for cat in r["categories"]).most_common(),
        "with_website": sum(1 for r in db.rows if r.get("website")),
        "with_public_contact": sum(1 for r in db.rows if r.get("public_contact")),
        "channel_overlap_annotations": overlap,
        "related_channel_filled": sum(1 for r in db.rows if r.get("related_channel")),
    }
    (ROOT / "merchants-build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
