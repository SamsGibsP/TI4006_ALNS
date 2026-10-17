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
        # jumlah_kendaraan adalah k nominal / armada minimal
        self.jumlah_kendaraan = jumlah_kendaraan
        self.k_min = jumlah_kendaraan
        # batas_armada adalah batas atas kaku jika ada; default None (k adalah minimum)
        self.batas_armada = batas_armada

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

    def cari_armada_minimal_layak(self, verbose=True):
        """
        Menguji kelayakan armada mulai dari k nominal/file (misal k=25),
        lalu k=26, dan seterusnya hingga ditemukan jumlah kendaraan terkecil
        yang secara kapasitas (bin-packing) mampu melayani seluruh pelanggan.
        """
        k_nominal = self.jumlah_kendaraan if self.jumlah_kendaraan > 0 else self.kendaraan_minimal()
        k_awal = min(k_nominal, self.kendaraan_minimal())
        cap = self.kapasitas
        tot_d = self.total_demand()
        pel_desc = sorted(self.pelanggan, key=lambda n: n.demand, reverse=True)

        if verbose:
            print("=" * 72)
            print(" PENGUJIAN KELAYAKAN MINIMUM ARMADA KENDARAAN (K)")
            print("=" * 72)
            print(f"  Total Permintaan Pelanggan : {tot_d}")
            print(f"  Kapasitas per Kendaraan     : {cap}")
            print(f"  Batas Bawah Teoritis (BPP) : ceil({tot_d} / {cap}) = {self.kendaraan_minimal()} kendaraan")
            print(f"  Uji coba bertahap mulai dari K = {k_awal} kendaraan...")

        k_test = k_awal
        while k_test <= len(self.pelanggan):
            bins = [0] * k_test
            ok = True
            for p in pel_desc:
                best_b = None
                min_sisa = cap + 1
                for b in range(k_test):
                    sisa = cap - (bins[b] + p.demand)
                    if 0 <= sisa < min_sisa:
                        min_sisa = sisa
                        best_b = b
                if best_b is not None:
                    bins[best_b] += p.demand
                else:
                    ok = False
                    break

            if ok:
                if verbose:
                    sisa_total = k_test * cap - tot_d
                    print(f"  -> Uji K = {k_test} kendaraan : LAYAK")
                    print(f"     (Demand 100% termuat, sisa kapasitas total = {sisa_total} unit)")
                    print(f"  => Batas armada ditetapkan : K = {k_test} kendaraan (Maksimum sesuai batas optimal)")
                    print("=" * 72)
                self.batas_armada = k_test
                return k_test
            else:
                if verbose:
                    slack = k_test * cap - tot_d
                    print(f"  -> Uji K = {k_test} kendaraan : TIDAK LAYAK")
                    print(f"     (Total kapasitas {k_test}x{cap}={k_test*cap}, selisih hanya {slack} unit, fragmentasi demand tidak muat)")
                k_test += 1

        self.batas_armada = len(self.pelanggan)
        return self.batas_armada

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
