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
    {"nama": "X-n101-k25.vrp", "bks": 27591},
    {"nama": "X-n143-k7.vrp", "bks": 15700},
    {"nama": "X-n351-k40.vrp", "bks": 25896},
]

# Folder X berada langsung di dalam folder tahap19_adaptive
folder_x = os.path.join(folder_tahap19, "X")
csv_path_root = os.path.join(dir_root, "hasil_mentah_baseline.csv")
csv_path_local = os.path.join(folder_tahap19, "hasil_mentah_baseline.csv")

hasil_rekap = []

with open(csv_path_root, "w", newline="", encoding="utf-8") as f_csv_root, \
     open(csv_path_local, "w", newline="", encoding="utf-8") as f_csv_local:
    writer_root = csv.writer(f_csv_root)
    writer_local = csv.writer(f_csv_local)
    writer_root.writerow(["instance", "seed", "konfigurasi", "jarak", "waktu_detik", "status"])
    writer_local.writerow(["instance", "seed", "konfigurasi", "jarak", "waktu_detik", "status"])

    for inst_info in INSTANCES:
        path_vrp = os.path.join(folder_x, inst_info["nama"])
        if not os.path.exists(path_vrp):
            print(f"[ERROR] File tidak ditemukan: {path_vrp}")
            continue

        daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
        instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)

        jarak_seed = []
        waktu_seed = []

        print("=" * 60, flush=True)
        print(f"Menjalankan Baseline: {inst_info['nama']} (BKS: {inst_info['bks']})", flush=True)
        print("=" * 60, flush=True)

        for seed in SEEDS:
            random.seed(seed)
            solusi_awal = ConstructionHeuristic(instance).nearest_neighbor()

            pencari = ALNS(instance, maks_iterasi=2000, tampilkan_setiap=0)

            t_mulai = time.time()
            hasil = pencari.jalankan(solusi_awal)
            t_selesai = time.time() - t_mulai

            status = "LAYAK" if hasil.layak() else "TIDAK LAYAK"
            row = [inst_info["nama"], seed, "Baseline", hasil.total_jarak, f"{t_selesai:.2f}", status]
            writer_root.writerow(row)
            writer_local.writerow(row)
            f_csv_root.flush()
            f_csv_local.flush()


            jarak_seed.append(hasil.total_jarak)
            waktu_seed.append(t_selesai)
            print(f"  Seed {seed}: Jarak = {hasil.total_jarak} | Waktu = {t_selesai:.2f}s | {status}", flush=True)

        terbaik = min(jarak_seed)
        terburuk = max(jarak_seed)
        rata_rata = sum(jarak_seed) / len(jarak_seed)
        std = math.sqrt(sum((x - rata_rata) ** 2 for x in jarak_seed) / len(jarak_seed))
        gap_best = ((terbaik - inst_info["bks"]) / inst_info["bks"]) * 100
        gap_avg = ((rata_rata - inst_info["bks"]) / inst_info["bks"]) * 100
        waktu_avg = sum(waktu_seed) / len(waktu_seed)

        hasil_rekap.append({
            "Instance": inst_info["nama"].replace(".vrp", ""),
            "BKS": inst_info["bks"],
            "Terbaik": terbaik,
            "Rata-rata": f"{rata_rata:.2f}",
            "Terburuk": terburuk,
            "Std": f"{std:.2f}",
            "Gap Best (%)": f"{gap_best:.2f}%",
            "Gap Avg (%)": f"{gap_avg:.2f}%",
            "Waktu Avg (s)": f"{waktu_avg:.2f}",
        })

print("\n" + "=" * 80, flush=True)
print("RINGKASAN HASIL BASELINE UNTUK LAPORAN", flush=True)
print("=" * 80, flush=True)
for r in hasil_rekap:
    print(r, flush=True)