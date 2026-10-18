"""
route.py — TAHAP 7 & 13 (TEROPTIMASI & LENGKAP)
"""
from visit import Visit


class Route:
    def __init__(self, instance):
        self.instance = instance
        self.daftar_visit = []
        self.node_ids = []
        self.total_muatan = 0
        self.total_jarak = 0

    def tambah_node(self, node):
        self.daftar_visit.append(Visit(node))
        self.hitung_ulang()

    def sisip_di(self, posisi, node):
        if posisi is None or posisi < 0 or posisi > len(self.daftar_visit):
            posisi = len(self.daftar_visit)
        self.daftar_visit.insert(posisi, Visit(node))
        self.hitung_ulang()

    def keluarkan_di(self, posisi):
        v = self.daftar_visit.pop(posisi)
        self.hitung_ulang()
        return v.node

    def hitung_ulang(self):
        muatan = 0
        for i, v in enumerate(self.daftar_visit):
            v.urutan = i
            muatan += v.demand
            v.muatan_sesudah = muatan
        self.total_muatan = muatan
        self.node_ids = [v.nomor for v in self.daftar_visit]

        n = len(self.node_ids)
        if n == 0:
            self.total_jarak = 0
            return

        depot = self.instance.depot.nomor
        d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
        nodes = self.node_ids

        jarak = d[depot][nodes[0]]
        for i in range(n - 1):
            jarak += d[nodes[i]][nodes[i + 1]]
        jarak += d[nodes[-1]][depot]

        self.total_jarak = jarak

    def nomor_node(self):
        return self.node_ids

    def nomor_node_lengkap(self):
        depot = self.instance.depot.nomor
        return [depot] + self.node_ids + [depot]

    def sisa_kapasitas(self):
        return self.instance.kapasitas - self.total_muatan

    def masih_muat(self, node):
        return node.demand <= (self.instance.kapasitas - self.total_muatan)

    def kosong(self):
        return len(self.daftar_visit) == 0

    def copy(self):
        baru = Route(self.instance)
        baru.daftar_visit = [v.copy() for v in self.daftar_visit]
        baru.node_ids = [v.nomor for v in baru.daftar_visit]
        baru.total_muatan = self.total_muatan
        baru.total_jarak = self.total_jarak
        return baru

    def biaya_sisip(self, node, posisi):
        depot = self.instance.depot.nomor
        n = len(self.node_ids)

        sebelum = depot if posisi == 0 else self.node_ids[posisi - 1]
        sesudah = depot if posisi >= n else self.node_ids[posisi]

        d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
        nid = node.nomor
        return d[sebelum][nid] + d[nid][sesudah] - d[sebelum][sesudah]

    def sisip_terbaik(self, node):
        if not self.masih_muat(node):
            return None, float("inf")

        nodes = self.node_ids
        n = len(nodes)
        d = getattr(self.instance, "_matriks_jarak", self.instance.matrix_jarak)
        depot = self.instance.depot.nomor
        nid = node.nomor
        d_nid = d[nid]

        posisi_terbaik = 0
        biaya_terbaik = float("inf")
        for posisi in range(n + 1):
            sebelum = depot if posisi == 0 else nodes[posisi - 1]
            sesudah = depot if posisi == n else nodes[posisi]
            biaya = d[sebelum][nid] + d_nid[sesudah] - d[sebelum][sesudah]
            if biaya < biaya_terbaik:
                posisi_terbaik = posisi
                biaya_terbaik = biaya
        return posisi_terbaik, biaya_terbaik