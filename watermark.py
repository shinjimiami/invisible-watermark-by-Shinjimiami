"""
watermark.py - Embed digital watermark into a face image using invisible-watermark.

Usage:
    python watermark.py

Output:
    images/watermarked.jpg  - image with embedded watermark
    images/comparison.png   - side-by-side before/after visual
"""

import os
import sys
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from imwatermark import WatermarkEncoder, WatermarkDecoder

# ── Configuration ──────────────────────────────────────────────────────────────
WATERMARK_TEXT  = "atharmdh"          # ganti sesuai kebutuhan
WATERMARK_BYTES = WATERMARK_TEXT.encode('utf-8')
WATERMARK_BITS  = len(WATERMARK_BYTES) * 8   # 8 chars × 8 bits = 64 bits
METHOD          = 'dwtDct'

ORIGINAL_PATH    = os.path.join('images', 'original.jpg')
WATERMARKED_PATH = os.path.join('images', 'watermarked.jpg')
COMPARISON_PATH  = os.path.join('images', 'comparison.png')
# ───────────────────────────────────────────────────────────────────────────────


def bytes_to_bits(data: bytes) -> str:
    return ''.join(format(b, '08b') for b in data)


def calculate_ber(original: bytes, extracted: bytes) -> float:
    if extracted is None:
        return 1.0
    orig_bits = bytes_to_bits(original)
    try:
        ext_bits = bytes_to_bits(extracted)
    except Exception:
        return 1.0
    errors = sum(a != b for a, b in zip(orig_bits, ext_bits))
    return errors / len(orig_bits)


MAX_DIM = 1024   # resize jika gambar lebih besar dari ini (dwtDct lebih stabil)


def resize_if_needed(bgr: np.ndarray, max_dim: int = MAX_DIM) -> np.ndarray:
    h, w = bgr.shape[:2]
    if max(h, w) <= max_dim:
        return bgr
    scale = max_dim / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def embed_watermark(image_path: str, output_path: str) -> tuple:
    """
    Embed WATERMARK_BYTES into image using dwtDct.
    Returns (original_bgr, watermarked_bgr).
    """
    bgr = cv2.imread(image_path)
    if bgr is None:
        raise FileNotFoundError(f"Gambar tidak ditemukan: {image_path}")

    h, w = bgr.shape[:2]
    print(f"  Gambar dimuat  : {image_path}  ({w}×{h} px)")

    # Resize agar dwtDct bekerja optimal
    bgr = resize_if_needed(bgr)
    h2, w2 = bgr.shape[:2]
    if (h2, w2) != (h, w):
        print(f"  Di-resize ke   : {w2}×{h2} px  (agar watermark stabil)")

    print(f"  Teks watermark : '{WATERMARK_TEXT}'")
    print(f"  Bytes          : {WATERMARK_BYTES}")
    print(f"  Jumlah bit     : {WATERMARK_BITS}")
    print(f"  Metode         : {METHOD}")

    encoder = WatermarkEncoder()
    encoder.set_watermark('bytes', WATERMARK_BYTES)
    bgr_wm = encoder.encode(bgr, METHOD)

    # Simpan JPEG untuk display
    cv2.imwrite(output_path, bgr_wm, [cv2.IMWRITE_JPEG_QUALITY, 100])
    print(f"  Disimpan ke    : {output_path}  (JPEG quality=100)")

    # Simpan PNG lossless sebagai sumber evaluasi (tanpa JPEG artifact)
    png_path = output_path.replace('.jpg', '_clean.png')
    cv2.imwrite(png_path, bgr_wm)
    print(f"  Sumber eval    : {png_path}  (PNG lossless)")

    return bgr, bgr_wm


def extract_watermark(image_path: str) -> bytes:
    bgr = cv2.imread(image_path)
    if bgr is None:
        raise FileNotFoundError(f"Gambar tidak ditemukan: {image_path}")
    decoder = WatermarkDecoder('bytes', WATERMARK_BITS)
    return decoder.decode(bgr, METHOD)


def save_comparison(original_bgr: np.ndarray, watermarked_bgr: np.ndarray,
                    save_path: str) -> None:
    orig_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)
    wm_rgb   = cv2.cvtColor(watermarked_bgr, cv2.COLOR_BGR2RGB)
    psnr     = cv2.PSNR(original_bgr, watermarked_bgr)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    axes[0].imshow(orig_rgb)
    axes[0].set_title('Original', fontsize=15, fontweight='bold', pad=10)
    axes[0].axis('off')

    axes[1].imshow(wm_rgb)
    axes[1].set_title(
        f'Watermarked\n(teks: "{WATERMARK_TEXT}")',
        fontsize=15, fontweight='bold', pad=10
    )
    axes[1].axis('off')

    fig.suptitle(
        f'Digital Watermarking  |  Metode: {METHOD}  |  PSNR: {psnr:.2f} dB',
        fontsize=13, y=1.01
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Perbandingan   : {save_path}  (PSNR = {psnr:.2f} dB)")


def main():
    os.makedirs('images', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    print("=" * 55)
    print("  DIGITAL WATERMARKING — Tahap Embedding")
    print("=" * 55)

    if not os.path.exists(ORIGINAL_PATH):
        print(f"\n[ERROR] File tidak ada: {ORIGINAL_PATH}")
        print("  Letakkan foto wajah sebagai  images/original.jpg")
        sys.exit(1)

    original_bgr, watermarked_bgr = embed_watermark(ORIGINAL_PATH, WATERMARKED_PATH)

    # Verifikasi langsung dari array (bukan baca ulang dari disk)
    print("\n  Verifikasi watermark (dari memory)...")
    decoder = WatermarkDecoder('bytes', WATERMARK_BITS)
    extracted = decoder.decode(watermarked_bgr, METHOD)
    ber = calculate_ber(WATERMARK_BYTES, extracted)

    try:
        extracted_text = extracted.decode('utf-8', errors='replace')
    except Exception:
        extracted_text = repr(extracted)

    print(f"  Hasil ekstraksi: '{extracted_text}'")
    print(f"  BER            : {ber:.4f}")

    if ber == 0.0:
        print("  Status         : BERHASIL ✓ (BER = 0)")
    else:
        print(f"  Status         : Sebagian cocok (BER = {ber:.4f})")

    save_comparison(original_bgr, watermarked_bgr, COMPARISON_PATH)

    print("\n[SELESAI] Embedding watermark berhasil!")
    print(f"  → {WATERMARKED_PATH}")
    print(f"  → {COMPARISON_PATH}")


if __name__ == '__main__':
    main()
