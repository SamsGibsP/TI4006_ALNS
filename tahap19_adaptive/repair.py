import random


class RepairOperator:
    DAFTAR = ["greedy_insertion", "regret2_insertion", "regret3_insertion"]

    def __init__(self, instance):
        self.instance = instance

    def jalankan(self, nama, solusi, bank, pakai_noise=False, tingkat_noise=0.1):
        fn = getattr(self, nama, None)
        if fn is None:
            raise ValueError(f"Operator perbaikan '{nama}' tidak dikenal.")
        try:
            return fn(solusi, bank, pakai_noise=pakai_noise, tingkat_noise=tingkat_noise)
        except TypeError:
            return fn(solusi, bank)

    def perbaiki_kelebihan_muatan(self, solusi):
        cap = self.instance.kapasitas

        # Early exit: Jika tidak ada rute yang kelebihan muatan, langsung kembali
        if not any(r.total_muatan > cap for r in solusi.daftar_rute):
            return True

        for _ in range(15):
            overloaded = [r for r in solusi.daftar_rute if r.total_muatan > cap]
            if not overloaded:
                break

            r1 = overloaded[0]
            fixed = False

            kandidat_v1 = sorted(
                list(enumerate(r1.daftar_visit)),
                key=lambda x: x[1].node.demand,
                reverse=True
            )

            # Strategi 1: Relokasi 1 node ke rute lain yang muat
            for pos1, v1 in kandidat_v1:
                q1 = v1.node
                for r2 in solusi.daftar_rute:
                    if r2 is not r1 and r2.masih_muat(q1):
                        p2, biaya = r2.sisip_terbaik(q1)
                        if p2 is not None:
                            r1.keluarkan_di(pos1)
                            r2.sisip_di(p2, q1)
                            fixed = True
                            break
                if fixed:
                    break

            # Strategi 2: Swap dengan node di rute lain
            if not fixed:
                for pos1, v1 in kandidat_v1:
                    q1 = v1.node
                    for r2 in solusi.daftar_rute:
                        if r2 is r1:
                            continue
                        selisih_maks = cap - (r1.total_muatan - q1.demand)
                        for pos2, v2 in enumerate(r2.daftar_visit):
                            q2 = v2.node
                            if (q2.demand < q1.demand and 
                                q2.demand <= selisih_maks and 
                                (r2.total_muatan - q2.demand + q1.demand <= cap)):
                                r1.keluarkan_di(pos1)
                                r2.keluarkan_di(pos2)
                                r1.sisip_di(pos1, q2)
                                r2.sisip_di(pos2, q1)
                                fixed = True
                                break
                        if fixed:
                            break
                    if fixed:
                        break

            if not fixed:
                break

        return not any(r.total_muatan > cap for r in solusi.daftar_rute)

    def _masukkan_node(self, solusi, node, rute_terpilih, posisi_terpilih):
        if rute_terpilih is not None and posisi_terpilih is not None:
            rute_terpilih.sisip_di(posisi_terpilih, node)
            return True

        for r in solusi.daftar_rute:
            if r.kosong() and r.masih_muat(node):
                r.tambah_node(node)
                return True

        # Boleh buka rute baru jika tidak ada batas armada kaku, atau masih di bawah batas armada
        if self.instance.batas_armada is None or len(solusi.daftar_rute) < self.instance.batas_armada:
            r_baru = solusi.rute_baru()
            r_baru.tambah_node(node)
            return True

        return False


    def greedy_insertion(self, solusi, bank, pakai_noise=False, tingkat_noise=0.1):
        """Greedy insertion dengan incremental caching dan opsi noise."""
        max_d = getattr(self.instance, "_max_d", 1000.0)
        cache = {}
        for node in bank:
            cache[node.nomor] = {}
            for r_idx, rute in enumerate(solusi.daftar_rute):
                pos, biaya = rute.sisip_terbaik(node)
                if pos is not None:
                    noise = (random.uniform(-1, 1) * max_d * tingkat_noise) if pakai_noise else 0.0
                    cache[node.nomor][r_idx] = (biaya + noise, rute, pos)

        while bank:
            biaya_min = float("inf")
            node_terbaik = None
            posisi_terbaik = None
            rute_terbaik = None
            r_idx_terbaik = None

            for node in bank:
                c_node = cache[node.nomor]
                for r_idx, (biaya, rute, pos) in c_node.items():
                    if biaya < biaya_min:
                        biaya_min = biaya
                        node_terbaik = node
                        posisi_terbaik = pos
                        rute_terbaik = rute
                        r_idx_terbaik = r_idx

            if node_terbaik is None:
                node_terbaik = bank[0]

            n_rute_lama = len(solusi.daftar_rute)
            berhasil = self._masukkan_node(solusi, node_terbaik, rute_terbaik, posisi_terbaik)
            if not berhasil:
                return False

            bank.remove(node_terbaik)
            del cache[node_terbaik.nomor]
            if not bank:
                break

            rute_berubah = []
            if r_idx_terbaik is not None:
                rute_berubah.append((r_idx_terbaik, rute_terbaik))
            else:
                for idx, r in enumerate(solusi.daftar_rute):
                    rute_berubah.append((idx, r))

            if len(solusi.daftar_rute) > n_rute_lama:
                for idx in range(n_rute_lama, len(solusi.daftar_rute)):
                    rute_berubah.append((idx, solusi.daftar_rute[idx]))

            for n_sisa in bank:
                c_node = cache[n_sisa.nomor]
                for idx, r in rute_berubah:
                    pos, biaya = r.sisip_terbaik(n_sisa)
                    if pos is not None:
                        noise = (random.uniform(-1, 1) * max_d * tingkat_noise) if pakai_noise else 0.0
                        c_node[idx] = (biaya + noise, r, pos)
                    else:
                        c_node.pop(idx, None)

        self.perbaiki_kelebihan_muatan(solusi)
        return True

    def regret2_insertion(self, solusi, bank, pakai_noise=False, tingkat_noise=0.1):
        """Regret-2 insertion dengan incremental caching dan opsi noise."""
        max_d = getattr(self.instance, "_max_d", 1000.0)
        cache = {}
        for node in bank:
            cache[node.nomor] = {}
            for r_idx, rute in enumerate(solusi.daftar_rute):
                pos, biaya = rute.sisip_terbaik(node)
                if pos is not None:
                    noise = (random.uniform(-1, 1) * max_d * tingkat_noise) if pakai_noise else 0.0
                    cache[node.nomor][r_idx] = (biaya + noise, rute, pos)

        while bank:
            regret_maks = -float("inf")
            node_terpilih = None
            rute_terpilih = None
            posisi_terpilih = None
            r_idx_terpilih = None

            for node in bank:
                c_node = cache[node.nomor]
                if not c_node:
                    regret = float("inf")
                    r_best, p_best, r_idx_best = None, None, None
                else:
                    pilihan = sorted(c_node.items(), key=lambda item: item[1][0])
                    c1 = pilihan[0][1][0]
                    r_best, p_best = pilihan[0][1][1], pilihan[0][1][2]
                    r_idx_best = pilihan[0][0]

                    if len(pilihan) == 1:
                        regret = 1e9 + c1
                    else:
                        c2 = pilihan[1][1][0]
                        regret = c2 - c1

                if regret > regret_maks:
                    regret_maks = regret
                    node_terpilih = node
                    rute_terpilih = r_best
                    posisi_terpilih = p_best
                    r_idx_terpilih = r_idx_best

            if node_terpilih is None:
                node_terpilih = bank[0]

            n_rute_lama = len(solusi.daftar_rute)
            berhasil = self._masukkan_node(solusi, node_terpilih, rute_terpilih, posisi_terpilih)
            if not berhasil:
                return False

            bank.remove(node_terpilih)
            del cache[node_terpilih.nomor]
            if not bank:
                break

            rute_berubah = []
            if r_idx_terpilih is not None:
                rute_berubah.append((r_idx_terpilih, rute_terpilih))
            else:
                for idx, r in enumerate(solusi.daftar_rute):
                    rute_berubah.append((idx, r))

            if len(solusi.daftar_rute) > n_rute_lama:
                for idx in range(n_rute_lama, len(solusi.daftar_rute)):
                    rute_berubah.append((idx, solusi.daftar_rute[idx]))

            for n_sisa in bank:
                c_node = cache[n_sisa.nomor]
                for idx, r in rute_berubah:
                    pos, biaya = r.sisip_terbaik(n_sisa)
                    if pos is not None:
                        noise = (random.uniform(-1, 1) * max_d * tingkat_noise) if pakai_noise else 0.0
                        c_node[idx] = (biaya + noise, r, pos)
                    else:
                        c_node.pop(idx, None)

        self.perbaiki_kelebihan_muatan(solusi)
        return True

    def regret3_insertion(self, solusi, bank, pakai_noise=False, tingkat_noise=0.1):
        """Regret-3 insertion (Ropke & Pisinger 2006) dengan incremental caching dan opsi noise."""
        max_d = getattr(self.instance, "_max_d", 1000.0)
        cache = {}
        for node in bank:
            cache[node.nomor] = {}
            for r_idx, rute in enumerate(solusi.daftar_rute):
                pos, biaya = rute.sisip_terbaik(node)
                if pos is not None:
                    noise = (random.uniform(-1, 1) * max_d * tingkat_noise) if pakai_noise else 0.0
                    cache[node.nomor][r_idx] = (biaya + noise, rute, pos)

        while bank:
            regret_maks = -float("inf")
            node_terpilih = None
            rute_terpilih = None
            posisi_terpilih = None
            r_idx_terpilih = None

            for node in bank:
                c_node = cache[node.nomor]
                if not c_node:
                    regret = float("inf")
                    r_best, p_best, r_idx_best = None, None, None
                else:
                    pilihan = sorted(c_node.items(), key=lambda item: item[1][0])
                    c1 = pilihan[0][1][0]
                    r_best, p_best = pilihan[0][1][1], pilihan[0][1][2]
                    r_idx_best = pilihan[0][0]

                    if len(pilihan) == 1:
                        regret = 1e9 + c1
                    elif len(pilihan) == 2:
                        c2 = pilihan[1][1][0]
                        regret = c2 - c1
                    else:
                        c2 = pilihan[1][1][0]
                        c3 = pilihan[2][1][0]
                        regret = (c2 - c1) + (c3 - c1)

                if regret > regret_maks:
                    regret_maks = regret
                    node_terpilih = node
                    rute_terpilih = r_best
                    posisi_terpilih = p_best
                    r_idx_terpilih = r_idx_best

            if node_terpilih is None:
                node_terpilih = bank[0]

            n_rute_lama = len(solusi.daftar_rute)
            berhasil = self._masukkan_node(solusi, node_terpilih, rute_terpilih, posisi_terpilih)
            if not berhasil:
                return False

            bank.remove(node_terpilih)
            del cache[node_terpilih.nomor]
            if not bank:
                break

            rute_berubah = []
            if r_idx_terpilih is not None:
                rute_berubah.append((r_idx_terpilih, rute_terpilih))
            else:
                for idx, r in enumerate(solusi.daftar_rute):
                    rute_berubah.append((idx, r))

            if len(solusi.daftar_rute) > n_rute_lama:
                for idx in range(n_rute_lama, len(solusi.daftar_rute)):
                    rute_berubah.append((idx, solusi.daftar_rute[idx]))

            for n_sisa in bank:
                c_node = cache[n_sisa.nomor]
                for idx, r in rute_berubah:
                    pos, biaya = r.sisip_terbaik(n_sisa)
                    if pos is not None:
                        noise = (random.uniform(-1, 1) * max_d * tingkat_noise) if pakai_noise else 0.0
                        c_node[idx] = (biaya + noise, r, pos)
                    else:
                        c_node.pop(idx, None)

        self.perbaiki_kelebihan_muatan(solusi)
        return True


def greedy_insertion(solusi, bank, instance=None, **kwargs):
    inst = instance if instance is not None else solusi.instance
    return RepairOperator(inst).greedy_insertion(solusi, bank, **kwargs)


def regret2_insertion(solusi, bank, instance=None, **kwargs):
    inst = instance if instance is not None else solusi.instance
    return RepairOperator(inst).regret2_insertion(solusi, bank, **kwargs)


def regret3_insertion(solusi, bank, instance=None, **kwargs):
    inst = instance if instance is not None else solusi.instance
    return RepairOperator(inst).regret3_insertion(solusi, bank, **kwargs)

