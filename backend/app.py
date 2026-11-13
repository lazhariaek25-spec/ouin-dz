"""وين؟ DZ — API (Flask + SQLite): البحث + حسابات المؤسسات + لوحة الإدارة."""
import math
import os
import re
import secrets
import shutil
import sqlite3
import time

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("OUIN_DB", os.path.join(ROOT, "data", "ouin.db"))
SEED = os.path.join(ROOT, "data", "osm_seed.db")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
SECTORS = {"health", "shopping", "auto", "food", "trades", "public", "education",
           "realestate", "sport", "finance", "agriculture", "tourism"}
PUBLIC_COLS = ("osm_id,wilaya,sector,subtype,name,name_ar,name_fr,phone,"
               "opening_hours,website,address,lat,lon,source")


def _secret():
    k = os.environ.get("SECRET_KEY")
    if k:
        return k
    f = os.path.join(os.path.dirname(DB), "secret.key")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    if not os.path.exists(f):
        with open(f, "w") as fh:
            fh.write(secrets.token_hex(32))
    return open(f).read().strip()


app = Flask(__name__, static_folder=os.path.join(ROOT, "frontend"), static_url_path="")
app.secret_key = _secret()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                   SESSION_COOKIE_SECURE=bool(os.environ.get("PROD")),
                   MAX_CONTENT_LENGTH=64 * 1024)

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


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if not os.path.exists(DB) and os.path.exists(SEED):
        shutil.copy(SEED, DB)
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS places (
        osm_id TEXT PRIMARY KEY, wilaya TEXT, sector TEXT, subtype TEXT,
        name TEXT, name_ar TEXT, name_fr TEXT, phone TEXT, opening_hours TEXT,
        website TEXT, address TEXT, lat REAL, lon REAL);
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT,
        pw_hash TEXT NOT NULL, is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    have = {r[1] for r in con.execute("PRAGMA table_info(places)")}
    for col, typ in (("owner_id", "INTEGER"), ("status", "TEXT"), ("source", "TEXT")):
        if col not in have:
            con.execute(f"ALTER TABLE places ADD COLUMN {col} {typ}")
    con.execute("CREATE INDEX IF NOT EXISTS places_ws ON places (wilaya, sector)")
    con.commit()
    con.close()


init_db()


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def err(msg, code=400):
    return jsonify(error=msg), code


@app.errorhandler(ValueError)
def _bad(e):
    return err(str(e))


@app.errorhandler(413)
def _big(e):
    return err("الطلب كبير جداً", 413)


def user():
    uid = session.get("uid")
    if not uid:
        return None
    return db().execute("SELECT id,email,name,is_admin FROM users WHERE id=?", (uid,)).fetchone()


def json_body():
    if not request.is_json:
        raise ValueError("يجب إرسال JSON")
    return request.get_json(silent=True) or {}


# ---------- الصفحات والبحث العام ----------
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/places")
def places():
    a = request.args
    where, p = ["(status IS NULL OR status='approved')"], []
    if a.get("wilaya"):
        where.append("wilaya=?")
        p.append(a["wilaya"].zfill(2))
    if a.get("sector"):
        where.append("sector=?")
        p.append(a["sector"])
    q = a.get("q", "").strip().lower()[:80]
    if q:
        like = f"%{q}%"
        cond = ("(lower(name) LIKE ? OR lower(coalesce(name_ar,'')) LIKE ? OR lower(coalesce(name_fr,'')) LIKE ? "
                "OR lower(coalesce(address,'')) LIKE ? OR lower(coalesce(subtype,'')) LIKE ?")
        p += [like] * 5
        subs = sorted({v for k, v in SYN.items() if k in q})
        if subs:
            cond += " OR subtype IN (%s)" % ",".join("?" * len(subs))
            p += subs
        where.append(cond + ")")
    sql = f"SELECT {PUBLIC_COLS} FROM places WHERE " + " AND ".join(where) + " LIMIT 3000"
    rows = [dict(r) for r in db().execute(sql, p)]
    lat, lon = a.get("lat", type=float), a.get("lon", type=float)
    if lat is not None and lon is not None:
        for r in rows:
            r["km"] = round(hav(lat, lon, r["lat"], r["lon"]), 2)
        rows.sort(key=lambda r: (r["source"] != "owner", r["km"]))
    return jsonify(rows[: min(a.get("limit", 50, type=int), 200)])


@app.get("/api/stats")
def stats():
    rows = db().execute("SELECT wilaya, sector, COUNT(*) n FROM places "
                        "WHERE status IS NULL OR status='approved' GROUP BY 1,2").fetchall()
    return jsonify([dict(r) for r in rows])


# ---------- الحسابات ----------
FAILS = {}


def throttled():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    now = time.time()
    FAILS[ip] = [t for t in FAILS.get(ip, []) if now - t < 600]
    return ip, len(FAILS[ip]) >= 8


@app.post("/api/register")
def register():
    d = json_body()
    email = str(d.get("email", "")).strip().lower()[:120]
    pw = str(d.get("password", ""))
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("بريد غير صالح")
    if len(pw) < 8:
        raise ValueError("كلمة السر 8 أحرف على الأقل")
    con = db()
    try:
        cur = con.execute("INSERT INTO users (email,name,pw_hash,is_admin) VALUES (?,?,?,?)",
                          (email, str(d.get("name", ""))[:80], generate_password_hash(pw),
                           1 if ADMIN_EMAIL and email == ADMIN_EMAIL else 0))
        con.commit()
    except sqlite3.IntegrityError:
        return err("هذا البريد مسجل من قبل", 409)
    session.clear()
    session["uid"] = cur.lastrowid
    return jsonify(ok=True)


@app.post("/api/login")
def login():
    d = json_body()
    ip, blocked = throttled()
    if blocked:
        return err("محاولات كثيرة، انتظر عشر دقائق", 429)
    r = db().execute("SELECT id,pw_hash FROM users WHERE email=?",
                     (str(d.get("email", "")).strip().lower(),)).fetchone()
    if not r or not check_password_hash(r["pw_hash"], str(d.get("password", ""))):
        FAILS.setdefault(ip, []).append(time.time())
        return err("بيانات الدخول غير صحيحة", 401)
    session.clear()
    session["uid"] = r["id"]
    return jsonify(ok=True)


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
def me():
    u = user()
    return jsonify(user=dict(u) if u else None)


# ---------- مؤسسات المستخدم ----------
def clean(d):
    def g(k, n=200):
        return (str(d.get(k) or "").strip()[:n]) or None
    name = g("name", 120)
    if not name:
        raise ValueError("اسم المؤسسة مطلوب")
    w = str(d.get("wilaya", "")).strip().zfill(2)
    if not (w.isdigit() and 1 <= int(w) <= 58):
        raise ValueError("ولاية غير صالحة")
    if d.get("sector") not in SECTORS:
        raise ValueError("قطاع غير صالح")
    try:
        lat, lon = float(d.get("lat")), float(d.get("lon"))
    except (TypeError, ValueError):
        raise ValueError("الموقع الجغرافي مطلوب (خط العرض وخط الطول)")
    if not (18 <= lat <= 38 and -9 <= lon <= 12):
        raise ValueError("الإحداثيات خارج الجزائر")
    site = g("website")
    if site and not re.match(r"https?://", site):
        raise ValueError("الموقع الإلكتروني يجب أن يبدأ بـ http:// أو https://")
    phone = g("phone", 30)
    if phone and not re.fullmatch(r"[0-9+\-() /]{6,30}", phone):
        raise ValueError("رقم هاتف غير صالح")
    return dict(wilaya=w, sector=d["sector"], subtype=g("subtype", 60), name=name,
                name_ar=g("name_ar", 120), name_fr=g("name_fr", 120), phone=phone,
                opening_hours=g("opening_hours", 120), website=site, address=g("address", 200),
                lat=lat, lon=lon)


def need_user():
    u = user()
    if not u:
        raise PermissionError
    return u


@app.errorhandler(PermissionError)
def _auth(e):
    return err("سجّل الدخول أولاً", 401)


@app.get("/api/my/places")
def my_places():
    u = need_user()
    rows = db().execute(f"SELECT {PUBLIC_COLS},status FROM places WHERE owner_id=? ORDER BY rowid DESC",
                        (u["id"],)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/my/places")
def add_place():
    u = need_user()
    d = clean(json_body())
    con = db()
    if con.execute("SELECT COUNT(*) FROM places WHERE owner_id=?", (u["id"],)).fetchone()[0] >= 20:
        return err("الحد الأقصى 20 مؤسسة لكل حساب")
    pid = "u" + secrets.token_hex(6)
    cols = list(d)
    con.execute(f"INSERT INTO places (osm_id,owner_id,status,source,{','.join(cols)}) "
                f"VALUES (?,?,'pending','owner',{','.join('?' * len(cols))})",
                [pid, u["id"]] + [d[c] for c in cols])
    con.commit()
    return jsonify(ok=True, id=pid)


@app.put("/api/my/places/<pid>")
def edit_place(pid):
    u = need_user()
    d = clean(json_body())
    con = db()
    cur = con.execute("UPDATE places SET " + ",".join(f"{c}=?" for c in d) +
                      ",status='pending' WHERE osm_id=? AND owner_id=?",
                      list(d.values()) + [pid, u["id"]])
    con.commit()
    return jsonify(ok=True) if cur.rowcount else err("غير موجود", 404)


@app.delete("/api/my/places/<pid>")
def del_place(pid):
    u = need_user()
    con = db()
    cur = con.execute("DELETE FROM places WHERE osm_id=? AND owner_id=?", (pid, u["id"]))
    con.commit()
    return jsonify(ok=True) if cur.rowcount else err("غير موجود", 404)


# ---------- الإدارة المركزية ----------
def need_admin():
    u = need_user()
    if not u["is_admin"]:
        raise PermissionError
    return u


@app.get("/api/admin/pending")
def pending():
    need_admin()
    rows = db().execute(f"SELECT {PUBLIC_COLS},status,(SELECT email FROM users WHERE id=owner_id) owner "
                        "FROM places WHERE status='pending' ORDER BY rowid").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/admin/places/<pid>/<action>")
def review(pid, action):
    need_admin()
    if action not in ("approve", "reject"):
        return err("إجراء غير معروف", 404)
    con = db()
    cur = con.execute("UPDATE places SET status=? WHERE osm_id=? AND source='owner'",
                      ("approved" if action == "approve" else "rejected", pid))
    con.commit()
    return jsonify(ok=True) if cur.rowcount else err("غير موجود", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
