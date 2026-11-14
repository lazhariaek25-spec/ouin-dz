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
## رابط عام مؤقت + تثبيت كتطبيق
```
ADMIN_EMAIL=بريدك bash share.sh
```
يظهر رابط https؛ افتحه في Chrome ثم «ثبّت التطبيق» (PWA).

## الرفع إلى GitHub
```
bash push_github.sh ouin-dz
```
البيانات © مساهمو OpenStreetMap (ترخيص ODbL).

## صفحة الهبوط وتطبيق أندرويد (APK)
- `/` صفحة هبوط: زر «افتح في المتصفح» (`/app`) وزر «حمّل APK» (يظهر عند وجود الملف) وزر تثبيت كتطبيق ويب.
- `android/`: تطبيق WebView يفتح `APP_URL/app`. يبنيه GitHub Actions (`.github/workflows/android.yml`) ويحفظ الناتج في `frontend/downloads/ouin-dz.apk`.
- التشغيل: GitHub ثم Actions ثم Build APK ثم Run workflow ثم أدخل رابط المنصة العام.
