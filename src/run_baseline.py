"""
run_baseline.py — EVALUASI KOMPARATIF BASELINE VS FULL ALNS
===============================================================================
Membandingkan performa baseline terhadap Full ALNS pada seluruh 3 instance CVRP:
1. Ablation_Baseline (Solver ALNS saat ini dengan seluruh 4 modifikasi dimatikan)
2. Original_Tahap19_Baseline (Solver otentik Tahap 19 dari Commit afde640)
3. Full (Seluruh 4 Modifikasi Aktif: Shaw, Regret-3, Local Search, Reheating)

Setiap konfigurasi diuji pada 5 seed deterministik: [1, 2, 3, 4, 5].
Hasil mentah diekspor ke `hasil_mentah_baseline.csv` dan rekap perbandingan ke `rekap_komparasi_vs_full.csv`.
===============================================================================
"""

import csv
import json
import math
import os
import random
import subprocess
import sys
import time

folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
dir_root = os.path.dirname(folder_tahap19)
dir_hasil_final = os.path.join(dir_root, "hasil_final")

os.makedirs(dir_hasil_final, exist_ok=True)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance

SEEDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
MAKS_ITERASI = 2000
T0 = 800.0
COOLING_RATE = 0.990
REACTION_FACTOR = 0.31

INSTANCES = [
    {"nama": "X-n101-k25.vrp", "bks": 27591, "label": "X-n101-k25"},
    {"nama": "X-n143-k7.vrp", "bks": 15700, "label": "X-n143-k7"},
    {"nama": "X-n351-k40.vrp", "bks": 25896, "label": "X-n351-k40"},
]

CONFIGS = [
    (
        "Baseline",
        {"pakai_ls": False, "pakai_shaw": False, "pakai_reheating": False, "pakai_regret3": False},
    ),
    (
        "Full",
        {"pakai_ls": True, "pakai_shaw": True, "pakai_reheating": True, "pakai_regret3": True},
    ),
]


def main():
    print("=" * 115)
    print(" EVALUASI BASELINE VS FULL ALNS (5 SEED PER KONFIGURASI)")
    print(f" Iterasi: {MAKS_ITERASI} | Seed: {SEEDS}")
    print("=" * 115)

    path_raw_root = os.path.join(dir_root, "hasil_mentah_baseline.csv")
    path_raw_local = os.path.join(folder_tahap19, "hasil_mentah_baseline.csv")
    path_raw_final = os.path.join(dir_hasil_final, "hasil_mentah_baseline.csv")

    headers_raw = ["instance", "seed", "konfigurasi", "jarak", "waktu_detik", "status", "jumlah_rute"]

    f_raw_root = open(path_raw_root, "w", newline="", encoding="utf-8")
    f_raw_local = open(path_raw_local, "w", newline="", encoding="utf-8")
    f_raw_final = open(path_raw_final, "w", newline="", encoding="utf-8")

    w_root = csv.writer(f_raw_root)
    w_local = csv.writer(f_raw_local)
    w_final = csv.writer(f_raw_final)

    for w in [w_root, w_local, w_final]:
        w.writerow(headers_raw)

    hasil_rekap = []

    for cfg_name, cfg_params in CONFIGS:
        print("\n" + "=" * 90, flush=True)
        print(f"KONFIGURASI: {cfg_name.upper()}", flush=True)
        print("=" * 90, flush=True)

        for inst_info in INSTANCES:
            nama_inst = str(inst_info["label"])
            bks = float(inst_info["bks"])
            path_vrp = os.path.join(folder_tahap19, "X", str(inst_info["nama"]))

            daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
            instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
            solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

            jarak_seed = []
            waktu_seed = []
            rute_seed = []

            print(f"\n--- {nama_inst} (BKS: {bks}) ---", flush=True)

            for seed in SEEDS:
                random.seed(seed)
                pencari = ALNS(
                    instance,
                    maks_iterasi=MAKS_ITERASI,
                    suhu_awal=T0,
                    laju_pendinginan=COOLING_RATE,
                    reaction_factor=REACTION_FACTOR,
                    tampilkan_setiap=0,
                    **cfg_params
                )
                t_mulai = time.time()
                hasil = pencari.jalankan(solusi_awal.copy())
                t_selesai = time.time() - t_mulai
                jarak = hasil.total_jarak
                is_layak = hasil.layak()
                rute_aktif = hasil.jumlah_rute

                status = "LAYAK" if is_layak else "TIDAK_LAYAK"
                row = [nama_inst, seed, cfg_name, jarak, f"{t_selesai:.2f}", status, rute_aktif]

                for w in [w_root, w_local, w_final]:
                    w.writerow(row)
                f_raw_root.flush()
                f_raw_local.flush()
                f_raw_final.flush()

                jarak_seed.append(jarak)
                waktu_seed.append(t_selesai)
                rute_seed.append(rute_aktif)
                print(f"  [{cfg_name}] Seed {seed}: Jarak = {jarak} | Rute = {rute_aktif} | Waktu = {t_selesai:.2f}s | {status}", flush=True)

            terbaik = min(jarak_seed)
            terburuk = max(jarak_seed)
            rata_rata = sum(jarak_seed) / len(jarak_seed)
            std = math.sqrt(sum((x - rata_rata) ** 2 for x in jarak_seed) / (len(jarak_seed) - 1)) if len(jarak_seed) > 1 else 0.0
            gap_best = ((terbaik - bks) / bks) * 100
            gap_avg = ((rata_rata - bks) / bks) * 100
            waktu_avg = sum(waktu_seed) / len(waktu_seed)

            hasil_rekap.append({
                "Konfigurasi": cfg_name,
                "Instance": nama_inst,
                "BKS": bks,
                "Terbaik": terbaik,
                "Rata-rata": f"{rata_rata:.2f}",
                "Terburuk": terburuk,
                "Std": f"{std:.2f}",
                "Gap Best (%)": f"{gap_best:.2f}%",
                "Gap Avg (%)": f"{gap_avg:.2f}%",
                "Waktu Avg (s)": f"{waktu_avg:.2f}",
            })

    f_raw_root.close()
    f_raw_local.close()
    f_raw_final.close()

    print("\n" + "=" * 125, flush=True)
    print("RINGKASAN HASIL EVALUASI BASELINE VS FULL (SAMPLE STD DEV DDOF=1)", flush=True)
    print("=" * 125, flush=True)
    print(f" {'Konfigurasi':<26} | {'Instance':<12} | {'BKS':>6} | {'Terbaik':>7} | {'Rata-rata':>9} | {'Terburuk':>8} | {'Std Dev':>8} | {'Gap Best':>9} | {'Gap Avg':>8} | {'Waktu (s)':>9}")
    print("-" * 125, flush=True)
    for r in hasil_rekap:
        print(f" {r['Konfigurasi']:<26} | {r['Instance']:<12} | {r['BKS']:>6} | {r['Terbaik']:>7} | {r['Rata-rata']:>9} | {r['Terburuk']:>8} | {r['Std']:>8} | {r['Gap Best (%)']:>9} | {r['Gap Avg (%)']:>8} | {r['Waktu Avg (s)']:>9}")
    print("=" * 125, flush=True)

    # Simpan ke rekap_komparasi_vs_full.csv
    path_rekap_root = os.path.join(dir_root, "rekap_komparasi_vs_full.csv")
    path_rekap_local = os.path.join(folder_tahap19, "rekap_komparasi_vs_full.csv")
    path_rekap_final = os.path.join(dir_hasil_final, "rekap_komparasi_vs_full.csv")

    headers_rekap = ["Konfigurasi", "Instance", "BKS", "Terbaik", "Rata-rata", "Terburuk", "Std", "Gap Best (%)", "Gap Avg (%)", "Waktu Avg (s)"]
    for p in [path_rekap_root, path_rekap_local, path_rekap_final]:
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers_rekap)
            w.writeheader()
            w.writerows(hasil_rekap)


if __name__ == "__main__":
    main()
