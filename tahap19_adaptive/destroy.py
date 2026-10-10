"""
destroy.py  —  TAHAP 14
===============================================================================
DESTROY OPERATOR: merusak solusi dengan mengeluarkan beberapa pelanggan.

Berapa banyak yang dikeluarkan? Pada M6 dilambangkan dengan rho:

        lowerbound <= rho <= upperbound

rho terlalu kecil  -> perubahannya sedikit, mirip local search biasa
rho terlalu besar  -> solusinya hancur, repair harus membangun dari nol

Dua operator disediakan di sini. Nanti Anda bisa menambah sendiri
(Shaw removal, route removal, dan seterusnya).

    1. RANDOM REMOVAL  — pilih acak. Tugasnya DIVERSIFIKASI
    2. WORST REMOVAL   — pilih yang paling mahal. Tugasnya INTENSIFIKASI
===============================================================================
"""

import random


class DestroyOperator:
    """Kumpulan cara merusak solusi."""

    def __init__(self, instance):
        self.instance = instance

    # =====================================================================
    # OPERATOR 1 : RANDOM REMOVAL
    # =====================================================================
    def random_removal(self, solusi, rho):
        """
        Keluarkan rho pelanggan yang dipilih secara ACAK.

        Kelihatan bodoh, tapi justru inilah kekuatannya: ia tidak punya
        prasangka. Operator pintar cenderung mengeluarkan pelanggan yang
        itu-itu saja, sehingga pencarian berputar di tempat.
        """
        kandidat = solusi.nomor_pelanggan()
        rho = min(rho, len(kandidat))

        terpilih = random.sample(kandidat, rho)

        bank = []
        for nomor in terpilih:
            bank.append(solusi.keluarkan(nomor))
        return bank

    # =====================================================================
    # OPERATOR 2 : WORST REMOVAL
    # =====================================================================
    def worst_removal(self, solusi, rho):
        """
        Keluarkan rho pelanggan yang paling MAHAL.

        "Mahal" artinya: kalau pelanggan ini dikeluarkan, jarak rute
        berkurang paling banyak. Dengan kata lain, dialah yang membuat
        rutenya memutar jauh.

        Logikanya: pelanggan itu kemungkinan salah tempat. Siapa tahu
        ada rute lain yang lebih cocok untuknya.
        """
        kandidat = solusi.nomor_pelanggan()
        rho = min(rho, len(kandidat))

        bank = []
        for _ in range(rho):
            # hitung ulang setiap kali, karena setelah satu pelanggan
            # keluar, tetangga-tetangganya ikut berubah
            tersisa = solusi.nomor_pelanggan()
            if not tersisa:
                break

            terburuk = tersisa[0]
            hemat_terbesar = solusi.hemat_bila_dikeluarkan(terburuk)
            for nomor in tersisa[1:]:
                hemat = solusi.hemat_bila_dikeluarkan(nomor)
                if hemat > hemat_terbesar:
                    terburuk = nomor
                    hemat_terbesar = hemat

            bank.append(solusi.keluarkan(terburuk))
        return bank

    # =====================================================================
    # PEMILIH OPERATOR
    # =====================================================================
    def jalankan(self, nama, solusi, rho):
        """Menjalankan destroy operator sesuai namanya."""
        if nama == "random_removal":
            return self.random_removal(solusi, rho)
        if nama == "worst_removal":
            return self.worst_removal(solusi, rho)
        raise ValueError(f"Destroy operator tidak dikenal: {nama}")

    # daftar nama operator yang tersedia
    DAFTAR = ["random_removal", "worst_removal"]
