"""
run_tuning.py — SCRIPT EKSEKUSI GRID SEARCH PARAMETER TUNING ALNS
===============================================================================
Mengeksekusi tuning parameter ALNS (Simulated Annealing & Adaptif) secara 
sistematis menggunakan metode Grid Search (Tahap 20).

Kombinasi parameter yang dievaluasi:
  - suhu_awal          : [500.0, 1500.0, 3500.0]  (3 pilihan)
  - laju_pendinginan   : [0.990, 0.995, 0.998]    (3 pilihan)
  - reaction_factor (r): [0.1, 0.3, 0.5]          (3 pilihan)
  -------------------------------------------------------------
  Total kombinasi      : 27 kombinasi
  Seed per kombinasi   : 3 seed (1, 2, 3) -> 81 total eksekusi ALNS

Output:
  - Progres eksekusi real-time per kombinasi
  - Peringkat 10 kombinasi terbaik (diurutkan dari rata-rata jarak terkecil)
  - Analisis pengaruh/sensitivitas tiap parameter
  - Rekomendasi parameter terbaik
  - Ekspor hasil lengkap ke hasil_grid_search.csv
===============================================================================
"""

import os
import sys
import time

folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
dir_root = os.path.dirname(folder_tahap19)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance
from tuning import GridSearch


def main():
    print("=" * 78)
    print(" RUN TUNING: GRID SEARCH PARAMETER ALNS CVRP (TAHAP 20)")
    print("=" * 78)

    # 1. Muat Instance Uji
    nama_file = "X-n101-k25.vrp"
    bks = 27591
    path_vrp = os.path.join(folder_tahap19, "X", nama_file)

    if not os.path.exists(path_vrp):
        raise FileNotFoundError(f"File instance tidak ditemukan di: {path_vrp}")

    daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
    instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)

    # 2. Bangun Solusi Awal
    solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()
    print(f"\nSolusi Awal Terpilih : Jarak = {solusi_awal.total_jarak} | Rute = {solusi_awal.jumlah_rute}")
    assert solusi_awal.layak(), f"Solusi awal TIDAK LAYAK: {solusi_awal.daftar_pelanggaran()}"
    print(f"Status Kelayakan Solusi Awal: LAYAK (100% Valid)\n")

    # 3. Definisikan Kisi Parameter (Grid Search)
    kisi_parameter = {
        "suhu_awal": [500.0, 1500.0, 3500.0],
        "laju_pendinginan": [0.990, 0.995, 0.998],
        "reaction_factor": [0.1, 0.3, 0.5],
    }

    maks_iterasi = 500
    daftar_seed = (1, 2, 3)

    print("=" * 78)
    print(" KONFIGURASI GRID SEARCH")
    print("=" * 78)
    print(f"  Instance Uji       : {nama_file} (BKS = {bks}, Armada = {instance.jumlah_kendaraan}, Rute Awal = {solusi_awal.jumlah_rute})")
    print(f"  Maksimal Iterasi   : {maks_iterasi} per run")
    print(f"  Daftar Seed        : {daftar_seed}")
    for p, vals in kisi_parameter.items():
        print(f"  - {p:<18}: {vals}")
    print("=" * 78)
    print(" MEMULAI EKSEKUSI GRID SEARCH...")
    print("=" * 78)

    # 4. Jalankan GridSearch
    tuner = GridSearch(
        instance,
        solusi_awal,
        maks_iterasi=maks_iterasi,
        daftar_seed=daftar_seed,
    )
    
    t0 = time.time()
    tuner.jalankan(kisi_parameter)
    waktu_total = time.time() - t0

    # 5. Tampilkan Peringkat Kombinasi Terbaik
    kombinasi_terbaik = tuner.cetak_peringkat(berapa=10)
    gap_best = ((kombinasi_terbaik["terbaik"] - bks) / bks) * 100
    gap_avg = ((kombinasi_terbaik["rata"] - bks) / bks) * 100

    print(f"\n  [KOMBINASI JUARA #1]:")
    for k, v in kombinasi_terbaik["parameter"].items():
        print(f"    * {k:<18}: {v}")
    print(f"    * Jarak Rata-rata   : {kombinasi_terbaik['rata']:.1f} (Gap BKS: +{gap_avg:.2f}%)")
    print(f"    * Jarak Terbaik     : {kombinasi_terbaik['terbaik']} (Gap BKS: +{gap_best:.2f}%)")
    print(f"    * Jarak Terburuk    : {kombinasi_terbaik['terburuk']}")

    # 6. Analisis Pengaruh Masing-Masing Parameter
    print("\n" + "=" * 78)
    print(" ANALISIS SENSITIVITAS & PENGARUH MASING-MASING PARAMETER")
    print("=" * 78)
    for p in kisi_parameter:
        tuner.pengaruh_satu_parameter(p)

    # 7. Ekspor Hasil ke CSV
    csv_local = os.path.join(folder_tahap19, "hasil_grid_search.csv")
    csv_root = os.path.join(dir_root, "hasil_grid_search.csv")
    tuner.simpan_csv(csv_local)
    tuner.simpan_csv(csv_root)

    print("\n" + "=" * 78)
    print(f" GRID SEARCH SELESAI DALAM {waktu_total:.1f} DETIK")
    print("=" * 78)


if __name__ == "__main__":
    main()
