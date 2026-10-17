"""
run_ablation.py — STUDI ABLASI KONTRIBUSI MODIFIKASI ALNS (SLIDE 8 PANDUAN)
===============================================================================
Membuktikan kegunaan masing-masing modifikasi ALNS secara empiris:
1. Full ALNS (Seluruh 4 Modifikasi Aktif)
2. Tanpa Modifikasi 1: Tanpa Shaw Removal (pakai_shaw=False)
3. Tanpa Modifikasi 2: Tanpa Regret-3 Insertion (pakai_regret3=False)
4. Tanpa Modifikasi 3: Tanpa Intensifikasi Local Search (pakai_ls=False)
5. Tanpa Modifikasi 4: Tanpa Reheating Suhu SA (pakai_reheating=False)
6. Baseline (Seluruh modifikasi dimatikan)

Setiap konfigurasi diuji dalam 5 seed (1, 2, 3, 4, 5) sesuai aturan Slide 6.
Hasil dilaporkan lengkap dengan: Terbaik, Rata-rata, Terburuk, Simpangan Baku,
Gap (%) terhadap BKS, dan Delta Kinerja relatif terhadap Full ALNS.
===============================================================================
"""

import csv
import math
import os
import random
import sys
import time

folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
dir_root = os.path.dirname(folder_tahap19)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance

SEEDS = [1, 2, 3, 4, 5]
BKS = 27591
NAMA_INSTANCE = "X-n101-k25.vrp"

KONFIGURASI_ABLATION = [
    (
        "Full ALNS",
        {"pakai_shaw": True, "pakai_regret3": True, "pakai_ls": True, "pakai_reheating": True},
        "Semua 4 Modifikasi Aktif"
    ),
    (
        "Tanpa Shaw",
        {"pakai_shaw": False, "pakai_regret3": True, "pakai_ls": True, "pakai_reheating": True},
        "Hapus Shaw Removal (Hanya Random & Worst)"
    ),
    (
        "Tanpa Regret-3",
        {"pakai_shaw": True, "pakai_regret3": False, "pakai_ls": True, "pakai_reheating": True},
        "Hapus Regret-3 (Hanya Greedy & Regret-2)"
    ),
    (
        "Tanpa Local Search",
        {"pakai_shaw": True, "pakai_regret3": True, "pakai_ls": False, "pakai_reheating": True},
        "Hapus Pemolesan Rekor Local Search"
    ),
    (
        "Tanpa Reheating",
        {"pakai_shaw": True, "pakai_regret3": True, "pakai_ls": True, "pakai_reheating": False},
        "Hapus Mekanisme Reheating Suhu SA"
    ),
    (
        "Baseline",
        {"pakai_shaw": False, "pakai_regret3": False, "pakai_ls": False, "pakai_reheating": False},
        "ALNS Standar Tanpa Modifikasi"
    ),
]


def main():
    print("=" * 105)
    print(" STUDI ABLASI MODIFIKASI ALNS (SESUAI SLIDE 8 PANDUAN TUGAS)")
    print(f" Instance: {NAMA_INSTANCE} | BKS = {BKS} | Evaluasi 5 Seed: {SEEDS}")
    print("=" * 105)

    path_vrp = os.path.join(folder_tahap19, "X", NAMA_INSTANCE)
    daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
    instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
    k_eff = instance.cari_armada_minimal_layak(verbose=False)
    solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

    rekap_ablasi = []
    raw_rows = []
    full_mean_cost = None

    for nama_cfg, params, desc in KONFIGURASI_ABLATION:
        print(f"\n---> Menguji Konfigurasi: {nama_cfg:<20} ({desc})", flush=True)
        costs = []
        times = []

        for seed in SEEDS:
            random.seed(seed)
            a = ALNS(
                instance,
                maks_iterasi=1500,
                suhu_awal=800.0,
                laju_pendinginan=0.990,
                reaction_factor=0.31,
                tampilkan_setiap=0,
                **params
            )
            t0 = time.time()
            res = a.jalankan(solusi_awal)
            dur = time.time() - t0
            assert res.layak(), f"Solusi {nama_cfg} seed {seed} tidak layak!"

            costs.append(res.total_jarak)
            times.append(dur)
            raw_rows.append([NAMA_INSTANCE, seed, nama_cfg, res.total_jarak, f"{dur:.2f}", "LAYAK"])
            print(f"      Seed {seed}: Jarak = {res.total_jarak:>5} | Waktu = {dur:.2f}s | LAYAK", flush=True)

        best = min(costs)
        worst = max(costs)
        mean_c = sum(costs) / len(costs)
        std_c = math.sqrt(sum((c - mean_c) ** 2 for c in costs) / len(costs))
        gap_best = ((best - BKS) / BKS) * 100
        gap_mean = ((mean_c - BKS) / BKS) * 100
        mean_t = sum(times) / len(times)

        if nama_cfg == "Full ALNS":
            full_mean_cost = mean_c
            delta_vs_full = 0.0
        else:
            delta_vs_full = mean_c - full_mean_cost

        rekap_ablasi.append({
            "konfigurasi": nama_cfg,
            "keterangan": desc,
            "terbaik": best,
            "rata_rata": mean_c,
            "terburuk": worst,
            "std": std_c,
            "gap_best": gap_best,
            "gap_mean": gap_mean,
            "delta_full": delta_vs_full,
            "waktu_avg": mean_t,
        })

    # Cetak Tabel Rekapitulasi Studi Ablasi Sesuai Slide 7 & 8
    print("\n" + "=" * 115)
    print(" TABEL HASIL STUDI ABLASI KONTRIBUSI MODIFIKASI (5 SEED)")
    print("=" * 115)
    print(f" {'Konfigurasi':<19} | {'Terbaik':>7} | {'Rata-rata':>9} | {'Terburuk':>8} | {'Std Dev':>8} | {'Gap Best':>8} | {'Gap Rata':>8} | {'Delta vs Full':>13}")
    print("-" * 115)
    for r in rekap_ablasi:
        tanda = f"+{r['delta_full']:>6.1f}" if r['delta_full'] > 0 else (f"{r['delta_full']:>7.1f}" if r['delta_full'] < 0 else "      0.0 (Ref)")
        print(
            f" {r['konfigurasi']:<19} | {r['terbaik']:>7} | {r['rata_rata']:>9.1f} | {r['terburuk']:>8} | "
            f"{r['std']:>8.1f} | +{r['gap_best']:>6.2f}% | +{r['gap_mean']:>6.2f}% | {tanda:>13}"
        )
    print("=" * 115)

    print("\n  ANALISIS KONTRIBUSI INDIVIDUAL MASING-MASING MODIFIKASI:")
    for r in rekap_ablasi:
        if r["konfigurasi"] == "Full ALNS":
            continue
        if r["konfigurasi"] == "Baseline":
            print(f"  * {r['konfigurasi']:<19}: Gap rata-rata meningkat sebesar +{r['delta_full']:.1f} poin dibanding Full ALNS (+{r['gap_mean']:.2f}% vs +{rekap_ablasi[0]['gap_mean']:.2f}%).")
        else:
            status = "MEMPERBURUK" if r["delta_full"] > 0 else "MEMPENGARUHI"
            print(f"  * {r['konfigurasi']:<19}: Mematikan fitur ini {status} solusi rata-rata sebesar +{r['delta_full']:.1f} unit jarak.")

    # Simpan ke CSV
    path_csv_rekap = os.path.join(folder_tahap19, "hasil_studi_ablasi.csv")
    path_csv_root = os.path.join(dir_root, "hasil_studi_ablasi.csv")
    with open(path_csv_rekap, "w", newline="", encoding="utf-8") as f, \
         open(path_csv_root, "w", newline="", encoding="utf-8") as f_root:
        writer = csv.writer(f)
        writer_root = csv.writer(f_root)
        header = ["konfigurasi", "keterangan", "terbaik", "rata_rata", "terburuk", "std_dev", "gap_best_persen", "gap_mean_persen", "delta_vs_full", "waktu_avg_detik"]
        writer.writerow(header)
        writer_root.writerow(header)
        for r in rekap_ablasi:
            row = [r["konfigurasi"], r["keterangan"], r["terbaik"], f"{r['rata_rata']:.2f}", r["terburuk"], f"{r['std']:.2f}", f"{r['gap_best']:.2f}%", f"{r['gap_mean']:.2f}%", f"{r['delta_full']:.2f}", f"{r['waktu_avg']:.2f}"]
            writer.writerow(row)
            writer_root.writerow(row)

    print(f"\n  [CSV] Berkas hasil studi ablasi disimpan di: {path_csv_rekap}")


if __name__ == "__main__":
    main()
