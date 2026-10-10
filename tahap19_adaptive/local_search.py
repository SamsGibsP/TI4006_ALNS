"""
local_search.py  —  TAHAP 11
===============================================================================
Kelas LocalSearch: MEMPERBAIKI solusi yang sudah ada.

Heuristik konstruktif menyusun solusi sekali jalan lalu selesai.
Local search bekerja sebaliknya: ia mengambil solusi yang sudah ada,
lalu memperbaikinya sedikit demi sedikit.

Cara kerjanya:
    1. Coba semua perubahan kecil yang mungkin dilakukan
    2. Ambil yang paling banyak menurunkan total jarak
    3. Ulangi
    4. Berhenti kalau tidak ada lagi perubahan yang memperbaiki

Sekarang ada DUA jenis perubahan:
    RELOCATE : memindahkan satu pelanggan ke tempat lain
    SWAP     : menukar tempat dua pelanggan

Relocate dicoba lebih dulu. Swap baru dipakai kalau relocate sudah buntu.
===============================================================================
"""


class LocalSearch:
    """Memperbaiki solusi dengan perubahan-perubahan kecil."""

    def __init__(self, instance, operator=None, maks_iterasi=100, verbose=True):
        self.instance = instance
        self.operator = operator if operator else ["relocate", "swap"]
        self.maks_iterasi = maks_iterasi
        self.verbose = verbose
        self.jumlah_iterasi = 0
        self.riwayat = []          # catatan jarak tiap iterasi

    # =====================================================================
    # PENGENDALI UTAMA
    # =====================================================================
    def jalankan(self, solusi_awal):
        """
        Menjalankan perbaikan sampai tidak ada lagi yang bisa diperbaiki.
        Solusi awal tidak diubah; yang dikembalikan adalah salinannya
        yang sudah diperbaiki.
        """
        solusi = solusi_awal.copy()          # <-- inilah gunanya Tahap 10
        self.riwayat = [solusi.total_jarak]
        if self.verbose:
            print(f"  Iterasi  0 | jarak {solusi.total_jarak:>5} | solusi awal")

        for iterasi in range(1, self.maks_iterasi + 1):
            jarak_sebelum = solusi.total_jarak

            # coba tiap operator berurutan, berhenti pada yang berhasil
            ada_perbaikan = False
            for nama in self.operator:
                if nama == "relocate":
                    ada_perbaikan = self.relocate_terbaik(solusi)
                elif nama == "swap":
                    ada_perbaikan = self.swap_terbaik(solusi)
                if ada_perbaikan:
                    break

            if not ada_perbaikan:
                if self.verbose:
                    print(f"  Iterasi {iterasi:>2} | tidak ada perbaikan lagi "
                          f"-> OPTIMUM LOKAL")
                self.jumlah_iterasi = iterasi - 1
                break

            turun = jarak_sebelum - solusi.total_jarak
            self.riwayat.append(solusi.total_jarak)
            if self.verbose:
                print(f"  Iterasi {iterasi:>2} | jarak {solusi.total_jarak:>5} "
                      f"| turun {turun:>4} | {nama}")

        solusi.buang_rute_kosong()
        return solusi

    # =====================================================================
    # OPERATOR RELOCATE
    # =====================================================================
    def relocate_terbaik(self, solusi):
        """
        Mencoba memindahkan SATU pelanggan ke semua tempat yang mungkin,
        lalu menerapkan perpindahan yang paling menguntungkan.

        Mengembalikan True bila ada perbaikan yang diterapkan.
        """
        jarak_terbaik = solusi.total_jarak
        langkah_terbaik = None

        # dari rute mana, kunjungan ke berapa
        for i_asal in range(len(solusi.daftar_rute)):
            rute_asal = solusi.daftar_rute[i_asal]

            for pos_asal in range(len(rute_asal.daftar_visit)):
                node = rute_asal.daftar_visit[pos_asal].node

                # ke rute mana, disisipkan di posisi berapa
                for i_tujuan in range(len(solusi.daftar_rute)):
                    rute_tujuan = solusi.daftar_rute[i_tujuan]

                    # kalau pindah rute, pastikan muat
                    if i_asal != i_tujuan and not rute_tujuan.masih_muat(node):
                        continue

                    batas = len(rute_tujuan.daftar_visit)
                    if i_asal != i_tujuan:
                        batas = batas + 1

                    for pos_tujuan in range(batas):
                        # pindah ke tempatnya sendiri, tidak ada gunanya
                        if i_asal == i_tujuan and pos_tujuan == pos_asal:
                            continue

                        jarak = self.coba_relocate(
                            solusi, i_asal, pos_asal, i_tujuan, pos_tujuan)

                        if jarak < jarak_terbaik:
                            jarak_terbaik = jarak
                            langkah_terbaik = (i_asal, pos_asal,
                                               i_tujuan, pos_tujuan)

        # tidak ada satu pun perpindahan yang memperbaiki
        if langkah_terbaik is None:
            return False

        # terapkan langkah terbaik pada solusi yang sebenarnya
        i_asal, pos_asal, i_tujuan, pos_tujuan = langkah_terbaik
        self.lakukan_relocate(solusi, i_asal, pos_asal, i_tujuan, pos_tujuan)
        return True

    # =====================================================================
    # MENCOBA TANPA MERUSAK
    # =====================================================================
    def coba_relocate(self, solusi, i_asal, pos_asal, i_tujuan, pos_tujuan):
        """
        Menghitung total jarak SEANDAINYA perpindahan dilakukan,
        tanpa mengubah solusi aslinya.

        Caranya paling lugas: kerjakan pada SALINAN.
        Inilah alasan kita membuat metode copy() di Tahap 10.
        """
        uji = solusi.copy()
        self.lakukan_relocate(uji, i_asal, pos_asal, i_tujuan, pos_tujuan)
        return uji.total_jarak

    @staticmethod
    def lakukan_relocate(solusi, i_asal, pos_asal, i_tujuan, pos_tujuan):
        """Benar-benar memindahkan satu kunjungan."""
        rute_asal = solusi.daftar_rute[i_asal]
        rute_tujuan = solusi.daftar_rute[i_tujuan]

        visit = rute_asal.daftar_visit.pop(pos_asal)      # ambil
        rute_tujuan.daftar_visit.insert(pos_tujuan, visit)  # taruh

        rute_asal.hitung_ulang()
        rute_tujuan.hitung_ulang()

    # =====================================================================
    # OPERATOR SWAP  (baru di Tahap 12)
    # =====================================================================
    def swap_terbaik(self, solusi):
        """
        Mencoba menukar tempat DUA pelanggan, lalu menerapkan pertukaran
        yang paling menguntungkan.

        Perbedaan dengan relocate: di sini dua pelanggan sama-sama pindah,
        saling bertukar tempat.
        """
        jarak_terbaik = solusi.total_jarak
        langkah_terbaik = None

        for i_a in range(len(solusi.daftar_rute)):
            rute_a = solusi.daftar_rute[i_a]

            for pos_a in range(len(rute_a.daftar_visit)):
                for i_b in range(len(solusi.daftar_rute)):
                    rute_b = solusi.daftar_rute[i_b]

                    for pos_b in range(len(rute_b.daftar_visit)):
                        # hindari pasangan yang sama dan pengulangan
                        if (i_b, pos_b) <= (i_a, pos_a):
                            continue

                        if not self.swap_muat(solusi, i_a, pos_a, i_b, pos_b):
                            continue

                        jarak = self.coba_swap(solusi, i_a, pos_a, i_b, pos_b)
                        if jarak < jarak_terbaik:
                            jarak_terbaik = jarak
                            langkah_terbaik = (i_a, pos_a, i_b, pos_b)

        if langkah_terbaik is None:
            return False

        i_a, pos_a, i_b, pos_b = langkah_terbaik
        self.lakukan_swap(solusi, i_a, pos_a, i_b, pos_b)
        return True

    def swap_muat(self, solusi, i_a, pos_a, i_b, pos_b):
        """Memeriksa apakah pertukaran ini melanggar kapasitas."""
        if i_a == i_b:
            return True            # satu rute: muatannya tidak berubah

        rute_a = solusi.daftar_rute[i_a]
        rute_b = solusi.daftar_rute[i_b]
        d_a = rute_a.daftar_visit[pos_a].demand
        d_b = rute_b.daftar_visit[pos_b].demand
        kapasitas = self.instance.kapasitas

        muat_a = rute_a.total_muatan - d_a + d_b <= kapasitas
        muat_b = rute_b.total_muatan - d_b + d_a <= kapasitas
        return muat_a and muat_b

    def coba_swap(self, solusi, i_a, pos_a, i_b, pos_b):
        """Total jarak seandainya pertukaran dilakukan. Dikerjakan pada salinan."""
        uji = solusi.copy()
        self.lakukan_swap(uji, i_a, pos_a, i_b, pos_b)
        return uji.total_jarak

    @staticmethod
    def lakukan_swap(solusi, i_a, pos_a, i_b, pos_b):
        """Benar-benar menukar dua kunjungan."""
        rute_a = solusi.daftar_rute[i_a]
        rute_b = solusi.daftar_rute[i_b]

        rute_a.daftar_visit[pos_a], rute_b.daftar_visit[pos_b] = \
            rute_b.daftar_visit[pos_b], rute_a.daftar_visit[pos_a]

        rute_a.hitung_ulang()
        if i_a != i_b:
            rute_b.hitung_ulang()
