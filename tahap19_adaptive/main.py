"""
TAHAP 19 — ALNS LENGKAP: BOBOT YANG MENYESUAIKAN DIRI
===============================================================================
Inilah huruf "A" pada ALNS.

Di Tahap 18 bobot operator tetap sama rata selamanya. Padahal di Tahap 15
kita sudah melihat kualitas keempat pasangan jelas berbeda.

Sekarang bobot dihitung ulang setiap akhir SEGMEN, memakai rumus M6:

    w[i, j+1] = w[i, j] * (1 - r) + r * (pi_i / theta_i)

dengan skor sigma1 = 33, sigma2 = 9, sigma3 = 13.
===============================================================================
"""

import os
import random
import time

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance
from destroy import DestroyOperator
from repair import RepairOperator

NILAI_OPTIMAL = 784
MAKS_ITERASI = 2000
SEED = 42

folder = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(folder, "A", "A-n32-k5.vrp")
daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path)
instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)

solusi_awal = ConstructionHeuristic(instance).nearest_neighbor()
print(f"\nSolusi awal: {solusi_awal.total_jarak}\n")


# =============================================================================
# SATU KALI JALAN, SAMBIL MENGAMATI BOBOTNYA BERUBAH
# =============================================================================
print("=" * 72)
print(f" ALNS LENGKAP {MAKS_ITERASI} ITERASI")
print("=" * 72)

random.seed(SEED)
pencari = ALNS(instance, maks_iterasi=MAKS_ITERASI,
               reaction_factor=0.3, panjang_segmen=100,
               tampilkan_setiap=500)

mulai = time.time()
hasil = pencari.jalankan(solusi_awal)
waktu = time.time() - mulai

print("=" * 72)
print(f"  Waktu: {waktu:.1f} detik, diterima "
      f"{pencari.jumlah_diterima} iterasi")
print("=" * 72)

print()
hasil.cetak("SOLUSI AKHIR ALNS")


# =============================================================================
# BAGAIMANA BOBOT BERUBAH SEPANJANG PENCARIAN
# =============================================================================
print("=" * 72)
print(" PERJALANAN BOBOT TIAP OPERATOR")
print("=" * 72)
semua = DestroyOperator.DAFTAR + RepairOperator.DAFTAR

print("""  Hal yang penting bukan besar bobotnya, melainkan perbandingannya.
  Roulette wheel memakai peluang  p_i = w_i / jumlah w, jadi di bawah ini
  bobot sudah diubah menjadi persen peluang terpilih.
""")
print(f"  {'Iterasi':>8} | " + " | ".join(f"{n[:17]:>17}" for n in semua))
print("  " + "-" * 84)

for iterasi, bd, br in pencari.riwayat_bobot[::3]:
    total_d, total_r = sum(bd.values()), sum(br.values())
    baris = []
    for n in semua:
        if n in bd:
            baris.append(f"{bd[n] / total_d * 100:>16.1f}%")
        else:
            baris.append(f"{br[n] / total_r * 100:>16.1f}%")
    print(f"  {iterasi:>8} | " + " | ".join(baris))

print()
print("  Hasil akhir:")
td = sum(pencari.bobot_destroy.values())
tr = sum(pencari.bobot_repair.values())
for nama in semua:
    if nama in pencari.bobot_destroy:
        peluang = pencari.bobot_destroy[nama] / td * 100
    else:
        peluang = pencari.bobot_repair[nama] / tr * 100
    print(f"    {nama:<20} peluang {peluang:>5.1f}% | "
          f"dipakai {pencari.pemakaian[nama]:>5} kali")

print("""
  Dua hal yang layak diperhatikan:

  1. Peluangnya BERGESER dari 50-50 pada awal segmen. ALNS menemukan
     sendiri operator mana yang berguna dan kita tidak pernah memberitahunya.

  2. Angka mutlak bobot menyusut terus. Itu wajar: makin lama suhu makin
     dingin, makin sedikit solusi baru yang diterima, jadi skor yang
     masuk makin kecil.
""")


# =============================================================================
# JANGAN MENILAI DARI SATU KALI JALAN
# =============================================================================
print("=" * 72)
print(" UJI LIMA SEED: ADAPTIF vs BOBOT TETAP")
print("=" * 72)
print("""  Di Tahap 17 kebetulan kita mendapat 784 persis. Itu SATU kali jalan
  dengan SATU seed. Algoritma acak tidak boleh dinilai begitu.

  Sekarang kita jalankan lima kali dengan seed berbeda.
""")

print(f"  {'Seed':>5} | {'Bobot tetap (r=0)':>19} | {'Adaptif (r=0.3)':>17}")
print("  " + "-" * 50)

hasil_tetap, hasil_adaptif = [], []
for seed in range(1, 6):
    random.seed(seed)
    a = ALNS(instance, maks_iterasi=MAKS_ITERASI, reaction_factor=0.0,
             panjang_segmen=100, tampilkan_setiap=0).jalankan(solusi_awal)
    random.seed(seed)
    b = ALNS(instance, maks_iterasi=MAKS_ITERASI, reaction_factor=0.3,
             panjang_segmen=100, tampilkan_setiap=0).jalankan(solusi_awal)

    hasil_tetap.append(a.total_jarak)
    hasil_adaptif.append(b.total_jarak)
    print(f"  {seed:>5} | {a.total_jarak:>19} | {b.total_jarak:>17}")

print("  " + "-" * 50)
rata_t = sum(hasil_tetap) / len(hasil_tetap)
rata_a = sum(hasil_adaptif) / len(hasil_adaptif)
print(f"  {'Rata-rata':>5} | {rata_t:>19.1f} | {rata_a:>17.1f}")
print(f"  {'Terbaik':>5} | {min(hasil_tetap):>19} | {min(hasil_adaptif):>17}")
print(f"  {'Terburuk':>5} | {max(hasil_tetap):>19} | {max(hasil_adaptif):>17}")
print("  " + "-" * 50)

print(f"""
  Hal yang perlu diperhatikan bukan hanya nilai terbaik, melainkan juga
  nilai terburuk dan rata-ratanya. Algoritma yang baik adalah yang
  hasilnya stabil, bukan yang sesekali beruntung.

  Nilai optimal instance ini: {NILAI_OPTIMAL}
""")

# -----------------------------------------------------------------------------
# LATIHAN 19.1
#   Ubah reaction_factor menjadi 0.0, 0.1, 0.5, dan 1.0.
#   Bagaimana bentuk perjalanan bobotnya? Mana yang paling stabil?
#
# LATIHAN 19.2
#   Ubah panjang_segmen menjadi 20 (sering diperbarui) lalu 500 (jarang).
#   Apa akibatnya terhadap bobot?
# -----------------------------------------------------------------------------
