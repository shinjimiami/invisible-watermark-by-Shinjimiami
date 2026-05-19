"""
evaluate.py - Evaluasi robustness watermark terhadap kompresi JPEG berbagai QF.

Alur:
  1. Baca images/watermarked.jpg
  2. Kompres dengan QF 10, 20, ..., 100
  3. Ekstrak watermark dari hasil kompresi
  4. Hitung Bit Error Rate (BER) tiap QF
  5. Plot grafik BER vs QF  →  output/evaluation_chart.png
  6. Print tabel hasil + threshold QF

Usage:
    python evaluate.py
"""

import os
import sys
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from imwatermark import WatermarkDecoder

# ── Configuration ──────────────────────────────────────────────────────────────
WATERMARK_TEXT  = "atharmdh"
WATERMARK_BYTES = WATERMARK_TEXT.encode('utf-8')
WATERMARK_BITS  = len(WATERMARK_BYTES) * 8   # 64 bits
METHOD          = 'dwtDct'
BER_THRESHOLD   = 0.4   # batas BER agar watermark dianggap gagal

WATERMARKED_PATH = os.path.join('images', 'watermarked_clean.png')  # PNG lossless
RESULTS_DIR      = os.path.join('images', 'results')
CHART_PATH       = os.path.join('output', 'evaluation_chart.png')
# ───────────────────────────────────────────────────────────────────────────────


def bytes_to_bits(data: bytes) -> str:
    return ''.join(format(b, '08b') for b in data)


def calculate_ber(original: bytes, extracted) -> float:
    if extracted is None:
        return 1.0
    orig_bits = bytes_to_bits(original)
    try:
        ext_bits = bytes_to_bits(extracted)
    except Exception:
        return 1.0
    errors = sum(a != b for a, b in zip(orig_bits, ext_bits))
    return errors / len(orig_bits)


def compress_to_bgr(source_path: str, quality: int) -> np.ndarray:
    """Kompres gambar ke JPEG QF lalu decode kembali ke numpy array."""
    bgr = cv2.imread(source_path)
    params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buf = cv2.imencode('.jpg', bgr, params)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def extract_from_bgr(bgr: np.ndarray):
    try:
        decoder = WatermarkDecoder('bytes', WATERMARK_BITS)
        return decoder.decode(bgr, METHOD)
    except Exception as e:
        print(f"    [WARN] Gagal ekstrak: {e}")
        return None


def evaluate_all_qf() -> list:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs('output', exist_ok=True)

    if not os.path.exists(WATERMARKED_PATH):
        print(f"[ERROR] File tidak ada: {WATERMARKED_PATH}")
        print("  Jalankan dulu:  python watermark.py")
        print("  (file PNG lossless dibuat otomatis oleh watermark.py)")
        sys.exit(1)

    print("=" * 62)
    print("  DIGITAL WATERMARKING — Tahap Evaluasi")
    print("=" * 62)
    print(f"  Watermark    : '{WATERMARK_TEXT}'  ({WATERMARK_BITS} bit)")
    print(f"  Metode       : {METHOD}")
    print(f"  BER threshold: {BER_THRESHOLD}")
    print("=" * 62)

    quality_factors = list(range(10, 101, 10))
    results = []

    for qf in quality_factors:
        print(f"\n  [QF={qf:3d}]", end="  ")

        # Kompres
        compressed = compress_to_bgr(WATERMARKED_PATH, qf)

        # Simpan gambar hasil kompresi
        out_path = os.path.join(RESULTS_DIR, f'qf_{qf:02d}.jpg')
        cv2.imwrite(out_path, compressed, [cv2.IMWRITE_JPEG_QUALITY, qf])

        # Ekstrak watermark
        extracted = extract_from_bgr(compressed)

        # BER
        ber = calculate_ber(WATERMARK_BYTES, extracted)

        # PSNR vs watermarked (bukan original)
        ref = cv2.imread(WATERMARKED_PATH)
        psnr = cv2.PSNR(ref, compressed)

        # Decoded text
        try:
            ext_text = extracted.decode('utf-8', errors='replace') if extracted else ''
        except Exception:
            ext_text = ''

        status = 'Extracted ✓' if ber <= BER_THRESHOLD else 'Failed ✗'

        print(f"BER={ber:.4f}  PSNR={psnr:.1f}dB  {status}  → '{ext_text}'")

        results.append({
            'qf'        : qf,
            'ber'       : ber,
            'psnr'      : psnr,
            'status'    : status,
            'ext_text'  : ext_text,
        })

    return results


def print_table(results: list) -> None:
    print("\n" + "=" * 68)
    print("  TABEL HASIL EVALUASI")
    print("=" * 68)
    print(f"{'QF':>4}  {'BER':>8}  {'PSNR (dB)':>10}  {'Status':>13}  Extracted")
    print("-" * 68)
    for r in results:
        print(f"{r['qf']:>4}  {r['ber']:>8.4f}  {r['psnr']:>10.2f}  "
              f"{r['status']:>13}  '{r['ext_text']}'")
    print("=" * 68)

    # Threshold analysis
    fail_qfs = [r['qf'] for r in results if r['ber'] > BER_THRESHOLD]
    ok_qfs   = [r['qf'] for r in results if r['ber'] <= BER_THRESHOLD]

    print("\n  [ANALISIS THRESHOLD]")
    if fail_qfs:
        print(f"  Watermark GAGAL pada QF  : {fail_qfs}")
        print(f"  Watermark BERHASIL pada QF: {ok_qfs}")
        print(f"  QF minimum yang aman      : {min(ok_qfs) if ok_qfs else 'Tidak ada'}")
    else:
        print(f"  Watermark bertahan di SEMUA QF (BER ≤ {BER_THRESHOLD})")


def plot_chart(results: list, save_path: str) -> None:
    qfs   = [r['qf']   for r in results]
    bers  = [r['ber']  for r in results]
    psnrs = [r['psnr'] for r in results]
    colors = ['#2ecc71' if b <= BER_THRESHOLD else '#e74c3c' for b in bers]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 11))

    # ── Panel atas: BER vs QF ──────────────────────────────────────────────────
    bars = ax1.bar(qfs, bers, color=colors, alpha=0.82, width=7,
                   edgecolor='black', linewidth=0.6)

    ax1.axhline(y=BER_THRESHOLD, color='#f39c12', linestyle='--',
                linewidth=2.2, label=f'Threshold BER = {BER_THRESHOLD}')

    # Label nilai di atas batang
    for bar, ber in zip(bars, bers):
        ax1.text(
            bar.get_x() + bar.get_width() / 2.,
            bar.get_height() + 0.008,
            f'{ber:.3f}',
            ha='center', va='bottom', fontsize=8.5, fontweight='bold'
        )

    legend_patches = [
        Patch(facecolor='#2ecc71', alpha=0.82, edgecolor='black',
              label=f'Berhasil diekstrak (BER ≤ {BER_THRESHOLD})'),
        Patch(facecolor='#e74c3c', alpha=0.82, edgecolor='black',
              label=f'Gagal diekstrak (BER > {BER_THRESHOLD})'),
        plt.Line2D([0], [0], color='#f39c12', linestyle='--', linewidth=2,
                   label=f'Threshold BER = {BER_THRESHOLD}'),
    ]
    ax1.legend(handles=legend_patches, fontsize=10, loc='upper left')

    ax1.set_xlabel('JPEG Quality Factor (QF)', fontsize=12)
    ax1.set_ylabel('Bit Error Rate (BER)', fontsize=12)
    ax1.set_title('BER vs JPEG Quality Factor\n'
                  '(Hijau = Berhasil ✓  |  Merah = Gagal ✗)', fontsize=13)
    ax1.set_xlim(3, 107)
    ax1.set_ylim(0, max(bers) * 1.25 + 0.05)
    ax1.set_xticks(qfs)
    ax1.grid(axis='y', alpha=0.35)

    # ── Panel bawah: PSNR vs QF ────────────────────────────────────────────────
    ax2.plot(qfs, psnrs, 'b-o', linewidth=2.2, markersize=8,
             label='PSNR (dB)', zorder=3)
    ax2.fill_between(qfs, psnrs, alpha=0.15, color='blue')

    for x, y in zip(qfs, psnrs):
        ax2.annotate(f'{y:.1f}', (x, y),
                     textcoords='offset points', xytext=(0, 10),
                     ha='center', fontsize=8.5, fontweight='bold')

    ax2.set_xlabel('JPEG Quality Factor (QF)', fontsize=12)
    ax2.set_ylabel('PSNR (dB)', fontsize=12)
    ax2.set_title('PSNR vs JPEG Quality Factor\n'
                  '(Kualitas gambar setelah kompresi)', fontsize=13)
    ax2.set_xticks(qfs)
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.35)

    fig.suptitle(
        f'Evaluasi Digital Watermarking\n'
        f'Watermark: "{WATERMARK_TEXT}"  |  Metode: {METHOD}',
        fontsize=14, fontweight='bold', y=1.01
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  Grafik disimpan: {save_path}")


def main():
    results = evaluate_all_qf()
    print_table(results)
    plot_chart(results, CHART_PATH)

    print("\n[SELESAI] Evaluasi selesai!")
    print(f"  → Foto kompresi tiap QF : {RESULTS_DIR}/qf_XX.jpg")
    print(f"  → Grafik evaluasi       : {CHART_PATH}")


if __name__ == '__main__':
    main()
