"""
route.py  —  TAHAP 7
===============================================================================
Kelas Route: satu rute yang dilayani satu kendaraan.
Isinya kumpulan objek Visit, berurutan.

Di Tahap 6 kita menghitung muatan truk secara manual di dalam perulangan.
Itu berbahaya: kalau urutan kunjungan berubah, kita harus ingat menghitung
ulang. Dan manusia pasti lupa.

Solusinya: serahkan perhitungan itu kepada objek Route. Setiap kali isinya
berubah, Route menghitung ulang semuanya sendiri lewat metode hitung_ulang().

DUA ATURAN PENTING:
  1. Depot TIDAK disimpan sebagai Visit.
     Rute selalu dibaca sebagai:  depot -> visit[0] -> ... -> depot
  2. Setiap metode yang mengubah isi rute WAJIB memanggil hitung_ulang()
===============================================================================
"""

from visit import Visit


class Route:
    """Satu rute kendaraan."""

    def __init__(self, instance):
        self.instance = instance     # rujukan ke data masalah
        self.daftar_visit = []       # kumpulan objek Visit
        self.total_muatan = 0
        self.total_jarak = 0

    # =====================================================================
    # MENGUBAH ISI RUTE
    # =====================================================================
    def tambah_node(self, node):
        """Menambahkan satu node di akhir rute."""
        self.daftar_visit.append(Visit(node))
        self.hitung_ulang()          # <-- jangan sampai lupa

    # =====================================================================
    # MENGHITUNG ULANG SELURUH ANGKA
    # =====================================================================
    def hitung_ulang(self):
        """
        Menghitung ulang urutan, muatan truk, total muatan, dan total jarak.
        Dipanggil setiap kali isi rute berubah.
        """
        # --- urutan dan muatan truk tiap kunjungan -----------------------
        muatan = 0
        for i, v in enumerate(self.daftar_visit):
            v.urutan = i
            muatan = muatan + v.demand
            v.muatan_sesudah = muatan
        self.total_muatan = muatan

        # --- total jarak: depot -> ... -> depot ---------------------------
        if len(self.daftar_visit) == 0:
            self.total_jarak = 0
            return

        depot = self.instance.depot.nomor
        nomor = self.nomor_node()

        jarak = self.instance.jarak(depot, nomor[0])        # depot ke node pertama
        for i in range(len(nomor) - 1):
            jarak = jarak + self.instance.jarak(nomor[i], nomor[i + 1])
        jarak = jarak + self.instance.jarak(nomor[-1], depot)  # node terakhir ke depot

        self.total_jarak = jarak

    # =====================================================================
    # INFORMASI RUTE
    # =====================================================================
    def nomor_node(self):
        """Urutan nomor node, tanpa depot."""
        return [v.nomor for v in self.daftar_visit]

    def nomor_node_lengkap(self):
        """Urutan nomor node, dengan depot di awal dan akhir."""
        depot = self.instance.depot.nomor
        return [depot] + self.nomor_node() + [depot]

    def sisa_kapasitas(self):
        """Sisa ruang di truk."""
        return self.instance.kapasitas - self.total_muatan

    def masih_muat(self, node):
        """Apakah node ini masih muat di rute ini?"""
        return node.demand <= self.sisa_kapasitas()

    def kosong(self):
        return len(self.daftar_visit) == 0

    # =====================================================================
    # MEMBUAT SALINAN (lihat Tahap 10)
    # =====================================================================
    def copy(self):
        """Salinan rute yang sepenuhnya terpisah dari aslinya."""
        baru = Route(self.instance)
        baru.daftar_visit = [v.copy() for v in self.daftar_visit]
        baru.hitung_ulang()
        return baru

    # =====================================================================
    # =====================================================================
    # BAGIAN BARU (TAHAP 13) : MENILAI PENYISIPAN
    # =====================================================================
    def keluarkan_di(self, posisi):
        """
        Menghapus kunjungan pada posisi tertentu, mengembalikan objek Node-nya.
        Dipakai oleh destroy operator lewat Solution.keluarkan().
        """
        v = self.daftar_visit.pop(posisi)
        self.hitung_ulang()
        return v.node

    def biaya_sisip(self, node, posisi):
        """
        Berapa TAMBAHAN jarak bila node disisipkan pada posisi tertentu?

            delta = d(sebelum, baru) + d(baru, sesudah) - d(sebelum, sesudah)

        Hanya melihat TIGA node, tidak peduli rutenya sepanjang apa.
        Repair operator nanti memanggil metode ini ribuan kali, jadi ia
        harus murah. Inilah yang disebut EVALUASI DELTA.
        """
        depot = self.instance.depot.nomor
        nomor = self.nomor_node()

        sebelum = depot if posisi == 0 else nomor[posisi - 1]
        sesudah = depot if posisi >= len(nomor) else nomor[posisi]

        return (self.instance.jarak(sebelum, node.nomor)
                + self.instance.jarak(node.nomor, sesudah)
                - self.instance.jarak(sebelum, sesudah))

    def sisip_terbaik(self, node):
        """
        Mencari posisi penyisipan TERMURAH di rute ini.
        Mengembalikan (posisi, biaya).
        Bila node tidak muat di rute ini, mengembalikan (None, tak hingga).
        """
        if not self.masih_muat(node):
            return None, float("inf")

        posisi_terbaik = 0
        biaya_terbaik = float("inf")
        for posisi in range(len(self.daftar_visit) + 1):
            biaya = self.biaya_sisip(node, posisi)
            if biaya < biaya_terbaik:
                posisi_terbaik = posisi
                biaya_terbaik = biaya
        return posisi_terbaik, biaya_terbaik

    def __repr__(self):
        jalur = " - ".join(str(i) for i in self.nomor_node_lengkap())
        return (f"Route(muatan={self.total_muatan}/{self.instance.kapasitas}, "
                f"jarak={self.total_jarak}) : {jalur}")
