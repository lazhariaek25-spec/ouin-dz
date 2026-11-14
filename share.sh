#!/data/data/com.termux/files/usr/bin/bash
# رابط عام مؤقت للمنصة من هاتفك. يبقى ما دامت هذه الجلسة تعمل.
# الاستعمال:  ADMIN_EMAIL=بريدك bash share.sh
cd "$(dirname "$0")"
termux-wake-lock 2>/dev/null || true
pkg install -y cloudflared >/dev/null 2>&1 || true
python backend/app.py >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
sleep 2
if command -v cloudflared >/dev/null 2>&1; then
  echo "ابحث في الأسطر التالية عن رابط ينتهي بـ trycloudflare.com"
  cloudflared tunnel --url http://localhost:8000
else
  pkg install -y openssh
  echo "الرابط يظهر في السطر الذي فيه localhost.run"
  ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 nokey@localhost.run
fi
