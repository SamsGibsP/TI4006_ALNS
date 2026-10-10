"""alns.py — TAHAP 19 (TEROPTIMASI & TERVALIDASI)

===============================================================================
Perbaikan Penting:
  - Validasi kelayakan ketat: x_terbaik HANYA diperbarui bila kandidat LAYAK
    (semua pelanggan terlayani, kapasitas terpenuhi, armada <= K).
  - Mencegah solusi kosong/cacat berjarak 0 dijadikan solusi terbaik.
===============================================================================
"""

import math
import random

from destroy import DestroyOperator
from repair import RepairOperator


class ALNS:
    """ADAPTIVE Large Neighborhood Search untuk CVRP."""

    def __init__(
        self,
        instance,
        maks_iterasi=1000,
        rho_min=4,
        rho_maks=12,
        suhu_awal=5000.0,
        laju_pendinginan=0.995,
        sigma1=33.0,
        sigma2=9.0,
        sigma3=13.0,
        reaction_factor=0.3,
        panjang_segmen=100,
        tampilkan_setiap=100,
    ):
        self.instance = instance
        self.maks_iterasi = maks_iterasi
        self.rho_min = rho_min
        self.rho_maks = rho_maks

        # --- parameter simulated annealing ------------------------------
        self.suhu_awal = suhu_awal
        self.laju_pendinginan = laju_pendinginan
        self.suhu = suhu_awal

        # --- parameter adaptif -------------------------------------------
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.sigma3 = sigma3
        self.reaction_factor = reaction_factor
        self.panjang_segmen = panjang_segmen

        self.tampilkan_setiap = tampilkan_setiap

        self.perusak = DestroyOperator(instance)
        self.pembaik = RepairOperator(instance)

        # --- bobot operator ----------------------------------------------
        self.bobot_destroy = {n: 1.0 for n in DestroyOperator.DAFTAR}
        self.bobot_repair = {n: 1.0 for n in RepairOperator.DAFTAR}

        self.pemakaian = {
            n: 0 for n in DestroyOperator.DAFTAR + RepairOperator.DAFTAR
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

    @staticmethod
    def tanda_solusi(solusi):
        return tuple(sorted(tuple(r.nomor_node()) for r in solusi.daftar_rute))

    def reset_segmen(self):
        semua = DestroyOperator.DAFTAR + RepairOperator.DAFTAR
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
        if jarak_baru < jarak_sekarang:
            self.jumlah_lebih_baik += 1
            return True

        if jarak_baru == jarak_sekarang:
            self.jumlah_sama += 1
            return True

        selisih = jarak_baru - jarak_sekarang
        peluang = math.exp(-selisih / max(self.suhu, 1e-6))

        if random.random() < peluang:
            self.jumlah_lebih_buruk += 1
            return True
        return False

    def jalankan(self, solusi_awal):
        """Menjalankan ALNS."""
        x = solusi_awal.copy()
        x.siapkan_armada()

        x_terbaik = solusi_awal.copy()
        x_terbaik.buang_rute_kosong()
        x_terbaik.hitung_ulang()

        # SUHU AWAL ADAPTIF (5% dari jarak solusi awal)
        # Menjamin Simulated Annealing bisa eksplorasi di instance besar
        self.suhu_awal = max(self.suhu_awal, 0.05 * x.total_jarak)
        self.suhu = self.suhu_awal

        self.reset_segmen()
        self.pernah_dikunjungi = {self.tanda_solusi(x)}

        if self.tampilkan_setiap:
            print(f"  Iterasi     0 | sekarang {x.total_jarak:>5} "
                  f"| terbaik {x_terbaik.total_jarak:>5} | mulai")

        for iterasi in range(1, self.maks_iterasi + 1):
            nama_d = self.putar_roda(self.bobot_destroy)
            nama_r = self.putar_roda(self.bobot_repair)
            rho = random.randint(self.rho_min, self.rho_maks)

            self.pemakaian[nama_d] += 1
            self.pemakaian[nama_r] += 1
            self.percobaan[nama_d] += 1
            self.percobaan[nama_r] += 1

            kandidat = x.copy()
            bank = self.perusak.jalankan(nama_d, kandidat, rho)
            berhasil = self.pembaik.jalankan(nama_r, kandidat, bank)

            # Buang iterasi jika gagal atau ada pelanggan yang hilang
            if not berhasil or len(kandidat.nomor_pelanggan()) != len(self.instance.pelanggan):
                self.jumlah_gagal += 1
                continue

            tanda = self.tanda_solusi(kandidat)
            baru = tanda not in self.pernah_dikunjungi
            self.pernah_dikunjungi.add(tanda)

            diterima = self.terima(x.total_jarak, kandidat.total_jarak)
            lebih_baik = kandidat.total_jarak < x.total_jarak

            # Evaluasi kelayakan berbasis rute terisi (non-kosong)
            temp_kandidat = kandidat.copy()
            temp_kandidat.buang_rute_kosong()
            is_layak = temp_kandidat.layak()

            if is_layak and temp_kandidat.total_jarak < x_terbaik.total_jarak and baru:
                self.beri_skor(nama_d, nama_r, self.sigma1)
            elif lebih_baik and diterima and baru:
                self.beri_skor(nama_d, nama_r, self.sigma2)
            elif diterima and baru:
                self.beri_skor(nama_d, nama_r, self.sigma3)

            if diterima and is_layak:
                x = kandidat
                self.jumlah_diterima += 1

            # Rekor baru dievaluasi dari kandidat yang telah bersih
            if kandidat.total_jarak < x_terbaik.total_jarak:
                temp = kandidat.copy()
                temp.buang_rute_kosong()
                if temp.layak() and temp.total_jarak < x_terbaik.total_jarak:
                    x_terbaik = temp
                    self.iterasi_rekor = iterasi
                    if self.tampilkan_setiap:
                        print(
                            f"  Iterasi {iterasi:>5} | sekarang {x.total_jarak:>5} "
                            f"| terbaik {x_terbaik.total_jarak:>5} | REKOR BARU "
                            f"({nama_d[:6]}+{nama_r[:6]})"
                        )

            if iterasi % self.panjang_segmen == 0:
                self.perbarui_bobot()
                self.riwayat_bobot.append(
                    (iterasi, dict(self.bobot_destroy), dict(self.bobot_repair)))
                self.reset_segmen()

            self.suhu = self.suhu * self.laju_pendinginan
            self.riwayat_terbaik.append(x_terbaik.total_jarak)

            if self.tampilkan_setiap and iterasi % self.tampilkan_setiap == 0:
                print(f"  Iterasi {iterasi:>5} | sekarang {x.total_jarak:>5} "
                      f"| terbaik {x_terbaik.total_jarak:>5} | suhu {self.suhu:>7.2f}")

        x_terbaik.buang_rute_kosong()
        x_terbaik.hitung_ulang()
        return x_terbaik
        