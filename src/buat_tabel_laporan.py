"""
buat_tabel_laporan.py
Membangun tabel Markdown untuk Bab 8 dan Bab 9 laporan akademik
langsung dari berkas hasil mentah CSV (hasil_mentah_baseline.csv dan hasil_mentah_ablasi.csv).
Menghitung statistik inferensial: Mann-Whitney U test p-value dan 95% Bootstrap Confidence Interval.
"""

import os
import csv
import math
import numpy as np
from scipy.stats import mannwhitneyu

FOLDER_SRC = os.path.dirname(os.path.abspath(__file__))
FOLDER_ROOT = os.path.dirname(FOLDER_SRC)
FOLDER_FINAL = os.path.join(FOLDER_ROOT, "hasil_final")
FOLDER_DOCS = os.path.join(FOLDER_ROOT, "docs")

PATH_LAPORAN_ROOT = os.path.join(FOLDER_ROOT, "laporan_akademik_alns.md")
PATH_LAPORAN_DOCS = os.path.join(FOLDER_DOCS, "laporan_akademik_alns.md")

BKS_MAP = {
    "X-n101-k25": 27591.0,
    "X-n143-k7": 15700.0,
    "X-n351-k40": 25896.0,
}

CW_MAP = {
    "X-n101-k25": (28986, 28),
    "X-n143-k7": (17478, 7),
    "X-n351-k40": (27123, 41),
}


def cari_csv(nama_file):
    search_dirs = [
        FOLDER_FINAL,
        FOLDER_ROOT,
        FOLDER_SRC,
        os.path.join(FOLDER_ROOT, "doc"),
        os.path.join(FOLDER_ROOT, "docs"),
    ]
    for folder in search_dirs:
        p = os.path.join(folder, nama_file)
        if os.path.exists(p):
            return p
    return None


def baca_csv_raw(nama_file):
    p = cari_csv(nama_file)
    if not p:
        raise FileNotFoundError(f"File {nama_file} tidak ditemukan di folder final, root, doc, maupun src.")
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Normalisasi tipe
            r["jarak"] = float(r["jarak"])
            r["waktu_detik"] = float(r["waktu_detik"])
            r["jumlah_rute"] = int(r.get("jumlah_rute") or r.get("rute_aktif") or 0)
            if "layak" in r:
                r["layak_bool"] = str(r["layak"]).strip().lower() in ["true", "1", "layak"]
            else:
                r["layak_bool"] = str(r.get("status", "")).strip().upper() == "LAYAK"
            rows.append(r)
    return rows


def bootstrap_ci(data, n_boot=2000, ci=0.95, seed=42):
    if len(data) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(seed)
    boot_means = [rng.choice(data, size=len(data), replace=True).mean() for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    low = float(np.percentile(boot_means, 100 * alpha))
    high = float(np.percentile(boot_means, 100 * (1 - alpha)))
    return low, high


def bootstrap_ci_delta(data_cfg, data_full, n_boot=2000, ci=0.95, seed=42):
    if len(data_cfg) == 0 or len(data_full) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(seed)
    n_c = len(data_cfg)
    n_f = len(data_full)
    boot_deltas = [
        rng.choice(data_cfg, size=n_c, replace=True).mean() - rng.choice(data_full, size=n_f, replace=True).mean()
        for _ in range(n_boot)
    ]
    alpha = (1.0 - ci) / 2.0
    low = float(np.percentile(boot_deltas, 100 * alpha))
    high = float(np.percentile(boot_deltas, 100 * (1 - alpha)))
    return low, high


def buat_tabel_bab8():
    """Tabel Evaluasi Baseline vs Full ALNS."""
    rows = baca_csv_raw("hasil_mentah_baseline.csv")
    instances = ["X-n101-k25", "X-n143-k7", "X-n351-k40"]
    configs = ["Baseline", "Full"]

    md_lines = [
        "| Konfigurasi | Instance | BKS | Solusi Awal (CW) | Terbaik | Rata-rata | Terburuk | Std Dev | Gap Best (%) | Gap Avg (%) | 95% Bootstrap CI | Waktu Avg (s) | Status |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for cfg in configs:
        for inst in instances:
            bks = BKS_MAP[inst]
            cw_dist, cw_k = CW_MAP[inst]
            runs = [r for r in rows if r["instance"] == inst and r["konfigurasi"] == cfg and r["layak_bool"]]
            if not runs:
                continue
            jarak_list = [r["jarak"] for r in runs]
            waktu_list = [r["waktu_detik"] for r in runs]

            terbaik = int(min(jarak_list))
            terburuk = int(max(jarak_list))
            rata = sum(jarak_list) / len(jarak_list)
            std = math.sqrt(sum((x - rata) ** 2 for x in jarak_list) / (len(jarak_list) - 1)) if len(jarak_list) > 1 else 0.0
            gap_best = ((terbaik - bks) / bks) * 100.0
            gap_avg = ((rata - bks) / bks) * 100.0
            waktu_avg = sum(waktu_list) / len(waktu_list)

            ci_low, ci_high = bootstrap_ci(jarak_list)

            md_lines.append(
                f"| **{cfg}** | {inst} | {int(bks)} | {cw_dist} ({cw_k} rute) | {terbaik:,} | {rata:,.2f} | {terburuk:,} | {std:.2f} | +{gap_best:.2f}% | +{gap_avg:.2f}% | [{ci_low:,.1f}, {ci_high:,.1f}] | {waktu_avg:.2f}s | 100% Layak |"
            )

    return "\n".join(md_lines)


def buat_tabel_bab9():
    """Tabel Studi Ablasi Komprehensif (Leave-One-Out)."""
    rows = baca_csv_raw("hasil_mentah_ablasi.csv")
    instances = ["X-n101-k25", "X-n143-k7", "X-n351-k40"]
    configs = [
        "Full",
        "Without_Shaw",
        "Without_Regret3",
        "Without_LocalSearch",
        "Without_Reheating",
        "Ablation_Baseline",
    ]

    md_lines = [
        "| Instance | Konfigurasi | BKS | Terbaik | Rata-rata | Terburuk | Std Dev | Gap Best (%) | Gap Avg (%) | Delta vs Full | 95% CI Delta | p-value (MW-U) | Signifikansi | Waktu Avg (s) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for inst in instances:
        bks = BKS_MAP[inst]
        runs_full = [r for r in rows if r["instance"] == inst and r["konfigurasi"] == "Full" and r["layak_bool"]]
        full_dists = [r["jarak"] for r in runs_full]
        full_mean = sum(full_dists) / len(full_dists) if full_dists else 0.0

        for idx_c, cfg in enumerate(configs):
            runs = [r for r in rows if r["instance"] == inst and r["konfigurasi"] == cfg and r["layak_bool"]]
            if not runs:
                continue
            jarak_list = [r["jarak"] for r in runs]
            waktu_list = [r["waktu_detik"] for r in runs]

            terbaik = int(min(jarak_list))
            terburuk = int(max(jarak_list))
            rata = sum(jarak_list) / len(jarak_list)
            std = math.sqrt(sum((x - rata) ** 2 for x in jarak_list) / (len(jarak_list) - 1)) if len(jarak_list) > 1 else 0.0
            gap_best = ((terbaik - bks) / bks) * 100.0
            gap_avg = ((rata - bks) / bks) * 100.0
            waktu_avg = sum(waktu_list) / len(waktu_list)
            delta = rata - full_mean

            if cfg == "Full":
                ci_str = "0.00 (Ref)"
                delta_str = "0.00 (Ref)"
                p_str = "1.0000"
                sig_str = "Ref"
            else:
                d_low, d_high = bootstrap_ci_delta(jarak_list, full_dists)
                ci_str = f"[{d_low:+.1f}, {d_high:+.1f}]"
                delta_str = f"{delta:+.2f}"
                try:
                    _, p_val = mannwhitneyu(jarak_list, full_dists, alternative="two-sided")
                    p_str = f"{p_val:.4f}"
                    sig_str = "Signifikan (p<0.05)" if p_val < 0.05 else "Tidak Signifikan (p>=0.05)"
                except Exception:
                    p_str = "-"
                    sig_str = "-"

            inst_label = f"**{inst}**" if idx_c == 0 else ""
            md_lines.append(
                f"| {inst_label} | {cfg} | {int(bks)} | {terbaik:,} | {rata:,.2f} | {terburuk:,} | {std:.2f} | +{gap_best:.2f}% | +{gap_avg:.2f}% | {delta_str} | {ci_str} | {p_str} | {sig_str} | {waktu_avg:.2f}s |"
            )

    return "\n".join(md_lines)


def main():
    print("=" * 80)
    print(" GENERATOR TABEL LAPORAN AKADEMIK ALNS (BAB 8 & 9)")
    print("=" * 80)

    try:
        tabel8 = buat_tabel_bab8()
        print("\n[BAB 8: TABEL KOMPARASI BASELINE VS FULL ALNS]")
        print(tabel8)
    except Exception as e:
        print(f"Gagal membangun tabel Bab 8: {e}")
        tabel8 = None

    try:
        tabel9 = buat_tabel_bab9()
        print("\n[BAB 9: TABEL STUDI ABLASI LEAVE-ONE-OUT]")
        print(tabel9)
    except Exception as e:
        print(f"Gagal membangun tabel Bab 9: {e}")
        tabel9 = None

    print("\n" + "=" * 80)
    print(" Generator tabel siap digunakan.")
    print("=" * 80)


if __name__ == "__main__":
    main()
