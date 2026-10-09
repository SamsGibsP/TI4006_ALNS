"""
construction.py  —  TAHAP 9
===============================================================================
Kelas ConstructionHeuristic: menyusun solusi awal secara otomatis.

Sampai sekarang, semua kelas kita MENYIMPAN sesuatu:
    Node     menyimpan koordinat
    Route    menyimpan kunjungan
    Solution menyimpan rute

Kelas ini berbeda. Ia hampir tidak menyimpan apa-apa; ia MENGERJAKAN sesuatu.
Isinya cuma satu atribut (instance) dan beberapa metode.

Kelas semacam ini tetap berguna, karena:
  - semua cara menyusun solusi awal berkumpul di satu tempat
  - menambah metode baru tidak mengganggu yang lama
  - instance cukup diserahkan sekali saat objek dibuat, tidak perlu
    dioper berulang-ulang ke setiap fungsi

Dua metode disediakan:
    sequential()       - masukkan sesuai urutan nomor (paling naif)
    nearest_neighbor() - selalu ambil pelanggan terdekat yang masih muat
===============================================================================
"""

from solution import Solution


class ConstructionHeuristic:
    """Menyusun solusi awal CVRP."""

    def __init__(self, instance):
        self.instance = instance

    # =====================================================================
    # CARA 1 : SEQUENTIAL
    # =====================================================================
    def sequential(self):
        """
        Masukkan pelanggan sesuai urutan nomornya.
        Kalau rute yang sedang dipakai sudah penuh, buka rute baru.

        Aturan sesederhana mungkin. Sengaja dibuat sebagai pembanding,
        supaya terlihat seberapa besar perbaikan dari cara yang lebih pintar.
        """
        solusi = Solution(self.instance)
        rute = solusi.rute_baru()

        for node in self.instance.pelanggan:
            if not rute.masih_muat(node):
                rute = solusi.rute_baru()       # truk penuh, ganti truk
            rute.tambah_node(node)

        solusi.buang_rute_kosong()
        return solusi

    # =====================================================================
    # CARA 2 : NEAREST NEIGHBOR
    # =====================================================================
    def nearest_neighbor(self):
        """
        Dari posisi truk sekarang, cari pelanggan TERDEKAT yang belum
        dilayani dan masih muat. Kalau tidak ada yang muat lagi,
        kembali ke depot dan berangkatkan truk berikutnya.
        """
        solusi = Solution(self.instance)
        belum_dilayani = [n.nomor for n in self.instance.pelanggan]

        rute = solusi.rute_baru()
        posisi = self.instance.depot.nomor          # truk mulai dari depot

        while belum_dilayani:
            # siapa saja yang masih muat di truk ini?
            kandidat = []
            for nomor in belum_dilayani:
                node = self.instance.ambil_node(nomor)
                if rute.masih_muat(node):
                    kandidat.append(nomor)

            # tidak ada yang muat -> pulang ke depot, ganti truk
            if not kandidat:
                rute = solusi.rute_baru()
                posisi = self.instance.depot.nomor
                continue

            # pilih yang paling dekat dari posisi truk sekarang
            terdekat = kandidat[0]
            jarak_terdekat = self.instance.jarak(posisi, terdekat)
            for nomor in kandidat[1:]:
                j = self.instance.jarak(posisi, nomor)
                if j < jarak_terdekat:
                    terdekat = nomor
                    jarak_terdekat = j

            # datangi pelanggan itu
            rute.tambah_node(self.instance.ambil_node(terdekat))
            belum_dilayani.remove(terdekat)
            posisi = terdekat

        solusi.buang_rute_kosong()
        return solusi
