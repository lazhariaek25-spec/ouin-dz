#!/usr/bin/env bash
# يجهّز المستودع ويرفعه (شغّله من داخل مجلد المشروع):  bash deploy.sh
set -e
cd "$(dirname "$0")"
git add -A
git commit -m "الموقع الثابت + بناء APK على GitHub Pages" || true
git pull --rebase --no-edit origin main
git rm -rq --ignore-unmatch android/app/ouin.keystore frontend/downloads/ouin-dz.apk .github/workflows/android.yml
git commit -m "تنظيف قبل النشر" || true
git push
echo "تم الرفع. تابع الخطوات في GitHub."
