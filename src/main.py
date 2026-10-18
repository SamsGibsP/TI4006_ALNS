"""
TAHAP 19 — ALNS LENGKAP: ADAPTIF, MULTI-SEED, & PEMOLES LOCAL SEARCH
===============================================================================
Eksperimen komparatif:
1. Satu kali jalan ALNS Adaptif dengan analisis pergeseran bobot operator.
2. Uji Multi-Seed (5 Seed) membandingkan:
   - Random Search (kontrol acak)
   - Bobot Tetap (r = 0.0)
   - ALNS Adaptif (r = 0.3)
   - ALNS Adaptif + Pemoles Local Search (2-Opt, Relocate, Swap)
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
from local_search import LocalSearch
from repair import RepairOperator

NILAI_OPTIMAL = 25896
MAKS_ITERASI = 2000
SEED = 42

folder = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(folder, "X", "X-n351-k40.vrp")
daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path)
instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)

solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()
print(f"\nSolusi awal : {solusi_awal.total_jarak}")
assert solusi_awal.layak(), f"Solusi awal TIDAK LAYAK: {solusi_awal.daftar_pelanggaran()}"
print(f"Status kelayakan solusi awal: LAYAK\n")


# =============================================================================
# 1. SATU KALI JALAN ALNS ADAPTIF
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
print(f"  Waktu: {waktu:.1f} detik, diterima {pencari.jumlah_diterima} iterasi")
print("=" * 72)

# Poles hasil akhir dengan Local Search
ls = LocalSearch(instance, operators=["2opt", "relocate", "swap"], max_iterations=50)
hasil_poles = ls.run(hasil, nilai_optimal=NILAI_OPTIMAL, verbose=False)

print()
hasil_poles.cetak("SOLUSI AKHIR ALNS + LOCAL SEARCH")

# Ekspor berkas solusi format standar CVRPLIB .sol
nama_instance = os.path.splitext(os.path.basename(path))[0]
path_sol_out = os.path.join(folder, f"solusi_terbaik_{nama_instance}.sol")
hasil_poles.simpan_cvrplib_sol(path_sol_out)
print(f"  [EKSPOR SOLUSI] Berkas .sol tersimpan di: {path_sol_out}")


# =============================================================================
# 2. PERJALANAN BOBOT TIAP OPERATOR
# =============================================================================
print("=" * 72)
print(" PERJALANAN BOBOT TIAP OPERATOR")
print("=" * 72)
semua = DestroyOperator.DAFTAR + RepairOperator.DAFTAR

print("""  Hal yang penting bukan besar bobotnya, melainkan perbandingannya.
  Roulette wheel memakai peluang  p_i = w_i / jumlah w, jadi di bawah ini
  bobot sudah diubah menjadi persen peluang terpilih.
""")
lebar_tabel = 10 + len(semua) * 20
print(f"  {'Iterasi':>8} | " + " | ".join(f"{n[:17]:>17}" for n in semua))
print("  " + "-" * lebar_tabel)

for iterasi, bd, br in pencari.riwayat_bobot[::3]:
    total_d, total_r = sum(bd.values()), sum(br.values())
    baris = []
    for n in semua:
        if n in bd:
            baris.append(f"{bd[n] / total_d * 100:>16.1f}%")
        elif n in br:
            baris.append(f"{br[n] / total_r * 100:>16.1f}%")
        else:
            baris.append(f"{'-':>17}")
    print(f"  {iterasi:>8} | " + " | ".join(baris))

print()
print("  Hasil akhir:")
td = sum(pencari.bobot_destroy.values())
tr = sum(pencari.bobot_repair.values())
for nama in semua:
    if nama in pencari.bobot_destroy:
        peluang = pencari.bobot_destroy[nama] / td * 100
    elif nama in pencari.bobot_repair:
        peluang = pencari.bobot_repair[nama] / tr * 100
    else:
        continue
    print(f"    {nama:<20} peluang {peluang:>5.1f}% | dipakai {pencari.pemakaian.get(nama, 0):>5} kali")


# =============================================================================
# 3. UJI LIMA SEED LENGKAP: 4 METODE PEMBANDING (STUDI ABLASI)
# =============================================================================
print()
print("=" * 90)
print(" UJI LIMA SEED: RANDOM SEARCH vs BOBOT TETAP vs ADAPTIF vs FULL ALNS (4 MODIFIKASI)")
print("=" * 90)

print(f"  {'Seed':>5} | {'Random Search':>15} | {'Tetap (r=0)':>13} | {'Adaptif':>12} | {'Full ALNS':>14}")
print("  " + "-" * 72)

hasil_random, hasil_tetap, hasil_adaptif, hasil_full = [], [], [], []

for seed in range(42, 47):
    # A. RANDOM SEARCH (Tanpa adaptif, tanpa modifikasi, random walk)
    random.seed(seed)
    sol_rand = ALNS(
        instance, maks_iterasi=MAKS_ITERASI, mode_random_search=True,
        pakai_ls=False, pakai_shaw=False, pakai_reheating=False, pakai_regret3=False,
        panjang_segmen=100, tampilkan_setiap=0
    ).jalankan(solusi_awal)

    # B. BOBOT TETAP (Baseline r = 0.0, SA normal)
    random.seed(seed)
    sol_tetap = ALNS(
        instance, maks_iterasi=MAKS_ITERASI, reaction_factor=0.0, mode_random_search=False,
        pakai_ls=False, pakai_shaw=False, pakai_reheating=False, pakai_regret3=False,
        panjang_segmen=100, tampilkan_setiap=0
    ).jalankan(solusi_awal)

    # C. ADAPTIF (r = 0.3, SA normal tanpa modifikasi)
    random.seed(seed)
    sol_adap = ALNS(
        instance, maks_iterasi=MAKS_ITERASI, reaction_factor=0.3, mode_random_search=False,
        pakai_ls=False, pakai_shaw=False, pakai_reheating=False, pakai_regret3=False,
        panjang_segmen=100, tampilkan_setiap=0
    ).jalankan(solusi_awal)

    # D. FULL ALNS (4 Modifikasi: Shaw + Regret3 + Reheating + Local Search)
    random.seed(seed)
    sol_full = ALNS(
        instance, maks_iterasi=MAKS_ITERASI, reaction_factor=0.3, mode_random_search=False,
        pakai_ls=True, pakai_shaw=True, pakai_reheating=True, pakai_regret3=True,
        panjang_segmen=100, tampilkan_setiap=0
    ).jalankan(solusi_awal)

    assert sol_full.layak(), f"Solusi Full ALNS Seed {seed} TIDAK LAYAK!"

    hasil_random.append(sol_rand.total_jarak)
    hasil_tetap.append(sol_tetap.total_jarak)
    hasil_adaptif.append(sol_adap.total_jarak)
    hasil_full.append(sol_full.total_jarak)

    print(f"  {seed:>5} | {sol_rand.total_jarak:>15} | {sol_tetap.total_jarak:>13} | {sol_adap.total_jarak:>12} | {sol_full.total_jarak:>14}")

print("  " + "-" * 72)
print(f"  {'Rata':>5} | {sum(hasil_random)/5:>15.1f} | {sum(hasil_tetap)/5:>13.1f} | {sum(hasil_adaptif)/5:>12.1f} | {sum(hasil_full)/5:>14.1f}")
print(f"  {'Terbaik':>5} | {min(hasil_random):>15} | {min(hasil_tetap):>13} | {min(hasil_adaptif):>12} | {min(hasil_full):>14}")
print(f"  {'Terburuk':>5} | {max(hasil_random):>15} | {max(hasil_tetap):>13} | {max(hasil_adaptif):>12} | {max(hasil_full):>14}")
print("  " + "-" * 72)

gap_best = ((min(hasil_full) - NILAI_OPTIMAL) / NILAI_OPTIMAL) * 100
gap_avg = ((sum(hasil_full)/5 - NILAI_OPTIMAL) / NILAI_OPTIMAL) * 100
print(f"""
  Nilai BKS Instance ini : {NILAI_OPTIMAL}
  Gap Terbaik (Full ALNS): +{gap_best:.2f}%
  Gap Rata-rata          : +{gap_avg:.2f}%
""")