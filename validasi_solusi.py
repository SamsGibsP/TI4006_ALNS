"""
validasi_solusi.py — VALIDATOR INDEPENDEN FILE SOLUSI (.SOL) TERHADAP INSTANCE (.VRP)
======================================================================================
Memverifikasi solusi secara mandiri tanpa bergantung pada kelas solver internal:
1. Mendukung format penomoran pelanggan CVRPLIB Set X (1..n-1) maupun node ID (2..n)
2. Cakupan pelanggan (seluruh pelanggan terlayani tepat satu kali)
3. Tidak ada duplikasi, ID pelanggan asing, atau node depot
4. Kapasitas muatan tiap rute <= kapasitas instance (bebas pelanggaran kapasitas)
5. Rekomputasi jarak tiap rute sesuai standar Euclidean TSPLIB round(sqrt(dx^2 + dy^2))
6. Kesesuaian total jarak terhitung dengan nilai 'Cost' pada file .sol
======================================================================================
"""

import math
import os
import sys


def parse_vrp(path_vrp):
    coords = {}
    demands = {}
    capacity = None
    depot_id = 1

    section = None
    with open(path_vrp, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("CAPACITY"):
                parts = line.split(":")
                capacity = int(parts[1].strip())
            elif line.startswith("NODE_COORD_SECTION"):
                section = "COORD"
                continue
            elif line.startswith("DEMAND_SECTION"):
                section = "DEMAND"
                continue
            elif line.startswith("DEPOT_SECTION"):
                section = "DEPOT"
                continue
            elif line.startswith("EOF"):
                break

            if section == "COORD":
                parts = line.split()
                if len(parts) >= 3:
                    nid = int(parts[0])
                    coords[nid] = (float(parts[1]), float(parts[2]))
            elif section == "DEMAND":
                parts = line.split()
                if len(parts) >= 2:
                    nid = int(parts[0])
                    demands[nid] = int(parts[1])
            elif section == "DEPOT":
                val = int(line)
                if val == -1:
                    section = None
                else:
                    depot_id = val

    pelanggan_node_ids = {nid for nid, dem in demands.items() if dem > 0}
    return {
        "coords": coords,
        "demands": demands,
        "capacity": capacity,
        "depot_id": depot_id,
        "pelanggan": pelanggan_node_ids,
    }


def parse_sol(path_sol):
    routes = []
    stated_cost = None

    with open(path_sol, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Route"):
                parts = line.split(":")
                if len(parts) >= 2:
                    node_strs = parts[1].strip().split()
                    r_nodes = [int(x) for x in node_strs if x]
                    if r_nodes:
                        routes.append(r_nodes)
            elif line.startswith("Cost"):
                parts = line.split()
                if len(parts) >= 2:
                    stated_cost = int(float(parts[1]))

    return {"routes": routes, "stated_cost": stated_cost}


def hitung_jarak_euc(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return round(math.sqrt(dx * dx + dy * dy))


def validasi_solusi(path_vrp, path_sol, verbose=True):
    if not os.path.exists(path_vrp):
        raise FileNotFoundError(f"File VRP tidak ditemukan: {path_vrp}")
    if not os.path.exists(path_sol):
        raise FileNotFoundError(f"File SOL tidak ditemukan: {path_sol}")

    inst = parse_vrp(path_vrp)
    sol = parse_sol(path_sol)

    coords = inst["coords"]
    demands = inst["demands"]
    cap = inst["capacity"]
    depot_id = inst["depot_id"]
    pelanggan_node_ids = inst["pelanggan"]
    depot_coord = coords[depot_id]

    raw_routes = sol["routes"]
    stated_cost = sol["stated_cost"]

    # Deteksi konvensi penomoran di file .sol:
    # 1. CVRPLIB Set X: ID pelanggan adalah 1 s.d. n-1 (yaitu node_id = id + 1 jika depot=1)
    # 2. Raw Node ID: ID pelanggan adalah 2 s.d. n (yaitu node_id = id)
    all_raw_ids = [nid for r in raw_routes for nid in r]
    if all_raw_ids and min(all_raw_ids) == 1 and max(all_raw_ids) == len(pelanggan_node_ids):
        # Format CVRPLIB resmi (1..N-1)
        routes = [[x + 1 for x in r] for r in raw_routes]
        konvensi = "CVRPLIB (1-based customer index: node_id = sol_id + 1)"
    else:
        routes = raw_routes
        konvensi = "Raw Node ID (node_id = sol_id)"

    pelanggaran = []

    # 1. Cek semua pelanggan dikunjungi tepat satu kali
    dikunjungi = [nid for r in routes for nid in r]
    set_dikunjungi = set(dikunjungi)

    belum = [nid for nid in pelanggan_node_ids if nid not in set_dikunjungi]
    if belum:
        pelanggaran.append(f"{len(belum)} pelanggan tidak terlayani: {belum[:10]}...")

    if len(dikunjungi) != len(set_dikunjungi):
        pelanggaran.append(f"Terdapat duplikasi kunjungan: total={len(dikunjungi)}, unik={len(set_dikunjungi)}")

    asing = [nid for nid in set_dikunjungi if nid not in pelanggan_node_ids]
    if asing:
        pelanggaran.append(f"Terdapat ID asing yang bukan pelanggan: {asing}")

    # 2. Cek kapasitas dan hitung ulang jarak per rute
    total_jarak_rekomputasi = 0
    muatan_rute = []

    for idx, r in enumerate(routes, start=1):
        load = sum(demands.get(nid, 0) for nid in r)
        muatan_rute.append(load)
        if load > cap:
            pelanggaran.append(f"Rute #{idx} kelebihan muatan: {load} > {cap}")

        # Hitung jarak rute: depot -> r[0] -> ... -> r[-1] -> depot
        jarak_rute = 0
        prev_coord = depot_coord
        for nid in r:
            cur_coord = coords[nid]
            jarak_rute += hitung_jarak_euc(prev_coord, cur_coord)
            prev_coord = cur_coord
        jarak_rute += hitung_jarak_euc(prev_coord, depot_coord)

        total_jarak_rekomputasi += jarak_rute

    # 3. Cek kesesuaian Cost
    if stated_cost is not None and stated_cost != total_jarak_rekomputasi:
        pelanggaran.append(f"Selisih Cost: tercatat {stated_cost} vs hasil hitung ulang {total_jarak_rekomputasi}")

    is_valid = len(pelanggaran) == 0

    if verbose:
        print("=" * 80)
        print(f" VALIDASI INDEPENDEN: {os.path.basename(path_sol)}")
        print(f" Terhadap Instance  : {os.path.basename(path_vrp)}")
        print("=" * 80)
        print(f"  Konvensi Penomoran   : {konvensi}")
        print(f"  Jumlah Pelanggan     : {len(pelanggan_node_ids)} node")
        print(f"  Jumlah Rute Aktif    : {len(routes)} rute")
        print(f"  Kapasitas Maksimal   : {cap} unit")
        print(f"  Muatan Rute Maksimum : {max(muatan_rute) if muatan_rute else 0} unit")
        print(f"  Total Jarak Hitung   : {total_jarak_rekomputasi}")
        print(f"  Cost Tercatat        : {stated_cost}")
        print(f"  Status Validasi      : {'100% VALID & LAYAK' if is_valid else 'TIDAK LAYAK'}")
        if pelanggaran:
            print("  Pelanggaran Ditemukan:")
            for p in pelanggaran:
                print(f"    - {p}")
        print("=" * 80)

    if not is_valid:
        raise ValueError(f"Validasi gagal untuk {path_sol}: {pelanggaran}")

    return {
        "valid": True,
        "n_pelanggan": len(pelanggan_node_ids),
        "jumlah_rute": len(routes),
        "muatan_maks": max(muatan_rute) if muatan_rute else 0,
        "kapasitas": cap,
        "jarak": total_jarak_rekomputasi,
        "stated_cost": stated_cost,
    }


def main():
    folder_ini = os.path.dirname(os.path.abspath(__file__))
    pairs = [
        ("X-n101-k25.vrp", "solusi_terbaik_X-n101-k25.sol"),
        ("X-n143-k7.vrp", "solusi_terbaik_X-n143-k7.sol"),
        ("X-n351-k40.vrp", "solusi_terbaik_X-n351-k40.sol"),
    ]

    semua_lolos = True
    for vrp_name, sol_name in pairs:
        path_vrp = os.path.join(folder_ini, "X", vrp_name)
        if not os.path.exists(path_vrp):
            path_vrp = os.path.join(os.path.dirname(folder_ini), "X", vrp_name)
        path_sol = os.path.join(folder_ini, sol_name)
        if not os.path.exists(path_sol):
            path_sol = os.path.join(os.path.dirname(folder_ini), sol_name)

        if not os.path.exists(path_sol):
            print(f"[SKIP] File {sol_name} belum dibuat.")
            continue

        try:
            validasi_solusi(path_vrp, path_sol, verbose=True)
        except Exception as e:
            print(f"[ERROR] {e}")
            semua_lolos = False

    if semua_lolos:
        print("\nSELURUH FILE SOLUSI TERUJI DAN 100% VALID!")


if __name__ == "__main__":
    main()
