"""
tests/test_alns.py — SUITE PENGUJIAN OTOMATIS UNIT, REGRESI, DAN INTEGRASI ALNS-CVRP
====================================================================================
Mencakup pengujian menyeluruh:
1. Validator Solusi (Solusi valid, missing customer, duplikat, ID asing, overload, fleet bound)
2. Operator Destroy & Repair (Shaw removal, Regret-3, semantik return gagal, deteksi TypeError)
3. Local Search (Delta cost vs hitung ulang, invarian kapasitas dan cakupan pelanggan)
4. ALNS Control Flow & Bookkeeping (Invarian panjang riwayat = N, failure tidak bypass cooling, non-worsening best)
5. Reproduksibilitas (Seed sama menghasilkan trajectory identik)
6. Integrasi End-to-End pada 3 instance VRP riil dan validasi file .sol
====================================================================================
"""

import math
import os
import random
import sys
import unittest

folder_tahap19 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance
from destroy import DestroyOperator
from local_search import LocalSearch
from node import Node
from repair import RepairOperator
from route import Route
from solution import Solution
from validasi_solusi import validasi_solusi


def buat_instance_dummy(n_pelanggan=5, kapasitas=50, batas_armada=None):
    """Membuat instance kecil sintetis untuk pengujian unit deterministik."""
    depot = Node(1, 0, 0, 0)
    nodes = [depot]
    for i in range(1, n_pelanggan + 1):
        nid = i + 1
        nodes.append(Node(nid, i * 10, i * 5, 10))
    return CVRPInstance(nodes, kapasitas, 3, batas_armada=batas_armada)


class TestFeasibilityValidator(unittest.TestCase):
    """Pengujian Kritis #1: Validator Kelayakan Solusi."""

    def setUp(self):
        self.instance = buat_instance_dummy(n_pelanggan=4, kapasitas=50)

    def test_solusi_valid_diterima(self):
        sol = Solution(self.instance)
        r1 = sol.rute_baru()
        r1.tambah_node(self.instance.ambil_node(2))
        r1.tambah_node(self.instance.ambil_node(3))
        r2 = sol.rute_baru()
        r2.tambah_node(self.instance.ambil_node(4))
        r2.tambah_node(self.instance.ambil_node(5))
        self.assertTrue(sol.layak())
        self.assertEqual(len(sol.daftar_pelanggaran()), 0)

    def test_pelanggan_kurang_ditolak(self):
        sol = Solution(self.instance)
        r1 = sol.rute_baru()
        r1.tambah_node(self.instance.ambil_node(2))
        r1.tambah_node(self.instance.ambil_node(3))
        # Pelanggan 4 dan 5 tidak dimasukkan
        self.assertFalse(sol.layak())
        self.assertTrue(any("belum dilayani" in p for p in sol.daftar_pelanggaran()))

    def test_pelanggan_duplikat_ditolak(self):
        sol = Solution(self.instance)
        r1 = sol.rute_baru()
        r1.tambah_node(self.instance.ambil_node(2))
        r1.tambah_node(self.instance.ambil_node(3))
        r2 = sol.rute_baru()
        r2.tambah_node(self.instance.ambil_node(3))  # Duplikat node 3
        r2.tambah_node(self.instance.ambil_node(4))
        r2.tambah_node(self.instance.ambil_node(5))
        self.assertFalse(sol.layak())
        self.assertTrue(any("lebih dari sekali" in p for p in sol.daftar_pelanggaran()))

    def test_pelanggan_asing_ditolak(self):
        # Instance sintetis dengan pelanggan resmi: node 2, 3, 4 (node 5 dikeluarkan dari daftar resmi)
        inst = buat_instance_dummy(n_pelanggan=4, kapasitas=50)
        # Hilangkan node 5 dari daftar pelanggan resmi
        inst.pelanggan = [p for p in inst.pelanggan if p.nomor != 5]

        sol = Solution(inst)
        r1 = sol.rute_baru()
        r1.tambah_node(inst.ambil_node(2))
        r1.tambah_node(inst.ambil_node(3))
        r2 = sol.rute_baru()
        r2.tambah_node(inst.ambil_node(4))
        # Masukkan node 5 yang bukan pelanggan resmi
        r2.tambah_node(inst.ambil_node(5))
        self.assertFalse(sol.layak())
        self.assertTrue(any("asing" in p or "belum dilayani" in p for p in sol.daftar_pelanggaran()))

    def test_kelebihan_kapasitas_ditolak(self):
        # Kapasitas 25, node demand masing-masing 10
        inst_kecil = buat_instance_dummy(n_pelanggan=3, kapasitas=25)
        sol = Solution(inst_kecil)
        r = sol.rute_baru()
        r.tambah_node(inst_kecil.ambil_node(2))
        r.tambah_node(inst_kecil.ambil_node(3))
        r.tambah_node(inst_kecil.ambil_node(4))  # total muatan 30 > 25
        self.assertFalse(sol.layak())
        self.assertTrue(any("kelebihan muatan" in p for p in sol.daftar_pelanggaran()))

    def test_armada_bebas_tanpa_batas_keras(self):
        inst_fleet = buat_instance_dummy(n_pelanggan=3, kapasitas=50)
        sol = Solution(inst_fleet)
        r1 = sol.rute_baru()
        r1.tambah_node(inst_fleet.ambil_node(2))
        r2 = sol.rute_baru()
        r2.tambah_node(inst_fleet.ambil_node(3))
        r2.tambah_node(inst_fleet.ambil_node(4))
        # Membuka rute sesuai kebutuhan muatan tanpa dibatasi kuota keras
        self.assertTrue(sol.layak())
        self.assertEqual(len(sol.daftar_pelanggaran()), 0)

    def test_rute_kosong_ditangani_konsisten(self):
        sol = Solution(self.instance)
        r1 = sol.rute_baru()
        r1.tambah_node(self.instance.ambil_node(2))
        r1.tambah_node(self.instance.ambil_node(3))
        r2 = sol.rute_baru()
        r2.tambah_node(self.instance.ambil_node(4))
        r2.tambah_node(self.instance.ambil_node(5))
        r_kosong = sol.rute_baru()
        self.assertTrue(r_kosong.kosong())
        self.assertTrue(sol.layak())
        self.assertEqual(sol.jumlah_rute, 2)
        sol.buang_rute_kosong()
        self.assertEqual(len(sol.daftar_rute), 2)
        self.assertTrue(sol.layak())

    def test_semua_file_solusi_yang_ada_lolos_validasi(self):
        sol_files = [
            ("X-n101-k25.vrp", "solusi_terbaik_X-n101-k25.sol"),
            ("X-n143-k7.vrp", "solusi_terbaik_X-n143-k7.sol"),
            ("X-n351-k40.vrp", "solusi_terbaik_X-n351-k40.sol"),
        ]
        dir_final = os.path.join(os.path.dirname(folder_tahap19), "hasil_final")
        for vrp_name, sol_name in sol_files:
            p_vrp = os.path.join(folder_tahap19, "X", vrp_name)
            p_sol = os.path.join(dir_final, sol_name)
            if os.path.exists(p_sol):
                hasil = validasi_solusi(p_vrp, p_sol, verbose=False)
                self.assertTrue(hasil["valid"], f"File {sol_name} gagal validasi")
                self.assertEqual(hasil["total_jarak"], hasil["stated_cost"])


class TestOperatorsAndContracts(unittest.TestCase):
    """Pengujian Kritis #3: Semantik Operator & Kontrak TypeError."""

    def setUp(self):
        self.instance = buat_instance_dummy(n_pelanggan=4, kapasitas=50)

    def test_repair_operator_call_contract_preserves_genuine_typeerror(self):
        pembaik = RepairOperator(self.instance)
        # Pasang operator buggy yang sengaja melempar TypeError internal
        def buggy_repair(solusi, bank, **kwargs):
            raise TypeError("TypeError internal buatan")

        setattr(pembaik, "buggy_repair", buggy_repair)
        sol = Solution(self.instance)
        with self.assertRaises(TypeError):
            pembaik.jalankan("buggy_repair", sol, [])

    def test_repair_operator_returns_false_if_overload_unrepairable(self):
        inst = buat_instance_dummy(n_pelanggan=3, kapasitas=15, batas_armada=1)
        sol = Solution(inst)
        r = sol.rute_baru()
        # 3 node demand 10 masing-masing = 30 > 15, batas armada 1 rute
        r.tambah_node(inst.ambil_node(2))
        r.tambah_node(inst.ambil_node(3))
        r.tambah_node(inst.ambil_node(4))
        pembaik = RepairOperator(inst)
        # Tidak ada rute baru yang boleh dibuka, kapasitas tidak bisa diperbaiki
        hasil = pembaik.perbaiki_kelebihan_muatan(sol)
        self.assertFalse(hasil)

    def test_shaw_removal_count_and_determinism(self):
        inst = buat_instance_dummy(n_pelanggan=6, kapasitas=50)
        sol = ConstructionHeuristic(inst).clarke_wright_savings()
        perusak = DestroyOperator(inst)

        # Uji determinisme dengan seed identik
        random.seed(123)
        sol_copy1 = sol.copy()
        bank1 = perusak.shaw_removal(sol_copy1, rho=3)

        random.seed(123)
        sol_copy2 = sol.copy()
        bank2 = perusak.shaw_removal(sol_copy2, rho=3)

        self.assertEqual(len(bank1), 3)
        self.assertEqual([v.nomor for v in bank1], [v.nomor for v in bank2])

    def test_local_search_delta_cost_agreement(self):
        path_vrp = os.path.join(folder_tahap19, "X", "X-n101-k25.vrp")
        d, c, k = baca_instance(path_vrp)
        inst = CVRPInstance(d, c, k)
        sol = ConstructionHeuristic(inst).clarke_wright_savings()

        ls = LocalSearch(inst, operators=["two_opt", "relocate", "swap"], max_iterations=5)
        sol_poles = ls.run(sol.copy(), verbose=False)

        # Hitung ulang total jarak dari awal
        jarak_terhitung = 0
        for r in sol_poles.rute:
            jarak_rute = 0
            prev = inst.depot
            for v in r.daftar_visit:
                jarak_rute += prev.jarak_ke(v.node)
                prev = v.node
            jarak_rute += prev.jarak_ke(inst.depot)
            jarak_terhitung += jarak_rute

        self.assertEqual(sol_poles.total_jarak, jarak_terhitung)
        self.assertTrue(sol_poles.layak())

    def test_regret3_calculation_logic(self):
        # Memeriksa bahwa operator regret3_insertion berhasil memasukkan kembali node ke solusi multi-rute
        inst = buat_instance_dummy(n_pelanggan=5, kapasitas=100)
        sol = Solution(inst)
        r1 = sol.rute_baru()
        r1.tambah_node(inst.ambil_node(2))
        r2 = sol.rute_baru()
        r2.tambah_node(inst.ambil_node(3))
        r3 = sol.rute_baru()
        r3.tambah_node(inst.ambil_node(4))

        bank = [inst.ambil_node(5), inst.ambil_node(6)]
        pembaik = RepairOperator(inst)
        sukses = pembaik.regret3_insertion(sol, bank)
        self.assertTrue(sukses)
        self.assertEqual(len(bank), 0)
        self.assertTrue(sol.layak())


class TestALNSIterationBookkeeping(unittest.TestCase):
    """Pengujian Kritis #2: Invarian Bookkeeping dan Riwayat Iterasi ALNS."""

    def test_iteration_history_length_equals_n(self):
        inst = buat_instance_dummy(n_pelanggan=5, kapasitas=50)
        sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()

        N = 50
        alns = ALNS(inst, maks_iterasi=N, pakai_adaptif=False, tampilkan_setiap=0)
        alns.jalankan(sol_awal)

        self.assertEqual(len(alns.riwayat_terbaik), N, f"Panjang riwayat_terbaik harus tepat {N}")

    def test_failing_repair_operator_does_not_skip_cooling_or_history(self):
        """Memverifikasi bahwa kegagalan operator repair tidak memotong riwayat konvergensi atau pendinginan suhu."""
        inst = buat_instance_dummy(n_pelanggan=5, kapasitas=50)
        sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()

        N = 30
        alns = ALNS(inst, maks_iterasi=N, pakai_adaptif=False, tampilkan_setiap=0, suhu_awal=100.0, laju_pendinginan=0.9)

        # Modifikasi pembaik agar selalu gagal pada 50% iterasi pertama
        counter = {"count": 0}
        asli_jalankan = alns.pembaik.jalankan

        def mock_jalankan(nama, solusi, bank, pakai_noise=False, tingkat_noise=0.1, **kwargs):
            counter["count"] += 1
            if counter["count"] % 2 == 0:
                # Simulasikan kegagalan repair
                return False
            return asli_jalankan(nama, solusi, bank, pakai_noise=pakai_noise, tingkat_noise=tingkat_noise, **kwargs)

        alns.pembaik.jalankan = mock_jalankan  # type: ignore
        alns.jalankan(sol_awal)

        # Invarian 1: Riwayat konvergensi tetap harus persis N iterasi
        self.assertEqual(len(alns.riwayat_terbaik), N)
        # Invarian 2: Suhu harus terdinginkan sesuai jadwal penuh N kali: T = T0 * (laju ^ N)
        suhu_harapan = 100.0 * (0.9 ** N)
        self.assertIsNotNone(alns.suhu)
        assert alns.suhu is not None
        self.assertAlmostEqual(alns.suhu, suhu_harapan, places=4)
        # Invarian 3: Jumlah gagal terhitung secara diagnostik
        self.assertGreater(alns.jumlah_gagal, 0)

    def test_best_objective_history_is_monotonically_non_worsening(self):
        inst = buat_instance_dummy(n_pelanggan=5, kapasitas=50)
        sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()

        alns = ALNS(inst, maks_iterasi=40, pakai_adaptif=True, tampilkan_setiap=0)
        alns.jalankan(sol_awal)

        for i in range(1, len(alns.riwayat_terbaik)):
            self.assertLessEqual(alns.riwayat_terbaik[i], alns.riwayat_terbaik[i - 1],
                                 "Riwayat nilai terbaik tidak boleh pernah memburuk!")

    def test_reheating_stagnation_and_floor(self):
        inst = buat_instance_dummy(n_pelanggan=5, kapasitas=50)
        sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()

        alns = ALNS(inst, maks_iterasi=25, pakai_adaptif=False, pakai_reheating=True,
                    ambang_reheat=10, faktor_reheat=0.4, suhu_awal=1000.0, laju_pendinginan=0.8,
                    tampilkan_setiap=0)
        alns.jalankan(sol_awal)

        self.assertEqual(len(alns.riwayat_terbaik), 25)
        self.assertIsNotNone(alns.suhu)
        assert alns.suhu is not None
        self.assertGreaterEqual(alns.suhu, 1000.0 * (0.8 ** 25))

    def test_reproducibility_same_seed_identical_trajectory(self):
        inst = buat_instance_dummy(n_pelanggan=5, kapasitas=50)
        sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()

        random.seed(999)
        alns1 = ALNS(inst, maks_iterasi=20, pakai_adaptif=True, tampilkan_setiap=0)
        sol1 = alns1.jalankan(sol_awal.copy())

        random.seed(999)
        alns2 = ALNS(inst, maks_iterasi=20, pakai_adaptif=True, tampilkan_setiap=0)
        sol2 = alns2.jalankan(sol_awal.copy())

        self.assertEqual(sol1.total_jarak, sol2.total_jarak)
        self.assertEqual(alns1.riwayat_terbaik, alns2.riwayat_terbaik)


class TestEndToEndIntegration(unittest.TestCase):
    """Pengujian Integrasi End-to-End pada Instance Riil CVRPLIB."""

    def test_three_cvrplib_instances_initial_solution_and_smoke_alns(self):
        instances = [
            ("X-n101-k25.vrp", 28986),
            ("X-n143-k7.vrp", 17478),
            ("X-n351-k40.vrp", 27123),
        ]

        for vrp_name, target_cw in instances:
            path_vrp = os.path.join(folder_tahap19, "X", vrp_name)
            self.assertTrue(os.path.exists(path_vrp), f"File {path_vrp} tidak ditemukan")

            d, c, k = baca_instance(path_vrp)
            inst = CVRPInstance(d, c, k)
            sol_awal = ConstructionHeuristic(inst).clarke_wright_savings()

            # Verifikasi bahwa solusi awal sepenuhnya layak dan nilai target CW eksak
            self.assertTrue(sol_awal.layak())
            self.assertEqual(sol_awal.total_jarak, target_cw)
            self.assertEqual(len(sol_awal.daftar_pelanggaran()), 0)

            # Smoke test ALNS (5 iterasi)
            random.seed(42)
            alns = ALNS(inst, maks_iterasi=5, pakai_adaptif=True, tampilkan_setiap=0)
            hasil = alns.jalankan(sol_awal)

            self.assertTrue(hasil.layak())
            self.assertLessEqual(hasil.total_jarak, sol_awal.total_jarak)


if __name__ == "__main__":
    unittest.main(verbosity=2)
