"""
repair.py  —  TAHAP 15
===============================================================================
REPAIR OPERATOR: memasukkan kembali pelanggan yang ada di bank.

Dua operator disediakan di sini. Nanti Anda bisa menambah sendiri.

    1. GREEDY INSERTION   — selalu ambil penyisipan termurah saat itu juga.
                            RAKUS: hanya melihat satu langkah ke depan.

    2. REGRET-2 INSERTION — dahulukan pelanggan yang paling "menyesal"
                            kalau tidak ditangani sekarang.
                            BERPANDANGAN KE DEPAN.

Istilah REGRET (penyesalan):
    Untuk tiap pelanggan, bandingkan biaya penyisipan di rute TERBAIK
    dengan biaya di rute TERBAIK KEDUA.

        regret = biaya_terbaik_kedua - biaya_terbaik

    Regret besar berarti: kalau rute terbaiknya keburu penuh diisi orang
    lain, pelanggan ini akan menanggung biaya jauh lebih mahal.
    Jadi dia harus didahulukan.
===============================================================================
"""

from visit import Visit


class RepairOperator:
    """Kumpulan cara memperbaiki solusi yang rusak."""

    def __init__(self, instance):
        self.instance = instance

    # =====================================================================
    # ALAT BANTU : menilai semua kemungkinan penyisipan satu pelanggan
    # =====================================================================
    def pilihan_penyisipan(self, solusi, node):
        """
        Mengembalikan daftar (biaya, indeks_rute, posisi) untuk setiap rute
        yang masih muat, diurutkan dari yang termurah.
        """
        pilihan = []
        for i, rute in enumerate(solusi.daftar_rute):
            posisi, biaya = rute.sisip_terbaik(node)
            if posisi is not None:
                pilihan.append((biaya, i, posisi))
        pilihan.sort()
        return pilihan

    @staticmethod
    def sisipkan(solusi, node, indeks_rute, posisi):
        """Benar-benar memasukkan node ke dalam solusi."""
        rute = solusi.daftar_rute[indeks_rute]
        rute.daftar_visit.insert(posisi, Visit(node))
        rute.hitung_ulang()

    # =====================================================================
    # OPERATOR 1 : GREEDY INSERTION
    # =====================================================================
    def greedy_insertion(self, solusi, bank):
        """
        Berulang kali: dari SEMUA pelanggan di bank dan SEMUA posisi yang
        mungkin, ambil pasangan yang biayanya paling murah. Lakukan.
        Ulangi sampai bank kosong.

        Mengembalikan True bila semua pelanggan berhasil dimasukkan.
        """
        sisa = list(bank)

        while sisa:
            terbaik = None          # (biaya, node, indeks_rute, posisi)

            for node in sisa:
                pilihan = self.pilihan_penyisipan(solusi, node)
                if not pilihan:
                    continue
                biaya, i_rute, posisi = pilihan[0]
                if terbaik is None or biaya < terbaik[0]:
                    terbaik = (biaya, node, i_rute, posisi)

            if terbaik is None:
                return False        # ada pelanggan yang tidak muat di mana pun

            _, node, i_rute, posisi = terbaik
            self.sisipkan(solusi, node, i_rute, posisi)
            sisa.remove(node)

        return True

    # =====================================================================
    # OPERATOR 2 : REGRET-2 INSERTION
    # =====================================================================
    def regret2_insertion(self, solusi, bank):
        """
        Berulang kali: hitung regret setiap pelanggan di bank, lalu tangani
        yang regret-nya PALING BESAR. Masukkan dia ke posisi terbaiknya.

        Pelanggan yang hanya punya satu pilihan rute diberi regret tak
        hingga, karena dialah yang paling terancam.
        """
        sisa = list(bank)

        while sisa:
            terpilih = None         # (regret, biaya, node, indeks_rute, posisi)

            for node in sisa:
                pilihan = self.pilihan_penyisipan(solusi, node)
                if not pilihan:
                    continue

                biaya_1, i_rute, posisi = pilihan[0]
                if len(pilihan) >= 2:
                    biaya_2 = pilihan[1][0]
                    regret = biaya_2 - biaya_1
                else:
                    regret = float("inf")   # cuma satu pilihan: genting!

                if terpilih is None or regret > terpilih[0]:
                    terpilih = (regret, biaya_1, node, i_rute, posisi)

            if terpilih is None:
                return False

            _, _, node, i_rute, posisi = terpilih
            self.sisipkan(solusi, node, i_rute, posisi)
            sisa.remove(node)

        return True

    # =====================================================================
    # PEMILIH OPERATOR
    # =====================================================================
    def jalankan(self, nama, solusi, bank):
        """Menjalankan repair operator sesuai namanya."""
        if nama == "greedy_insertion":
            return self.greedy_insertion(solusi, bank)
        if nama == "regret2_insertion":
            return self.regret2_insertion(solusi, bank)
        raise ValueError(f"Repair operator tidak dikenal: {nama}")

    DAFTAR = ["greedy_insertion", "regret2_insertion"]
