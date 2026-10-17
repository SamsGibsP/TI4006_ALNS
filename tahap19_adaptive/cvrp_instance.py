"""
cvrp_instance.py  —  TAHAP 5
===============================================================================
Kelas CVRPInstance: membungkus SELURUH data masalah menjadi satu objek.

Konsep baru: KOMPOSISI.
Sebuah objek bisa berisi objek lain. Di sini, satu objek CVRPInstance
berisi 32 objek Node di dalamnya.

Catat perbedaan perlakuan:
  - daftar node  -> dijadikan objek, karena tiap node punya banyak data
                    sekaligus kemampuan (menghitung jarak)
  - kapasitas    -> cukup variabel biasa, karena hanya satu angka
  - jumlah kendaraan -> sama, cukup variabel biasa

Jangan membuat kelas hanya supaya terlihat "OOP". Buat kelas kalau
memang menyederhanakan.
===============================================================================
"""

import math


class CVRPInstance:
    def __init__(self, daftar_node, kapasitas, jumlah_kendaraan, batas_armada=None):
        self.daftar_node = daftar_node
        self.kapasitas = kapasitas
        self.k_file = jumlah_kendaraan

        self.depot = daftar_node[0]
        self.pelanggan = [n for n in daftar_node if not n.adalah_depot()]

        # 1. Lookup node O(1)
        self.node_dict = {n.nomor: n for n in self.daftar_node}

        # 2. Precompute matriks jarak 2D berbasis list of lists O(1)
        max_id = max(self.node_dict.keys())
        self._matriks_jarak = [[0] * (max_id + 1) for _ in range(max_id + 1)]
        for a in daftar_node:
            row = self._matriks_jarak[a.nomor]
            for b in daftar_node:
                row[b.nomor] = a.jarak_ke(b)

        # Alias matriks jarak untuk kompatibilitas
        self.matrix_jarak = self._matriks_jarak

        # 3. Precompute array demand dan jarak maksimum untuk Shaw removal cepat
        self._demand_node = [0] * (max_id + 1)
        for n in daftar_node:
            self._demand_node[n.nomor] = n.demand

        self._max_d = max(max(baris) for baris in self._matriks_jarak)
        if self._max_d <= 0:
            self._max_d = 1.0

        # Batas armada minimal fisik dihitung secara generik berbasis 1D Bin Packing Problem (BPP)
        if batas_armada is not None:
            self.jumlah_kendaraan = batas_armada
        else:
            self.jumlah_kendaraan = self._hitung_armada_minimal_fisik()

        self.batas_armada = self.jumlah_kendaraan

    def _hitung_armada_minimal_fisik(self):
        """
        Menghitung batas bawah armada fisik secara matematis & generik:
        1. Batas bawah kontinu L0 = ceil(sum(demand) / kapasitas)
        2. Batas bawah diskret 1D Bin Packing Problem (BPP) menggunakan First-Fit Decreasing (FFD)
        3. Menetapkan jumlah armada minimal fisik = max(k_file, L0, k_bpp)
        """
        demands = sorted([p.demand for p in self.pelanggan], reverse=True)
        total_demand = sum(demands)
        l0 = math.ceil(total_demand / self.kapasitas) if self.kapasitas > 0 else 1

        # Simulasi 1D Bin Packing Problem (First-Fit Decreasing)
        bins = []
        for d in demands:
            placed = False
            for i in range(len(bins)):
                if bins[i] + d <= self.kapasitas:
                    bins[i] += d
                    placed = True
                    break
            if not placed:
                bins.append(d)
        k_bpp = len(bins)

        k_nominal = self.k_file if self.k_file is not None else 1
        return max(k_nominal, l0, k_bpp)

    def ambil_node(self, nomor):
        return self.node_dict[nomor]

    def jarak(self, nomor_a, nomor_b):
        return self._matriks_jarak[nomor_a][nomor_b]

    # =====================================================================
    # METODE 3 : ringkasan angka-angka penting
    # =====================================================================
    def total_demand(self):
        """Total permintaan seluruh pelanggan."""
        return sum(n.demand for n in self.pelanggan)

    def kendaraan_minimal(self):
        """Jumlah kendaraan paling sedikit yang mungkin bisa melayani semua."""
        return math.ceil(self.total_demand() / self.kapasitas)

    def cetak_ringkasan(self):
        """Menampilkan isi instance untuk memastikan data terbaca benar."""
        print("=" * 60)
        print(" RINGKASAN INSTANCE")
        print("=" * 60)
        print(f"  Jumlah node        : {len(self.daftar_node)}")
        print(f"  Jumlah pelanggan   : {len(self.pelanggan)}")
        print(f"  Depot              : {self.depot}")
        print(f"  Kapasitas kendaraan: {self.kapasitas}")
        print(f"  Jumlah kendaraan   : {self.jumlah_kendaraan}")
        print(f"  Total demand       : {self.total_demand()}")
        print(f"  Kendaraan minimal  : {self.kendaraan_minimal()}")
        print("=" * 60)
