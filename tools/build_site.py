#!/usr/bin/env python3
"""يبني الموقع الثابت في _site/ من قاعدة data/ouin.db (لا يحتاج خادماً)."""
import json
import os
import shutil
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from search import CONCEPTS, STOP  # noqa: E402

DB = os.environ.get("OUIN_DB", os.path.join(ROOT, "data", "ouin.db"))
OUT = os.path.join(ROOT, "_site")
COLS = "osm_id,wilaya,sector,subtype,name,name_ar,name_fr,phone,opening_hours,website,address,lat,lon"

if not os.path.exists(DB):
    sys.exit(f"لا توجد قاعدة بيانات: {DB}")
shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(os.path.join(ROOT, "static_site"), OUT)
os.makedirs(os.path.join(OUT, "data"))

con = sqlite3.connect(DB)
have = {r[1] for r in con.execute("PRAGMA table_info(places)")}
where = ["wilaya IS NOT NULL", "lat IS NOT NULL", "lon IS NOT NULL"]
if "source" in have:
    where.append("(source IS NULL OR source!='owner')")
rows = con.execute(f"SELECT {COLS} FROM places WHERE {' AND '.join(where)} ORDER BY wilaya, sector, name").fetchall()

by = {}
for r in rows:
    by.setdefault(r[1], []).append(list(r))
dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
for code, lst in by.items():
    open(os.path.join(OUT, "data", f"{code}.json"), "w", encoding="utf-8").write(dump(lst))
open(os.path.join(OUT, "data", "index.json"), "w", encoding="utf-8").write(dump({c: len(v) for c, v in sorted(by.items())}))
open(os.path.join(OUT, "data", "concepts.json"), "w", encoding="utf-8").write(
    dump({"c": [[s, list(subs) if subs else None, list(t)] for s, subs, t in CONCEPTS], "stop": sorted(STOP)}))
print("ولايات:", {c: len(v) for c, v in sorted(by.items())}, "| المجموع:", len(rows))
