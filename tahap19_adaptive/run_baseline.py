import os
import sys

# Folder tempat script ini berada (folder tahap19_adaptive)
folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
# Folder induk (TI4006_ALNS)
dir_root = os.path.dirname(folder_tahap19)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

import csv
import math
import random
import time

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance

SEEDS = [1, 2, 3, 4, 5]
INSTANCES = [
    {"nama": "X-n101-k25.vrp", "bks": 27591, "label": "X-n101-k25 (K=25)"},
    {"nama": "X-n143-k7.vrp", "bks": 15700, "label": "X-n143-k7 (K=7)"},
    {"nama": "X-n351-k40.vrp", "bks": 25896, "label": "X-n351-k40 (K=40)"},
]


# Folder X berada langsung di dalam folder tahap19_adaptive
folder_x = os.path.join(folder_tahap19, "X")
csv_path_root = os.path.join(dir_root, "hasil_mentah_baseline.csv")
csv_path_local = os.path.join(folder_tahap19, "hasil_mentah_baseline.csv")

hasil_rekap = []

CONFIGS = [
    (
        "Baseline",
        {
            "pakai_ls": False,
            "pakai_shaw": False,
            "pakai_reheating": False,
            "pakai_regret3": False,
        },
    ),
    (
        "Full",
        {
            "pakai_ls": True,
            "pakai_shaw": True,
            "pakai_reheating": True,
            "pakai_regret3": True,
        },
    ),
]

with open(csv_path_root, "w", newline="", encoding="utf-8") as f_csv_root, \
     open(csv_path_local, "w", newline="", encoding="utf-8") as f_csv_local:
    writer_root = csv.writer(f_csv_root)
    writer_local = csv.writer(f_csv_local)
    writer_root.writerow(["instance", "seed", "konfigurasi", "jarak", "waktu_detik", "status"])
    writer_local.writerow(["instance", "seed", "konfigurasi", "jarak", "waktu_detik", "status"])

    for cfg_name, cfg_params in CONFIGS:
        print("\n" + "=" * 70, flush=True)
        print(f"KONFIGURASI: {cfg_name.upper()} {cfg_params}", flush=True)
        print("=" * 70, flush=True)

        for inst_info in INSTANCES:
            path_vrp = os.path.join(folder_x, inst_info["nama"])
            if not os.path.exists(path_vrp):
                print(f"[ERROR] File tidak ditemukan: {path_vrp}")
                continue

            daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
            instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
            k_efektif = instance.cari_armada_minimal_layak(verbose=False)

            jarak_seed = []
            waktu_seed = []
            sol_terbaik_instance = None

            print(f"\n--- {inst_info['nama']} (BKS: {inst_info['bks']}, Armada Nominal: {instance.jumlah_kendaraan}, Target Armada: {k_efektif}) ---", flush=True)

            for seed in SEEDS:
                random.seed(seed)
                solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

                pencari = ALNS(
                    instance,
                    maks_iterasi=2000,
                    tampilkan_setiap=0,
                    **cfg_params
                )

                t_mulai = time.time()
                hasil = pencari.jalankan(solusi_awal)
                t_selesai = time.time() - t_mulai

                is_layak = hasil.layak()
                status = "LAYAK" if is_layak else "TIDAK LAYAK"
                lbl = inst_info.get("label", inst_info["nama"])
                row = [lbl, seed, cfg_name, hasil.total_jarak, f"{t_selesai:.2f}", status]
                writer_root.writerow(row)
                writer_local.writerow(row)
                f_csv_root.flush()
                f_csv_local.flush()

                jarak_seed.append(hasil.total_jarak)
                waktu_seed.append(t_selesai)
                print(f"  [{cfg_name}] Seed {seed}: Jarak = {hasil.total_jarak} | Rute = {hasil.jumlah_rute} | Waktu = {t_selesai:.2f}s | {status}", flush=True)

                if cfg_name == "Full":
                    if sol_terbaik_instance is None or hasil.total_jarak < sol_terbaik_instance.total_jarak:
                        sol_terbaik_instance = hasil.copy()

            if cfg_name == "Full" and sol_terbaik_instance is not None:
                nama_bersih = inst_info["nama"].replace(".vrp", "")
                path_sol_inst = os.path.join(folder_tahap19, f"solusi_terbaik_{nama_bersih}.sol")
                sol_terbaik_instance.simpan_cvrplib_sol(path_sol_inst)
                print(f"  >>> [EKSPOR .SOL] Solusi terbaik {nama_bersih} disimpan ke {path_sol_inst} (Cost: {sol_terbaik_instance.total_jarak}, Rute: {sol_terbaik_instance.jumlah_rute})", flush=True)

            terbaik = min(jarak_seed)
            terburuk = max(jarak_seed)
            rata_rata = sum(jarak_seed) / len(jarak_seed)
            std = math.sqrt(sum((x - rata_rata) ** 2 for x in jarak_seed) / len(jarak_seed))
            gap_best = ((terbaik - inst_info["bks"]) / inst_info["bks"]) * 100
            gap_avg = ((rata_rata - inst_info["bks"]) / inst_info["bks"]) * 100
            waktu_avg = sum(waktu_seed) / len(waktu_seed)

            hasil_rekap.append({
                "Konfigurasi": cfg_name,
                "Instance": inst_info.get("label", inst_info["nama"].replace(".vrp", "")),
                "BKS": inst_info["bks"],
                "Terbaik": terbaik,
                "Rata-rata": f"{rata_rata:.2f}",
                "Terburuk": terburuk,
                "Std": f"{std:.2f}",
                "Gap Best (%)": f"{gap_best:.2f}%",
                "Gap Avg (%)": f"{gap_avg:.2f}%",
                "Waktu Avg (s)": f"{waktu_avg:.2f}",
            })


print("\n" + "=" * 115, flush=True)
print("RINGKASAN HASIL EVALUASI BASELINE VS FULL (SESUAI SLIDE 7 PANDUAN TUGAS)", flush=True)
print("=" * 115, flush=True)
print(f" {'Konfigurasi':<11} | {'Instance':<15} | {'BKS':>6} | {'Terbaik':>7} | {'Rata-rata':>9} | {'Terburuk':>8} | {'Std Dev':>8} | {'Gap Best':>8} | {'Gap Avg':>8} | {'Waktu (s)':>9}")
print("-" * 115, flush=True)
for r in hasil_rekap:
    print(f" {r['Konfigurasi']:<11} | {r['Instance']:<15} | {r['BKS']:>6} | {r['Terbaik']:>7} | {r['Rata-rata']:>9} | {r['Terburuk']:>8} | {r['Std']:>8} | {r['Gap Best (%)']:>8} | {r['Gap Avg (%)']:>8} | {r['Waktu Avg (s)']:>9}")
print("=" * 115, flush=True)

