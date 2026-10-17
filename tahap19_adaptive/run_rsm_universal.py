"""
run_rsm_universal.py — PENALAAN RESPONSE SURFACE METHODOLOGY (RSM) GLOBAL
===============================================================================
Mencari SATU KONFIGURASI PARAMETER TUNGGAL (Universal Parameter Set) yang optimal
untuk SELURUH INSTANCE sekaligus (X-n101-k25, X-n143-k7, X-n351-k40).

Metodologi:
1. Multi-Instance Response Surface Methodology berbasis Box-Behnken Design (15 titik).
2. Fungsi Respon (Response Variable):
   Y = Rata-rata Relative Percentage Gap (% Gap ke BKS) lintas 3 instance:
       Y = (Gap_X101 + Gap_X143 + Gap_X351) / 3
3. Membangun model permukaan kuadratik gabungan:
   Y_pred = b0 + b1*x1 + b2*x2 + b3*x3 + b11*x1^2 + b22*x2^2 + b33*x3^2 + b12*x1*x2 + ...
4. Meminimalkan model kuadratik untuk memperoleh 1 TITIK OPTIMUM GLOBAL:
   (suhu_awal*, laju_pendinginan*, reaction_factor*)
5. Melakukan validasi konfirmasi 5-seed pada ketiga instance dengan 1 set parameter ini.
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

# 15 Titik Rancangan Standar Box-Behnken Design (k=3)
BBD_POINTS = [
    (-1, -1,  0),
    ( 1, -1,  0),
    (-1,  1,  0),
    ( 1,  1,  0),
    (-1,  0, -1),
    ( 1,  0, -1),
    (-1,  0,  1),
    ( 1,  0,  1),
    ( 0, -1, -1),
    ( 0,  1, -1),
    ( 0, -1,  1),
    ( 0,  1,  1),
    ( 0,  0,  0),
    ( 0,  0,  0),
    ( 0,  0,  0),
]

# Rentang Parameter Global yang Diuji
FACTOR_RANGES = {
    "suhu_awal": (800.0, 2000.0, 3200.0),
    "laju_pendinginan": (0.990, 0.994, 0.998),
    "reaction_factor": (0.05, 0.25, 0.45),
}

INSTANCES_CONFIG = [
    {"nama": "X-n101-k25.vrp", "bks": 27591},
    {"nama": "X-n143-k7.vrp", "bks": 15700},
    {"nama": "X-n351-k40.vrp", "bks": 25896},
]


def coded_to_natural(coded):
    natural = {}
    names = list(FACTOR_RANGES.keys())
    for idx, name in enumerate(names):
        low, mid, high = FACTOR_RANGES[name]
        half = high - mid
        natural[name] = mid + coded[idx] * half
    return natural


def solve_ols_gauss_jordan(X, y):
    N = len(X)
    P = len(X[0])
    XtX = [[sum(X[r][i] * X[r][j] for r in range(N)) for j in range(P)] for i in range(P)]
    Xty = [sum(X[r][i] * y[r] for r in range(N)) for i in range(P)]

    Aug = [XtX[i][:] + [Xty[i]] for i in range(P)]
    for i in range(P):
        pivot = max(range(i, P), key=lambda r: abs(Aug[r][i]))
        Aug[i], Aug[pivot] = Aug[pivot], Aug[i]
        diag = Aug[i][i]
        if abs(diag) < 1e-12:
            diag = 1e-12
        for j in range(i, P + 1):
            Aug[i][j] /= diag
        for r in range(P):
            if r != i:
                factor = Aug[r][i]
                for j in range(i, P + 1):
                    Aug[r][j] -= factor * Aug[i][j]

    beta = [Aug[i][-1] for i in range(P)]
    y_mean = sum(y) / N
    ss_tot = sum((val - y_mean) ** 2 for val in y)
    y_pred = [
        sum(X[r][j] * beta[j] for j in range(P))
        for r in range(N)
    ]
    ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(N))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    r2_adj = 1.0 - ((ss_res / (N - P)) / (ss_tot / (N - 1))) if ss_tot > 0 and N > P else r2
    return beta, r2, r2_adj


def main():
    print("=" * 80)
    print(" MULTI-INSTANCE RESPONSE SURFACE METHODOLOGY (RSM)")
    print(" PENCARIAN SATU SET PARAMETER OPTIMUM UNTUK SELURUH INSTANCE")
    print("=" * 80)

    # 1. Muat Seluruh Instance dan Solusi Awal
    instances_data = []
    for item in INSTANCES_CONFIG:
        path_vrp = os.path.join(folder_tahap19, "X", item["nama"])
        daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path_vrp)
        inst = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
        k_eff = inst.cari_armada_minimal_layak(verbose=False)
        sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()
        assert sol_awal.layak(), f"Solusi awal {item['nama']} tidak layak!"
        instances_data.append({
            "nama": item["nama"],
            "bks": item["bks"],
            "armada": k_eff,
            "instance": inst,
            "solusi_awal": sol_awal,
        })
        print(f"  * Instance {item['nama']:<15}: BKS={item['bks']:<6} | Armada={k_eff:>2} | Solusi Awal={sol_awal.total_jarak}")

    print("\n" + "=" * 80)
    print(" MENJALANKAN 15 TITIK RANCANGAN BOX-BEHNKEN LINTAS INSTANCE...")
    print("=" * 80)

    X_mat = []
    y_mean_gap = []
    data_tabel_rsm = []
    t_mulai = time.time()

    seeds_tuning = [1, 2]

    for run_id, coded in enumerate(BBD_POINTS, start=1):
        x1, x2, x3 = coded
        nat = coded_to_natural(coded)

        # Baris matriks regresi orde-2
        row_X = [
            1.0,
            x1, x2, x3,
            x1**2, x2**2, x3**2,
            x1*x2, x1*x3, x2*x3
        ]
        X_mat.append(row_X)

        gaps_per_inst = []
        for d in instances_data:
            gaps_seed = []
            for s in seeds_tuning:
                random.seed(s)
                a = ALNS(
                    d["instance"],
                    maks_iterasi=400,
                    tampilkan_setiap=0,
                    **nat
                )
                hasil = a.jalankan(d["solusi_awal"])
                g = ((hasil.total_jarak - d["bks"]) / d["bks"]) * 100
                gaps_seed.append(g)
            gaps_per_inst.append(sum(gaps_seed) / len(gaps_seed))

        # Respon Gabungan: Rata-rata Gap ke BKS lintas seluruh instance
        mean_composite_gap = sum(gaps_per_inst) / len(gaps_per_inst)
        y_mean_gap.append(mean_composite_gap)

        data_tabel_rsm.append({
            "run_id": run_id,
            "coded": coded,
            "natural": nat,
            "gap_101": gaps_per_inst[0],
            "gap_143": gaps_per_inst[1],
            "gap_351": gaps_per_inst[2],
            "mean_gap": mean_composite_gap,
        })

        ringkas_nat = f"T0={nat['suhu_awal']:.0f}, c={nat['laju_pendinginan']:.3f}, r={nat['reaction_factor']:.2f}"
        print(
            f"  Run {run_id:>2}/15 | Coded: ({x1:>2}, {x2:>2}, {x3:>2}) | {ringkas_nat:<35} | "
            f"Gap: [X101: +{gaps_per_inst[0]:.2f}%, X143: +{gaps_per_inst[1]:.2f}%, X351: +{gaps_per_inst[2]:.2f}%] -> RATA: +{mean_composite_gap:.2f}%"
        )

    durasi_rsm = time.time() - t_mulai

    # 2. Fit Model Regresi Kuadratik
    beta, r2, r2_adj = solve_ols_gauss_jordan(X_mat, y_mean_gap)

    print("\n" + "=" * 80)
    print(" MODEL RESPONSE SURFACE GABUNGAN (MULTI-INSTANCE)")
    print("=" * 80)
    print(f"  Fungsi Respon: Y_pred (% Mean Gap ke BKS)")
    print(f"    Y_pred = {beta[0]:.2f}")
    print(f"             + ({beta[1]:.2f}*x1) + ({beta[2]:.2f}*x2) + ({beta[3]:.2f}*x3)")
    print(f"             + ({beta[4]:.2f}*x1^2) + ({beta[5]:.2f}*x2^2) + ({beta[6]:.2f}*x3^2)")
    print(f"             + ({beta[7]:.2f}*x1*x2) + ({beta[8]:.2f}*x1*x3) + ({beta[9]:.2f}*x2*x3)")
    print(f"  Kualitas Model: R^2 = {r2*100:.2f}% | Adjusted R^2 = {r2_adj*100:.2f}%")

    # 3. Pencarian Titik Minimum Global Terkode [-1, +1]^3
    def predict_gap(c_pt):
        x1, x2, x3 = c_pt
        b = beta
        return (
            b[0] + b[1]*x1 + b[2]*x2 + b[3]*x3
            + b[4]*(x1**2) + b[5]*(x2**2) + b[6]*(x3**2)
            + b[7]*(x1*x2) + b[8]*(x1*x3) + b[9]*(x2*x3)
        )

    best_gap = float("inf")
    best_c = (0.0, 0.0, 0.0)
    grid_res = [round(-1.0 + i * 0.05, 3) for i in range(41)]
    for x1 in grid_res:
        for x2 in grid_res:
            for x3 in grid_res:
                g_hat = predict_gap((x1, x2, x3))
                if g_hat < best_gap:
                    best_gap = g_hat
                    best_c = (x1, x2, x3)

    opt_natural = coded_to_natural(best_c)

    print("\n" + "=" * 80)
    print(" 1 SET PARAMETER OPTIMUM UNIVERSAL (UNTUK SEMUA INSTANCE)")
    print("=" * 80)
    print(f"  Titik Coded Optimum (x*) : x1={best_c[0]:+.2f}, x2={best_c[1]:+.2f}, x3={best_c[2]:+.2f}")
    print(f"  * SUHU AWAL (suhu_awal)          : {opt_natural['suhu_awal']:.1f}")
    print(f"  * LAJU PENDINGINAN (laju_pendinginan) : {opt_natural['laju_pendinginan']:.4f}")
    print(f"  * REACTION FACTOR (reaction_factor)  : {opt_natural['reaction_factor']:.4f}")
    print(f"  * Prediksi Rata-rata Gap Optimum     : +{best_gap:.2f}%")
    print("=" * 80)

    # 4. Validasi 5 Seed pada Ketiga Instance menggunakan 1 Set Parameter ini
    print("\n  >>> MELAKUKAN UJI VALIDASI 5 SEED PADA KETIGA INSTANCE DENGAN 1 PARAMETER INI...")
    rekap_val = []

    for d in instances_data:
        jarak_list = []
        for s in [1, 2, 3, 4, 5]:
            random.seed(s)
            a = ALNS(
                d["instance"],
                maks_iterasi=1000,
                tampilkan_setiap=0,
                **opt_natural
            )
            res = a.jalankan(d["solusi_awal"])
            assert res.layak(), f"Solusi {d['nama']} seed {s} tidak layak!"
            jarak_list.append(res.total_jarak)

        best_j = min(jarak_list)
        avg_j = sum(jarak_list) / len(jarak_list)
        gap_b = ((best_j - d["bks"]) / d["bks"]) * 100
        gap_a = ((avg_j - d["bks"]) / d["bks"]) * 100

        rekap_val.append({
            "instance": d["nama"],
            "bks": d["bks"],
            "armada": d["armada"],
            "best": best_j,
            "avg": avg_j,
            "gap_best": gap_b,
            "gap_avg": gap_a,
        })
        print(f"  * {d['nama']:<15} | Terbaik: {best_j:>6} (+{gap_b:.2f}%) | Rata: {avg_j:>7.1f} (+{gap_a:.2f}%)")

    # 5. Ringkasan Akhir
    print("\n" + "=" * 80)
    print(" REKAPITULASI HASIL DENGAN 1 PARAMETER UNIVERSAL TERPILIH")
    print("=" * 80)
    print(f"  {'Instance':<15} | {'Armada':>6} | {'BKS':>6} | {'Jarak Terbaik':>13} | {'Gap Best':>9} | {'Gap Rata':>9}")
    print("  " + "-" * 80)
    for r in rekap_val:
        print(f"  {r['instance']:<15} | {r['armada']:>6} | {r['bks']:>6} | {r['best']:>13} | +{r['gap_best']:>7.2f}% | +{r['gap_avg']:>7.2f}%")
    print("  " + "-" * 80)

    mean_gap_best = sum(r["gap_best"] for r in rekap_val) / len(rekap_val)
    mean_gap_avg = sum(r["gap_avg"] for r in rekap_val) / len(rekap_val)
    print(f"  Rata-rata Seluruh Instance : Gap Terbaik = +{mean_gap_best:.2f}% | Gap Rata-rata = +{mean_gap_avg:.2f}%")
    print("=" * 80)

    # 6. Ekspor Berkas CSV
    csv_uni = os.path.join(folder_tahap19, "parameter_universal_rsm.csv")
    csv_uni_root = os.path.join(dir_root, "parameter_universal_rsm.csv")
    with open(csv_uni, "w", newline="", encoding="utf-8") as f, \
         open(csv_uni_root, "w", newline="", encoding="utf-8") as f_root:
        writer1 = csv.writer(f)
        writer2 = csv.writer(f_root)
        header = ["suhu_awal", "laju_pendinginan", "reaction_factor", "r2_model", "prediksi_gap_mean", "validasi_gap_best_mean", "validasi_gap_avg_mean"]
        row = [
            f"{opt_natural['suhu_awal']:.1f}",
            f"{opt_natural['laju_pendinginan']:.4f}",
            f"{opt_natural['reaction_factor']:.4f}",
            f"{r2*100:.2f}%",
            f"{best_gap:.2f}%",
            f"{mean_gap_best:.2f}%",
            f"{mean_gap_avg:.2f}%"
        ]
        writer1.writerow(header)
        writer1.writerow(row)
        writer2.writerow(header)
        writer2.writerow(row)

    print(f"  [CSV] Parameter universal tersimpan di: {csv_uni}")


if __name__ == "__main__":
    main()
