"""
repair.py — TAHAP 14/19 (BERSIH & TEROPTIMASI)
"""

class RepairOperator:
    DAFTAR = ["greedy_insertion", "regret2_insertion"]

    def __init__(self, instance):
        self.instance = instance

    def jalankan(self, nama, solusi, bank):
        fn = getattr(self, nama, None)
        if fn is None:
            raise ValueError(f"Operator perbaikan '{nama}' tidak dikenal.")
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

        if len(solusi.daftar_rute) < self.instance.jumlah_kendaraan:
            r_baru = solusi.rute_baru()
            r_baru.tambah_node(node)
            return True

        return False

    def greedy_insertion(self, solusi, bank):
        while bank:
            biaya_min = float("inf")
            node_terbaik = None
            posisi_terbaik = None
            rute_terbaik = None

            for node in bank:
                for rute in solusi.daftar_rute:
                    pos, biaya = rute.sisip_terbaik(node)
                    if biaya < biaya_min:
                        biaya_min = biaya
                        node_terbaik = node
                        posisi_terbaik = pos
                        rute_terbaik = rute

            if node_terbaik is None:
                node_terbaik = bank[0]

            berhasil = self._masukkan_node(solusi, node_terbaik, rute_terbaik, posisi_terbaik)
            if not berhasil:
                return False
            bank.remove(node_terbaik)

        self.perbaiki_kelebihan_muatan(solusi)
        return True

    def regret2_insertion(self, solusi, bank):
        while bank:
            regret_maks = -float("inf")
            node_terpilih = None
            rute_terpilih = None
            posisi_terpilih = None

            for node in bank:
                pilihan = []
                for rute in solusi.daftar_rute:
                    pos, biaya = rute.sisip_terbaik(node)
                    if pos is not None:
                        pilihan.append((biaya, rute, pos))

                pilihan.sort(key=lambda x: x[0])

                if len(pilihan) == 0:
                    regret = float("inf")
                    r_best, p_best = None, None
                elif len(pilihan) == 1:
                    regret = pilihan[0][0]
                    r_best, p_best = pilihan[0][1], pilihan[0][2]
                else:
                    regret = pilihan[1][0] - pilihan[0][0]
                    r_best, p_best = pilihan[0][1], pilihan[0][2]

                if regret > regret_maks:
                    regret_maks = regret
                    node_terpilih = node
                    rute_terpilih = r_best
                    posisi_terpilih = p_best

            if node_terpilih is None:
                node_terpilih = bank[0]

            berhasil = self._masukkan_node(solusi, node_terpilih, rute_terpilih, posisi_terpilih)
            if not berhasil:
                return False
            bank.remove(node_terpilih)

        self.perbaiki_kelebihan_muatan(solusi)
        return True


def greedy_insertion(solusi, bank, instance=None):
    inst = instance if instance is not None else solusi.instance
    return RepairOperator(inst).greedy_insertion(solusi, bank)


def regret2_insertion(solusi, bank, instance=None):
    inst = instance if instance is not None else solusi.instance
    return RepairOperator(inst).regret2_insertion(solusi, bank)
