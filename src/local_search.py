"""
local_search.py — MODUL LOCAL SEARCH RESMI & TEROPTIMASI
Mendukung operator: 2-opt (intra-route), relocate (inter/intra), dan swap (inter/intra).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from solution import Solution
except ImportError:
    from .solution import Solution


class LocalSearch:
    def __init__(
        self,
        instance=None,
        operators: Optional[List[str]] = None,
        max_iterations: int = 30,
    ):
        self.instance = instance
        self.operators: List[str] = (
            operators if operators is not None else ["two_opt", "relocate", "swap"]
        )
        self.max_iterations: int = max_iterations
        self.jumlah_iterasi: int = 0
        self.riwayat: List[int] = []
        self.log_iterasi: List[Dict[str, Any]] = []
        self.pesan_berhenti: str = ""

    # =========================================================================
    # 1. OPERATOR 2-OPT (Intra-route Inversion - Evaluasi Delta O(1))
    # =========================================================================
    def two_opt_terbaik(self, solusi: Solution) -> bool:
        inst = self.instance if self.instance is not None else solusi.instance
        d = getattr(inst, "_matriks_jarak", inst.matrix_jarak)
        depot = inst.depot.nomor

        delta_terbaik = 0
        langkah_terbaik: Optional[Tuple[int, int, int]] = None

        for r_idx, r in enumerate(solusi.daftar_rute):
            node_ids = r.nomor_node()
            n = len(node_ids)
            if n < 2:
                continue

            for i in range(n - 1):
                u1 = depot if i == 0 else node_ids[i - 1]
                u2 = node_ids[i]
                for j in range(i + 1, n):
                    # Membalik seluruh rute menghasilkan rute simetris yang sama
                    if i == 0 and j == n - 1:
                        continue

                    v1 = node_ids[j]
                    v2 = depot if j == n - 1 else node_ids[j + 1]

                    # Perubahan jarak murni pada 2 sisi yang dipotong
                    d_lama = d[u1][u2] + d[v1][v2]
                    d_baru = d[u1][v1] + d[u2][v2]
                    delta = d_baru - d_lama

                    if delta < delta_terbaik:
                        delta_terbaik = delta
                        langkah_terbaik = (r_idx, i, j)

        if langkah_terbaik is None or delta_terbaik >= 0:
            return False

        r_idx, i, j = langkah_terbaik
        r = solusi.daftar_rute[r_idx]
        r.daftar_visit[i:j + 1] = list(reversed(r.daftar_visit[i:j + 1]))
        r.hitung_ulang()
        solusi.buang_rute_kosong()
        solusi.hitung_ulang()
        return True

    # =========================================================================
    # 2. OPERATOR RELOCATE (Best Improvement - Evaluasi Delta O(1))
    # =========================================================================
    def relocate_terbaik(self, solusi: Solution) -> bool:
        inst = self.instance if self.instance is not None else solusi.instance
        d = getattr(inst, "_matriks_jarak", inst.matrix_jarak)
        depot = inst.depot.nomor

        delta_terbaik = 0
        langkah_terbaik: Optional[Tuple[int, int, int, int]] = None
        n_rute = len(solusi.daftar_rute)

        for i_asal in range(n_rute):
            r_asal = solusi.daftar_rute[i_asal]
            nodes_asal = r_asal.node_ids
            m_asal = len(nodes_asal)
            if m_asal == 0:
                continue

            for pos_asal in range(m_asal):
                node_u = nodes_asal[pos_asal]
                v_u = r_asal.daftar_visit[pos_asal]

                # Tetangga u di rute asal
                pred_A = depot if pos_asal == 0 else nodes_asal[pos_asal - 1]
                succ_A = depot if pos_asal == m_asal - 1 else nodes_asal[pos_asal + 1]

                for i_tujuan in range(n_rute):
                    r_tujuan = solusi.daftar_rute[i_tujuan]

                    if i_asal != i_tujuan:
                        if not r_tujuan.masih_muat(v_u.node):
                            continue
                        nodes_tujuan = r_tujuan.node_ids
                        m_tujuan = len(nodes_tujuan)

                        # Pengurangan jarak di rute asal
                        delta_rem = d[pred_A][succ_A] - (d[pred_A][node_u] + d[node_u][succ_A])

                        # Uji setiap posisi sisip di rute tujuan
                        for pos_tujuan in range(m_tujuan + 1):
                            pred_B = depot if pos_tujuan == 0 else nodes_tujuan[pos_tujuan - 1]
                            succ_B = depot if pos_tujuan == m_tujuan else nodes_tujuan[pos_tujuan]

                            delta_ins = (d[pred_B][node_u] + d[node_u][succ_B]) - d[pred_B][succ_B]
                            delta = delta_rem + delta_ins

                            if delta < delta_terbaik:
                                delta_terbaik = delta
                                langkah_terbaik = (i_asal, pos_asal, i_tujuan, pos_tujuan)
                    else:
                        # Intra-route relocate
                        for pos_tujuan in range(m_asal):
                            if pos_tujuan == pos_asal or pos_tujuan == pos_asal + 1:
                                continue

                            if pos_tujuan < pos_asal:
                                pred_q = depot if pos_tujuan == 0 else nodes_asal[pos_tujuan - 1]
                                node_q = nodes_asal[pos_tujuan]
                                delta = (
                                    d[pred_q][node_u]
                                    + d[node_u][node_q]
                                    + d[pred_A][succ_A]
                                    - d[pred_q][node_q]
                                    - d[pred_A][node_u]
                                    - d[node_u][succ_A]
                                )
                            else:
                                # pos_tujuan > pos_asal + 1
                                pred_q = nodes_asal[pos_tujuan]
                                succ_q = depot if pos_tujuan == m_asal - 1 else nodes_asal[pos_tujuan + 1]
                                delta = (
                                    d[pred_A][succ_A]
                                    + d[pred_q][node_u]
                                    + d[node_u][succ_q]
                                    - d[pred_A][node_u]
                                    - d[node_u][succ_A]
                                    - d[pred_q][succ_q]
                                )

                            if delta < delta_terbaik:
                                delta_terbaik = delta
                                langkah_terbaik = (i_asal, pos_asal, i_tujuan, pos_tujuan)

        if langkah_terbaik is None or delta_terbaik >= 0:
            return False

        i_asal, pos_asal, i_tujuan, pos_tujuan = langkah_terbaik
        v = solusi.daftar_rute[i_asal].daftar_visit.pop(pos_asal)
        solusi.daftar_rute[i_tujuan].daftar_visit.insert(pos_tujuan, v)
        solusi.daftar_rute[i_asal].hitung_ulang()
        if i_asal != i_tujuan:
            solusi.daftar_rute[i_tujuan].hitung_ulang()
        solusi.buang_rute_kosong()
        solusi.hitung_ulang()
        return True

    # =========================================================================
    # 3. OPERATOR SWAP (Best Improvement - Evaluasi Delta O(1))
    # =========================================================================
    def swap_terbaik(self, solusi: Solution) -> bool:
        delta_terbaik = 0
        langkah_terbaik: Optional[Tuple[int, int, int, int]] = None
        n_rute = len(solusi.daftar_rute)
        inst = self.instance if self.instance is not None else solusi.instance
        kapasitas = inst.kapasitas
        d = getattr(inst, "_matriks_jarak", inst.matrix_jarak)
        depot = inst.depot.nomor

        for i_A in range(n_rute):
            r_A = solusi.daftar_rute[i_A]
            nodes_A = r_A.node_ids
            m_A = len(nodes_A)
            if m_A == 0:
                continue

            for pos_A in range(m_A):
                v_A = r_A.daftar_visit[pos_A]
                node_A = nodes_A[pos_A]
                pred_A = depot if pos_A == 0 else nodes_A[pos_A - 1]
                succ_A = depot if pos_A == m_A - 1 else nodes_A[pos_A + 1]

                for i_B in range(i_A, n_rute):
                    r_B = solusi.daftar_rute[i_B]
                    nodes_B = r_B.node_ids
                    m_B = len(nodes_B)
                    if m_B == 0:
                        continue
                    start_pos_B = (pos_A + 1) if i_A == i_B else 0

                    for pos_B in range(start_pos_B, m_B):
                        v_B = r_B.daftar_visit[pos_B]
                        node_B = nodes_B[pos_B]

                        if i_A != i_B:
                            # Cek kapasitas
                            if (r_A.total_muatan - v_A.demand + v_B.demand > kapasitas) or \
                               (r_B.total_muatan - v_B.demand + v_A.demand > kapasitas):
                                continue

                            pred_B = depot if pos_B == 0 else nodes_B[pos_B - 1]
                            succ_B = depot if pos_B == m_B - 1 else nodes_B[pos_B + 1]

                            delta_A = (d[pred_A][node_B] + d[node_B][succ_A]) - (d[pred_A][node_A] + d[node_A][succ_A])
                            delta_B = (d[pred_B][node_A] + d[node_A][succ_B]) - (d[pred_B][node_B] + d[node_B][succ_B])
                            delta = delta_A + delta_B
                        else:
                            # Intra-route swap
                            pred_B = nodes_A[pos_B - 1]
                            succ_B = depot if pos_B == m_A - 1 else nodes_A[pos_B + 1]

                            if pos_B == pos_A + 1:
                                delta = (
                                    d[pred_A][node_B]
                                    + d[node_A][succ_B]
                                    - d[pred_A][node_A]
                                    - d[node_B][succ_B]
                                )
                            else:
                                delta = (
                                    d[pred_A][node_B]
                                    + d[node_B][succ_A]
                                    + d[pred_B][node_A]
                                    + d[node_A][succ_B]
                                    - d[pred_A][node_A]
                                    - d[node_A][succ_A]
                                    - d[pred_B][node_B]
                                    - d[node_B][succ_B]
                                )

                        if delta < delta_terbaik:
                            delta_terbaik = delta
                            langkah_terbaik = (i_A, pos_A, i_B, pos_B)

        if langkah_terbaik is None or delta_terbaik >= 0:
            return False

        i_A, pos_A, i_B, pos_B = langkah_terbaik
        r_A = solusi.daftar_rute[i_A]
        r_B = solusi.daftar_rute[i_B]
        if i_A == i_B:
            r_A.daftar_visit[pos_A], r_A.daftar_visit[pos_B] = r_A.daftar_visit[pos_B], r_A.daftar_visit[pos_A]
            r_A.hitung_ulang()
        else:
            r_A.daftar_visit[pos_A], r_B.daftar_visit[pos_B] = r_B.daftar_visit[pos_B], r_A.daftar_visit[pos_A]
            r_A.hitung_ulang()
            r_B.hitung_ulang()

        solusi.buang_rute_kosong()
        solusi.hitung_ulang()
        return True

    # =========================================================================
    # MAIN RUNNER
    # =========================================================================
    def run(self, solusi_awal: Solution, nilai_optimal: int = 0, verbose: bool = True) -> Solution:
        solusi = solusi_awal.copy()
        self.jumlah_iterasi = 0
        self.riwayat = [solusi.total_jarak]
        self.log_iterasi = []

        if not self.operators:
            return solusi

        lebar = 88
        if verbose:
            print("-" * lebar)
            print(f" {'Timestamp':^10} | {'Iter':^5} | {'Jarak':^7} | {'Turun':^7} | {'Operator':^10} | {'BKS':^7} | {'Sisa Gap (%)':^14}")
            print("-" * lebar)
            t_now = datetime.now().strftime("%H:%M:%S")
            gap_awal = f"+{((solusi.total_jarak - nilai_optimal) / nilai_optimal) * 100:.2f}%" if nilai_optimal > 0 else "-"
            bks_s = str(nilai_optimal) if nilai_optimal > 0 else "-"
            print(f" [{t_now}] | {0:^5} | {solusi.total_jarak:>7} | {'-':^7} | {'awal':^10} | {bks_s:>7} | {gap_awal:>14}")

        for iterasi in range(1, self.max_iterations + 1):
            jarak_sebelum = solusi.total_jarak
            ada_perbaikan = False
            op_terpakai = ""

            for op_name in self.operators:
                op_clean = op_name.lower().replace("-", "").replace("_", "").strip()
                if op_clean in ["2opt", "twoopt"]:
                    ada_perbaikan = self.two_opt_terbaik(solusi)
                elif op_clean == "relocate":
                    ada_perbaikan = self.relocate_terbaik(solusi)
                elif op_clean == "swap":
                    ada_perbaikan = self.swap_terbaik(solusi)

                if ada_perbaikan:
                    op_terpakai = op_name
                    break

            t_now = datetime.now().strftime("%H:%M:%S")
            bks_s = str(nilai_optimal) if nilai_optimal > 0 else "-"

            if not ada_perbaikan:
                gap_akhir = f"+{((solusi.total_jarak - nilai_optimal) / nilai_optimal) * 100:.2f}%" if nilai_optimal > 0 else "-"
                if verbose:
                    print(f" [{t_now}] | {iterasi:^5} | {solusi.total_jarak:>7} | {'buntu':^7} | {'OPTIMUM':^10} | {bks_s:>7} | {gap_akhir:>14}")
                    print("-" * lebar)
                self.jumlah_iterasi = iterasi - 1
                break

            turun = jarak_sebelum - solusi.total_jarak
            self.riwayat.append(solusi.total_jarak)
            self.jumlah_iterasi = iterasi
            gap_cur = f"+{((solusi.total_jarak - nilai_optimal) / nilai_optimal) * 100:.2f}%" if nilai_optimal > 0 else "-"

            if verbose:
                print(f" [{t_now}] | {iterasi:^5} | {solusi.total_jarak:>7} | {turun:>7} | {op_terpakai:^10} | {bks_s:>7} | {gap_cur:>14}")

        solusi.buang_rute_kosong()
        return solusi

    def jalankan(self, solusi_awal: Solution, nilai_optimal: int = 0, verbose: bool = False) -> Solution:
        """Alias untuk metode run."""
        return self.run(solusi_awal, nilai_optimal=nilai_optimal, verbose=verbose)