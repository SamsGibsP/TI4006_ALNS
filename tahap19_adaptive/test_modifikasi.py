import os
import random
import unittest

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance
from destroy import DestroyOperator
from repair import RepairOperator


class TestModifikasiALNS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.join(os.path.dirname(__file__), "A", "A-n32-k5.vrp")
        nodes, capacity, fleet = baca_instance(path)
        cls.instance = CVRPInstance(nodes, capacity, fleet)
        cls.initial = ConstructionHeuristic(cls.instance).nearest_neighbor()

    def test_operator_baru_mempertahankan_semua_pelanggan(self):
        random.seed(7)
        kandidat = self.initial.copy()
        kandidat.siapkan_armada()
        bank = DestroyOperator(self.instance).shaw_removal(kandidat, 6)
        self.assertEqual(len(bank), 6)
        berhasil = RepairOperator(self.instance, tingkat_noise=0.1) \
            .regret3_insertion(kandidat, bank)
        self.assertTrue(berhasil)
        self.assertTrue(kandidat.layak(), kandidat.daftar_pelanggaran())

    def test_alns_modifikasi_layak_dan_adaptif(self):
        random.seed(42)
        pencari = ALNS(
            self.instance, maks_iterasi=80, rho_min=2, rho_maks=6,
            panjang_segmen=20, stagnasi_reheat=20,
            iterasi_local_search=2, tampilkan_setiap=0,
        )
        hasil = pencari.jalankan(self.initial)
        self.assertTrue(hasil.layak(), hasil.daftar_pelanggaran())
        self.assertLessEqual(hasil.total_jarak, self.initial.total_jarak)
        self.assertEqual(pencari.iterasi_dijalankan, 80)
        self.assertGreater(pencari.jumlah_local_search, 0)
        self.assertGreater(len(set(pencari.bobot_pasangan.values())), 1)


if __name__ == "__main__":
    unittest.main()
