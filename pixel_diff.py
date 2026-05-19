"""
pixel_diff.py - Visualisasi perbedaan piksel antara original dan watermarked.

Usage:
    python pixel_diff.py
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ORIGINAL_PATH    = 'images/original.jpg'
WATERMARKED_PATH = 'images/watermarked.jpg'
OUTPUT_PATH      = 'images/pixel_diff.png'

watermarked = cv2.imread(WATERMARKED_PATH)
original_full = cv2.imread(ORIGINAL_PATH)

# Resize original ke ukuran watermarked (watermark.py sudah resize saat embed)
h, w = watermarked.shape[:2]
original = cv2.resize(original_full, (w, h), interpolation=cv2.INTER_AREA)

# Hitung selisih piksel
diff = cv2.absdiff(original, watermarked).astype(np.float32)

# Statistik
max_diff  = diff.max()
mean_diff = diff.mean()
changed   = np.count_nonzero(diff.sum(axis=2))
total_px  = original.shape[0] * original.shape[1]

print(f"  Max perbedaan piksel : {max_diff:.0f}  (dari 0–255)")
print(f"  Rata-rata perbedaan  : {mean_diff:.4f}")
print(f"  Piksel yang berubah  : {changed:,} / {total_px:,}  ({100*changed/total_px:.2f}%)")
print(f"  PSNR                 : {cv2.PSNR(original, watermarked):.2f} dB")

# Amplifikasi biar terlihat (×20)
diff_vis = np.clip(diff * 20, 0, 255).astype(np.uint8)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
axes[0].set_title('Original', fontsize=13, fontweight='bold')
axes[0].axis('off')

axes[1].imshow(cv2.cvtColor(watermarked, cv2.COLOR_BGR2RGB))
axes[1].set_title('Watermarked', fontsize=13, fontweight='bold')
axes[1].axis('off')

im = axes[2].imshow(cv2.cvtColor(diff_vis, cv2.COLOR_BGR2RGB))
axes[2].set_title(f'Perbedaan Piksel (×20)\nMax={max_diff:.0f}  Mean={mean_diff:.4f}', fontsize=12)
axes[2].axis('off')
plt.colorbar(im, ax=axes[2], fraction=0.046)

plt.suptitle(f'Analisis Perbedaan Piksel  |  PSNR = {cv2.PSNR(original, watermarked):.2f} dB\n'
             f'Piksel berubah: {changed:,} / {total_px:,} ({100*changed/total_px:.2f}%)',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight')
print(f"\n  Disimpan ke: {OUTPUT_PATH}")
