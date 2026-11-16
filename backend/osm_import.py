#!/usr/bin/env python3
"""
وين؟ DZ — استيراد أماكن حقيقية من OpenStreetMap (Overpass API) لولاية واحدة.

التثبيت:   pip install requests psycopg2-binary      (psycopg2 غير لازم مع --sqlite)
PostgreSQL: python osm_import.py --wilaya 31 --pg "postgresql://user:pass@localhost/ouin"
SQLite:     python osm_import.py --wilaya 31 --sqlite ouin.db        (مناسب لـ Termux)

--wilaya = رمز الولاية (16 الجزائر، 31 وهران، 25 قسنطينة، 15 تيزي وزو، 19 سطيف...)
البيانات © مساهمو OpenStreetMap — ترخيص ODbL: يجب ذكر المصدر داخل المنصة.
"""
import argparse
import os
import sqlite3
import sys
import time

import requests

from search import is_security

TIMEOUT = int(os.environ.get("OSM_TIMEOUT", "240"))   # ثوانٍ لكل طلب
ATTEMPTS = int(os.environ.get("OSM_ATTEMPTS", "2"))

ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# وسم OSM -> قيمته -> القطاع (slug) في منصة وين؟ DZ
TAGS = {
    "amenity": {
        "pharmacy": "health", "clinic": "health", "doctors": "health",
        "dentist": "health", "hospital": "health",
        "restaurant": "food", "cafe": "food", "fast_food": "food",
        "fuel": "auto", "bank": "finance", "bureau_de_change": "finance",
        "school": "education", "university": "education", "college": "education",
        "townhall": "public", "post_office": "public", "veterinary": "agriculture", "marketplace": "shopping", "kindergarten": "education", "driving_school": "education",
    },
    "shop": {
        "car_repair": "auto", "car_parts": "auto", "supermarket": "shopping",
        "convenience": "shopping", "bakery": "shopping", "clothes": "shopping",
        "mobile_phone": "shopping", "electronics": "shopping", "agrarian": "agriculture", "butcher": "shopping", "hardware": "shopping", "travel_agency": "tourism",
    },
    "healthcare": {"laboratory": "health"},
    "craft": {"electrician": "trades", "plumber": "trades", "carpenter": "trades", "painter": "trades", "welder": "trades", "tiler": "trades", "locksmith": "trades", "tailor": "trades", "builder": "trades"},
    "office": {"estate_agent": "realestate", "insurance": "finance"},
    "tourism": {"hotel": "tourism", "guest_house": "tourism", "museum": "tourism", "attraction": "tourism"},
    "leisure": {"fitness_centre": "sport", "sports_centre": "sport", "stadium": "sport", "pitch": "sport"},
}

PG_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS places (
    osm_id text PRIMARY KEY, wilaya text, sector text, subtype text,
    name text, name_ar text, name_fr text, phone text, opening_hours text,
    website text, address text, geom geography(Point, 4326),
    updated_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS places_geom_idx ON places USING GIST (geom);
CREATE INDEX IF NOT EXISTS places_sector_idx ON places (wilaya, sector);
"""

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS places (
    osm_id TEXT PRIMARY KEY, wilaya TEXT, sector TEXT, subtype TEXT,
    name TEXT, name_ar TEXT, name_fr TEXT, phone TEXT, opening_hours TEXT,
    website TEXT, address TEXT, lat REAL, lon REAL
);
CREATE INDEX IF NOT EXISTS places_sector_idx ON places (wilaya, sector);
"""


def build_query(code, key):
    regex = "|".join(TAGS[key])
    return (
        "[out:json][timeout:180];"
        f'area["ISO3166-2"="DZ-{code}"]["boundary"="administrative"]->.a;'
        f'nwr["{key}"~"^({regex})$"](area.a);out center tags;'
    )


def fetch(query):
    headers = {"User-Agent": "ouin-dz/1.0 (https://github.com/lazhariaek25-spec/ouin-dz)", "Accept": "*/*"}
    for attempt in range(ATTEMPTS):
        for url in ENDPOINTS:
            try:
                r = requests.post(url, data={"data": query}, headers=headers, timeout=TIMEOUT)
                if r.status_code == 200:
                    return r.json()["elements"]
                print(f"    {url.split('/')[2]} -> HTTP {r.status_code}", file=sys.stderr)
            except requests.RequestException as e:
                print(f"    {url.split('/')[2]} -> {type(e).__name__}", file=sys.stderr)
        time.sleep(10)
    return None


def classify(tags):
    for key, values in TAGS.items():
        v = tags.get(key)
        if v in values:
            return values[v], v
    return None, None


def to_rows(elements, code):
    rows = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ar") or tags.get("name:fr")
        if not name:
            continue  # نتجاهل الأماكن بلا اسم
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        sector, subtype = classify(tags)
        if not sector:
            continue
        if is_security(subtype, " ".join(filter(None, [name, tags.get("name:ar"), tags.get("name:fr")]))):
            continue   # المؤسسات الأمنية مستبعدة
        addr = " ".join(
            x for x in (tags.get("addr:housenumber"), tags.get("addr:street"),
                        tags.get("addr:city")) if x
        ) or None
        rows.append((
            f'{el["type"][0]}{el["id"]}', code, sector, subtype, name,
            tags.get("name:ar"), tags.get("name:fr"),
            tags.get("phone") or tags.get("contact:phone"),
            tags.get("opening_hours"),
            tags.get("website") or tags.get("contact:website"),
            addr, float(lat), float(lon),
        ))
    return rows


def save_pg(rows, dsn):
    import psycopg2
    from psycopg2.extras import execute_batch
    with psycopg2.connect(dsn) as con, con.cursor() as cur:
        cur.execute(PG_SCHEMA)
        execute_batch(cur, """
            INSERT INTO places (osm_id, wilaya, sector, subtype, name, name_ar,
                name_fr, phone, opening_hours, website, address, geom)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography)
            ON CONFLICT (osm_id) DO UPDATE SET
                sector=EXCLUDED.sector, subtype=EXCLUDED.subtype,
                name=EXCLUDED.name, name_ar=EXCLUDED.name_ar,
                name_fr=EXCLUDED.name_fr, phone=EXCLUDED.phone,
                opening_hours=EXCLUDED.opening_hours, website=EXCLUDED.website,
                address=EXCLUDED.address, geom=EXCLUDED.geom, updated_at=now()
        """, [r[:11] + (r[12], r[11]) for r in rows], page_size=500)  # lon, lat


def save_sqlite(rows, path):
    con = sqlite3.connect(path)
    con.executescript(SQLITE_SCHEMA)
    con.executemany("INSERT OR REPLACE INTO places (osm_id,wilaya,sector,subtype,name,name_ar,name_fr,"
                    "phone,opening_hours,website,address,lat,lon) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wilaya", default="31", help="رمز الولاية، مثل 31 لوهران")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pg", help="رابط PostgreSQL")
    g.add_argument("--sqlite", help="مسار ملف SQLite")
    a = ap.parse_args()
    code = a.wilaya.zfill(2)

    print(f"جلب بيانات الولاية {code} من OpenStreetMap ...")
    els = {}
    for key in TAGS:   # طلب صغير لكل نوع وسم: أنجح مع الولايات الكبيرة مثل الجزائر العاصمة
        print(f"  - {key} ...", flush=True)
        got = fetch(build_query(code, key))
        if got is None:
            print(f"    تعذّر جلب {key}؛ أعد تشغيل الأمر لاحقاً لإكماله", file=sys.stderr)
            continue
        for e in got:
            els[(e["type"], e["id"])] = e
        time.sleep(2)
    if not els:
        sys.exit("تعذر الوصول إلى Overpass. أعد المحاولة لاحقاً.")
    rows = to_rows(list(els.values()), code)
    if not rows:
        sys.exit("لا نتائج. تحقق من رمز الولاية.")

    (save_pg if a.pg else save_sqlite)(rows, a.pg or a.sqlite)

    stats = {}
    for r in rows:
        stats[r[2]] = stats.get(r[2], 0) + 1
    print(f"تم حفظ {len(rows)} مكاناً:")
    for s, n in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")


if __name__ == "__main__":
    main()
