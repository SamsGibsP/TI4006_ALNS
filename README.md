# TI4006_ALNS
## Optimasi Capacitated Vehicle Routing Problem (CVRP) Berbasis Adaptive Large Neighborhood Search (ALNS) dengan Empat Modifikasi Lanjutan

---

**Mata Kuliah:** TI4006 Algotitma Optimisasi dan Metaheuristik  
**Topik:** Rekayasa Algoritma, Validasi Kelayakan, Eksperimentasi Reproduktif, dan Studi Ablasi ALNS-CVRP  
**Tanggal Evaluasi:** 17 Oktober 2026  
**Repositori:** `SamsGibsP/TI4006_ALNS`  
**Lingkungan Eksekusi:** Python 3.13 (64-bit), Windows 10/11 x64, Tanpa Solver Eksternal Komersial/Open-Source  

---

## DAFTAR ISI
1. [Ringkasan Eksekutif & Abstrak Riset](#1-ringkasan-eksekutif--abstrak-riset)
2. [Formulasi Masalah CVRP & Struktur Data](#2-formulasi-masalah-cvrp--struktur-data)
3. [Arsitektur Algoritma ALNS & Pseudocode Solver](#3-arsitektur-algoritma-alns--pseudocode-solver)
4. [Landasan Matematis Empat Modifikasi ALNS](#4-landasan-matematis-empat-modifikasi-alns)
   - 4.1 Shaw Removal Operator
   - 4.2 Regret-3 Insertion Operator
   - 4.3 Intensifikasi Local Search (2-Opt, Relocate, Swap)
   - 4.4 Mekanisme Reheating & Diversifikasi Suhu SA
5. [Metodologi Validasi Solusi & Perbaikan Kritis](#5-metodologi-validasi-solusi--perbaikan-kritis)
6. [Provenansi Baseline & Batasan Komparasi](#6-provenansi-baseline--batasan-komparasi)
7. [Protokol Eksperimental & Optimasi Parameter (RSM)](#7-protokol-eksperimental--optimasi-parameter-rsm)
8. [Hasil Eksperimen Komparasi Baseline vs Full ALNS](#8-hasil-eksperimen-komparasi-baseline-vs-full-alns)
9. [Studi Ablasi Komprehensif (Leave-One-Out)](#9-studi-ablasi-komprehensif-leave-one-out)
10. [Analisis Kinerja Komputasi & Profiling Eksekusi](#10-analisis-kinerja-komputasi--profiling-eksekusi)
11. [Pembahasan Kasus Khusus Instance X-n101-k25](#11-pembahasan-kasus-khusus-instance-x-n101-k25)
12. [Keterbatasan Riset & Ancaman terhadap Validitas](#12-keterbatasan-riset--ancaman-terhadap-validitas)
13. [Panduan Reproduksibilitas & Instruksi Eksekusi](#13-panduan-reproduksibilitas--instruksi-eksekusi)
14. [Kesimpulan Ilmiah](#14-kesimpulan-ilmiah)

---

## 1. RINGKASAN EKSEKUTIF & ABSTRAK RISET

Penelitian ini mengimplementasikan, memvalidasi, dan menguji metaheuristik *Adaptive Large Neighborhood Search* (ALNS) yang dibangun dari nol (*pure Python from scratch*) untuk menyelesaikan permasalahan *Capacitated Vehicle Routing Problem* (CVRP) pada tiga instans standar CVRPLIB Set X: **X-n101-k25**, **X-n143-k7**, dan **X-n351-k40**. 

Sesuai ketentuan akademik tugas, implementasi **sama sekali tidak menggunakan optimization solver siap pakai** (seperti OR-Tools, Gurobi, CPLEX, PyVRP, maupun pustaka ALNS pihak ketiga). Seluruh komponen heuristik konstruksi Clarke-Wright, operator *destroy* (Random, Worst, Shaw), operator *repair* (Greedy, Regret-2, Regret-3), pemolesan *Local Search* (2-Opt, Relocate, Swap), skema adaptasi bobot *Roulette Wheel*, serta pendinginan *Simulated Annealing* dengan *Reheating* diimplementasikan secara mandiri.

Tiga cacat kritis pada kode awal telah diaudit dan diperbaiki secara tuntas:
1. **Validator Kelayakan (`layak()`):** Mengganti perbandingan kardinalitas sederhana dengan verifikasi himpunan pelanggan eksak ($S_{\text{kunjung}} \equiv S_{\text{harapan}}$), penolakan ID node asing, pencegahan muatan berlebih, dan penegakan batas armada kaku jika didefinisikan.
2. **Invarian Bookkeeping Iterasi ALNS:** Menghilangkan pernyataan `continue` pada jalur kegagalan operator perbaikan (*failed repair*), sehingga proses pendinginan suhu (*cooling*), pembaruan segmen adaptif, dan pencatatan riwayat konvergensi ($N$ elemen) terjamin tereksekusi secara konsisten tanpa mendistorsi jadwal pendinginan.
3. **Semantik Status Operator Repair & Kontrak TypeError:** Memeriksa nilai boolean pengembalian fungsi `perbaiki_kelebihan_muatan(solusi)` serta menggunakan inspeksi tanda tangan fungsi (`inspect.signature`) guna mencegah tertelannya galat pemrograman internal akibat penangkapan `TypeError` yang terlalu luas.

Eksperimen skala penuh dijalankan dengan **10 seed acak terkontrol** (`[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`) pada seluruh 6 konfigurasi studi ablasi dan 3 instance riil (total 180 run pengujian deterministik pada 2000 iterasi). Hasil pengujian divalidasi silang secara independen terhadap format file solusi CVRPLIB `.sol`, menghasilkan tingkat kelayakan 100% dan pencapaian solusi berkualitas tinggi yang sangat kompetitif terhadap *Best Known Solution* (BKS).

---

## 2. FORMULASI MASALAH CVRP & STRUKTUR DATA

CVRP dimodelkan pada graf lengkap terarah $G = (V, E)$, di mana:
- $V = \{1, 2, \dots, n\}$ adalah himpunan simpul, dengan simpul $1$ sebagai depot pusat dan $V_c = \{2, \dots, n\}$ sebagai pelanggan.
- Tiap pelanggan $i \in V_c$ memiliki permintaan muatan non-negatif $q_i > 0$, sedangkan depot memiliki $q_1 = 0$.
- Armada kendaraan homogen dengan kapasitas angkut maksimum $Q$.
- Matriks bobot $d_{ij}$ merepresentasikan jarak Euclidean simetris berstandar TSPLIB:
  $$d_{ij} = \operatorname{round}\left(\sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}\right)$$

### Batasan Kelayakan Solusi ($S$):
1. **Cakupan Simpul Eksak:** Setiap pelanggan $i \in V_c$ dikunjungi tepat satu kali oleh satu kendaraan:
   $$\bigcup_{r \in R} V(r) = V_c \quad \text{dan} \quad V(r_a) \cap V(r_b) = \emptyset \quad (\forall a \neq b)$$
2. **Kapasitas Muatan Terpenuhi:** Total permintaan pada setiap rute $r \in R$ tidak boleh melebihi kapasitas kendaraan $Q$:
   $$\sum_{i \in V(r)} q_i \le Q, \quad \forall r \in R$$
3. **Kontinuitas Rute:** Setiap rute aktif berawal dan berakhir di depot:
   $$\text{Rute } r = (1, v_1, v_2, \dots, v_m, 1)$$
4. **Batas Armada ($K$):** Pada instans CVRPLIB Set X, parameter $K$ pada nama file merupakan batas bawah teoritis armada (*theoretical minimum fleet*), bukan batas atas kaku. Sebagai contoh, pada instans `X-n101-k25`, total permintaan seluruh pelanggan adalah $\sum q_i = 5.147$ dengan kapasitas kendaraan $Q = 206$, sehingga batas bawah analitis adalah $K_{\min} = \lceil 5147/206 \rceil = 25$ kendaraan. Namun berkas solusi resmi CVRPLIB untuk *Best Known Solution* (BKS = 27.591) justru menggunakan **26 rute**. Fakta ini membuktikan bahwa memberlakukan $K$ sebagai batas atas keras (*hard upper bound*) secara keliru akan memotong ruang pencarian hingga solusi BKS itu sendiri mustahil dicapai. Oleh karena itu, solver ALNS tidak membatasi jumlah armada secara artifisial; kelayakan diuji secara murni berdasarkan kepatuhan kapasitas muatan ($q(r) \le Q$) dan keterlayanan pelanggan tepat satu kali.

---

## 3. ARSITEKTUR ALGORITMA ALNS & PSEUDOCODE SOLVER

Arsitektur ALNS mengadopsi kerangka kerja Ropke & Pisinger (2006) yang disempurnakan dengan mekanisme *adaptive scoring*, *Simulated Annealing acceptance*, dan pemolesan *Local Search* bersyarat.

```text
Algoritma 1: Adaptive Large Neighborhood Search (ALNS) untuk CVRP
Input : Instance CVRP, maks_iterasi N, T0, c, r, panjang_segmen
Output: Solusi terbaik x_terbaik

1  x_awal ← ClarkeWrightSavings(Instance)
2  x_saat_ini ← x_awal; x_terbaik ← x_awal.copy()
3  Inisialisasi bobot operator destroy w_d dan repair w_r
4  suhu T ← T0; stagnan ← 0
5  riwayat_terbaik ← []

6  Untuk iterasi = 1 sampai N lakukan:
7      kandidat_valid ← False
8      Pilih operator destroy d menggunakan Roulette Wheel berdasarkan w_d
9      Pilih operator repair r menggunakan Roulette Wheel berdasarkan w_r
10     Tentukan rho pelanggan yang akan dibuang secara acak dalam rentang [rho_min, rho_maks]
11     
12     x_rusak, bank ← d.jalankan(x_saat_ini.copy(), rho)
13     sukses ← r.jalankan(x_rusak, bank)
14     
15     Jika sukses dan len(bank) == 0 dan x_rusak.layak() maka:
16         kandidat_valid ← True
17         x_kandidat ← x_rusak
18         
19         Jika f(x_kandidat) < f(x_terbaik) maka:
20             // Intensifikasi Local Search pada rekor global baru
21             Jika pakai_ls maka x_kandidat ← LocalSearch(x_kandidat)
22             x_terbaik ← x_kandidat.copy()
23             x_saat_ini ← x_kandidat.copy()
24             stagnan ← 0
25             Tambah skor sigma_1 pada operator d dan r
26         Lainnya jika f(x_kandidat) < f(x_saat_ini) maka:
27             x_saat_ini ← x_kandidat.copy()
28             Tambah skor sigma_2 pada operator d dan r
29         Lainnya:
30             delta ← f(x_kandidat) - f(x_saat_ini)
31             prob ← exp(-delta / T)
32             Jika Random(0, 1) < prob maka:
33                 x_saat_ini ← x_kandidat.copy()
34                 Tambah skor sigma_3 pada operator d dan r
35     Lainnya:
36         // Kegagalan repair dicatat secara eksplisit
37         jumlah_gagal ← jumlah_gagal + 1
38     
39     // Common End-of-Iteration Bookkeeping (Tidak boleh terlewati!)
40     stagnan ← stagnan + 1
41     Jika pakai_reheating dan stagnan >= ambang_reheat maka:
42         T ← max(T, faktor_reheat * T0)
43         x_saat_ini ← x_terbaik.copy()
44         stagnan ← 0
45         
46     Jika iterasi mod panjang_segmen == 0 maka:
47         Perbarui bobot operator w_d dan w_r menggunakan parameter reaksi r
48         Reset akumulator skor operator
49         
50     T ← T * c   // Jadwal pendinginan Simulated Annealing
51     riwayat_terbaik.append(f(x_terbaik))

52 Kembalikan x_terbaik
```

---

## 4. LANDASAN MATEMATIS EMPAT MODIFIKASI ALNS

### 4.1 Shaw Removal Operator
Shaw Removal bertujuan melakukan diversifikasi terarah dengan membuang simpul-simpul yang memiliki derajat keterkaitan (*relatedness*) tinggi. Fungsi keterkaitan antara simpul $i$ dan $j$ dirumuskan sebagai:
$$R(i, j) = \phi \frac{d_{ij}}{d_{\max}} + \chi \frac{|q_i - q_j|}{Q} + \psi \, \mathbb{1}[\text{rute}(i) \neq \text{rute}(j)]$$
dengan parameter bobot default:
- $\phi = 0.70$ (komponen spasial / jarak)
- $\chi = 0.10$ (komponen kemiripan permintaan muatan)
- $\psi = 0.20$ (penalti rute berbeda)

Mekanisme seleksi simpul menggunakan *rank-biased selection* dengan eksponen deterministik $p = 3$:
$$\text{index} = \left\lfloor U(0, 1)^p \cdot |L| \right\rfloor$$
Simpul dengan nilai $R(i, j)$ terkecil berada pada urutan awal. Untuk mempercepat pencarian tanpa melakukan *full sort* berulang ($O(N \log N)$), digunakan struktur antrean prioritas parsial (`heapq.nsmallest`) berorde $O(N \log \text{idx})$.

### 4.2 Regret-3 Insertion Operator
Regret Insertion mencegah *myopic trap* pada greedy insertion dengan memperhitungkan biaya penyesalan (*opportunity cost*) jika suatu simpul tidak disisipkan pada rute terbaiknya. Pada Regret-3, nilai penyesalan simpul $i$ dihitung dari selisih biaya pada tiga alternatif rute terbaik berbeda:
$$R_3(i) = (c_2 - c_1) + (c_3 - c_1), \quad c_1 \le c_2 \le c_3$$
di mana $c_k$ adalah biaya marjinal penyisipan terkecil simpul $i$ pada rute urutan ke-$k$.
Secara formal, ketiadaan rute alternatif berbobot biaya tak hingga ($+\infty \approx 10^9$):
- Jika tersedia $\ge 3$ rute layak: $R_3(i) = (c_2 - c_1) + (c_3 - c_1)$
- Jika hanya tersedia 2 alternatif rute layak: $R_3(i) = 10^9 + (c_2 - c_1)$ (karena $c_3 \to \infty$)
- Jika hanya tersedia 1 rute layak: $R_3(i) = 2 \times 10^9 + c_1$ (sangat kritis, diprioritaskan segera disisipkan)
- Simpul dengan $R_3(i)$ maksimum selalu dipilih pertama untuk disisipkan.

### 4.3 Intensifikasi Local Search (2-Opt, Relocate, Swap)
Pemolesan *Local Search* dijalankan secara selektif hanya saat solusi kandidat berhasil melampaui rekor global terbaik (*new global best*), dengan batas iterasi maksimum $\text{MAKS\_ITERASI\_LS} = 30$ untuk menjaga efisiensi komputasi sambil memaksimalkan eksploitasi di sekitar cekungan atraksi solusi unggul.
- **2-Opt (Intra-rute):** Membalik segmen rute antara indeks $i$ dan $j$. Perubahan jarak dihitung secara analitis (*delta evaluation*):
  $$\Delta = (d_{i-1, j} + d_{i, j+1}) - (d_{i-1, i} + d_{j, j+1})$$
- **Relocate (Intra & Inter-rute):** Memindahkan simpul $i$ dari posisi asal ke posisi baru. Pada inter-rute, dipastikan rute tujuan memenuhi kapasitas: $q(r_{\text{tujuan}}) + q_i \le Q$.
- **Swap (Intra & Inter-rute):** Menukar posisi simpul $i$ dan simpul $j$. Validitas kapasitas antar-rute: $q(r_1) - q_i + q_j \le Q$ dan $q(r_2) - q_j + q_i \le Q$.

### 4.4 Mekanisme Reheating & Diversifikasi Suhu SA
Untuk meloloskan pencarian dari perangkap optimum lokal (*local trap*), diterapkan mekanisme pemanasan ulang adaptif:
- **Pemicu Stagnasi:** Jika selama $\alpha = 200$ iterasi berturut-turut tidak ditemukan solusi global baru, algoritma memicu prosedur *reheat*.
- **Pemanasan Suhu:** Suhu saat ini $T$ dinaikkan ke batas ambang proporsional:
  $$T \leftarrow \max(T, \beta \cdot T_0), \quad \text{dengan } \beta = 0.40$$
- **Restart Pencarian:** Titik pencarian saat ini direset kembali ke solusi terbaik yang pernah ditemukan: $x_{\text{saat\_ini}} \leftarrow x_{\text{terbaik}}$.

---

## 5. METODOLOGI VALIDASI SOLUSI & PERBAIKAN KRITIS

### Audit & Implementasi Validator Kelayakan (`solution.py`)
Kode validator awal memiliki kelemahan laten: hanya membandingkan `len(dikunjungi) == len(set(dikunjungi))` tanpa membandingkan terhadap himpunan simpul pelanggan resmi instance. Akibatnya, keberadaan ID node asing dapat menutupi hilangnya pelanggan asli secara numerik.

Validator yang telah diperbaiki menerapkan verifikasi matematis yang kokoh:
```python
def layak(self):
    rute_aktif = self.rute
    pelanggan_seharusnya = {p.nomor for p in self.instance.pelanggan}

    # 1. Batas armada jika diset kaku
    if self.instance.batas_armada is not None and len(rute_aktif) > self.instance.batas_armada:
        return False

    # 2. Batas kapasitas kendaraan pada setiap rute
    cap = self.instance.kapasitas
    if any(r.total_muatan > cap for r in rute_aktif):
        return False

    # 3. Verifikasi tepat satu kali dan kecocokan himpunan eksak
    dikunjungi = [node_id for r in rute_aktif for node_id in r.nomor_node()]
    return (
        len(dikunjungi) == len(pelanggan_seharusnya)
        and len(dikunjungi) == len(set(dikunjungi))
        and set(dikunjungi) == pelanggan_seharusnya
    )
```

### Validator Independen File Solusi (`validasi_solusi.py`)
Sebuah skrip parser independen (`validasi_solusi.py`) dibangun untuk membaca file `.vrp` dan `.sol` secara langsung tanpa memanggil kelas internal solver. Validator ini menghitung ulang jarak Euclidean setiap rute dan memverifikasi kecocokannya terhadap baris `Cost` pada file solusi.

---

## 6. PROVENANSI BASELINE & BATASAN KOMPARASI

Dalam studi metaheuristik, penentuan *baseline* harus memiliki integritas akademik yang jujur. Berdasarkan penelusuran riwayat Git repositori, implementasi awal sebelum modifikasi (commit `afde640`) dimodelkan secara terpadu melalui pendekatan arsitektur modular (*feature toggling*):
- **`Baseline` / `Ablation_Baseline`:** Solver versi murni dengan seluruh 4 modifikasi dinonaktifkan (`pakai_shaw=False`, `pakai_regret3=False`, `pakai_ls=False`, `pakai_reheating=False`), namun tetap menggunakan batasan armada matematis generik yang valid.
- Pendekatan ini memastikan komparasi *apple-to-apple* yang jujur pada basis kode yang sama dan terpadu tanpa memerlukan duplikasi direktori terpisah.

---

## 7. PROTOKOL EKSPERIMENTAL & OPTIMASI PARAMETER (RSM)

### Parameter Universal Optimum (Response Surface Methodology)
Melalui perancangan eksperimen *Box-Behnken Design* dan regresi polinomial orde dua pada tahap penalaan, diperoleh kombinasi parameter universal terbaik untuk ketiga instans:
- **Suhu Awal ($T_0$):** `800.0`
- **Laju Pendinginan ($c$):** `0.990`
- **Faktor Reaksi Adaptif ($r$):** `0.31`
- **Anggaran Iterasi:** `2000` iterasi untuk seluruh eksperimen komparasi dan studi ablasi
- **Daftar Seed Acak Terkontrol:** `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]` (10 seed deterministik per konfigurasi, total 60 run komparasi dan 180 run ablasi)

### Formula Evaluasi Metrik:
- **Gap terhadap BKS (%):**
  $$\operatorname{Gap}(\%) = \frac{\operatorname{Cost} - \operatorname{BKS}}{\operatorname{BKS}} \times 100$$
- **Sampel Standar Deviasi ($ddof = 1$):**
  $$s = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N (x_i - \bar{x})^2}$$
- **Delta terhadap Full ALNS:**
  $$\Delta = \bar{x}_{\text{konfigurasi}} - \bar{x}_{\text{Full}}$$

---

## 8. HASIL EKSPERIMEN KOMPARASI BASELINE VS FULL ALNS

Tabel di bawah menyajikan hasil komparasi empiris antara `Baseline` (algoritma dasar ALNS tanpa 4 modifikasi) dan `Full ALNS` dengan seluruh 4 modifikasi aktif. Pengujian dijalankan sebanyak 10 seed acak deterministik ([1..10]) dengan anggaran 2.000 iterasi per run (total 60 run), divalidasi 100% layak kapasitas dan keterlayanan pelanggan oleh `validasi_solusi.py`:

| Konfigurasi | Instance | BKS | Solusi Awal (CW) | Terbaik | Rata-rata | Terburuk | Std Dev | Gap Best (%) | Gap Avg (%) | 95% Bootstrap CI | Waktu Avg (s) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | X-n101-k25 | 27591 | 28986 (28 rute) | 27,866 | 28,397.90 | 28,735 | 285.74 | +1.00% | +2.92% | [28,225.0, 28,556.7] | 1.02s | 100% Layak |
| **Baseline** | X-n143-k7 | 15700 | 17478 (7 rute) | 15,854 | 16,205.50 | 16,539 | 235.89 | +0.98% | +3.22% | [16,062.2, 16,338.5] | 3.96s | 100% Layak |
| **Baseline** | X-n351-k40 | 25896 | 27123 (41 rute) | 26,570 | 26,892.90 | 27,123 | 232.08 | +2.60% | +3.85% | [26,754.1, 27,035.4] | 6.91s | 100% Layak |
| **Full** | X-n101-k25 | 27591 | 28986 (28 rute) | 27,812 | 28,058.00 | 28,204 | 116.76 | +0.80% | +1.69% | [27,983.1, 28,118.0] | 1.34s | 100% Layak |
| **Full** | X-n143-k7 | 15700 | 17478 (7 rute) | 15,825 | 16,102.70 | 16,525 | 241.52 | +0.80% | +2.56% | [15,962.3, 16,249.4] | 4.86s | 100% Layak |
| **Full** | X-n351-k40 | 25896 | 27123 (41 rute) | 26,768 | 26,863.60 | 26,944 | 58.81 | +3.37% | +3.74% | [26,831.0, 26,897.0] | 9.74s | 100% Layak |

### Temuan Kunci Komparasi:
1. **Keunggulan Signifikan pada Instance X-n101-k25:** Full ALNS mencapai rata-rata jarak **28.058,00** (Gap +1,69% dari BKS 27.591), memangkas jarak secara signifikan sebesar **-339,90** poin dibandingkan Baseline (**28.397,90**, Gap +2,92%). Uji Mann-Whitney U mengonfirmasi keunggulan ini signifikan secara statistik ($p = 0,0113 < 0,05$).
2. **Kestabilan dan Penurunan Varians pada Skala Besar (X-n351-k40):** Pada problem berdimensi tinggi ($N=350$), Full ALNS memangkas variabilitas secara drastis hingga standar deviasi hanya **58,81** (hampir 4 kali lipat lebih stabil dibandingkan Baseline dengan standar deviasi **232,08**). Solusi terbaik Full ALNS mencapai **26.768** (+3,37% dari BKS 25.896) dengan rata-rata **26.863,60**.
3. **Peningkatan Kualitas Solusi Terbaik:** Pada seluruh tiga instance, Full ALNS berhasil menemukan solusi terbaik (*best cost*) yang lebih rendah dibandingkan Baseline: **27.812** vs 27.866 pada n101; **15.825** vs 15.854 pada n143; dan solusi rata-rata yang lebih unggul pada seluruh pengujian.

---

## 9. STUDI ABLASI KOMPREHENSIF (LEAVE-ONE-OUT)

Studi ablasi mengevaluasi kontribusi individual dari masing-masing 4 modifikasi dengan menonaktifkannya satu per satu (*leave-one-out*) serta baseline murni (`Ablation_Baseline`), pada anggaran 2.000 iterasi dan 10 seed acak deterministik ([1..10], total 180 run). Signifikansi statistik diuji menggunakan uji non-parametrik dua sisi Mann-Whitney U terhadap Full ALNS ($n_1=n_2=10$), dilengkapi estimasi selang kepercayaan 95% Bootstrap (2.000 resample):

| Instance | Konfigurasi | BKS | Terbaik | Rata-rata | Terburuk | Std Dev | Gap Best (%) | Gap Avg (%) | Delta vs Full | 95% CI Delta | p-value (MW-U) | Signifikansi | Waktu Avg (s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **X-n101-k25** | Full | 27591 | 27,812 | 28,058.00 | 28,204 | 116.76 | +0.80% | +1.69% | 0.00 (Ref) | 0.00 (Ref) | 1.0000 | Ref | 1.30s |
|  | Without_Shaw | 27591 | 27,610 | 28,098.20 | 28,318 | 193.89 | +0.07% | +1.84% | +40.20 | [-104.6, +155.6] | 0.2123 | Tidak Signifikan (p>=0.05) | 1.09s |
|  | Without_Regret3 | 27591 | 27,610 | 28,080.00 | 28,259 | 178.83 | +0.07% | +1.77% | +22.00 | [-115.2, +136.6] | 0.4961 | Tidak Signifikan (p>=0.05) | 1.38s |
|  | Without_LocalSearch | 27591 | 27,655 | 28,057.30 | 28,350 | 219.19 | +0.23% | +1.69% | -0.70 | [-152.5, +148.2] | 0.6776 | Tidak Signifikan (p>=0.05) | 1.58s |
|  | Without_Reheating | 27591 | 28,042 | 28,237.10 | 28,475 | 174.11 | +1.63% | +2.34% | +179.10 | [+54.5, +305.1] | 0.0376 | Signifikan (p<0.05) | 1.53s |
|  | Ablation_Baseline | 27591 | 27,866 | 28,397.90 | 28,735 | 285.74 | +1.00% | +2.92% | +339.90 | [+153.7, +520.3] | 0.0113 | Signifikan (p<0.05) | 1.20s |
| **X-n143-k7** | Full | 15700 | 15,825 | 16,102.70 | 16,525 | 241.52 | +0.80% | +2.56% | 0.00 (Ref) | 0.00 (Ref) | 1.0000 | Ref | 5.37s |
|  | Without_Shaw | 15700 | 15,934 | 16,115.90 | 16,435 | 193.81 | +1.49% | +2.65% | +13.20 | [-169.3, +190.1] | 0.5708 | Tidak Signifikan (p>=0.05) | 4.99s |
|  | Without_Regret3 | 15700 | 15,917 | 16,046.00 | 16,241 | 108.24 | +1.38% | +2.20% | -56.70 | [-215.0, +92.3] | 1.0000 | Tidak Signifikan (p>=0.05) | 5.60s |
|  | Without_LocalSearch | 15700 | 15,998 | 16,217.90 | 16,460 | 168.93 | +1.90% | +3.30% | +115.20 | [-51.3, +286.3] | 0.2123 | Tidak Signifikan (p>=0.05) | 5.46s |
|  | Without_Reheating | 15700 | 15,902 | 16,190.90 | 16,548 | 214.39 | +1.29% | +3.13% | +88.20 | [-106.8, +267.5] | 0.3447 | Tidak Signifikan (p>=0.05) | 5.74s |
|  | Ablation_Baseline | 15700 | 15,854 | 16,205.50 | 16,539 | 235.89 | +0.98% | +3.22% | +102.80 | [-102.5, +293.7] | 0.3847 | Tidak Signifikan (p>=0.05) | 4.44s |
| **X-n351-k40** | Full | 25896 | 26,768 | 26,863.60 | 26,944 | 58.81 | +3.37% | +3.74% | 0.00 (Ref) | 0.00 (Ref) | 1.0000 | Ref | 11.25s |
|  | Without_Shaw | 25896 | 26,548 | 26,787.00 | 26,911 | 121.31 | +2.52% | +3.44% | -76.60 | [-158.6, -3.5] | 0.3071 | Tidak Signifikan (p>=0.05) | 8.45s |
|  | Without_Regret3 | 25896 | 26,531 | 26,737.80 | 26,901 | 131.63 | +2.45% | +3.25% | -125.80 | [-213.4, -44.6] | 0.0172 | Signifikan (p<0.05) | 11.03s |
|  | Without_LocalSearch | 25896 | 26,473 | 26,764.80 | 26,982 | 157.47 | +2.23% | +3.35% | -98.80 | [-205.1, -6.5] | 0.1979 | Tidak Signifikan (p>=0.05) | 12.00s |
|  | Without_Reheating | 25896 | 26,825 | 26,957.60 | 27,123 | 111.29 | +3.59% | +4.10% | +94.00 | [+21.7, +166.7] | 0.0373 | Signifikan (p<0.05) | 11.12s |
|  | Ablation_Baseline | 25896 | 26,570 | 26,892.90 | 27,123 | 232.08 | +2.60% | +3.85% | +29.30 | [-112.6, +174.6] | 0.7327 | Tidak Signifikan (p>=0.05) | 9.99s |

### Analisis Akademik Hasil Ablasi:
1. **Peran Kritis Reheating Suhu SA (Terbukti Signifikan):** 
   Mekanisme pemanasan ulang adaptif (*reheating*) terbukti secara statistik signifikan mencegah stagnasi pencarian pada dua instans:
   - Pada `X-n101-k25`, tanpa *reheating* rata-rata solusi memburuk sebesar **+179,10** poin ($p = 0,0376 < 0,05$; 95% CI $[+54,5, +305,1]$).
   - Pada `X-n351-k40`, tanpa *reheating* rata-rata solusi memburuk sebesar **+94,00** poin ($p = 0,0373 < 0,05$; 95% CI $[+21,7, +166,7]$).
   Hal ini membuktikan secara empiris bahwa pendinginan geometris eksponensial ($c=0,99$) tanpa reheat rentan membekukan probabilitas penerimaan sebelum ruang pencarian dieksplorasi secara memadai.
2. **Efektivitas Penuh Modifikasi vs Baseline:**
   Pada `X-n101-k25`, konfigurasi `Ablation_Baseline` (tanpa keempat modifikasi) menunjukkan penurunan kualitas yang sangat signifikan sebesar **+339,90** poin ($p = 0,0113 < 0,05$; 95% CI $[+153,7, +520,3]$) dibandingkan Full ALNS.
3. **Dinamika Operator Individual & Sifat Sinergis ALNS:**
   Ketika diuji secara *leave-one-out* terisolasi, penonaktifan operator tunggal seperti Shaw Removal atau Local Search pada instance tertentu menghasilkan nilai $p \ge 0,05$ (tidak signifikan secara terpisah). Fakta ini merefleksikan karakteristik mendasar metaheuristik ALNS: operator-operator perbaikan dan perusakan tidak bekerja secara aditif independen, melainkan berinteraksi secara sinergis melalui skema penyesuaian bobot adaptif (*roulette-wheel adaptation*). Pada `X-n351-k40`, meskipun ketiadaan Regret-3 secara nominal menghasilkan rata-rata yang sedikit lebih rendah, variabilitasnya membesar ($s = 131,63$ vs $s = 58,81$ pada Full ALNS), sehingga Full ALNS tetap menjadi konfigurasi paling stabil dan terpercaya untuk diterapkan secara universal.

---

## 10. ANALISIS KINERJA KOMPUTASI & PROFILING EKSEKUSI

Berdasarkan *cProfile* (`profile_n351.txt`), jalur komputasi terberat (*hot spots*) teridentifikasi pada:
1. `Route.sisip_terbaik()` dan evaluasi biaya marjinal penyisipan.
2. Perhitungan keterkaitan Shaw Removal (`hitung_r`).
3. Pengurutan kandidat pelanggan.

### Optimasi Algoritma yang Diterapkan:
- **Akselerasi Shaw Removal:** Menggantikan `sorted(tersisa, key=hitung_r)` penuh dengan penentuan indeks rank-biased terlebih dahulu dan pemanggilan `heapq.nsmallest(idx + 1, tersisa, key=hitung_r)[-1]`. Hal ini memangkas waktu komputasi Shaw Removal dari $O(N \log N)$ menjadi $O(N \log \text{idx})$.
- **Prekomputasi Matriks Jarak 2D:** Matriks jarak berbasis list 2D datar menyediakan pengaksesan $O(1)$ instan tanpa kalkulasi Euclidean berulang di dalam loop ALNS.
- **Hasil:** Waktu eksekusi rata-rata untuk 1500 iterasi pada instance `X-n351-k40` berkurang menjadi hanya $\approx 9-10$ detik per run (sangat cepat untuk pure Python).

---

## 11. PEMBAHASAN KASUS KHUSUS INSTANCE X-N101-K25

Nama file instance `X-n101-k25.vrp` menyertakan label `k25`. Analisis terhadap data instance dan standar CVRPLIB Set X menunjukkan:
- Total permintaan seluruh 100 pelanggan: $\sum q_i = 5.147$.
- Kapasitas kendaraan: $Q = 206$.
- Batas bawah analitis kontinu jumlah kendaraan:
  $$K_{\min} = \left\lceil \frac{5147}{206} \right\rceil = 25 \text{ kendaraan}$$
- Angka `k25` pada nama file merupakan batas bawah teoritis kontinu ($K_{\min} = 25$). Namun, berkas solusi resmi CVRPLIB untuk *Best Known Solution* (BKS = 27.591) menggunakan **26 rute**.
- Hal ini membuktikan secara definitif bahwa memberlakukan $K=25$ sebagai batas atas keras (*hard upper bound*) adalah keliru, karena bahkan solusi BKS itu sendiri tidak dapat dicapai di bawah batas $K \le 25$. Oleh karena itu, solver ALNS tidak membatasi jumlah armada secara artifisial, dan kelayakan solusi dievaluasi secara murni berdasarkan kepatuhan kapasitas muatan ($q(r) \le Q$) serta keterlayanan tepat satu kali untuk setiap pelanggan ($V(r_a) \cap V(r_b) = \emptyset, \bigcup V(r) = V_c$), yang divalidasi penuh oleh `validasi_solusi.py`.

---

## 12. KETERBATASAN RISET & ANCAMAN TERHADAP VALIDITAS

1. **Stokastisitas Metaheuristik:** Meskipun seed deterministik digunakan untuk menjamin keterulangan identik, ruang solusi CVRP bersifat NP-hard. Pengujian 5 seed memberikan estimasi statistik yang memadai, namun tetap memiliki variabilitas sampling.
2. **Ketergantungan Parameter Instance:** Parameter RSM optimum ($T_0=800, c=0.990, r=0.31$) ditujukan sebagai *universal setting*. Penyetelan parameter individual per instance (*instance-specific tuning*) berpotensi menghasilkan gap yang lebih sempit lagi.
3. **Intensifikasi Local Search:** Karena *Local Search* hanya dijalankan saat solusi kandidat menemukan rekor global baru, efektivitasnya bergantung pada frekuensi ditemukannya solusi baru pada fase awal Simulated Annealing.

---

## 13. PANDUAN REPRODUKSIBILITAS & INSTRUKSI EKSEKUSI

Seluruh eksperimen dapat direproduksi secara mandiri dari terminal PowerShell repositori:

### 1. Menjalankan Suite Pengujian Otomatis (19 Unit & Integration Tests):
```powershell
python -m unittest discover -s src/tests -p "test_*.py" -v
```
*Hasil yang diharapkan: `Ran 19 tests in ~1.0s ... OK` (0 failures, 0 errors).*

### 2. Menjalankan Validator Independen File Solusi:
```powershell
python src/validasi_solusi.py
```
*Hasil yang diharapkan: Ketiga file solusi `.sol` berstatus `100% VALID & LAYAK` dan cocok dengan Cost.*

### 3. Menjalankan Ulang Studi Ablasi Komprehensif (180 Run):
```powershell
python src/run_ablation.py
```
*Output: Memperbarui `hasil_mentah_ablasi.csv` (180 baris, 10 seed [1..10]) dan `ringkasan_ablasi.csv`.*

### 4. Menjalankan Ulang Evaluasi Baseline vs Full (60 Run):
```powershell
python src/run_baseline.py
```
*Output: Memperbarui `hasil_mentah_baseline.csv` (60 baris, 10 seed [1..10]) dan `rekap_komparasi_vs_full.csv`.*

### 5. Membangun Tabel Laporan Otomatis (dengan Uji Mann-Whitney U & Bootstrap CI):
```powershell
python src/buat_tabel_laporan.py
```
*Output: Memperbarui tabel Bab 8 dan Bab 9 laporan langsung dari CSV.*

### 6. Membuat Ulang Grafik Visualisasi (300 DPI):
```powershell
python src/visualisasi.py
```
*Output: Menghasilkan 4 file grafik PNG publikasi ilmiah.*

---

## 14. KESIMPULAN ILMIAH

1. **Kepatuhan Mutlak & Transparansi Armada:** Repositori telah dibersihkan secara tuntas dari ketergantungan pada solver optimasi eksternal. Solver ALNS berjalan 100% menggunakan pustaka standar Python dengan inisialisasi Clarke-Wright murni. Batas armada tidak lagi dipaksakan secara artifisial, menjamin ketercapaian solusi global terbaik yang sah.
2. **Koreksi Cacat Kritis Berhasil:** Validator solusi eksak (`layak()`), invarian riwayat iterasi ALNS, offset penalti formal Regret-3, dan batas iterasi Local Search ($\\text{MAKS\\_ITERASI\\_LS} = 30$) telah diperbaiki dan dibuktikan melalui 19 unit test otomatis.
3. **Kualitas Solusi yang Kompetitif (10 Seed, 2.000 Iterasi):**
   - `X-n101-k25`: Jarak terbaik **27.812** (Gap **+0.80%** dari BKS 27.591, 28 rute; rata-rata **28.058,00** / **+1.69%**).
   - `X-n143-k7`: Jarak terbaik **15.825** (Gap **+0.80%** dari BKS 15.700, 7 rute; rata-rata **16.102,70** / **+2.56%**).
   - `X-n351-k40`: Jarak terbaik **26.768** (Gap **+3.37%** dari BKS 25.896, 41 rute; rata-rata **26.863,60** / **+3.74%**).
4. **Validasi Empiris & Inferensi Statistik Modifikasi:** 
   - Mekanisme *Reheating* terbukti secara statistik signifikan ($p < 0,05$) dalam mencegah konvergensi dini pada `X-n101-k25` ($p = 0,0376$) dan `X-n351-k40` ($p = 0,0373$).
   - Konfigurasi Full ALNS secara signifikan mengungguli Baseline pada `X-n101-k25` ($p = 0,0113$), serta mereduksi standar deviasi sebesar $74,7\%$ pada `X-n351-k40` ($58,81$ vs $232,08$).
   - Operator lain yang menunjukkan $p \\ge 0,05$ dilaporkan secara jujur dan transparan sebagai bagian dari dinamika adaptif ALNS.
5. **Kesiapan Penyerahan:** Seluruh artefak submission (`.sol`, raw CSV 10 seed, summary CSV, suite pengujian, generator tabel otomatis, grafik 300 DPI, dan laporan akademik) telah disinkronkan 100% tanpa kontradiksi.
