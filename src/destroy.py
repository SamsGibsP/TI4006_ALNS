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

import heapq
import random


class DestroyOperator:
    """Kumpulan cara merusak solusi."""

    _matriks_jarak: list[list[float]]
    _demand_node: list[int]
    max_d: float
    kapasitas: float

    def __init__(self, instance):
        self.instance = instance

        matriks = getattr(
            self.instance, "_matriks_jarak", getattr(self.instance, "matrix_jarak", None)
        )
        if matriks is None:
            max_id = max(n.nomor for n in self.instance.daftar_node)
            matriks = [[0.0] * (max_id + 1) for _ in range(max_id + 1)]
            for a in self.instance.daftar_node:
                for b in self.instance.daftar_node:
                    matriks[a.nomor][b.nomor] = float(a.jarak_ke(b))
        self._matriks_jarak = matriks

        demand_node = getattr(self.instance, "_demand_node", None)
        if demand_node is None:
            max_id = max(n.nomor for n in self.instance.daftar_node)
            demand_node = [0] * (max_id + 1)
            for n in self.instance.daftar_node:
                demand_node[n.nomor] = int(n.demand)
        self._demand_node = demand_node

        max_d_val = getattr(self.instance, "_max_d", None)
        if max_d_val is None:
            max_d_val = max(max(baris) for baris in self._matriks_jarak)
        if max_d_val <= 0:
            max_d_val = 1.0
        self.max_d = float(max_d_val)

        self.kapasitas = float(getattr(self.instance, "kapasitas", 1.0))
        if self.kapasitas <= 0:
            self.kapasitas = 1.0

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
        Keluarkan rho pelanggan yang paling MAHAL (Single-pass O(N) per iterasi).
        Menggunakan direct matrix lookup O(1) tanpa overhead fungsi.
        """
        kandidat_len = len(solusi.nomor_pelanggan())
        rho = min(rho, kandidat_len)
        if rho <= 0:
            return []

        bank = []
        d = self._matriks_jarak
        depot = self.instance.depot.nomor

        for _ in range(rho):
            terburuk = None
            hemat_terbesar = -float("inf")
            target_r_idx = -1
            target_pos = -1

            # Single pass O(N) untuk seluruh rute dan posisinya
            for r_idx, rute in enumerate(solusi.daftar_rute):
                nodes = rute.node_ids
                m = len(nodes)
                if m == 0:
                    continue
                for pos, nomor in enumerate(nodes):
                    sebelum = depot if pos == 0 else nodes[pos - 1]
                    sesudah = depot if pos == m - 1 else nodes[pos + 1]
                    hemat = d[sebelum][nomor] + d[nomor][sesudah] - d[sebelum][sesudah]
                    if hemat > hemat_terbesar:
                        hemat_terbesar = hemat
                        terburuk = nomor
                        target_r_idx = r_idx
                        target_pos = pos

            if terburuk is None:
                break

            # Keluarkan langsung menggunakan index dan pos yang sudah diketahui O(1)
            visit = solusi.daftar_rute[target_r_idx].keluarkan_di(target_pos)
            bank.append(visit)

        return bank

    # =====================================================================
    # OPERATOR 3 : SHAW REMOVAL / RELATEDNESS REMOVAL
    # =====================================================================
    def shaw_removal(self, solusi, rho, phi=0.7, chi=0.1, psi=0.2, p=3.0):
        """
        Keluarkan sekelompok pelanggan yang saling mirip (related).
        Rujukan: Shaw (1998); Ropke & Pisinger (2006).

        R(i, j) = phi * (jarak(i, j) / max_d) 
                + chi * (|demand_i - demand_j| / kapasitas)
                + psi * (0 jika satu rute, 1 jika beda rute)
        """
        kandidat = solusi.nomor_pelanggan()
        rho = min(rho, len(kandidat))
        if rho <= 0:
            return []

        # Peta lokasi rute tiap node untuk evaluasi status rute sama O(1)
        node_route = {}
        for r_idx, r in enumerate(solusi.daftar_rute):
            for nid in r.node_ids:
                node_route[nid] = r_idx

        # 1. Pilih 1 node bibit acak dari solusi, keluarkan dan masukkan ke bank
        seed_id = random.choice(kandidat)
        bank = [solusi.keluarkan(seed_id)]

        factor_d = phi / self.max_d
        factor_q = chi / self.kapasitas
        d_mat = self._matriks_jarak
        demands = self._demand_node

        # 2. Selama panjang bank < rho:
        while len(bank) < rho:
            tersisa = solusi.nomor_pelanggan()
            if not tersisa:
                break

            # Ambil 1 node acak dari bank
            ref_node = random.choice(bank)
            ref_id = ref_node.nomor
            ref_demand = ref_node.demand
            ref_r = node_route.get(ref_id, -1)
            d_row = d_mat[ref_id]

            # Hitung skor kemiripan (relatedness) secara cepat tanpa overhead fungsi/lookup
            def hitung_r(nid):
                same_route_cost = 0.0 if node_route.get(nid) == ref_r else psi
                return d_row[nid] * factor_d + abs(ref_demand - demands[nid]) * factor_q + same_route_cost

            # Tentukan indeks acak terlebih dahulu sesuai rank-biased selection
            idx = int((random.random() ** p) * len(tersisa))
            if idx >= len(tersisa):
                idx = len(tersisa) - 1

            # Ambil elemen ke-idx tanpa harus mengurutkan seluruh tersisa O(N log N)
            if idx == 0:
                terpilih_id = min(tersisa, key=hitung_r)
            else:
                terpilih_id = heapq.nsmallest(idx + 1, tersisa, key=hitung_r)[-1]

            bank.append(solusi.keluarkan(terpilih_id))

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
        if nama == "shaw_removal":
            return self.shaw_removal(solusi, rho)
        raise ValueError(f"Destroy operator tidak dikenal: {nama}")

    # daftar nama operator yang tersedia
    DAFTAR = ["random_removal", "worst_removal", "shaw_removal"]


def random_removal(solusi, rho, instance=None):
    inst = instance if instance is not None else solusi.instance
    return DestroyOperator(inst).random_removal(solusi, rho)


def worst_removal(solusi, rho, instance=None):
    inst = instance if instance is not None else solusi.instance
    return DestroyOperator(inst).worst_removal(solusi, rho)


def shaw_removal(solusi, rho, instance=None, phi=0.7, chi=0.1, psi=0.2, p=3.0):
    inst = instance if instance is not None else solusi.instance
    return DestroyOperator(inst).shaw_removal(solusi, rho, phi=phi, chi=chi, psi=psi, p=p)

