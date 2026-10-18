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

    @property
    def rute(self):
        """Daftar rute aktif / terisi (tidak kosong)."""
        return self.rute_terisi()

    def batas_armada_efektif(self):
        """Mengembalikan batas maksimal armada instance asli jika ada."""
        return self.instance.batas_armada

    # =====================================================================
    # MEMERIKSA KELAYAKAN
    # =====================================================================
    def daftar_pelanggaran(self):
        masalah = []
        rute_aktif = [r for r in self.daftar_rute if len(r.daftar_visit) > 0]

        # 1. Tiap rute terisi tidak boleh melebihi kapasitas
        cap = self.instance.kapasitas
        for i, r in enumerate(rute_aktif, start=1):
            if r.total_muatan > cap:
                masalah.append(f"Rute {i} kelebihan muatan: {r.total_muatan} > {cap}")

        # 2. Semua pelanggan harus dilayani tepat satu kali dan tidak ada ID asing
        pelanggan_seharusnya = {p.nomor for p in self.instance.pelanggan}
        dikunjungi = [node_id for r in rute_aktif for node_id in r.nomor_node()]
        set_dikunjungi = set(dikunjungi)

        belum = [n for n in pelanggan_seharusnya if n not in set_dikunjungi]
        if belum:
            masalah.append(f"{len(belum)} pelanggan belum dilayani: {belum}")

        if len(dikunjungi) != len(set_dikunjungi):
            masalah.append("Ada pelanggan yang dikunjungi lebih dari sekali")

        asing = [n for n in set_dikunjungi if n not in pelanggan_seharusnya]
        if asing:
            masalah.append(f"Ada ID node asing yang bukan pelanggan: {asing}")

        return masalah

    def layak(self):
        rute_aktif = [r for r in self.daftar_rute if len(r.daftar_visit) > 0]
        pelanggan_seharusnya = {p.nomor for p in self.instance.pelanggan}

        # 1. Cek kapasitas tiap rute aktif
        cap = self.instance.kapasitas
        if any(r.total_muatan > cap for r in rute_aktif):
            return False

        # 2. Cek pemenuhan tepat satu kali untuk seluruh pelanggan yang seharusnya
        dikunjungi = [node_id for r in rute_aktif for node_id in r.nomor_node()]

        return (
            len(dikunjungi) == len(pelanggan_seharusnya)
            and len(dikunjungi) == len(set(dikunjungi))
            and set(dikunjungi) == pelanggan_seharusnya
        )


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
                pos = rute.node_ids.index(node_nomor)
                depot = self.instance.depot.nomor
                d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
            
                sebelum = depot if pos == 0 else rute.node_ids[pos - 1]
                sesudah = depot if pos == len(rute.node_ids) - 1 else rute.node_ids[pos + 1]
            
                # Hemat = jarak lama yang dihapus - jarak baru yang terbentuk O(1)
                return d[sebelum][node_nomor] + d[node_nomor][sesudah] - d[sebelum][sesudah]
        return 0.0

    def siapkan_armada(self):
        """Memastikan jumlah rute minimal mencukupi jumlah kendaraan instance."""
        target_k = self.instance.jumlah_kendaraan
        while len(self.daftar_rute) < target_k:
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
        print(f"  Jumlah rute : {self.jumlah_rute} (k min: {self.instance.jumlah_kendaraan})")
        print(f"  TOTAL JARAK : {self.total_jarak}")

        masalah = self.daftar_pelanggaran()
        if masalah:
            print("  Status      : TIDAK LAYAK")
            for m in masalah:
                print(f"     - {m}")
        else:
            print("  Status      : LAYAK")
        print("=" * 72)

    def simpan_cvrplib_sol(self, path_file, sesuaikan_indeks_cvrplib=True):
        """
        Menyimpan solusi ke format standar CVRPLIB .sol:
        Route #1: 31 46 35
        Route #2: ...
        Cost <total_jarak>

        Pada instance Set X CVRPLIB, penomoran pelanggan di file .sol menggunakan
        indeks 1..n-1 (yaitu nomor_node - 1 jika depot bernomor 1).
        """
        import os
        dir_tujuan = os.path.dirname(os.path.abspath(path_file))
        if dir_tujuan:
            os.makedirs(dir_tujuan, exist_ok=True)

        depot_id = self.instance.depot.nomor
        with open(path_file, "w", encoding="utf-8") as f:
            idx = 1
            for r in self.rute:
                if r.kosong():
                    continue
                if sesuaikan_indeks_cvrplib and depot_id == 1:
                    nodes_str = " ".join(str(nid - 1) for nid in r.node_ids)
                else:
                    nodes_str = " ".join(str(nid) for nid in r.node_ids)
                f.write(f"Route #{idx}: {nodes_str}\n")
                idx += 1
            f.write(f"Cost {self.total_jarak}\n")