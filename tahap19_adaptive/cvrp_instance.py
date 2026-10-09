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
    """Seluruh data satu instance CVRP."""

    def __init__(self, daftar_node, kapasitas, jumlah_kendaraan):
        self.daftar_node = daftar_node              # berisi objek Node
        self.kapasitas = kapasitas                  # variabel biasa
        self.jumlah_kendaraan = jumlah_kendaraan    # variabel biasa

        # depot adalah node pertama pada instance ini
        self.depot = daftar_node[0]

        # pelanggan = semua node selain depot
        self.pelanggan = [n for n in daftar_node if not n.adalah_depot()]

    # =====================================================================
    # METODE 1 : mengambil node berdasarkan nomornya
    # =====================================================================
    def ambil_node(self, nomor):
        """Mengembalikan objek Node dengan nomor tertentu."""
        for n in self.daftar_node:
            if n.nomor == nomor:
                return n
        raise KeyError(f"Node nomor {nomor} tidak ada.")

    # =====================================================================
    # METODE 2 : jarak antara dua node
    # =====================================================================
    def jarak(self, nomor_a, nomor_b):
        """Jarak antara dua node, ditunjuk dengan nomornya."""
        return self.ambil_node(nomor_a).jarak_ke(self.ambil_node(nomor_b))

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
