#!/usr/bin/env bash
# يجلب عدة ولايات بالتتابع ثم يحذف المؤسسات الأمنية ويجهّز ملف البيانات للرفع.
# الاستعمال:  bash tools/import_many.sh 11 12 13 14 15
cd "$(dirname "$0")/.."
termux-wake-lock 2>/dev/null || true
for c in "$@"; do
  echo "=== الولاية $c ==="
  python backend/osm_import.py --wilaya "$c" --sqlite data/ouin.db
done
python tools/purge_security.py data/ouin.db
cp data/ouin.db data/osm_seed.db
echo "جاهز للرفع:  git add -A && git commit -m 'بيانات ولايات جديدة' && git push"
