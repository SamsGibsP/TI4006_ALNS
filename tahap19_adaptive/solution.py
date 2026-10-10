"""
solution.py — TAHAP 8 (TEROPTIMASI)
===============================================================================
Kelas Solution: satu solusi lengkap CVRP.
Optimasi:
  - hemat_bila_dikeluarkan langsung memanfaatkan cache rute.node_ids (tanpa generate list)
  - keluarkan() menggunakan index lookup langsung pada rute.node_ids
===============================================================================
"""

from route import Route


class Solution:
    """Satu solusi lengkap: kumpulan rute."""

    def __init__(self, instance):
        self.instance = instance
        self.daftar_rute = []

    # =====================================================================
    # MENGELOLA RUTE
    # =====================================================================
    def rute_baru(self):
        """Membuat rute kosong, memasukkannya ke solusi, lalu mengembalikannya."""
        r = Route(self.instance)
        self.daftar_rute.append(r)
        return r

    def buang_rute_kosong(self):
        self.daftar_rute = [r for r in self.daftar_rute if not r.kosong()]

    def rute_terisi(self):
        return [r for r in self.daftar_rute if not r.kosong()]

    def jumlah_rute_terisi(self):
        return len(self.rute_terisi())

    # =====================================================================
    # NILAI YANG DIHITUNG DARI ISI SOLUSI
    # =====================================================================
    @property
    def total_jarak(self):
        return sum(r.total_jarak for r in self.daftar_rute)

    @property
    def jumlah_rute(self):
        return self.jumlah_rute_terisi()

    def hitung_ulang(self):
        for r in self.daftar_rute:
            r.hitung_ulang()

    def nomor_dikunjungi(self):
        """Semua nomor pelanggan yang sudah masuk ke dalam rute."""
        return [node_id for r in self.rute_terisi() for node_id in r.node_ids]

    # =====================================================================
    # MEMERIKSA KELAYAKAN
    # =====================================================================
    def daftar_pelanggaran(self):
        masalah = []

        # 1. Tiap rute terisi tidak boleh melebihi kapasitas
        for i, r in enumerate(self.rute_terisi(), start=1):
            if r.total_muatan > self.instance.kapasitas:
                masalah.append(f"Rute {i} kelebihan muatan: "
                               f"{r.total_muatan} > {self.instance.kapasitas}")

        # 2. Semua pelanggan harus dilayani tepat satu kali
        dikunjungi = self.nomor_dikunjungi()
        seharusnya = [n.nomor for n in self.instance.pelanggan]

        belum = [n for n in seharusnya if n not in dikunjungi]
        if belum:
            masalah.append(f"{len(belum)} pelanggan belum dilayani: {belum}")

        if len(dikunjungi) != len(set(dikunjungi)):
            masalah.append("Ada pelanggan yang dikunjungi lebih dari sekali")

        # 3. Jumlah rute terisi tidak boleh melebihi armada
        rute_terisi = self.jumlah_rute_terisi()
        if rute_terisi > self.instance.jumlah_kendaraan:
            masalah.append(f"Butuh {rute_terisi} rute terisi, "
                           f"armada hanya {self.instance.jumlah_kendaraan}")

        return masalah

    def layak(self):
        # 1. Cek jumlah armada kendaraan (hanya rute yang terisi)
        if len(self.rute_terisi()) > self.instance.jumlah_kendaraan:
            return False

        # 2. Cek kapasitas tiap rute
        for r in self.rute_terisi():
            if r.total_muatan > self.instance.kapasitas:
                return False

        # 3. Cek semua pelanggan terlayani tepat satu kali
        dikunjungi = []
        for r in self.rute_terisi():
            dikunjungi.extend(r.nomor_node())

        if len(dikunjungi) != len(self.instance.pelanggan):
            return False
        if len(set(dikunjungi)) != len(self.instance.pelanggan):
            return False

        return True

    # =====================================================================
    # MEMBUAT SALINAN
    # =====================================================================
    def copy(self):
        baru = Solution(self.instance)
        baru.daftar_rute = [r.copy() for r in self.daftar_rute]
        return baru

    # =====================================================================
    # UNTUK DESTROY DAN REPAIR
    # =====================================================================
    def keluarkan(self, nomor):
        """Mengeluarkan satu pelanggan dari solusi secara cepat."""
        for rute in self.daftar_rute:
            try:
                posisi = rute.node_ids.index(nomor)
                return rute.keluarkan_di(posisi)
            except ValueError:
                continue
        raise KeyError(f"Pelanggan {nomor} tidak ada dalam solusi.")

    def nomor_pelanggan(self):
        """Semua nomor pelanggan yang sedang ada di dalam solusi."""
        return [node_id for r in self.daftar_rute for node_id in r.node_ids]

    def hemat_bila_dikeluarkan(self, node_nomor):
    # Cari rute yang memuat node_nomor
        for rute in self.daftar_rute:
            if node_nomor in rute.node_ids:
            # Dapatkan posisi langsung tanpa scanning index berulang
                pos = rute.node_ids.index(node_nomor)
                depot = self.instance.depot.nomor
                d = self.instance.jarak
            
                sebelum = depot if pos == 0 else rute.node_ids[pos - 1]
                sesudah = depot if pos == len(rute.node_ids) - 1 else rute.node_ids[pos + 1]
            
            # Hemat = jarak lama yang dihapus - jarak baru yang terbentuk
                return d(sebelum, node_nomor) + d(node_nomor, sesudah) - d(sebelum, sesudah)
        return 0.0

    def siapkan_armada(self):
        """Memastikan jumlah rute selalu sama dengan jumlah kendaraan."""
        while len(self.daftar_rute) < self.instance.jumlah_kendaraan:
            self.rute_baru()

    def cetak(self, judul="SOLUSI"):
        print("=" * 72)
        print(f" {judul}")
        print("=" * 72)
        for i, r in enumerate(self.daftar_rute, start=1):
            print(f"  Kendaraan {i} | muatan {r.total_muatan:>3}/"
                  f"{self.instance.kapasitas} | jarak {r.total_jarak:>5}")
            print(f"              | "
                  f"{' - '.join(str(x) for x in r.nomor_node_lengkap())}")
        print("-" * 72)
        print(f"  Jumlah rute : {self.jumlah_rute}/{self.instance.jumlah_kendaraan}")
        print(f"  TOTAL JARAK : {self.total_jarak}")

        masalah = self.daftar_pelanggaran()
        if masalah:
            print("  Status      : TIDAK LAYAK")
            for m in masalah:
                print(f"     - {m}")
        else:
            print("  Status      : LAYAK")
        print("=" * 72)