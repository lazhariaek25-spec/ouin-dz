# نشر وين؟ DZ على PythonAnywhere (مجاني، بدون بطاقة)

الخطة المجانية Beginner: تطبيق ويب واحد على `اسمك.pythonanywhere.com`، قرص 512MB، وتنتهي صلاحية التطبيق كل شهر ويُجدَّد بضغطة زر.

## 1) جهّز بيانات OSM (على Termux)
```
cd ~/ouin-dz
cp data/ouin.db data/osm_seed.db      # قبل تسجيل أي مؤسسة على جهازك
git add -A && git commit -m "لوحة المؤسسات + بيانات OSM" && git push
```
`osm_seed.db` نسخة بيانات OSM تُنسخ تلقائياً عند أول تشغيل على الخادم.

## 2) على PythonAnywhere
1. أنشئ حساباً مجانياً (Beginner) من pythonanywhere.com.
2. تبويب **Consoles** ثم **Bash**:
```
git clone https://lazhariaek25-spec:الرمز@github.com/lazhariaek25-spec/ouin-dz.git
cd ouin-dz && pip install --user -r requirements.txt
```
(المستودع خاص فنضع رمز الوصول في الرابط. أو اجعله Public وأزل `:الرمز`.)
3. تبويب **Web** ثم **Add a new web app** ثم **Manual configuration** ثم اختر Python 3.10 أو أحدث.
4. افتح ملف **WSGI configuration file** واستبدل محتواه بالكامل بـ:
```python
import os, sys
os.environ["PROD"] = "1"
os.environ["ADMIN_EMAIL"] = "بريدك@gmail.com"      # من يسجّل بهذا البريد يصبح مديراً
os.environ["SECRET_KEY"] = "ضع-هنا-نصاً-عشوائياً-طويلاً"
sys.path.insert(0, "/home/اسمك/ouin-dz/backend")
from app import app as application
```
5. اضغط **Reload**. افتح `https://اسمك.pythonanywhere.com`.
6. سجّل أنت أولاً من `/business.html` بنفس بريد `ADMIN_EMAIL` لتصبح مديراً.

## التحديث لاحقاً
```
cd ~/ouin-dz && git pull
```
ثم **Reload** من تبويب Web. وتذكّر تجديد التطبيق شهرياً (زر Run until... في تبويب Web).

## ملاحظات
- الخادم المجاني لا يصل إلى Overpass، فالاستيراد يتم على Termux ثم يُرفع `osm_seed.db`.
- قاعدة SQLite تعيش على القرص الدائم لحسابك، فتبقى بيانات المؤسسات المسجلة.
- للنشر على خادم Docker (Fly.io/Railway/VPS): يوجد `Dockerfile`؛ اربط مجلد `/data` بقرص دائم.
