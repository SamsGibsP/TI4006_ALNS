"""
cek_instance.py — Analisis Kapasitas dan Armada (K) untuk Instance CVRP
======================================================================
Menganalisis:
- Total Demand
- Kapasitas Kendaraan (Q)
- Batas Bawah Teoritis Kapasitas: ceil(Total Demand / Q)
- K dari Nama File / Header
- Utilisasi Rata-rata: Total Demand / (K * Q)
- Jumlah Rute Aktual pada Berkas Solusi BKS (.sol)
======================================================================
"""

import math
import os
import re
import sys

folder_ini = os.path.dirname(os.path.abspath(__file__))
if folder_ini not in sys.path:
    sys.path.insert(0, folder_ini)

from baca_data import baca_instance
from cvrp_instance import CVRPInstance

def hitung_info_instance(path_vrp):
    nama_file = os.path.basename(path_vrp)
    daftar_node, kapasitas, k_file = baca_instance(path_vrp)
    inst = CVRPInstance(daftar_node, kapasitas, k_file)

    total_demand = inst.total_demand()
    q = inst.kapasitas
    k_min_teoritis = math.ceil(total_demand / q)
    utilisasi = (total_demand / (k_file * q)) * 100 if (k_file * q) > 0 else 0

    # Cek file .sol pendamping
    path_sol = os.path.splitext(path_vrp)[0] + ".sol"
    rute_bks = None
    cost_bks = None
    if os.path.exists(path_sol):
        with open(path_sol, "r", encoding="utf-8", errors="ignore") as f:
            rute_count = 0
            for line in f:
                line = line.strip()
                if line.startswith("Route #"):
                    rute_count += 1
                elif line.startswith("Cost"):
                    cost_match = re.search(r"Cost\s+(\d+)", line)
                    if cost_match:
                        cost_bks = int(cost_match.group(1))
            rute_bks = rute_count

    catatan = "-"
    if rute_bks is not None:
        if rute_bks > k_file:
            catatan = f"BKS BUTUH {rute_bks} RUTE (> K={k_file})!"
        elif rute_bks == k_file:
            catatan = f"BKS pas K={k_file}"
        else:
            catatan = f"BKS < K ({rute_bks} < {k_file})"

    return {
        "nama": nama_file,
        "n": len(inst.pelanggan),
        "total_demand": total_demand,
        "Q": q,
        "k_min": k_min_teoritis,
        "k_file": k_file,
        "utilisasi": utilisasi,
        "rute_bks": rute_bks if rute_bks is not None else "-",
        "cost_bks": cost_bks if cost_bks is not None else "-",
        "catatan": catatan,
    }


def main():
    print("=" * 105)
    print(" ANALISIS KELAYAKAN ARMADA (K) INSTANCE UTAMA")
    print("=" * 105)

    fokus_instances = [
        os.path.join(folder_ini, "A", "A-n32-k5.vrp"),
        os.path.join(folder_ini, "X", "X-n101-k25.vrp"),
        os.path.join(folder_ini, "X", "X-n143-k7.vrp"),
        os.path.join(folder_ini, "X", "X-n351-k40.vrp"),
    ]

    hasil_fokus = []
    for p in fokus_instances:
        if os.path.exists(p):
            hasil_fokus.append(hitung_info_instance(p))

    header = (
        f" {'Instance':<16} | {'Total Demand':>12} | {'Q':>6} | "
        f"{'ceil(D/Q)':>9} | {'K file':>6} | {'Utilisasi':>9} | "
        f"{'Rute BKS':>8} | {'Cost BKS':>8} | {'Status BKS vs K':<20}"
    )
    print(header)
    print("-" * 105)
    for h in hasil_fokus:
        print(
            f" {h['nama']:<16} | {h['total_demand']:>12} | {h['Q']:>6} | "
            f"{h['k_min']:>9} | {h['k_file']:>6} | {h['utilisasi']:>8.1f}% | "
            f"{str(h['rute_bks']):>8} | {str(h['cost_bks']):>8} | {h['catatan']:<20}"
        )
    print("=" * 105)

    # Cek seluruh instance X untuk mendeteksi apakah ada kasus serupa
    folder_x = os.path.join(folder_ini, "X")
    all_x = sorted([f for f in os.listdir(folder_x) if f.endswith(".vrp")])

    kasus_lebih = []
    kasus_kurang = []
    kasus_pas = []

    for f_vrp in all_x:
        p_vrp = os.path.join(folder_x, f_vrp)
        info = hitung_info_instance(p_vrp)
        if isinstance(info["rute_bks"], int):
            if info["rute_bks"] > info["k_file"]:
                kasus_lebih.append(info)
            elif info["rute_bks"] < info["k_file"]:
                kasus_kurang.append(info)
            else:
                kasus_pas.append(info)

    print(f"\nRINGKASAN POPULASI INSTANCE SET X ({len(all_x)} berkas):")
    print(f"  - BKS menggunakan rute LEBIH dari K nama file : {len(kasus_lebih)} instance")
    print(f"  - BKS menggunakan rute PAS dengan K nama file   : {len(kasus_pas)} instance")
    print(f"  - BKS menggunakan rute KURANG dari K nama file : {len(kasus_kurang)} instance")

    if kasus_lebih:
        print("\nContoh instance di mana BKS membutuhkan rute > K:")
        for k in kasus_lebih[:10]:
            print(f"  * {k['nama']}: K={k['k_file']} tapi BKS={k['rute_bks']} rute (ceil(D/Q)={k['k_min']}, util={k['utilisasi']:.1f}%)")


if __name__ == "__main__":
    main()
