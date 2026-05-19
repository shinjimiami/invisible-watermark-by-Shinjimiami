#!/usr/bin/env bash
# setup_and_run.sh — Setup venv, install dependencies, dan jalankan project
# Usage: bash setup_and_run.sh

set -e

echo "=== Digital Watermarking — Setup & Run ==="

# 1. Buat virtual environment jika belum ada
if [ ! -d "venv" ]; then
    echo "[1/3] Membuat virtual environment..."
    python3 -m venv venv
else
    echo "[1/3] Virtual environment sudah ada."
fi

# 2. Aktifkan venv & install dependencies
echo "[2/3] Menginstall dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q

# 3. Cek apakah original.jpg ada
if [ ! -f "images/original.jpg" ]; then
    echo ""
    echo "[ERROR] images/original.jpg tidak ditemukan!"
    echo "  Letakkan foto wajah sebagai images/original.jpg lalu jalankan ulang."
    exit 1
fi

echo "[3/3] Menjalankan watermark.py..."
python3 watermark.py

echo ""
echo "Menjalankan evaluate.py..."
python3 evaluate.py

echo ""
echo "=== SELESAI ==="
echo "Cek output di:"
echo "  images/watermarked.jpg"
echo "  images/comparison.png"
echo "  images/results/qf_XX.jpg"
echo "  output/evaluation_chart.png"
