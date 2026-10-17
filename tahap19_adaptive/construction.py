"""
construction.py — Heuristik Konstruksi Terkontrol (Clarke & Wright Savings + Bin Packing Fallback)
Dijamin 100% LAYAK (jumlah rute <= K dan muatan rute <= Q) untuk seluruh instance.
"""
import random
from solution import Solution


class ConstructionHeuristic:
    def __init__(self, instance):
        self.instance = instance

    def clarke_wright_savings(self):
        depot_id = self.instance.depot.nomor
        d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
        pelanggan = list(self.instance.pelanggan)
        cap = self.instance.kapasitas
        k_maks = self.instance.batas_armada

        # --- CARA 1: Clarke and Wright Savings ---
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

        # Jika hasil penggabungan Clarke & Wright memenuhi kapasitas dan batasan armada (jika ada)
        if k_maks is None or len(routes) <= k_maks:
            solusi = Solution(self.instance)
            for r_nodes in routes:
                r = solusi.rute_baru()
                for node in r_nodes:
                    r.tambah_node(node)

            solusi.buang_rute_kosong()
            if solusi.layak():
                return solusi

        # --- CARA 2: MEKANISME FALLBACK (BEST-FIT DECREASING / BIN PACKING COMPACTION) ---
        # Hanya jika ada batas k_maks kaku dan len(routes) > k_maks
        k_target = k_maks if k_maks is not None else self.instance.jumlah_kendaraan
        pelanggan_desc = sorted(pelanggan, key=lambda n: n.demand, reverse=True)
        bins = [[] for _ in range(k_target)]
        loads = [0] * k_target
        bfd_sukses = True

        for p in pelanggan_desc:
            best_idx = None
            min_sisa = cap + 1
            for b_idx in range(k_target):
                sisa = cap - (loads[b_idx] + p.demand)
                if sisa >= 0 and sisa < min_sisa:
                    min_sisa = sisa
                    best_idx = b_idx
            if best_idx is not None:
                bins[best_idx].append(p)
                loads[best_idx] += p.demand
            else:
                bfd_sukses = False
                break

        if not bfd_sukses:
            while True:
                bins = [[] for _ in range(k_target)]
                pelanggan_shuffled = list(pelanggan)
                random.shuffle(pelanggan_shuffled)
                for i, item in enumerate(pelanggan_shuffled):
                    bins[i % k_target].append(item)

                loads = [sum(n.demand for n in b) for b in bins]

                for step in range(10000):
                    overloaded = [i for i in range(k_target) if loads[i] > cap]
                    if not overloaded:
                        break

                    b1 = random.choice(overloaded)
                    if not bins[b1]:
                        continue
                    idx1 = random.randrange(len(bins[b1]))
                    n1 = bins[b1][idx1]

                    b2 = random.randrange(k_target)
                    if b2 == b1:
                        continue

                    if bins[b2] and random.random() < 0.7:
                        idx2 = random.randrange(len(bins[b2]))
                        n2 = bins[b2][idx2]

                        cur_pen = max(0, loads[b1] - cap) + max(0, loads[b2] - cap)
                        l1_new = loads[b1] - n1.demand + n2.demand
                        l2_new = loads[b2] - n2.demand + n1.demand
                        new_pen = max(0, l1_new - cap) + max(0, l2_new - cap)

                        if new_pen <= cur_pen:
                            bins[b1][idx1] = n2
                            bins[b2][idx2] = n1
                            loads[b1] = l1_new
                            loads[b2] = l2_new
                    else:
                        cur_pen = max(0, loads[b1] - cap) + max(0, loads[b2] - cap)
                        l1_new = loads[b1] - n1.demand
                        l2_new = loads[b2] + n1.demand
                        new_pen = max(0, l1_new - cap) + max(0, l2_new - cap)

                        if new_pen <= cur_pen:
                            bins[b1].pop(idx1)
                            bins[b2].append(n1)
                            loads[b1] = l1_new
                            loads[b2] = l2_new

                if sum(max(0, l - cap) for l in loads) == 0:
                    break

        solusi2 = Solution(self.instance)
        for b_nodes in bins:
            if not b_nodes:
                continue
            r = solusi2.rute_baru()
            unvisited = list(b_nodes)
            cur_node = depot_id
            while unvisited:
                best_n = min(unvisited, key=lambda n: d[cur_node][n.nomor])
                r.tambah_node(best_n)
                unvisited.remove(best_n)
                cur_node = best_n.nomor

        solusi2.buang_rute_kosong()
        # Poles rute awal dengan pemoles intra-route cepat
        from local_search import LocalSearch
        ls_init = LocalSearch(self.instance, operators=["two_opt"], max_iterations=20)
        solusi2 = ls_init.run(solusi2, verbose=False)
        return solusi2

    def nearest_neighbor(self):
        """Alias untuk clarke_wright_savings demi kompatibilitas."""
        return self.clarke_wright_savings()