# وين؟ DZ — Ouin ? DZ

المنصة الوطنية الجزائرية للبحث الجغرافي الذكي: «كل ما تبحث عنه حولك، بذكاء».

- **backend/osm_import.py**: يجلب أماكن حقيقية من OpenStreetMap لولاية معينة (SQLite أو PostgreSQL/PostGIS).
- **backend/app.py**: واجهة API (Flask): `/api/places?wilaya=31&sector=health&q=أسنان&lat=..&lon=..` و`/api/stats`.
- **frontend/business.html**: لوحة المؤسسات (تسجيل، إضافة وتعديل الأنشطة، ومراجعة الإدارة).
- **DEPLOY.md**: النشر العام على PythonAnywhere.
- **frontend/index.html**: الواجهة (عربي/فرنسي/إنجليزي): بحث حسب الولاية والقطاع والتخصص، أو بحث عام بالاسم، مع العنوان والموقع.

## التشغيل على Termux
```
bash setup_termux.sh 31     # تثبيت + جلب بيانات وهران
bash run.sh                 # ثم افتح http://localhost:8000
bash setup_termux.sh 16     # أضف ولاية أخرى (الجزائر)... وهكذا
```
## الرفع إلى GitHub
```
bash push_github.sh ouin-dz
```
البيانات © مساهمو OpenStreetMap (ترخيص ODbL).
