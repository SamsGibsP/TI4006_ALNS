"""
response_surface.py — TAHAP 20 (RESPONSE SURFACE METHODOLOGY / RSM)
===============================================================================
Implementasi Response Surface Methodology (RSM) untuk penalaan parameter ALNS
secara kontinu menggunakan Box-Behnken Design (BBD) dan Regresi Kuadratik
(Second-Order Polynomial Model).

Keunggulan RSM dibandingkan Grid Search:
1. Efisiensi Eksperimen: Untuk 3 faktor, Box-Behnken hanya membutuhkan 15 titik
   rancangan (dibandingkan 27 titik pada Grid Search 3-level).
2. Model Kontinu: Menangkap kelengkungan (curvature / kuadratik) serta interaksi
   antar-faktor (T0 * c, T0 * r, c * r).
3. Penentuan Titik Optimum Matematis: Menghitung parameter optimum kontinu (x*)
   yang berada di antara grid diskret melalui minimalisasi fungsi respon turunan.
4. Estimasi Kesalahan: Replikasi pada titik tengah (center points) mengukur error
   murni (pure error) dan koefisien determinasi (R^2).

Semua perhitungan matriks dan regresi diimplementasikan dengan PURE PYTHON
standar (tanpa solver eksternal / tanpa scipy).
===============================================================================
"""

import csv
import math
import os
import random
import time

from alns import ALNS


class ResponseSurfaceMethodology:
    """Metodologi Permukaan Respon (RSM) berbasis Box-Behnken Design (BBD)."""

    def __init__(
        self,
        instance,
        solusi_awal,
        factor_ranges,
        maks_iterasi=500,
        daftar_seed=(1, 2, 3),
        nama_instance="CVRP",
    ):
        """
        factor_ranges : dict {
            "suhu_awal": (min_val, center_val, max_val),
            "laju_pendinginan": (min_val, center_val, max_val),
            "reaction_factor": (min_val, center_val, max_val)
        }
        """
        self.instance = instance
        self.solusi_awal = solusi_awal
        self.factor_ranges = factor_ranges
        self.factor_names = list(factor_ranges.keys())
        self.maks_iterasi = maks_iterasi
        self.daftar_seed = daftar_seed
        self.nama_instance = nama_instance

        self.design_points = self._generate_box_behnken()
        self.hasil_eksperimen = []
        self.beta = None
        self.r2 = 0.0
        self.r2_adj = 0.0
        self.optimum_coded = None
        self.optimum_natural = None
        self.optimum_prediksi = None

    def _generate_box_behnken(self):
        """
        Membangkitkan 15 titik rancangan Box-Behnken Design (k=3):
        - 12 titik tepi (edge midpoints) dengan koordinat (+-1, +-1, 0), dll.
        - 3 replikasi titik tengah (center points) (0, 0, 0).
        """
        bbd = [
            # Bidang X1 - X2 (x3 = 0)
            (-1, -1,  0),
            ( 1, -1,  0),
            (-1,  1,  0),
            ( 1,  1,  0),
            # Bidang X1 - X3 (x2 = 0)
            (-1,  0, -1),
            ( 1,  0, -1),
            (-1,  0,  1),
            ( 1,  0,  1),
            # Bidang X2 - X3 (x1 = 0)
            ( 0, -1, -1),
            ( 0,  1, -1),
            ( 0, -1,  1),
            ( 0,  1,  1),
            # Titik Tengah (Center Points)
            ( 0,  0,  0),
            ( 0,  0,  0),
            ( 0,  0,  0),
        ]
        return bbd

    def coded_to_natural(self, coded_vals):
        """Mengonversi nilai terkode [-1, 0, +1] ke skala parameter alami."""
        natural = {}
        for idx, name in enumerate(self.factor_names):
            c_val = coded_vals[idx]
            low, mid, high = self.factor_ranges[name]
            half_range = high - mid
            nat_val = mid + c_val * half_range
            natural[name] = nat_val
        return natural

    def natural_to_coded(self, natural_vals):
        """Mengonversi nilai parameter alami ke skala terkode [-1, +1]."""
        coded = []
        for name in self.factor_names:
            nat_val = natural_vals[name]
            low, mid, high = self.factor_ranges[name]
            half_range = high - mid
            c_val = (nat_val - mid) / half_range
            coded.append(c_val)
        return coded

    def uji_satu_titik(self, parameter):
        """Menjalankan ALNS beberapa kali dengan seed berbeda untuk satu titik parameter."""
        nilai = []
        for seed in self.daftar_seed:
            random.seed(seed)
            pencari = ALNS(
                self.instance,
                maks_iterasi=self.maks_iterasi,
                tampilkan_setiap=0,
                **parameter,
            )
            hasil = pencari.jalankan(self.solusi_awal)
            nilai.append(hasil.total_jarak)

        rata = sum(nilai) / len(nilai)
        terbaik = min(nilai)
        terburuk = max(nilai)
        return rata, terbaik, terburuk, nilai

    def jalankan(self, verbose=True):
        """Mengeksekusi eksperimen BBD dan membangun model Response Surface."""
        if verbose:
            print("=" * 78)
            print(f" EKSEKUSI RESPONSE SURFACE METHODOLOGY (RSM) — {self.nama_instance}")
            print(f" Rancangan: Box-Behnken Design (15 Titik Rancangan, {len(self.daftar_seed)} Seed/Titik)")
            print("=" * 78)

        mulai = time.time()
        self.hasil_eksperimen = []
        y_list = []

        for run_id, coded in enumerate(self.design_points, start=1):
            parameter = self.coded_to_natural(coded)
            rata, terbaik, terburuk, raw_seeds = self.uji_satu_titik(parameter)
            y_list.append(rata)

            entry = {
                "run_id": run_id,
                "coded": coded,
                "parameter": parameter,
                "rata": rata,
                "terbaik": terbaik,
                "terburuk": terburuk,
                "seeds": raw_seeds,
            }
            self.hasil_eksperimen.append(entry)

            if verbose:
                ringkas_nat = ", ".join(
                    f"{k}={v:.3f}" if isinstance(v, float) and v < 10 else f"{k}={v:.1f}"
                    for k, v in parameter.items()
                )
                print(
                    f"  Run {run_id:>2}/15 | Coded: ({coded[0]:>2}, {coded[1]:>2}, {coded[2]:>2}) | "
                    f"{ringkas_nat:<55} -> Rata: {rata:>7.1f} (Best: {terbaik})"
                )

        # Fitting Second-Order Polynomial Model via Ordinary Least Squares (OLS)
        self._fit_polynomial(y_list)

        # Cari Titik Optimum Kontinu
        self._cari_titik_optimum()

        durasi = time.time() - mulai
        if verbose:
            print("=" * 78)
            print(f" Waktu Eksekusi RSM: {durasi:.1f} detik | R^2 = {self.r2:.4f} (R^2 Adj = {self.r2_adj:.4f})")
            print("=" * 78)

        return self.optimum_natural

    def _fit_polynomial(self, y):
        """
        Menyelesaikan regresi kuadratik 10 parameter menggunakan eliminasi Gauss-Jordan:
        y = b0 + b1*x1 + b2*x2 + b3*x3 + b11*x1^2 + b22*x2^2 + b33*x3^2 + b12*x1*x2 + b13*x1*x3 + b23*x2*x3
        """
        N = len(self.design_points)
        # Bentuk matriks X rancangan
        X = []
        for x1, x2, x3 in self.design_points:
            row = [
                1.0,                    # b0
                x1, x2, x3,             # b1, b2, b3
                x1**2, x2**2, x3**2,    # b11, b22, b33
                x1 * x2, x1 * x3, x2 * x3  # b12, b13, b23
            ]
            X.append(row)

        P = len(X[0])  # 10 koefisien

        # Hitung Matriks Normal: (X^T * X) * beta = (X^T * y)
        XtX = [[sum(X[r][i] * X[r][j] for r in range(N)) for j in range(P)] for i in range(P)]
        Xty = [sum(X[r][i] * y[r] for r in range(N)) for i in range(P)]

        # Solusi Gauss-Jordan dengan Partial Pivoting
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

        self.beta = [Aug[i][-1] for i in range(P)]

        # Hitung R^2 dan R^2 adjusted
        y_mean = sum(y) / N
        ss_tot = sum((val - y_mean) ** 2 for val in y)
        y_pred = [self.prediksi_coded(pt) for pt in self.design_points]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(N))

        self.r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
        self.r2_adj = (
            max(0.0, 1.0 - ((ss_res / max(1, N - P)) / (ss_tot / max(1, N - 1))))
            if ss_tot > 0 and N > P
            else self.r2
        )

    def prediksi_coded(self, coded_pt):
        """Memprediksi nilai respon y berdasarkan koordinat terkode (x1, x2, x3)."""
        x1, x2, x3 = coded_pt
        b = self.beta
        y_hat = (
            b[0]
            + b[1] * x1 + b[2] * x2 + b[3] * x3
            + b[4] * (x1**2) + b[5] * (x2**2) + b[6] * (x3**2)
            + b[7] * (x1 * x2) + b[8] * (x1 * x3) + b[9] * (x2 * x3)
        )
        return y_hat

    def _cari_titik_optimum(self):
        """
        Mencari titik minimum dari persamaan kuadratik di dalam domain terkode [-1, +1]^3.
        Dilakukan dengan optimasi bounded grid berkisi halus (resolusi 0.05).
        """
        best_val = float("inf")
        best_coded = (0.0, 0.0, 0.0)

        # Evaluasi pada kisi berdensitas tinggi di [-1, +1]
        langkah = 0.05
        grid_vals = [round(-1.0 + i * langkah, 3) for i in range(int(2.0 / langkah) + 1)]

        for x1 in grid_vals:
            for x2 in grid_vals:
                for x3 in grid_vals:
                    val = self.prediksi_coded((x1, x2, x3))
                    if val < best_val:
                        best_val = val
                        best_coded = (x1, x2, x3)

        self.optimum_coded = best_coded
        self.optimum_prediksi = best_val
        self.optimum_natural = self.coded_to_natural(best_coded)

    def cetak_laporan_lengkap(self, bks=None):
        """Menampilkan laporan lengkap Response Surface, koefisien model, dan parameter optimum."""
        print("\n" + "=" * 78)
        print(f" LAPORAN RESPONSE SURFACE METHODOLOGY — {self.nama_instance}")
        print("=" * 78)

        # 1. Tabel Rancangan Eksperimen
        print(f"  {'Run':>3} | {'x1':>4} {'x2':>4} {'x3':>4} | " + " | ".join(f"{n:>17}" for n in self.factor_names) + " | {'Rata':>8} | {'Best':>8}")
        print("  " + "-" * 74)

        for e in self.hasil_eksperimen:
            c = e["coded"]
            p = e["parameter"]
            vals_str = " | ".join(
                f"{p[n]:>17.3f}" if isinstance(p[n], float) and p[n] < 10 else f"{p[n]:>17.1f}"
                for n in self.factor_names
            )
            print(f"  {e['run_id']:>3} | {c[0]:>4} {c[1]:>4} {c[2]:>4} | {vals_str} | {e['rata']:>8.1f} | {e['terbaik']:>8}")

        print("  " + "-" * 74)

        # 2. Persamaan Regresi Kuadratik
        b = self.beta
        fn = self.factor_names
        print(f"\n  PERSAMAAN PERMUKAAN RESPON (Model Kuadratik Orde-2):")
        print(f"    Y_pred = {b[0]:.2f}")
        print(f"             + ({b[1]:.2f} * {fn[0]}) + ({b[2]:.2f} * {fn[1]}) + ({b[3]:.2f} * {fn[2]})")
        print(f"             + ({b[4]:.2f} * {fn[0]}^2) + ({b[5]:.2f} * {fn[1]}^2) + ({b[6]:.2f} * {fn[2]}^2)")
        print(f"             + ({b[7]:.2f} * {fn[0]}*{fn[1]}) + ({b[8]:.2f} * {fn[0]}*{fn[2]}) + ({b[9]:.2f} * {fn[1]}*{fn[2]})")

        print(f"\n  Kualitas Kesesuaian Model (Goodness of Fit):")
        print(f"    * Koefisien Determinasi R^2      : {self.r2 * 100:.2f}%")
        print(f"    * Adjusted R^2                   : {self.r2_adj * 100:.2f}%")

        # 3. Parameter Optimum Terpilih
        print("\n  " + "=" * 74)
        print("  PARAMETER OPTIMUM HASIL MINIMALISASI RESPONSE SURFACE:")
        print("  " + "=" * 74)
        print(f"    * Titik Terkode (Coded x*)        : x1={self.optimum_coded[0]:+.2f}, x2={self.optimum_coded[1]:+.2f}, x3={self.optimum_coded[2]:+.2f}")
        for k, v in self.optimum_natural.items():
            fmt = f"{v:.4f}" if v < 10 else f"{v:.1f}"
            print(f"    * {k:<30} : {fmt}")
        print(f"    * Prediksi Nilai Objektif Optimum: {self.optimum_prediksi:.1f}")

        if bks is not None:
            gap = ((self.optimum_prediksi - bks) / bks) * 100
            print(f"    * BKS Instance ({self.nama_instance:<15}) : {bks} (Prediksi Gap: +{gap:.2f}%)")

        print("  " + "=" * 74)

    def simpan_csv(self, path_csv):
        """Menyimpan seluruh data Box-Behnken dan estimasi model ke berkas CSV."""
        with open(path_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["instance", "run_id", "x1_coded", "x2_coded", "x3_coded"] + self.factor_names + ["jarak_rata", "jarak_terbaik", "jarak_terburuk"]
            writer.writerow(header)
            for e in self.hasil_eksperimen:
                c = e["coded"]
                p = e["parameter"]
                row = [self.nama_instance, e["run_id"], c[0], c[1], c[2]] + [p[k] for k in self.factor_names] + [f"{e['rata']:.2f}", e["terbaik"], e["terburuk"]]
                writer.writerow(row)
