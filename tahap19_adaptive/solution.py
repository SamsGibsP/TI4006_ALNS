"""
solution.py  —  TAHAP 8
===============================================================================
Kelas Solution: satu solusi lengkap CVRP.

Susunannya bersarang tiga lapis:

    Solution  berisi beberapa  Route
    Route     berisi beberapa  Visit
    Visit     merujuk ke satu  Node

Solution inilah yang nanti dihasilkan oleh heuristik konstruktif,
diperbaiki oleh local search, dan dibandingkan dengan nilai optimal.
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

    # =====================================================================
    # NILAI YANG DIHITUNG DARI ISI SOLUSI
    # =====================================================================
    @property
    def total_jarak(self):
        """
        FUNGSI TUJUAN: total jarak seluruh rute. Inilah yang diminimalkan.

        @property membuat kita menulis  solusi.total_jarak  tanpa kurung,
        seolah-olah sebuah atribut biasa, padahal nilainya dihitung
        saat itu juga.
        """
        return sum(r.total_jarak for r in self.daftar_rute)

    @property
    def jumlah_rute(self):
        return len([r for r in self.daftar_rute if not r.kosong()])

    def nomor_dikunjungi(self):
        """Semua nomor pelanggan yang sudah masuk ke dalam rute."""
        return [v.nomor for r in self.daftar_rute for v in r.daftar_visit]

    # =====================================================================
    # MEMERIKSA KELAYAKAN
    # =====================================================================
    def daftar_pelanggaran(self):
        """
        Mengembalikan DAFTAR pelanggaran. Daftar kosong berarti solusi layak.

        Sengaja berupa daftar, bukan True/False. Saat solusi ditolak, yang
        ingin kita tahu bukan sekadar "layak atau tidak", melainkan
        aturan MANA yang dilanggar.
        """
        masalah = []

        # 1. tiap rute tidak boleh melebihi kapasitas
        for i, r in enumerate(self.daftar_rute, start=1):
            if r.total_muatan > self.instance.kapasitas:
                masalah.append(f"Rute {i} kelebihan muatan: "
                               f"{r.total_muatan} > {self.instance.kapasitas}")

        # 2. semua pelanggan harus dilayani, tepat satu kali
        dikunjungi = self.nomor_dikunjungi()
        seharusnya = [n.nomor for n in self.instance.pelanggan]

        belum = [n for n in seharusnya if n not in dikunjungi]
        if belum:
            masalah.append(f"{len(belum)} pelanggan belum dilayani: {belum}")

        if len(dikunjungi) != len(set(dikunjungi)):
            masalah.append("Ada pelanggan yang dikunjungi lebih dari sekali")

        # 3. jumlah rute tidak boleh melebihi armada
        if self.jumlah_rute > self.instance.jumlah_kendaraan:
            masalah.append(f"Butuh {self.jumlah_rute} rute, "
                           f"armada hanya {self.instance.jumlah_kendaraan}")

        return masalah

    def layak(self):
        return len(self.daftar_pelanggaran()) == 0

    # =====================================================================
    # MEMBUAT SALINAN (lihat Tahap 10)
    # =====================================================================
    def copy(self):
        """
        Salinan solusi yang sepenuhnya terpisah dari aslinya.
        Perhatikan rantainya: Solution.copy memanggil Route.copy,
        Route.copy memanggil Visit.copy.
        """
        baru = Solution(self.instance)
        baru.daftar_rute = [r.copy() for r in self.daftar_rute]
        return baru

    # =====================================================================
    # MENCETAK
    # =====================================================================
    # =====================================================================
    # BAGIAN BARU (TAHAP 13) : UNTUK DESTROY DAN REPAIR
    # =====================================================================
    def keluarkan(self, nomor):
        """
        Mengeluarkan satu pelanggan dari solusi, mengembalikan objek Node-nya.
        Dipakai oleh DESTROY operator.
        """
        for rute in self.daftar_rute:
            for i, v in enumerate(rute.daftar_visit):
                if v.nomor == nomor:
                    return rute.keluarkan_di(i)
        raise KeyError(f"Pelanggan {nomor} tidak ada dalam solusi.")

    def nomor_pelanggan(self):
        """Semua nomor pelanggan yang sedang ada di dalam solusi."""
        return [v.nomor for r in self.daftar_rute for v in r.daftar_visit]

    def hemat_bila_dikeluarkan(self, nomor):
        """
        Berapa jarak yang DIHEMAT bila pelanggan ini dikeluarkan?

            hemat = d(sebelum, ini) + d(ini, sesudah) - d(sebelum, sesudah)

        Dipakai oleh WORST REMOVAL untuk mencari pelanggan paling "mahal".
        """
        depot = self.instance.depot.nomor
        for rute in self.daftar_rute:
            urutan = rute.nomor_node()
            if nomor in urutan:
                i = urutan.index(nomor)
                sebelum = depot if i == 0 else urutan[i - 1]
                sesudah = depot if i == len(urutan) - 1 else urutan[i + 1]
                return (self.instance.jarak(sebelum, nomor)
                        + self.instance.jarak(nomor, sesudah)
                        - self.instance.jarak(sebelum, sesudah))
        raise KeyError(f"Pelanggan {nomor} tidak ada dalam solusi.")

    def siapkan_armada(self):
        """
        Memastikan jumlah rute selalu sama dengan jumlah kendaraan.

        Selama ALNS berjalan, rute kosong TIDAK dibuang. Repair operator
        membutuhkannya sebagai "truk cadangan" yang masih kosong.
        """
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
