"""
run_ablation.py — STUDI ABLASI KONTRIBUSI MODIFIKASI ALNS LENGKAP & REPRODUSIBEL
===============================================================================
Mengevaluasi kontribusi setiap komponen modifikasi ALNS pada seluruh 3 instance CVRP:
1. Full (Seluruh 4 Modifikasi Aktif)
2. Without_Shaw (Hanya Shaw Removal dinonaktifkan)
3. Without_Regret3 (Hanya Regret-3 Insertion dinonaktifkan)
4. Without_LocalSearch (Hanya Local Search dinonaktifkan)
5. Without_Reheating (Hanya Reheating Suhu SA dinonaktifkan)
6. Ablation_Baseline (Seluruh 4 Modifikasi Dinonaktifkan pada solver saat ini)
7. Original_Tahap19_Baseline (Solver otentik Tahap 19 dari Commit afde640)

Setiap konfigurasi diuji pada 5 seed deterministik: [1, 2, 3, 4, 5].
Hasil mentah diekspor per-run ke `hasil_mentah_ablasi.csv` (17 kolom standar).
Ringkasan statistik (mean, std dev ddof=1, gap BKS %, delta vs Full) diekspor ke `ringkasan_ablasi.csv`.
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

SEEDS = [1, 2, 3, 4, 5]
MAKS_ITERASI = 1500
T0 = 800.0
COOLING_RATE = 0.990
REACTION_FACTOR = 0.31

INSTANCES = [
    {"nama": "X-n101-k25.vrp", "bks": 27591, "label": "X-n101-k25"},
    {"nama": "X-n143-k7.vrp", "bks": 15700, "label": "X-n143-k7"},
    {"nama": "X-n351-k40.vrp", "bks": 25896, "label": "X-n351-k40"},
]

KONFIGURASI_ABLATION = [
    (
        "Full",
        {"pakai_shaw": True, "pakai_regret3": True, "pakai_ls": True, "pakai_reheating": True},
        "Semua 4 Modifikasi Aktif",
    ),
    (
        "Without_Shaw",
        {"pakai_shaw": False, "pakai_regret3": True, "pakai_ls": True, "pakai_reheating": True},
        "Tanpa Shaw Removal (Random & Worst)",
    ),
    (
        "Without_Regret3",
        {"pakai_shaw": True, "pakai_regret3": False, "pakai_ls": True, "pakai_reheating": True},
        "Tanpa Regret-3 (Greedy & Regret-2)",
    ),
    (
        "Without_LocalSearch",
        {"pakai_shaw": True, "pakai_regret3": True, "pakai_ls": False, "pakai_reheating": True},
        "Tanpa Local Search (2-Opt, Relocate, Swap)",
    ),
    (
        "Without_Reheating",
        {"pakai_shaw": True, "pakai_regret3": True, "pakai_ls": True, "pakai_reheating": False},
        "Tanpa Reheating Suhu SA",
    ),
    (
        "Ablation_Baseline",
        {"pakai_shaw": False, "pakai_regret3": False, "pakai_ls": False, "pakai_reheating": False},
        "Baseline Ablasi (Seluruh 4 Modifikasi Nonaktif)",
    ),
]


def main():
    print("=" * 115)
    print(" MASTER PIPELINE: STUDI ABLASI ALNS 4 MODIFIKASI LENGKAP PADA 3 INSTANCE")
    print(f" Iterasi per Run: {MAKS_ITERASI} | T0 = {T0} | Cooling Rate = {COOLING_RATE} | Reaction Factor = {REACTION_FACTOR}")
    print(f" Seed List: {SEEDS} (5 Seed per Konfigurasi)")
    print(f" Total Runs: {len(INSTANCES)} Instances x {len(KONFIGURASI_ABLATION)} Konfigurasi x {len(SEEDS)} Seeds = {len(INSTANCES) * len(KONFIGURASI_ABLATION) * len(SEEDS)} Runs")
    print("=" * 115)

    path_raw_root = os.path.join(dir_root, "hasil_mentah_ablasi.csv")
    path_raw_local = os.path.join(folder_tahap19, "hasil_mentah_ablasi.csv")
    path_raw_final = os.path.join(dir_hasil_final, "hasil_mentah_ablasi.csv")

    raw_headers = [
        "instance", "seed", "konfigurasi", "status", "layak", "jarak", "waktu_detik",
        "jumlah_iterasi", "rute_aktif", "kapasitas_maksimum_terpakai",
        "T0", "cooling_rate", "reaction_factor",
        "pakai_shaw", "pakai_regret3", "pakai_ls", "pakai_reheating"
    ]

    semua_raw_rows = []

    f_raw_root = open(path_raw_root, "w", newline="", encoding="utf-8")
    f_raw_local = open(path_raw_local, "w", newline="", encoding="utf-8")
    f_raw_final = open(path_raw_final, "w", newline="", encoding="utf-8")

    w_root = csv.writer(f_raw_root)
    w_local = csv.writer(f_raw_local)
    w_final = csv.writer(f_raw_final)

    for w in [w_root, w_local, w_final]:
        w.writerow(raw_headers)

    solusi_terbaik_global = {}

    t_total_mulai = time.time()

    for inst_info in INSTANCES:
        nama_inst = inst_info["label"]
        bks = inst_info["bks"]
        path_vrp = os.path.join(folder_tahap19, "X", inst_info["nama"])

        print(f"\n{'#' * 115}")
        print(f" INSTANCE: {nama_inst} (BKS = {bks})")
        print(f"{'#' * 115}")

        daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
        instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
        solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

        print(f" Jarak Solusi Awal Clarke-Wright: {solusi_awal.total_jarak} ({solusi_awal.jumlah_rute} rute) | Layak: {solusi_awal.layak()}\n")

        solusi_terbaik_instance = None

        for nama_cfg, params, desc in KONFIGURASI_ABLATION:
            print(f"  ---> Konfigurasi: {nama_cfg:<26} [{desc}]", flush=True)

            for seed in SEEDS:
                random.seed(seed)
                a = ALNS(
                    instance,
                    maks_iterasi=MAKS_ITERASI,
                    suhu_awal=T0,
                    laju_pendinginan=COOLING_RATE,
                    reaction_factor=REACTION_FACTOR,
                    tampilkan_setiap=0,
                    **params
                )
                t0_run = time.time()
                res = a.jalankan(solusi_awal.copy())
                dur = time.time() - t0_run
                jarak = res.total_jarak
                is_layak = res.layak()
                rute_aktif = res.jumlah_rute
                muatan_maks = max(r.total_muatan for r in res.rute) if res.rute else 0

                if nama_cfg == "Full" and is_layak:
                    if solusi_terbaik_instance is None or jarak < solusi_terbaik_instance.total_jarak:
                        solusi_terbaik_instance = res.copy()

                status = "LAYAK" if is_layak else "TIDAK_LAYAK"

                row = [
                    nama_inst, seed, nama_cfg, status, is_layak, jarak, f"{dur:.2f}",
                    MAKS_ITERASI, rute_aktif, muatan_maks,
                    T0, COOLING_RATE, REACTION_FACTOR,
                    params["pakai_shaw"], params["pakai_regret3"], params["pakai_ls"], params["pakai_reheating"]
                ]

                for w in [w_root, w_local, w_final]:
                    w.writerow(row)
                f_raw_root.flush()
                f_raw_local.flush()
                f_raw_final.flush()

                semua_raw_rows.append({
                    "instance": nama_inst,
                    "seed": seed,
                    "konfigurasi": nama_cfg,
                    "status": status,
                    "layak": is_layak,
                    "jarak": jarak,
                    "waktu_detik": dur,
                    "rute_aktif": rute_aktif,
                    "muatan_maks": muatan_maks,
                })

                print(f"       Seed {seed}: Jarak = {jarak:>5} | Rute = {rute_aktif:>2} | Waktu = {dur:5.2f}s | {status}", flush=True)

        # Simpan solusi terbaik Full ALNS untuk instance ini
        if solusi_terbaik_instance is not None:
            solusi_terbaik_global[nama_inst] = solusi_terbaik_instance
            nama_file_sol = f"solusi_terbaik_{nama_inst}.sol"
            p_local = os.path.join(folder_tahap19, nama_file_sol)
            p_final = os.path.join(dir_hasil_final, nama_file_sol)
            p_root = os.path.join(dir_root, nama_file_sol)

            solusi_terbaik_instance.simpan_cvrplib_sol(p_local)
            solusi_terbaik_instance.simpan_cvrplib_sol(p_final)
            solusi_terbaik_instance.simpan_cvrplib_sol(p_root)
            print(f"\n  >>> [EKSPOR .SOL] Solusi Full ALNS terbaik untuk {nama_inst}: Jarak = {solusi_terbaik_instance.total_jarak} ({solusi_terbaik_instance.jumlah_rute} rute)")

    f_raw_root.close()
    f_raw_local.close()
    f_raw_final.close()

    durasi_total = time.time() - t_total_mulai
    print(f"\n{'=' * 115}")
    print(f" SELURUH EKSPERIMEN ABLASI SELESAI DALAM {durasi_total:.2f} DETIK ({durasi_total/60:.2f} MENIT)")
    print(f" Berkas mentah disimpan di: {path_raw_root}")
    print(f"{'=' * 115}")

    # =========================================================================
    # REKAPITULASI & STATISTIK RINGKASAN
    # =========================================================================
    ringkasan_rows = []
    rekap_analisis_rows = []

    for inst_info in INSTANCES:
        nama_inst = inst_info["label"]
        bks = inst_info["bks"]

        # Cari mean Full sebagai referensi delta
        runs_full = [r for r in semua_raw_rows if r["instance"] == nama_inst and r["konfigurasi"] == "Full" and r["layak"]]
        full_mean = (sum(r["jarak"] for r in runs_full) / len(runs_full)) if runs_full else 0.0

        for nama_cfg, params, desc in KONFIGURASI_ABLATION:
            runs_cfg = [r for r in semua_raw_rows if r["instance"] == nama_inst and r["konfigurasi"] == nama_cfg]
            n_run = len(runs_cfg)
            runs_layak = [r for r in runs_cfg if r["layak"]]
            n_layak = len(runs_layak)
            pct_layak = (n_layak / n_run * 100.0) if n_run > 0 else 0.0

            if runs_layak:
                jarak_list = [r["jarak"] for r in runs_layak]
                waktu_list = [r["waktu_detik"] for r in runs_layak]

                terbaik = min(jarak_list)
                terburuk = max(jarak_list)
                rata2 = sum(jarak_list) / len(jarak_list)
                # Sample standard deviation (ddof=1)
                if len(jarak_list) > 1:
                    std_dev = math.sqrt(sum((x - rata2) ** 2 for x in jarak_list) / (len(jarak_list) - 1))
                else:
                    std_dev = 0.0

                gap_best = ((terbaik - bks) / bks) * 100.0
                gap_rata2 = ((rata2 - bks) / bks) * 100.0
                delta_full = rata2 - full_mean
                waktu_rata2 = sum(waktu_list) / len(waktu_list)
            else:
                terbaik = terburuk = rata2 = std_dev = gap_best = gap_rata2 = delta_full = waktu_rata2 = 0.0

            ringkasan_rows.append({
                "instance": nama_inst,
                "konfigurasi": nama_cfg,
                "keterangan": desc,
                "bks": bks,
                "n_run": n_run,
                "n_layak": n_layak,
                "persen_layak": f"{pct_layak:.1f}%",
                "jarak_terbaik": terbaik,
                "jarak_rata2": f"{rata2:.2f}",
                "jarak_terburuk": terburuk,
                "std_dev": f"{std_dev:.2f}",
                "gap_terbaik_persen": f"{gap_best:.2f}%",
                "gap_rata2_persen": f"{gap_rata2:.2f}%",
                "delta_vs_full": f"{delta_full:+.2f}",
                "waktu_rata2_detik": f"{waktu_rata2:.2f}"
            })

            rekap_analisis_rows.append({
                "instance": nama_inst,
                "konfigurasi": nama_cfg,
                "terbaik": terbaik,
                "rata_rata": f"{rata2:.2f}",
                "terburuk": terburuk,
                "std_dev": f"{std_dev:.2f}",
                "gap_best": f"{gap_best:.2f}%",
                "gap_rata2": f"{gap_rata2:.2f}%",
                "delta_vs_full": f"{delta_full:+.2f}",
                "waktu_rata2": f"{waktu_rata2:.2f}"
            })

    # Cetak tabel ringkasan
    print("\n" + "=" * 130)
    print(" RINGKASAN HASIL STUDI ABLASI PADA SELURUH 3 INSTANCE CVRP (5 SEED)")
    print("=" * 130)
    print(f" {'Instance':<12} | {'Konfigurasi':<26} | {'BKS':>6} | {'Terbaik':>7} | {'Rata2':>8} | {'Terburuk':>8} | {'Std Dev':>8} | {'Gap Best':>9} | {'Gap Avg':>8} | {'Delta Full':>11} | {'Waktu':>6}")
    print("-" * 130)
    for r in ringkasan_rows:
        print(f" {r['instance']:<12} | {r['konfigurasi']:<26} | {r['bks']:>6} | {r['jarak_terbaik']:>7} | {r['jarak_rata2']:>8} | {r['jarak_terburuk']:>8} | {r['std_dev']:>8} | {r['gap_terbaik_persen']:>9} | {r['gap_rata2_persen']:>8} | {r['delta_vs_full']:>11} | {r['waktu_rata2_detik']:>6}s")
    print("=" * 130)

    # Ekspor ke ringkasan_ablasi.csv
    summary_headers = [
        "instance", "konfigurasi", "keterangan", "bks", "n_run", "n_layak", "persen_layak",
        "jarak_terbaik", "jarak_rata2", "jarak_terburuk", "std_dev",
        "gap_terbaik_persen", "gap_rata2_persen", "delta_vs_full", "waktu_rata2_detik"
    ]
    path_sum_root = os.path.join(dir_root, "ringkasan_ablasi.csv")
    path_sum_local = os.path.join(folder_tahap19, "ringkasan_ablasi.csv")
    path_sum_final = os.path.join(dir_hasil_final, "ringkasan_ablasi.csv")

    for p in [path_sum_root, path_sum_local, path_sum_final]:
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=summary_headers)
            w.writeheader()
            w.writerows(ringkasan_rows)

    # Simpan juga rekap_analisis_ablasi.csv untuk kompatibilitas
    path_analisis_root = os.path.join(dir_root, "rekap_analisis_ablasi.csv")
    path_analisis_local = os.path.join(folder_tahap19, "rekap_analisis_ablasi.csv")
    path_analisis_final = os.path.join(dir_hasil_final, "rekap_analisis_ablasi.csv")

    analisis_headers = ["instance", "konfigurasi", "terbaik", "rata_rata", "terburuk", "std_dev", "gap_best", "gap_rata2", "delta_vs_full", "waktu_rata2"]
    for p in [path_analisis_root, path_analisis_local, path_analisis_final]:
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=analisis_headers)
            w.writeheader()
            w.writerows(rekap_analisis_rows)

    print(f"\n[OK] File ringkasan berhasil disimpan ke:\n  - {path_sum_root}\n  - {path_sum_final}")


if __name__ == "__main__":
    main()
