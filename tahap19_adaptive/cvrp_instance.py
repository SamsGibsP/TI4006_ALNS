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
    def __init__(self, daftar_node, kapasitas, jumlah_kendaraan):
        self.daftar_node = daftar_node
        self.kapasitas = kapasitas
        self.jumlah_kendaraan = jumlah_kendaraan
        self.depot = daftar_node[0]
        self.pelanggan = [n for n in daftar_node if not n.adalah_depot()]

        # 1. Lookup node O(1)
        self.node_dict = {n.nomor: n for n in self.daftar_node}

        # 2. Precompute matriks jarak O(1)
        max_id = max(self.node_dict.keys())
        self.matrix_jarak = [[0] * (max_id + 1) for _ in range(max_id + 1)]
        for a in daftar_node:
            for b in daftar_node:
                self.matrix_jarak[a.nomor][b.nomor] = a.jarak_ke(b)

    def ambil_node(self, nomor):
        return self.node_dict[nomor]

    def jarak(self, nomor_a, nomor_b):
        return self.matrix_jarak[nomor_a][nomor_b]

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
