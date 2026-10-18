"""
construction.py — Heuristik Konstruksi Clarke & Wright Savings Murni untuk CVRP.
"""
import math
from solution import Solution


class ConstructionHeuristic:
    def __init__(self, instance):
        self.instance = instance

    def clarke_wright_savings(self):
        depot_id = self.instance.depot.nomor
        d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
        pelanggan = list(self.instance.pelanggan)
        cap = self.instance.kapasitas

        # Inisialisasi: setiap pelanggan membentuk rute mandiri (depot -> p -> depot)
        routes = [[p] for p in pelanggan]

        def demand_rute(r):
            return sum(node.demand for node in r)

        savings = []
        n_pel = len(pelanggan)
        for i in range(n_pel):
            p1 = pelanggan[i]
            p1_id = p1.nomor
            for j in range(i + 1, n_pel):
                p2 = pelanggan[j]
                p2_id = p2.nomor
                s = d[depot_id][p1_id] + d[depot_id][p2_id] - d[p1_id][p2_id]
                savings.append((s, p1, p2))

        # Urutkan penghematan dari terbesar ke terkecil
        savings.sort(key=lambda x: x[0], reverse=True)

        def cari_rute(node, active_routes):
            for idx, r in enumerate(active_routes):
                if node in r:
                    return idx
            return None

        for s, p1, p2 in savings:
            idx1 = cari_rute(p1, routes)
            idx2 = cari_rute(p2, routes)

            if idx1 is None or idx2 is None or idx1 == idx2:
                continue

            r1 = routes[idx1]
            r2 = routes[idx2]

            # Periksa batasan kapasitas kendaraan
            if demand_rute(r1) + demand_rute(r2) > cap:
                continue

            is_p1_start = (r1[0] == p1)
            is_p1_end = (r1[-1] == p1)
            is_p2_start = (r2[0] == p2)
            is_p2_end = (r2[-1] == p2)

            if not ((is_p1_start or is_p1_end) and (is_p2_start or is_p2_end)):
                continue

            if is_p1_end and is_p2_start:
                new_r = r1 + r2
            elif is_p1_start and is_p2_end:
                new_r = r2 + r1
            elif is_p1_end and is_p2_end:
                new_r = r1 + list(reversed(r2))
            elif is_p1_start and is_p2_start:
                new_r = list(reversed(r1)) + r2
            else:
                continue

            routes.pop(max(idx1, idx2))
            routes.pop(min(idx1, idx2))
            routes.append(new_r)

        # Bangun objek Solution dari hasil Clarke & Wright
        solusi = Solution(self.instance)
        for r_nodes in routes:
            r = solusi.rute_baru()
            for node in r_nodes:
                r.tambah_node(node)

        solusi.buang_rute_kosong()
        solusi.hitung_ulang()
        return solusi

    def nearest_neighbor(self):
        """
        Heuristik Konstruksi Greedy Nearest Neighbor Sekuensial:
        Membangun rute satu per satu dengan selalu memilih pelanggan terdekat yang masih muat.
        Dilengkapi dengan pemolesan intra-route 2-opt cepat untuk mengoptimasi urutan kunjungan.
        Menghasilkan rute yang menghormati kedekatan geografis.
        """
        solusi = Solution(self.instance)
        belum_dilayani = [n.nomor for n in self.instance.pelanggan]

        rute = solusi.rute_baru()
        posisi = self.instance.depot.nomor

        while belum_dilayani:
            kandidat = [
                nomor for nomor in belum_dilayani
                if rute.masih_muat(self.instance.ambil_node(nomor))
            ]

            if not kandidat:
                rute = solusi.rute_baru()
                posisi = self.instance.depot.nomor
                continue

            terdekat = min(kandidat, key=lambda n: self.instance.jarak(posisi, n))
            rute.tambah_node(self.instance.ambil_node(terdekat))
            belum_dilayani.remove(terdekat)
            posisi = terdekat

        solusi.buang_rute_kosong()
        self._poles_2opt_intra_route(solusi)
        solusi.hitung_ulang()
        return solusi

    def _poles_2opt_intra_route(self, solusi):
        """Memoles rute solusi secara lokal dengan intra-route 2-opt deterministik cepat."""
        depot_id = self.instance.depot.nomor
        d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
        for r in solusi.daftar_rute:
            nodes = [v.node for v in r.daftar_visit]
            n = len(nodes)
            if n < 4:
                continue
            improved = True
            while improved:
                improved = False
                for i in range(n - 1):
                    for j in range(i + 1, n):
                        p_i = depot_id if i == 0 else nodes[i - 1].nomor
                        n_i = nodes[i].nomor
                        n_j = nodes[j].nomor
                        nxt_j = depot_id if j == n - 1 else nodes[j + 1].nomor

                        cur_d = d[p_i][n_i] + d[n_j][nxt_j]
                        new_d = d[p_i][n_j] + d[n_i][nxt_j]
                        if new_d < cur_d:
                            nodes[i : j + 1] = reversed(nodes[i : j + 1])
                            improved = True
                            break
                    if improved:
                        break
            r.daftar_visit.clear()
            for node in nodes:
                r.tambah_node(node)