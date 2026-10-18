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

try:
    import numpy as np  # type: ignore
    from scipy import stats  # type: ignore
    from scipy.optimize import minimize  # type: ignore
    from sklearn.linear_model import LinearRegression  # type: ignore
    HAS_SCIENTIFIC = True
except ImportError:
    np = None  # type: ignore
    stats = None  # type: ignore
    minimize = None  # type: ignore
    LinearRegression = None  # type: ignore
    HAS_SCIENTIFIC = False

from alns import ALNS


class ResponseSurfaceMethodology:
    """Metodologi Permukaan Respon (RSM) berbasis Box-Behnken Design (BBD) didukung scikit-learn & scipy."""

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
        self.beta = [0.0] * 10
        self.r2 = 0.0
        self.r2_adj = 0.0
        self.f_stat = 0.0
        self.p_model = 0.0
        self.se_beta = []
        self.t_stat_beta = []
        self.p_val_beta = []
        self.kanonikal = {}
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
            print(" Solver: scikit-learn (LinearRegression) & scipy.optimize (L-BFGS-B)")
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

        # Fitting Second-Order Polynomial Model via scikit-learn
        self._fit_polynomial(y_list)

        # Cari Titik Optimum Kontinu Eksak via scipy.optimize
        self._cari_titik_optimum()

        durasi = time.time() - mulai
        if verbose:
            print("=" * 78)
            print(f" Waktu Eksekusi RSM: {durasi:.1f} detik | R^2 = {self.r2:.4f} (R^2 Adj = {self.r2_adj:.4f}) | F = {self.f_stat:.2f} (p = {self.p_model:.4e})")
            print("=" * 78)

        return self.optimum_natural

    def _fit_polynomial(self, y):
        """
        Menyelesaikan regresi kuadratik 10 parameter menggunakan scikit-learn LinearRegression:
        y = b0 + b1*x1 + b2*x2 + b3*x3 + b11*x1^2 + b22*x2^2 + b33*x3^2 + b12*x1*x2 + b13*x1*x3 + b23*x2*x3
        Dilengkapi penghitungan ANOVA dan uji signifikansi koefisien (t-test & p-value).
        """
        if not HAS_SCIENTIFIC or np is None or LinearRegression is None or stats is None:
            return
        N = len(self.design_points)
        X = []
        for x1, x2, x3 in self.design_points:
            X.append([
                1.0,                    # b0
                x1, x2, x3,             # b1, b2, b3
                x1**2, x2**2, x3**2,    # b11, b22, b33
                x1 * x2, x1 * x3, x2 * x3  # b12, b13, b23
            ])
        X = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=float)
        P = X.shape[1]

        # 1. Regresi Linear OLS via scikit-learn
        reg = LinearRegression(fit_intercept=False).fit(X, y_arr)
        self.beta = [float(c) for c in reg.coef_]

        # 2. ANOVA & Goodness-of-Fit
        y_pred = reg.predict(X)
        ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))
        ss_res = float(np.sum((y_arr - y_pred) ** 2))
        ss_reg = max(0.0, ss_tot - ss_res)
        df_reg = P - 1
        df_res = N - P

        self.r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
        self.r2_adj = (
            max(0.0, 1.0 - ((ss_res / max(1, df_res)) / (ss_tot / max(1, N - 1))))
            if ss_tot > 0 and df_res > 0
            else self.r2
        )

        ms_reg = ss_reg / max(1, df_reg)
        ms_res = ss_res / max(1, df_res)
        self.f_stat = float(ms_reg / ms_res) if ms_res > 0 else 0.0
        self.p_model = float(stats.f.sf(self.f_stat, df_reg, df_res)) if ms_res > 0 and df_res > 0 else 1.0

        # 3. Standard Error & Uji t untuk Masing-Masing Koefisien
        try:
            cov_beta = ms_res * np.linalg.inv(X.T @ X)
            self.se_beta = [float(np.sqrt(max(0.0, cov_beta[i, i]))) for i in range(P)]
            self.t_stat_beta = [
                float(self.beta[i] / self.se_beta[i]) if self.se_beta[i] > 1e-12 else 0.0
                for i in range(P)
            ]
            self.p_val_beta = [
                float(2.0 * stats.t.sf(abs(t), df_res)) if df_res > 0 else 1.0
                for t in self.t_stat_beta
            ]
        except Exception:
            self.se_beta = [0.0] * P
            self.t_stat_beta = [0.0] * P
            self.p_val_beta = [1.0] * P

        # 4. Analisis Kanonikal (Canonical Analysis) Titik Stasioner
        self._analisis_kanonikal()

    def _analisis_kanonikal(self):
        """
        Analisis kanonikal model kuadratik orde-2 (Montgomery, Design & Analysis of Experiments):
        Mengevaluasi matriks Hessian B untuk menentukan sifat kelengkungan (curvature) permukaan.
        """
        if not HAS_SCIENTIFIC or np is None:
            return
        b = self.beta
        B = np.array([
            [b[4], 0.5 * b[7], 0.5 * b[8]],
            [0.5 * b[7], b[5], 0.5 * b[9]],
            [0.5 * b[8], 0.5 * b[9], b[6]]
        ], dtype=float)
        b_vec = np.array([b[1], b[2], b[3]], dtype=float)

        eigvals, _ = np.linalg.eig(B)
        real_eigvals = [float(v.real) for v in eigvals]

        try:
            xs = -0.5 * np.linalg.inv(B) @ b_vec
            xs_tuple = tuple(float(x) for x in xs)
        except Exception:
            xs_tuple = (0.0, 0.0, 0.0)

        all_pos = all(v > 1e-6 for v in real_eigvals)
        all_neg = all(v < -1e-6 for v in real_eigvals)
        if all_pos:
            sifat = "Minimum Unik (Positive Definite / Bowl-shaped)"
        elif all_neg:
            sifat = "Maksimum Unik (Negative Definite / Dome-shaped)"
        else:
            sifat = "Titik Pelana (Saddle Point / Ridge System)"

        self.kanonikal = {
            "eigenvalues": real_eigvals,
            "titik_stasioner": xs_tuple,
            "sifat": sifat
        }

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
        Mencari titik minimum kontinu eksak dari persamaan kuadratik di dalam domain terkode [-1, +1]^3
        menggunakan optimasi non-linear berkendala scipy.optimize.minimize (metode L-BFGS-B).
        """
        if not HAS_SCIENTIFIC or minimize is None:
            return

        def obj(c):
            return self.prediksi_coded(c)

        bounds = [(-1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0)]

        # Multi-start optimization untuk menjamin konvergensi global di dalam batas eksperimen
        restarts = [
            [0.0, 0.0, 0.0],
            [-1.0, -1.0, -1.0], [1.0, -1.0, -1.0], [-1.0, 1.0, -1.0], [1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0], [1.0, -1.0, 1.0], [-1.0, 1.0, 1.0], [1.0, 1.0, 1.0]
        ]
        if hasattr(self, "kanonikal") and "titik_stasioner" in self.kanonikal:
            xs = self.kanonikal["titik_stasioner"]
            if all(-1.0 <= x <= 1.0 for x in xs):
                restarts.append(list(xs))

        best_res = None
        best_fun = float("inf")

        for x0 in restarts:
            res = minimize(obj, x0=x0, method="L-BFGS-B", bounds=bounds)
            if res.fun < best_fun:
                best_fun = float(res.fun)
                best_res = res

        if best_res is not None and getattr(best_res, "x", None) is not None:
            self.optimum_coded = tuple(round(float(x), 4) for x in best_res.x)
            self.optimum_prediksi = best_fun
            self.optimum_natural = self.coded_to_natural(self.optimum_coded)

    def cetak_laporan_lengkap(self, bks=None):
        """Menampilkan laporan lengkap Response Surface, koefisien model, ANOVA, dan parameter optimum."""
        print("\n" + "=" * 85)
        print(f" LAPORAN RESPONSE SURFACE METHODOLOGY — {self.nama_instance}")
        print(" (Didukung scikit-learn & scipy.optimize L-BFGS-B)")
        print("=" * 85)

        # 1. Tabel Rancangan Eksperimen
        print(f"  {'Run':>3} | {'x1':>4} {'x2':>4} {'x3':>4} | " + " | ".join(f"{n:>17}" for n in self.factor_names) + " | {'Rata':>8} | {'Best':>8}")
        print("  " + "-" * 81)

        for e in self.hasil_eksperimen:
            c = e["coded"]
            p = e["parameter"]
            vals_str = " | ".join(
                f"{p[n]:>17.3f}" if isinstance(p[n], float) and p[n] < 10 else f"{p[n]:>17.1f}"
                for n in self.factor_names
            )
            print(f"  {e['run_id']:>3} | {c[0]:>4} {c[1]:>4} {c[2]:>4} | {vals_str} | {e['rata']:>8.1f} | {e['terbaik']:>8}")

        print("  " + "-" * 81)

        # 2. Tabel Estimasi Parameter & Uji Signifikansi
        nama_istilah = [
            "Intercept (b0)",
            f"Linear {self.factor_names[0]} (b1)",
            f"Linear {self.factor_names[1]} (b2)",
            f"Linear {self.factor_names[2]} (b3)",
            f"Kuadratik {self.factor_names[0]}^2 (b11)",
            f"Kuadratik {self.factor_names[1]}^2 (b22)",
            f"Kuadratik {self.factor_names[2]}^2 (b33)",
            f"Interaksi {self.factor_names[0]}*{self.factor_names[1]} (b12)",
            f"Interaksi {self.factor_names[0]}*{self.factor_names[2]} (b13)",
            f"Interaksi {self.factor_names[1]}*{self.factor_names[2]} (b23)",
        ]

        print(f"\n  ESTIMASI PARAMETER MODEL KUADRATIK & UJI SIGNIFIKANSI (t-Test):")
        print(f"  {'Istilah':<38} | {'Koefisien':>10} | {'Std Error':>10} | {'t-Stat':>8} | {'p-Value':>9} | {'Signifikansi':<12}")
        print("  " + "-" * 98)
        for i in range(10):
            p_val = self.p_val_beta[i] if i < len(self.p_val_beta) else 1.0
            b_val = self.beta[i] if i < len(self.beta) else 0.0
            se_val = self.se_beta[i] if i < len(self.se_beta) else 0.0
            t_val = self.t_stat_beta[i] if i < len(self.t_stat_beta) else 0.0
            sig = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else ("." if p_val < 0.1 else "ns")))
            print(f"  {nama_istilah[i]:<38} | {b_val:>10.2f} | {se_val:>10.2f} | {t_val:>8.2f} | {p_val:>9.4f} | {sig:<12}")
        print("  " + "-" * 98)
        print("  Keterangan signifikansi: '***' p<0.001, '**' p<0.01, '*' p<0.05, 'ns' tidak signifikan")

        # 3. Kualitas Kesesuaian Model (ANOVA)
        print(f"\n  ANALISIS VARIANSI (ANOVA) & GOODNESS OF FIT:")
        print(f"    * Koefisien Determinasi R^2      : {self.r2 * 100:.2f}%")
        print(f"    * Adjusted R^2                   : {self.r2_adj * 100:.2f}%")
        print(f"    * Model F-Statistic              : {self.f_stat:.2f} (p-value: {self.p_model:.4e})")

        # 4. Analisis Kanonikal
        if hasattr(self, "kanonikal") and self.kanonikal:
            ev = self.kanonikal["eigenvalues"]
            xs = self.kanonikal["titik_stasioner"]
            print(f"\n  ANALISIS KANONIKAL TITIK STASIONER:")
            print(f"    * Nilai Eigen Matriks Hessian (lambda) : [{ev[0]:.2f}, {ev[1]:.2f}, {ev[2]:.2f}]")
            print(f"    * Sifat Permukaan Respon               : {self.kanonikal['sifat']}")
            print(f"    * Titik Stasioner Terkode              : ({xs[0]:+.3f}, {xs[1]:+.3f}, {xs[2]:+.3f})")

        # 5. Parameter Optimum Terpilih
        print("\n  " + "=" * 81)
        print("  PARAMETER OPTIMUM KONTINU HASIL MINIMALISASI RESPONSE SURFACE (L-BFGS-B):")
        print("  " + "=" * 81)
        if self.optimum_coded is not None:
            print(f"    * Titik Terkode (Coded x*)        : x1={self.optimum_coded[0]:+.4f}, x2={self.optimum_coded[1]:+.4f}, x3={self.optimum_coded[2]:+.4f}")
        if self.optimum_natural is not None:
            for k, v in self.optimum_natural.items():
                fmt = f"{v:.4f}" if v < 10 else f"{v:.1f}"
                print(f"    * {k:<30} : {fmt}")
        if self.optimum_prediksi is not None:
            print(f"    * Prediksi Nilai Objektif Optimum: {self.optimum_prediksi:.1f}")

            if bks is not None:
                gap = ((self.optimum_prediksi - bks) / bks) * 100
                print(f"    * BKS Instance ({self.nama_instance:<15}) : {bks} (Prediksi Gap: +{gap:.2f}%)")

        print("  " + "=" * 81)

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
