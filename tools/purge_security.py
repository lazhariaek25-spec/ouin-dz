#!/usr/bin/env python3
"""يحذف المؤسسات الأمنية (شرطة، درك، جيش...) من قواعد بيانات SQLite.
الاستعمال:  python tools/purge_security.py data/ouin.db data/osm_seed.db"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
from search import is_security  # noqa: E402

for path in sys.argv[1:] or ["data/ouin.db"]:
    if not os.path.exists(path):
        print("غير موجود:", path)
        continue
    con = sqlite3.connect(path)
    rows = con.execute("SELECT osm_id,subtype,name,name_ar,name_fr FROM places").fetchall()
    bad = [(r[0],) for r in rows if is_security(r[1], " ".join(x or "" for x in r[2:5]))]
    con.executemany("DELETE FROM places WHERE osm_id=?", bad)
    con.commit()
    con.execute("VACUUM")
    print(f"{path}: حُذف {len(bad)} من {len(rows)}")
    con.close()
