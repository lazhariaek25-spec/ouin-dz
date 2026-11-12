#!/data/data/com.termux/files/usr/bin/bash
# التثبيت على Termux:  bash setup_termux.sh [رمز الولاية]   (الافتراضي 31 = وهران)
set -e
pkg update -y
pkg install -y python git
pip install -r requirements.txt
mkdir -p data
python backend/osm_import.py --wilaya "${1:-31}" --sqlite data/ouin.db
echo "تم. شغّل المنصة بالأمر: bash run.sh"
