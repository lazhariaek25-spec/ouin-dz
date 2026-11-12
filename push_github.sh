#!/data/data/com.termux/files/usr/bin/bash
# رفع المشروع إلى GitHub.  bash push_github.sh [اسم المستودع]
set -e
REPO="${1:-ouin-dz}"
pkg install -y gh git
git config user.name  >/dev/null 2>&1 || git config --global user.name  "yakine1823"
git config user.email >/dev/null 2>&1 || git config --global user.email "yakine2318@gmail.com"
gh auth status >/dev/null 2>&1 || gh auth login
[ -d .git ] || git init -b main
git add .
git commit -m "وين؟ DZ: النسخة الأولى" || true
gh repo create "$REPO" --public --source=. --remote=origin --push
