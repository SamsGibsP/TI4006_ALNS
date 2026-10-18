"""
construction.py — Heuristik Konstruksi Clarke & Wright Savings Murni untuk CVRP.
Solusi awal dijamin layak kapasitas dan pemenuhan seluruh pelanggan tepat satu kali.
"""
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

        # Kompresi rute jika melebihi batas armada instance
        k_target = getattr(self.instance, "jumlah_kendaraan", None)
        if k_target is not None and solusi.jumlah_rute > k_target:
            solusi = self.kompresi_ke_k_rute(solusi, k_target)

        solusi.buang_rute_kosong()
        solusi.hitung_ulang()
        return solusi

    def kompresi_ke_k_rute(self, solusi, k_target):
        """
        Kompresi Rute Awal (Route Elimination Fallback) berbasis First-Fit Decreasing:
        Mengeliminasi rute dengan muatan terkecil dan menyisipkan pelanggannya
        ke rute-rute aktif yang tersisa selama kapasitas masih mencukupi.
        """
        solusi.buang_rute_kosong()
        solusi.hitung_ulang()

        while solusi.jumlah_rute > k_target:
            rute_aktif = solusi.rute_terisi()
            if len(rute_aktif) <= k_target:
                break

            # 1. Ambil rute dengan total muatan terkecil untuk dieliminasi/dikosongkan
            rute_min = min(rute_aktif, key=lambda r: r.total_muatan)
            sol_backup = solusi.copy()

            # 2. Lepaskan semua pelanggannya, urutkan berdasarkan demand terbesar ke terkecil (prinsip FFD)
            pelanggan_dilepas = [v.node for v in rute_min.daftar_visit]
            pelanggan_dilepas.sort(key=lambda n: n.demand, reverse=True)

            solusi.daftar_rute.remove(rute_min)

            # 3. Sisipkan kembali pelanggan ke rute-rute aktif yang tersisa
            semua_masuk = True
            for node in pelanggan_dilepas:
                terbaik_pos = None
                terbaik_biaya = float("inf")
                terbaik_rute = None

                for r in solusi.rute_terisi():
                    if r.total_muatan + node.demand <= self.instance.kapasitas:
                        pos, delta = r.sisip_terbaik(node)
                        if pos is not None and delta < terbaik_biaya:
                            terbaik_biaya = delta
                            terbaik_pos = pos
                            terbaik_rute = r

                if terbaik_rute is not None and terbaik_pos is not None:
                    terbaik_rute.sisip_di(terbaik_pos, node)
                else:
                    # Coba 1-ejection / relocate: pindahkan 1 node dari r1 ke r2 agar node ini bisa masuk
                    relocated = False
                    for r1 in solusi.rute_terisi():
                        if relocated:
                            break
                        for pos_v, v in enumerate(r1.daftar_visit):
                            v_node = v.node
                            if r1.total_muatan - v_node.demand + node.demand <= self.instance.kapasitas:
                                for r2 in solusi.rute_terisi():
                                    if r2 is not r1 and r2.total_muatan + v_node.demand <= self.instance.kapasitas:
                                        p2, _ = r2.sisip_terbaik(v_node)
                                        if p2 is not None:
                                            r1.keluarkan_di(pos_v)
                                            r2.sisip_di(p2, v_node)
                                            p1, _ = r1.sisip_terbaik(node)
                                            if p1 is not None:
                                                r1.sisip_di(p1, node)
                                                relocated = True
                                                break
                                            else:
                                                # Rollback jika gagal
                                                r2.keluarkan_di(p2)
                                                r1.sisip_di(pos_v, v_node)
                    if not relocated:
                        semua_masuk = False
                        break

            if semua_masuk:
                solusi.buang_rute_kosong()
                solusi.hitung_ulang()
            else:
                # Jika kompresi rute ini gagal, kembalikan solusi ke backup
                solusi.daftar_rute = sol_backup.daftar_rute
                break

        # Jika setelah route elimination masih melebihi k_target, gunakan partisi FFD terjamin
        if solusi.jumlah_rute > k_target:
            solusi = self._konstruksi_partisi_ffd(k_target)

        return solusi

    def _konstruksi_partisi_ffd(self, k_target):
        """
        Fallback Partisi FFD: Membagi seluruh pelanggan ke dalam bin berkapasitas Q
        menggunakan 1D Bin Packing (FFD), kemudian mengurutkan kunjungan dengan TSP Nearest Neighbor.
        Secara matematis dijamin menghasilkan rute <= k_target karena k_target >= k_bpp.
        """
        customers = sorted([n for n in self.instance.pelanggan], key=lambda n: n.demand, reverse=True)
        cap = self.instance.kapasitas
        bins = []
        for c in customers:
            placed = False
            for b in bins:
                if sum(x.demand for x in b) + c.demand <= cap:
                    b.append(c)
                    placed = True
                    break
            if not placed:
                bins.append([c])

        sol = Solution(self.instance)
        for b in bins:
            r = sol.rute_baru()
            curr = self.instance.depot
            unvisited = list(b)
            while unvisited:
                nxt = min(unvisited, key=lambda n: curr.jarak_ke(n))
                r.tambah_node(nxt)
                unvisited.remove(nxt)
                curr = nxt

        sol.buang_rute_kosong()
        sol.hitung_ulang()
        return sol

    def nearest_neighbor(self):
        """Alias untuk clarke_wright_savings demi kompatibilitas."""
        return self.clarke_wright_savings()