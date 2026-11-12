"""وين؟ DZ — واجهة API صغيرة (Flask + SQLite) تخدم أيضاً الواجهة الأمامية."""
import math
import os
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("OUIN_DB", os.path.join(ROOT, "data", "ouin.db"))
app = Flask(__name__, static_folder=os.path.join(ROOT, "frontend"), static_url_path="")

# كلمات البحث بالعربية/الفرنسية/الإنجليزية -> نوع المكان في OSM
SYN = {
    "أسنان": "dentist", "dentiste": "dentist", "dentist": "dentist",
    "صيدلية": "pharmacy", "pharmacie": "pharmacy", "pharmacy": "pharmacy",
    "طبيب": "doctors", "doctor": "doctors", "médecin": "doctors",
    "مستشفى": "hospital", "hôpital": "hospital", "hospital": "hospital",
    "عيادة": "clinic", "clinique": "clinic", "clinic": "clinic",
    "مخبر": "laboratory", "laboratoire": "laboratory",
    "مطعم": "restaurant", "restaurant": "restaurant",
    "مقهى": "cafe", "café": "cafe", "cafe": "cafe",
    "وقود": "fuel", "بنزين": "fuel", "essence": "fuel", "fuel": "fuel",
    "ميكانيكي": "car_repair", "mécanicien": "car_repair", "garage": "car_repair",
    "قطع غيار": "car_parts", "pièces": "car_parts",
    "بنك": "bank", "banque": "bank", "bank": "bank",
    "مخبزة": "bakery", "boulangerie": "bakery", "bakery": "bakery",
    "فندق": "hotel", "hôtel": "hotel", "hotel": "hotel",
    "كهربائي": "electrician", "électricien": "electrician",
    "سباك": "plumber", "plombier": "plumber",
    "نجار": "carpenter", "menuisier": "carpenter",
    "مدرسة": "school", "école": "school", "جامعة": "university", "université": "university",
    "بريد": "post_office", "poste": "post_office",
}


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/places")
def places():
    a = request.args
    where, p = [], []
    if a.get("wilaya"):
        where.append("wilaya=?")
        p.append(a["wilaya"].zfill(2))
    if a.get("sector"):
        where.append("sector=?")
        p.append(a["sector"])
    q = a.get("q", "").strip().lower()
    if q:
        like = f"%{q}%"
        cond = ("(lower(name) LIKE ? OR lower(coalesce(name_ar,'')) LIKE ? "
                "OR lower(coalesce(name_fr,'')) LIKE ? OR lower(coalesce(address,'')) LIKE ?")
        p += [like] * 4
        subs = sorted({v for k, v in SYN.items() if k in q})
        if subs:
            cond += " OR subtype IN (%s)" % ",".join("?" * len(subs))
            p += subs
        where.append(cond + ")")
    sql = "SELECT * FROM places" + (" WHERE " + " AND ".join(where) if where else "") + " LIMIT 3000"
    try:
        rows = [dict(r) for r in db().execute(sql, p)]
    except sqlite3.OperationalError:
        return jsonify(error="قاعدة البيانات فارغة. شغّل backend/osm_import.py أولاً."), 503
    lat, lon = a.get("lat", type=float), a.get("lon", type=float)
    if lat is not None and lon is not None:
        for r in rows:
            r["km"] = round(hav(lat, lon, r["lat"], r["lon"]), 2)
        rows.sort(key=lambda r: r["km"])
    return jsonify(rows[: min(a.get("limit", 50, type=int), 200)])


@app.get("/api/stats")
def stats():
    try:
        rows = db().execute("SELECT wilaya, sector, COUNT(*) n FROM places GROUP BY 1,2").fetchall()
    except sqlite3.OperationalError:
        return jsonify([])
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
