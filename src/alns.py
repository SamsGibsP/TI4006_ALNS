"""
alns.py — TAHAP 19 (TEROPTIMASI, TERVALIDASI, & TERINTEGRASI LOCAL SEARCH)
"""

import math
import random

from destroy import DestroyOperator
from local_search import LocalSearch
from repair import RepairOperator


def hitung_parameter_adaptif(instance, maks_iterasi, jarak_awal):
    """Menghitung parameter dinamis berdasarkan ukuran instance (Langkah 3)."""
    n = len(instance.pelanggan)
    K = max(1, instance.jumlah_kendaraan)
    avg_len = n / K

    # rho berkisar 8% s.d. 28% dari total pelanggan
    rho_min = max(8, round(0.08 * n))
    rho_maks = min(
        round(0.28 * n),
        max(rho_min + 8, round(3.5 * avg_len)),
        60,
    )
    if rho_maks <= rho_min:
        rho_maks = rho_min + 4

    panjang_segmen = max(50, maks_iterasi // 200)

    delta = 0.05 * jarak_awal
    T0 = -delta / math.log(0.5)

    T_end = 1.0
    c = (T_end / max(T0, 1e-6)) ** (1.0 / max(1, maks_iterasi))

    ambang_reheat = max(200, int(0.02 * maks_iterasi))

    return {
        "rho_min": rho_min,
        "rho_maks": rho_maks,
        "panjang_segmen": panjang_segmen,
        "suhu_awal": T0,
        "laju_pendinginan": c,
        "ambang_reheat": ambang_reheat,
    }


class ALNS:
    """Adaptive Large Neighborhood Search untuk CVRP."""

    def __init__(
        self,
        instance,
        maks_iterasi=1000,
        rho_min=None,
        rho_maks=None,
        suhu_awal=None,
        laju_pendinginan=None,
        sigma1=33.0,
        sigma2=9.0,
        sigma3=13.0,
        reaction_factor=0.3,
        panjang_segmen=None,
        ambang_reheat=None,
        faktor_reheat=0.4,
        tampilkan_setiap=100,
        mode_random_search=False,
        pakai_ls=True,
        pakai_shaw=True,
        pakai_reheating=True,
        pakai_regret3=True,
        pakai_noise=False,
        tingkat_noise=0.1,
        pakai_adaptif=True,
    ):
        """
        Adaptive Large Neighborhood Search untuk CVRP.

        Parameter:
            ambang_reheat (int, optional): Jumlah iterasi tanpa rekor sebelum reheating
                dipicu. Jika None dan pakai_adaptif=True, menggunakan nilai adaptif.
            faktor_reheat (float): Fraksi dari suhu awal (T0) saat pemanasan kembali
                (default 0.4, yaitu T = max(T, faktor_reheat * T0)).
        """
        self.instance = instance
        self.maks_iterasi = maks_iterasi
        self.rho_min = rho_min
        self.rho_maks = rho_maks

        # Parameter simulated annealing
        self.suhu_awal = suhu_awal
        self.laju_pendinginan = laju_pendinginan
        self.suhu = suhu_awal

        # Parameter adaptif
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.sigma3 = sigma3
        self.reaction_factor = reaction_factor
        self.panjang_segmen = panjang_segmen
        self.ambang_reheat = ambang_reheat
        self.faktor_reheat = faktor_reheat
        self.pakai_adaptif = pakai_adaptif

        self.tampilkan_setiap = tampilkan_setiap
        self.mode_random_search = mode_random_search

        # Sakelar studi ablasi (4 Modifikasi ALNS)
        self.pakai_ls = pakai_ls
        self.pakai_shaw = pakai_shaw
        self.pakai_reheating = pakai_reheating
        self.pakai_regret3 = pakai_regret3
        self.pakai_noise = pakai_noise
        self.tingkat_noise = tingkat_noise
        self.jumlah_panggil_ls = 0


        self.perusak = DestroyOperator(instance)
        self.pembaik = RepairOperator(instance)
        self.local_search = LocalSearch(
            instance, operators=["two_opt", "relocate", "swap"], max_iterations=30
        )

        # Tentukan daftar operator aktif berdasarkan sakelar ablasi
        self.daftar_destroy = ["random_removal", "worst_removal"]
        if self.pakai_shaw:
            self.daftar_destroy.append("shaw_removal")

        self.daftar_repair = ["greedy_insertion", "regret2_insertion"]
        if self.pakai_regret3:
            self.daftar_repair.append("regret3_insertion")

        # Bobot operator
        self.bobot_destroy = {n: 1.0 for n in self.daftar_destroy}
        self.bobot_repair = {n: 1.0 for n in self.daftar_repair}

        self.pemakaian = {
            n: 0 for n in self.daftar_destroy + self.daftar_repair
        }

        self.skor = {}
        self.percobaan = {}
        self.reset_segmen()


        self.pernah_dikunjungi = set()
        self.riwayat_bobot = []
        self.riwayat_terbaik = []
        self.jumlah_diterima = 0
        self.jumlah_gagal = 0
        self.jumlah_lebih_baik = 0
        self.jumlah_sama = 0
        self.jumlah_lebih_buruk = 0
        self.iterasi_rekor = 0
        self.x_terbaik = None

    @staticmethod
    def tanda_solusi(solusi):
        return tuple(
            sorted(
                tuple(r.nomor_node())
                for r in solusi.daftar_rute
                if not r.kosong()
            )
        )

    def reset_segmen(self):
        semua = self.daftar_destroy + self.daftar_repair
        self.skor = {n: 0.0 for n in semua}
        self.percobaan = {n: 0 for n in semua}

    def perbarui_bobot(self):
        for bobot in (self.bobot_destroy, self.bobot_repair):
            for nama in bobot:
                theta = self.percobaan[nama]
                if theta == 0:
                    continue
                rata_skor = self.skor[nama] / theta
                bobot[nama] = (
                    bobot[nama] * (1 - self.reaction_factor)
                    + self.reaction_factor * rata_skor
                )
                bobot[nama] = max(bobot[nama], 0.01)

    def beri_skor(self, nama_d, nama_r, nilai):
        self.skor[nama_d] += nilai
        self.skor[nama_r] += nilai

    @staticmethod
    def putar_roda(bobot):
        total = sum(bobot.values())
        titik = random.random() * total

        batas = 0.0
        for nama, w in bobot.items():
            batas += w
            if titik <= batas:
                return nama
        return list(bobot)[-1]

    def terima(self, jarak_sekarang, jarak_baru):
        if self.mode_random_search:
            # Random Walk: peluang terima acak seragam
            diterima = random.random() < 0.5
            if diterima:
                self.jumlah_diterima += 1
            return diterima

        if jarak_baru < jarak_sekarang:
            self.jumlah_lebih_baik += 1
            return True

        if jarak_baru == jarak_sekarang:
            self.jumlah_sama += 1
            return True

        selisih = jarak_baru - jarak_sekarang
        suhu_efektif = self.suhu if self.suhu is not None else 1.0
        peluang = math.exp(-selisih / max(suhu_efektif, 1e-6))

        if random.random() < peluang:
            self.jumlah_lebih_buruk += 1
            return True

        return False

    def jalankan(self, solusi_awal):
        x = solusi_awal.copy()
        x.siapkan_armada()

        self.x_terbaik = solusi_awal.copy()
        self.x_terbaik.buang_rute_kosong()
        self.x_terbaik.hitung_ulang()

        self.riwayat_terbaik = []
        self.riwayat_bobot = []
        self.jumlah_gagal = 0
        self.jumlah_diterima = 0
        self.jumlah_lebih_baik = 0
        self.jumlah_sama = 0
        self.jumlah_lebih_buruk = 0

        if self.pakai_adaptif:
            p_adp = hitung_parameter_adaptif(
                self.instance, self.maks_iterasi, x.total_jarak
            )
            if self.rho_min is None:
                self.rho_min = p_adp["rho_min"]
            if self.rho_maks is None:
                self.rho_maks = p_adp["rho_maks"]
            if self.panjang_segmen is None:
                self.panjang_segmen = p_adp["panjang_segmen"]
            if self.suhu_awal is None:
                self.suhu_awal = p_adp["suhu_awal"]
            if self.laju_pendinginan is None:
                self.laju_pendinginan = p_adp["laju_pendinginan"]
            if self.ambang_reheat is None:
                self.ambang_reheat = p_adp["ambang_reheat"]
            self.suhu = self.suhu_awal
            if self.tampilkan_setiap:
                print(
                    f"  [PARAM ADAPTIF] rho=[{self.rho_min}, {self.rho_maks}] | "
                    f"segmen={self.panjang_segmen} | T0={self.suhu_awal:.2f} | "
                    f"c={self.laju_pendinginan:.6f} | reheat={self.ambang_reheat}"
                )
        else:
            if self.rho_min is None:
                self.rho_min = 4
            if self.rho_maks is None:
                self.rho_maks = 12
            if self.panjang_segmen is None:
                self.panjang_segmen = 100
            if self.suhu_awal is None:
                self.suhu_awal = 100.0
            if self.laju_pendinginan is None:
                self.laju_pendinginan = 0.995
            if self.ambang_reheat is None:
                self.ambang_reheat = 200
            if not self.mode_random_search:
                self.suhu_awal = max(self.suhu_awal, 0.05 * x.total_jarak)
            self.suhu = self.suhu_awal

        self.reset_segmen()
        self.pernah_dikunjungi = {self.tanda_solusi(x)}
        iter_tanpa_rekor = 0
        self.jumlah_panggil_ls = 0

        if self.tampilkan_setiap:
            print(
                f"  Iterasi     0 | sekarang {x.total_jarak:>5} "
                f"| terbaik {self.x_terbaik.total_jarak:>5} | mulai"
            )

        for iterasi in range(1, self.maks_iterasi + 1):
            iter_tanpa_rekor += 1
            nama_d = self.putar_roda(self.bobot_destroy)
            nama_r = self.putar_roda(self.bobot_repair)
            rho = random.randint(self.rho_min, self.rho_maks)

            self.pemakaian[nama_d] += 1
            self.pemakaian[nama_r] += 1
            self.percobaan[nama_d] += 1
            self.percobaan[nama_r] += 1

            kandidat = x.copy()
            bank = self.perusak.jalankan(nama_d, kandidat, rho)
            berhasil = self.pembaik.jalankan(
                nama_r,
                kandidat,
                bank,
                pakai_noise=self.pakai_noise,
                tingkat_noise=self.tingkat_noise,
            )

            kandidat_valid = False
            if berhasil and len(kandidat.nomor_pelanggan()) == len(self.instance.pelanggan):
                kandidat.buang_rute_kosong()
                kandidat.hitung_ulang()
                if kandidat.layak():
                    kandidat_valid = True

            if not kandidat_valid:
                # Rollback: kandidat tidak layak / repair gagal diabaikan, kembali ke x
                self.jumlah_gagal += 1
            else:
                is_layak = True
                tanda = self.tanda_solusi(kandidat)
                baru = tanda not in self.pernah_dikunjungi
                self.pernah_dikunjungi.add(tanda)

                diterima = self.terima(x.total_jarak, kandidat.total_jarak)
                lebih_baik = kandidat.total_jarak < x.total_jarak

                if (
                    is_layak
                    and kandidat.total_jarak < self.x_terbaik.total_jarak
                    and baru
                ):
                    self.beri_skor(nama_d, nama_r, self.sigma1)
                elif lebih_baik and diterima and baru:
                    self.beri_skor(nama_d, nama_r, self.sigma2)
                elif diterima and baru:
                    self.beri_skor(nama_d, nama_r, self.sigma3)

                if diterima and is_layak:
                    x = kandidat
                    self.jumlah_diterima += 1

                # Pembaruan rekor dan pemolesan Local Search
                # Wajib memanggil kandidat.layak() terlebih dahulu agar solusi tidak layak
                # tidak pernah dipoles oleh Local Search atau disimpan sebagai x_terbaik.
                if is_layak and kandidat.total_jarak < self.x_terbaik.total_jarak:
                    calon_terbaik = kandidat.copy()
                    calon_terbaik.buang_rute_kosong()
                    calon_terbaik.hitung_ulang()

                    if self.pakai_ls:
                        self.jumlah_panggil_ls += 1
                        calon_terbaik = self.local_search.run(
                            calon_terbaik, verbose=False
                        )

                    if (
                        calon_terbaik.layak()
                        and calon_terbaik.total_jarak < self.x_terbaik.total_jarak
                    ):
                        self.x_terbaik = calon_terbaik
                        self.iterasi_rekor = iterasi
                        iter_tanpa_rekor = 0
                        x = self.x_terbaik.copy()
                        x.siapkan_armada()

                        if self.tampilkan_setiap:
                            print(
                                f"  Iterasi {iterasi:>5} | sekarang {x.total_jarak:>5} "
                                f"| terbaik {self.x_terbaik.total_jarak:>5} | REKOR BARU "
                                f"({nama_d[:6]}+{nama_r[:6]})"
                            )

            # Reheating mechanism saat stagnasi
            if (
                self.pakai_reheating
                and not self.mode_random_search
                and iter_tanpa_rekor >= self.ambang_reheat
            ):
                self.suhu = max(self.suhu, self.faktor_reheat * self.suhu_awal)
                x = self.x_terbaik.copy()
                x.siapkan_armada()
                iter_tanpa_rekor = 0
                if self.tampilkan_setiap:
                    print(
                        f"  Iterasi {iterasi:>5} | [REHEATING] Suhu dihangatkan "
                        f"kembali ke {self.suhu:.2f} & restart ke solusi terbaik"
                    )

            if iterasi % self.panjang_segmen == 0:
                self.perbarui_bobot()
                self.riwayat_bobot.append(
                    (iterasi, dict(self.bobot_destroy), dict(self.bobot_repair))
                )
                self.reset_segmen()

            if not self.mode_random_search:
                self.suhu = self.suhu * self.laju_pendinginan

            self.riwayat_terbaik.append(self.x_terbaik.total_jarak)

            if self.tampilkan_setiap and iterasi % self.tampilkan_setiap == 0:
                print(
                    f"  Iterasi {iterasi:>5} | sekarang {x.total_jarak:>5} "
                    f"| terbaik {self.x_terbaik.total_jarak:>5} | suhu {self.suhu:>7.2f}"
                )


        if self.tampilkan_setiap and self.pakai_ls:
            print(f"  [LOCAL SEARCH] Pemoles rekor dipanggil {self.jumlah_panggil_ls} kali")

        self.x_terbaik.buang_rute_kosong()
        self.x_terbaik.hitung_ulang()
        return self.x_terbaik