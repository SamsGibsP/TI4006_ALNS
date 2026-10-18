"""
visualisasi.py — MODUL VISUALISASI GRAFIK ALNS & MODIFIKASI
===============================================================================
Menghasilkan grafik publikasi ilmiah beresolusi tinggi (300 DPI)
tersimpan secara tunggal di folder `hasil_final/`:
1. grafik_probabilitas_operator.png
   - Plot probabilitas dinamis adaptif tiap operator destroy & repair sepanjang iterasi (2000 iterasi).
2. grafik_konvergensi_modifikasi.png
   - Kurva konvergensi (Cost vs Iteration) membandingkan Baseline vs Full ALNS vs Nilai BKS (seed yang sama).
3. grafik_studi_ablasi.png & grafik_studi_ablasi_grouped.png
   - Diagram batang studi ablasi pada 3 instance CVRP yang DIBACA LANGSUNG dari CSV hasil eksperimen terbaru.
4. grafik_rute_solusi.png
   - Peta visual rute kendaraan untuk instance X-n143-k7.
===============================================================================
"""

import csv
import os
import random
import sys
from typing import Any

folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
dir_root = os.path.dirname(folder_tahap19)
dir_hasil_final = os.path.join(dir_root, "hasil_final")
os.makedirs(dir_hasil_final, exist_ok=True)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

try:
    import matplotlib  # type: ignore
    import matplotlib.pyplot as _plt  # type: ignore

    # Konfigurasi style grafik ilmiah
    matplotlib.rcParams['font.sans-serif'] = 'DejaVu Sans'
    matplotlib.rcParams['axes.edgecolor'] = '#333333'
    matplotlib.rcParams['axes.linewidth'] = 1.0
    plt: Any = _plt
except ImportError:
    matplotlib: Any = None
    plt: Any = None

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance


def plot_probabilitas_operator(pencari, instance_name="X-n101-k25", output_path=None):
    """
    Menghasilkan grafik probabilitas adaptif operator terhadap iterasi.
    """
    if plt is None:
        print("[WARN] matplotlib tidak terpasang.")
        return
    if output_path is None:
        output_path = os.path.join(dir_hasil_final, "grafik_probabilitas_operator.png")

    riwayat = pencari.riwayat_bobot
    if not riwayat:
        print("[WARN] Riwayat bobot kosong.")
        return

    iterasi_list = [r[0] for r in riwayat]

    # Kumpulkan semua nama operator
    semua_destroy = list(riwayat[0][1].keys())
    semua_repair = list(riwayat[0][2].keys())

    # Hitung probabilitas p_i = w_i / sum(w) pada tiap titik segmen
    prob_d = {name: [] for name in semua_destroy}
    prob_r = {name: [] for name in semua_repair}

    for it, bd, br in riwayat:
        tot_d = sum(bd.values())
        tot_r = sum(br.values())
        for name in semua_destroy:
            prob_d[name].append(bd[name] / tot_d if tot_d > 0 else 0)
        for name in semua_repair:
            prob_r[name].append(br[name] / tot_r if tot_r > 0 else 0)

    # Plot 2 Subplot: Destroy Operators & Repair Operators
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    fig.patch.set_facecolor('#ffffff')

    warna_d = {"random_removal": "#1f77b4", "worst_removal": "#ff7f0e", "shaw_removal": "#2ca02c"}
    warna_r = {"greedy_insertion": "#d62728", "regret2_insertion": "#9467bd", "regret3_insertion": "#8c564b"}

    # Subplot 1: Destroy
    for name in semua_destroy:
        label_clean = name.replace("_", " ").title()
        color = warna_d.get(name, None)
        ax1.plot(iterasi_list, prob_d[name], label=label_clean, color=color, linewidth=2.0)

    ax1.set_ylabel("Selection Probability", fontsize=11, fontweight='bold')
    ax1.set_title(f"Adaptive Operator Probabilities over Iterations ({instance_name})\n(a) Destroy Operators", fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", framealpha=0.9, fontsize=10)
    ax1.set_ylim(-0.02, max(0.6, max(max(v) for v in prob_d.values()) + 0.05))

    # Subplot 2: Repair
    for name in semua_repair:
        label_clean = name.replace("_", " ").title()
        color = warna_r.get(name, None)
        ax2.plot(iterasi_list, prob_r[name], label=label_clean, color=color, linewidth=2.0)

    ax2.set_xlabel("Iteration", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Selection Probability", fontsize=11, fontweight='bold')
    ax2.set_title("(b) Repair Operators", fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", framealpha=0.9, fontsize=10)
    ax2.set_ylim(-0.02, max(0.6, max(max(v) for v in prob_r.values()) + 0.05))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [GRAFIK 1] Tersimpan di: {output_path}")


def plot_konvergensi(riwayat_baseline, riwayat_full, bks, instance_name="X-n101-k25", output_path=None):
    """
    Kurva konvergensi perbandingan Baseline vs Full ALNS pada seed yang sama.
    """
    if plt is None:
        print("[WARN] matplotlib tidak terpasang.")
        return
    if output_path is None:
        output_path = os.path.join(dir_hasil_final, "grafik_konvergensi_modifikasi.png")

    plt.figure(figsize=(10, 6))
    plt.plot(riwayat_baseline, label="Baseline ALNS (Tanpa Modifikasi)", color="#d62728", linestyle="--", linewidth=1.8, alpha=0.8)
    plt.plot(riwayat_full, label="Full ALNS (4 Modifikasi)", color="#1f77b4", linewidth=2.2)
    plt.axhline(y=bks, color="#2ca02c", linestyle=":", linewidth=2.0, label=f"BKS Optimal ({bks})")

    plt.title(f"Kurva Konvergensi ALNS: Baseline vs Full Modifikasi ({instance_name})", fontsize=12, fontweight='bold')
    plt.xlabel("Iterasi", fontsize=11, fontweight='bold')
    plt.ylabel("Total Jarak Solusi (Cost)", fontsize=11, fontweight='bold')
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=10, loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [GRAFIK 2] Tersimpan di: {output_path}")


def muat_data_ablasi_dari_csv(path_csv=None):
    """
    Membaca data gap rata-rata studi ablasi secara dinamis dari CSV terbaru.
    Tidak menggunakan angka hardcoded sama sekali.
    """
    if path_csv is None:
        path_csv = os.path.join(dir_hasil_final, "ringkasan_ablasi.csv")

    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"File ringkasan ablasi tidak ditemukan di {path_csv}")

    data_ablasi_semua = {}
    label_cfg_map = {
        "Full": "Full ALNS",
        "Without_Shaw": "Tanpa Shaw",
        "Without_Regret3": "Tanpa Regret-3",
        "Without_LocalSearch": "Tanpa Local Search",
        "Without_Reheating": "Tanpa Reheating",
        "Ablation_Baseline": "Baseline",
    }

    with open(path_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            inst = r["instance"]
            cfg = r["konfigurasi"]
            gap_str = r["gap_rata2_persen"].replace("%", "").strip()
            gap_val = float(gap_str)
            label_clean = label_cfg_map.get(cfg, cfg)

            if inst not in data_ablasi_semua:
                data_ablasi_semua[inst] = []

            data_ablasi_semua[inst].append({
                "konfigurasi": label_clean,
                "gap_mean": gap_val,
                "raw_cfg": cfg,
            })

    return data_ablasi_semua


def plot_studi_ablasi(data_ablasi_semua, output_path=None):
    """
    Diagram batang perbandingan performa studi ablasi untuk 3 instance (3-panel).
    Dibangun dari data CSV aktual.
    """
    if plt is None:
        print("[WARN] matplotlib tidak terpasang.")
        return
    if output_path is None:
        output_path = os.path.join(dir_hasil_final, "grafik_studi_ablasi.png")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.patch.set_facecolor('#ffffff')

    instance_keys = [
        ("X-n101-k25", "(a) X-n101-k25 (n=100, K=25)"),
        ("X-n143-k7", "(b) X-n143-k7 (n=142, K=7)"),
        ("X-n351-k40", "(c) X-n351-k40 (n=350, K=40)")
    ]

    for ax, (inst_id, title) in zip(axes, instance_keys):
        items = data_ablasi_semua[inst_id]
        labels = [d["konfigurasi"] for d in items]
        gaps = [d["gap_mean"] for d in items]

        colors = ["#2ca02c" if "Full" in l else ("#d62728" if "Baseline" in l else "#1f77b4") for l in labels]
        bars = ax.bar(labels, gaps, color=colors, width=0.55, edgecolor="#333333", linewidth=1.0)

        max_g = max(gaps) if gaps else 1.0
        for bar, gap in zip(bars, gaps):
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2.0, yval + (max_g * 0.015), f"+{gap:.2f}%",
                    ha='center', va='bottom', fontsize=8.5, fontweight='bold')

        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_ylabel("Rata-rata Gap terhadap BKS (%)" if ax == axes[0] else "", fontsize=10, fontweight='bold')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=8.5)
        ax.grid(axis='y', linestyle="--", alpha=0.5)
        ax.set_ylim(0, max_g * 1.18)

    plt.suptitle("Studi Ablasi Multi-Instance: Pengaruh Mematikan Tiap Modifikasi terhadap Solusi ALNS", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [GRAFIK 3 - 3 INSTANCE] Tersimpan di: {output_path}")


def plot_studi_ablasi_grouped(data_ablasi_semua, output_path=None):
    """
    Diagram batang berkelompok (Clustered Bar Chart) 3 instance dalam 1 grafik sumbu tunggal.
    """
    if plt is None:
        print("[WARN] matplotlib tidak terpasang.")
        return
    if output_path is None:
        output_path = os.path.join(dir_hasil_final, "grafik_studi_ablasi_grouped.png")

    labels = [d["konfigurasi"] for d in data_ablasi_semua["X-n101-k25"]]
    n_labels = len(labels)
    x_indices = list(range(n_labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#ffffff')

    gaps_101 = [d["gap_mean"] for d in data_ablasi_semua["X-n101-k25"]]
    gaps_143 = [d["gap_mean"] for d in data_ablasi_semua["X-n143-k7"]]
    gaps_351 = [d["gap_mean"] for d in data_ablasi_semua["X-n351-k40"]]

    x_101 = [i - width for i in x_indices]
    x_143 = x_indices
    x_351 = [i + width for i in x_indices]

    ax.bar(x_101, gaps_101, width, label='X-n101-k25 (n=100)', color='#1f77b4', edgecolor='#333333')
    ax.bar(x_143, gaps_143, width, label='X-n143-k7 (n=142)', color='#ff7f0e', edgecolor='#333333')
    ax.bar(x_351, gaps_351, width, label='X-n351-k40 (n=350)', color='#2ca02c', edgecolor='#333333')

    ax.set_ylabel('Rata-rata Gap terhadap BKS (%)', fontsize=11, fontweight='bold')
    ax.set_title('Perbandingan Gap Studi Ablasi pada 3 Instance CVRPLIB (Hasil CSV Terbaru)', fontsize=12, fontweight='bold')
    ax.set_xticks(x_indices)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=9.5)
    ax.legend(framealpha=0.9, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [GRAFIK 3B - GROUPED] Tersimpan di: {output_path}")


def plot_rute_solusi(solusi, output_path=None):
    """
    Plot koordinat geografis depot dan pelanggan beserta rute kendaraan.
    """
    if plt is None:
        print("[WARN] matplotlib tidak terpasang.")
        return
    if output_path is None:
        output_path = os.path.join(dir_hasil_final, "grafik_rute_solusi.png")

    plt.figure(figsize=(9, 8))
    depot = solusi.instance.depot
    rute_aktif = [r for r in solusi.rute if not r.kosong()]

    cmap = plt.get_cmap("tab20", max(len(rute_aktif), 1))

    for idx, r in enumerate(rute_aktif):
        coords_x = [depot.x] + [v.node.x for v in r.daftar_visit] + [depot.x]
        coords_y = [depot.y] + [v.node.y for v in r.daftar_visit] + [depot.y]
        color = cmap(idx % 20)
        plt.plot(coords_x, coords_y, marker='o', markersize=4, color=color, alpha=0.75, linewidth=1.5)

    # Plot Depot
    plt.scatter([depot.x], [depot.y], marker='s', s=160, color='red', edgecolor='black', linewidth=1.5, zorder=5, label='Depot')

    plt.title(f"Visualisasi Rute Solusi Terbaik ALNS (X-n101-k25)\n{len(rute_aktif)} Kendaraan | Total Jarak = {solusi.total_jarak}", fontsize=12, fontweight='bold')
    plt.xlabel("Koordinat X", fontsize=11, fontweight='bold')
    plt.ylabel("Koordinat Y", fontsize=11, fontweight='bold')
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [GRAFIK 4] Tersimpan di: {output_path}")


def main():
    if plt is None:
        print("[ERROR] matplotlib tidak terpasang.")
        return
    print("=" * 80)
    print(" PEMBUATAN GRAFIK VISUALISASI MODIFIKASI ALNS (PUBLIKASI ILMIAH)")
    print(f" Target Folder Output Tunggal: {dir_hasil_final}")
    print("=" * 80)

    # 1. Jalankan ALNS Full dan Baseline untuk mengambil data riwayat iterasi (seed yang sama: 42)
    path_vrp = os.path.join(folder_tahap19, "X", "X-n101-k25.vrp")
    d, c, k = baca_instance(path_vrp)
    instance = CVRPInstance(d, c, k)
    solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

    SEED_VISUALISASI = 42

    print("  * Menjalankan ALNS Full (2000 iterasi, seed 42) untuk merekam probabilitas operator...")
    random.seed(SEED_VISUALISASI)
    pencari_full = ALNS(
        instance,
        maks_iterasi=2000,
        suhu_awal=800.0,
        laju_pendinginan=0.990,
        reaction_factor=0.31,
        panjang_segmen=100,
        pakai_ls=True,
        pakai_shaw=True,
        pakai_reheating=True,
        pakai_regret3=True,
        tampilkan_setiap=0
    )
    hasil_full = pencari_full.jalankan(solusi_awal.copy())

    print("  * Menjalankan ALNS Baseline (2000 iterasi, seed 42) untuk data pembanding konvergensi...")
    random.seed(SEED_VISUALISASI)
    pencari_base = ALNS(
        instance,
        maks_iterasi=2000,
        suhu_awal=800.0,
        laju_pendinginan=0.990,
        reaction_factor=0.31,
        panjang_segmen=100,
        pakai_ls=False,
        pakai_shaw=False,
        pakai_reheating=False,
        pakai_regret3=False,
        tampilkan_setiap=0
    )
    hasil_base = pencari_base.jalankan(solusi_awal.copy())

    # 2. Gambar Grafik 1: Probabilitas Operator
    out1 = os.path.join(dir_hasil_final, "grafik_probabilitas_operator.png")
    plot_probabilitas_operator(pencari_full, instance_name="X-n101-k25", output_path=out1)

    # 3. Gambar Grafik 2: Kurva Konvergensi
    out2 = os.path.join(dir_hasil_final, "grafik_konvergensi_modifikasi.png")
    plot_konvergensi(pencari_base.riwayat_terbaik, pencari_full.riwayat_terbaik, bks=27591, instance_name="X-n101-k25", output_path=out2)

    # 4. Gambar Grafik 3 & 3B: Diagram Batang Studi Ablasi (DIBACA LANGSUNG DARI CSV TERBARU)
    print("  * Membaca data ringkasan ablasi dari hasil_final/ringkasan_ablasi.csv...")
    data_ablasi_semua = muat_data_ablasi_dari_csv()

    out3 = os.path.join(dir_hasil_final, "grafik_studi_ablasi.png")
    plot_studi_ablasi(data_ablasi_semua, output_path=out3)

    out3b = os.path.join(dir_hasil_final, "grafik_studi_ablasi_grouped.png")
    plot_studi_ablasi_grouped(data_ablasi_semua, output_path=out3b)

    # 5. Gambar Grafik 4: Peta Visual Rute Solusi
    out4 = os.path.join(dir_hasil_final, "grafik_rute_solusi.png")
    plot_rute_solusi(hasil_full, output_path=out4)

    print("\n" + "=" * 80)
    print(" SELURUH GRAFIK VISUALISASI BERHASIL DIBUAT SECARA TUNGGAL DI HASIL_FINAL (300 DPI)")
    print("=" * 80)


if __name__ == "__main__":
    main()
