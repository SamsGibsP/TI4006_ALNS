"""
alns.py  —  TAHAP 19  (ALNS LENGKAP: bobot menyesuaikan diri)
===============================================================================
Sekarang kita gabungkan destroy dan repair ke dalam satu perulangan.

PSEUDOCODE LNS (M6):

    1  x  <- buildSolution()
    2  x* <- x
    3  SELAMA kriteria berhenti belum tercapai :
    4      x'  <- d(x)                    (destroy)
    5      x'' <- r(x')                   (repair)
    6      JIKA acceptanceDecision(x, x'') :
    7          x <- x''
    8      JIKA z(x) < z(x*) :
    9          x* <- x
    10 KEMBALIKAN x*

BARU DI TAHAP 17 — acceptanceDecision memakai SIMULATED ANNEALING (M6):

    JIKA f(S') < f(S) :
        S <- S'
        JIKA f(S) < f(S*) :  S* <- S
    SELAIN ITU :
        JIKA rand(0,1) < exp( -(f(S') - f(S)) / T ) :  S <- S'

    T mulai dari T0, lalu setiap iterasi:  T <- T * alpha,  0 < alpha < 1

Makin kecil T, makin kecil peluang menerima solusi yang lebih buruk.
Jadi di awal pencarian ALNS berani menjelajah, di akhir ia makin memilih.

BARU DI TAHAP 18 — operator tidak lagi dipilih acak rata, melainkan lewat
ROULETTE WHEEL. Tiap operator punya BOBOT w. Peluang terpilihnya:

        p_i = w_i / jumlah semua w

Bayangkan papan roda putar: operator berbobot besar mendapat juring yang
lebih lebar, jadi lebih sering kena.

BARU DI TAHAP 19 — inilah huruf "A" pada ALNS: bobot MENYESUAIKAN DIRI.

SKOR (Ropke dan Pisinger 2006, dipakai di M6):
    sigma1 = 33  solusi baru menjadi REKOR GLOBAL baru
    sigma2 =  9  lebih baik dari solusi sekarang, belum pernah dikunjungi
    sigma3 = 13  lebih buruk tapi DITERIMA, belum pernah dikunjungi
    (bila solusi sudah pernah dikunjungi: skor 0)

Perhatikan sigma3 > sigma2. Ini disengaja: operator yang membawa
pencarian ke wilayah BARU dihargai lebih tinggi daripada yang sekadar
memperbaiki sedikit.

PEMBARUAN BOBOT, dilakukan setiap akhir SEGMEN (M6):

    w[i, j+1] = w[i, j] * (1 - r) + r * (pi_i / theta_i)

    r       : reaction factor, 0 <= r <= 1
    pi_i    : total skor operator i selama segmen terakhir
    theta_i : berapa kali operator i dipakai selama segmen terakhir

    r = 0  -> bobot tidak pernah berubah (kembali ke Tahap 18)
    r = 1  -> bobot lama dilupakan sama sekali, hanya segmen terakhir
===============================================================================
"""

import math
import random

from destroy import DestroyOperator
from repair import RepairOperator


class ALNS:
    """ADAPTIVE Large Neighborhood Search untuk CVRP."""

    def __init__(self, instance, maks_iterasi=1000,
                 rho_min=4, rho_maks=12,
                 suhu_awal=100.0, laju_pendinginan=0.995,
                 sigma1=33.0, sigma2=9.0, sigma3=13.0,
                 reaction_factor=0.3, panjang_segmen=100,
                 tampilkan_setiap=100):
        self.instance = instance
        self.maks_iterasi = maks_iterasi
        self.rho_min = rho_min            # batas bawah jumlah yang dikeluarkan
        self.rho_maks = rho_maks          # batas atas

        # --- parameter simulated annealing (BARU di Tahap 17) ------------
        self.suhu_awal = suhu_awal              # T0
        self.laju_pendinginan = laju_pendinginan  # alpha
        self.suhu = suhu_awal                   # T saat ini

        # --- parameter adaptif (BARU di Tahap 19) ------------------------
        self.sigma1 = sigma1                    # rekor global baru
        self.sigma2 = sigma2                    # lebih baik dari sekarang
        self.sigma3 = sigma3                    # lebih buruk tapi diterima
        self.reaction_factor = reaction_factor  # r
        self.panjang_segmen = panjang_segmen

        self.tampilkan_setiap = tampilkan_setiap

        self.perusak = DestroyOperator(instance)
        self.pembaik = RepairOperator(instance)

        # --- bobot operator (BARU di Tahap 18) ---------------------------
        # Pada M6 ditulis rho- untuk destroy dan rho+ untuk repair.
        # Keduanya dimulai dari 1, artinya semua operator sama rata.
        self.bobot_destroy = {n: 1.0 for n in DestroyOperator.DAFTAR}
        self.bobot_repair = {n: 1.0 for n in RepairOperator.DAFTAR}

        # berapa kali tiap operator dipakai, untuk analisis
        self.pemakaian = {n: 0 for n in
                          DestroyOperator.DAFTAR + RepairOperator.DAFTAR}

        # --- untuk pembaruan bobot (BARU di Tahap 19) --------------------
        self.skor = {}        # pi  : skor terkumpul selama segmen ini
        self.percobaan = {}   # theta: berapa kali dipakai selama segmen ini
        self.reset_segmen()

        # catatan solusi yang pernah dikunjungi, agar tahu mana yang "baru"
        self.pernah_dikunjungi = set()

        # riwayat bobot, untuk digambar grafiknya
        self.riwayat_bobot = []

        # catatan untuk analisis
        self.riwayat_terbaik = []
        self.jumlah_diterima = 0
        self.jumlah_gagal = 0
        # dipecah menjadi tiga agar tidak rancu:
        self.jumlah_lebih_baik = 0      # f(S') < f(S)
        self.jumlah_sama = 0            # f(S') = f(S)  (langkah menyamping)
        self.jumlah_lebih_buruk = 0     # f(S') > f(S)  tapi tetap diterima
        self.iterasi_rekor = 0

    # =====================================================================
    @staticmethod
    def tanda_solusi(solusi):
        """
        Sidik jari sebuah solusi: urutan pelanggan di tiap rute.

        Dipakai untuk menjawab "apakah solusi ini pernah dikunjungi?".
        JANGAN memakai total jarak sebagai penanda karena dua solusi yang
        sama sekali berbeda bisa saja kebetulan berjarak sama, sehingga
        solusi baru akan dikira lama dan tidak pernah diberi skor.
        """
        return tuple(sorted(tuple(r.nomor_node()) for r in solusi.daftar_rute))

    # =====================================================================
    # PEMBARUAN BOBOT (BARU DI TAHAP 19)
    # =====================================================================
    def reset_segmen(self):
        """Mengosongkan skor dan hitungan percobaan di awal tiap segmen."""
        semua = DestroyOperator.DAFTAR + RepairOperator.DAFTAR
        self.skor = {n: 0.0 for n in semua}
        self.percobaan = {n: 0 for n in semua}

    def perbarui_bobot(self):
        """
        Menerapkan rumus M6 pada setiap operator:

            w_baru = w_lama * (1 - r) + r * (pi / theta)

        Operator yang tidak pernah dipakai pada segmen ini (theta = 0)
        bobotnya dibiarkan apa adanya — tidak ada bukti baru tentang dia.
        """
        for bobot in (self.bobot_destroy, self.bobot_repair):
            for nama in bobot:
                theta = self.percobaan[nama]
                if theta == 0:
                    continue
                rata_skor = self.skor[nama] / theta
                bobot[nama] = (bobot[nama] * (1 - self.reaction_factor)
                               + self.reaction_factor * rata_skor)
                bobot[nama] = max(bobot[nama], 0.01)   # jangan sampai nol

    def beri_skor(self, nama_d, nama_r, nilai):
        """Menambahkan skor ke pasangan operator yang baru saja dipakai."""
        self.skor[nama_d] += nilai
        self.skor[nama_r] += nilai

    # =====================================================================
    # LANGKAH 5 : MEMILIH OPERATOR DENGAN ROULETTE WHEEL
    # =====================================================================
    @staticmethod
    def putar_roda(bobot):
        """
        Memilih satu operator secara acak, dengan peluang sebanding bobotnya.

            p_i = w_i / jumlah semua w

        Cara kerjanya: bayangkan semua bobot dideretkan pada satu garis.
        Lempar satu titik acak di sepanjang garis itu, lihat jatuh di
        bagian siapa.
        """
        total = sum(bobot.values())
        titik = random.random() * total

        batas = 0.0
        for nama, w in bobot.items():
            batas += w
            if titik <= batas:
                return nama
        return list(bobot)[-1]       # jaga-jaga terhadap galat pembulatan

    # =====================================================================
    # LANGKAH 6 : KEPUTUSAN PENERIMAAN
    # =====================================================================
    def terima(self, jarak_sekarang, jarak_baru):
        """
        SIMULATED ANNEALING (M6, Ropke dan Pisinger 2006).

        Lebih baik  -> SELALU diterima.
        Lebih buruk -> diterima dengan peluang  exp( -selisih / T ).

        Makin besar selisihnya, makin kecil peluangnya.
        Makin kecil T, makin kecil pula peluangnya.
        """
        # --- lebih baik: selalu diterima --------------------------------
        if jarak_baru < jarak_sekarang:
            self.jumlah_lebih_baik += 1
            return True

        # --- sama persis: selisih 0, jadi exp(0) = 1, selalu diterima ----
        #
        # PERHATIAN. Kasus ini mudah terlewat. Solusi yang jaraknya SAMA
        # bukan "lebih baik", jadi ia masuk ke rumus di bawah. Dan karena
        # selisihnya nol, peluangnya exp(0) = 1 alias selalu diterima.
        #
        # Jadi langkah menyamping SELALU diterima, berapa pun suhunya.
        # Ini perilaku baku simulated annealing, bukan kesalahan — tetapi
        # harus dihitung terpisah, jangan dicampur dengan "lebih buruk".
        if jarak_baru == jarak_sekarang:
            self.jumlah_sama += 1
            return True

        # --- lebih buruk: diterima dengan peluang exp(-selisih / T) ------
        selisih = jarak_baru - jarak_sekarang
        peluang = math.exp(-selisih / self.suhu)

        if random.random() < peluang:
            self.jumlah_lebih_buruk += 1
            return True
        return False

    # =====================================================================
    # ALGORITMA UTAMA
    # =====================================================================
    def jalankan(self, solusi_awal):
        """Menjalankan LNS. Mengembalikan solusi terbaik yang ditemukan."""

        # langkah 1-2
        x = solusi_awal.copy()
        x.siapkan_armada()
        x_terbaik = x.copy()
        self.suhu = self.suhu_awal
        self.reset_segmen()
        self.pernah_dikunjungi = {self.tanda_solusi(x)}

        if self.tampilkan_setiap:
            print(f"  Iterasi     0 | sekarang {x.total_jarak:>5} "
                  f"| terbaik {x_terbaik.total_jarak:>5} | mulai")

        # langkah 3
        for iterasi in range(1, self.maks_iterasi + 1):

            # langkah 5 : pilih operator lewat roulette wheel
            nama_d = self.putar_roda(self.bobot_destroy)
            nama_r = self.putar_roda(self.bobot_repair)
            rho = random.randint(self.rho_min, self.rho_maks)

            self.pemakaian[nama_d] += 1
            self.pemakaian[nama_r] += 1
            self.percobaan[nama_d] += 1        # theta
            self.percobaan[nama_r] += 1

            # langkah 4 : destroy
            kandidat = x.copy()
            bank = self.perusak.jalankan(nama_d, kandidat, rho)

            # langkah 5 : repair
            berhasil = self.pembaik.jalankan(nama_r, kandidat, bank)
            if not berhasil:
                # ada pelanggan yang tidak muat di mana pun -> buang iterasi ini
                self.jumlah_gagal += 1
                continue

            # --- tentukan skor sesuai aturan M6 --------------------------
            tanda = self.tanda_solusi(kandidat)
            baru = tanda not in self.pernah_dikunjungi
            self.pernah_dikunjungi.add(tanda)

            # langkah 6-7 : keputusan penerimaan
            diterima = self.terima(x.total_jarak, kandidat.total_jarak)
            lebih_baik = kandidat.total_jarak < x.total_jarak

            if kandidat.total_jarak < x_terbaik.total_jarak and baru:
                self.beri_skor(nama_d, nama_r, self.sigma1)    # rekor global
            elif lebih_baik and diterima and baru:
                self.beri_skor(nama_d, nama_r, self.sigma2)    # lebih baik
            elif diterima and baru:
                self.beri_skor(nama_d, nama_r, self.sigma3)    # diterima
            # solusi yang sudah pernah dikunjungi: tidak diberi skor

            if diterima:
                x = kandidat
                self.jumlah_diterima += 1

            # langkah 8-9 : catat bila ini rekor baru
            if x.total_jarak < x_terbaik.total_jarak:
                x_terbaik = x.copy()
                self.iterasi_rekor = iterasi
                if self.tampilkan_setiap:
                    print(f"  Iterasi {iterasi:>5} | sekarang "
                          f"{x.total_jarak:>5} | terbaik "
                          f"{x_terbaik.total_jarak:>5} | REKOR BARU "
                          f"({nama_d[:6]}+{nama_r[:6]})")

            # --- akhir segmen: perbarui bobot (BARU di Tahap 19) ---------
            if iterasi % self.panjang_segmen == 0:
                self.perbarui_bobot()
                self.riwayat_bobot.append(
                    (iterasi, dict(self.bobot_destroy), dict(self.bobot_repair)))
                self.reset_segmen()

            # --- dinginkan suhu (BARU di Tahap 17) -----------------------
            self.suhu = self.suhu * self.laju_pendinginan

            self.riwayat_terbaik.append(x_terbaik.total_jarak)

            if (self.tampilkan_setiap
                    and iterasi % self.tampilkan_setiap == 0):
                print(f"  Iterasi {iterasi:>5} | sekarang {x.total_jarak:>5} "
                      f"| terbaik {x_terbaik.total_jarak:>5} "
                      f"| suhu {self.suhu:>7.2f}")

        # langkah 10
        x_terbaik.buang_rute_kosong()
        return x_terbaik
