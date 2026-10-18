"""
parameters.py — TAHAP 19 (KONFIGURASI ALNS CVRP & SAKELAR STUDI ABLASI)
===============================================================================
Pusat konfigurasi parameter eksperimen ALNS (Adaptive Large Neighborhood Search).
Seluruh parameter algoritma, instance, dan sakelar modular 4 modifikasi
dapat diatur di sini untuk keperluan studi ablasi dan analisis sensitivitas.
===============================================================================
"""


class Parameter:

    # ---- 1. Data Instance -----------------------------------------------
    FOLDER_INSTANCE = "X"
    NAMA_FILE = "X-n101-k25.vrp"
    NILAI_OPTIMAL = 27591               # BKS CVRPLIB

    # ---- 2. Heuristik Konstruksi Solusi Awal ----------------------------
    # Pilihan: "clarke_wright_savings" (direkomendasikan) atau "nearest_neighbor"
    METODE_KONSTRUKSI = "clarke_wright_savings"

    # ---- 3. Parameter ALNS Dasar (Optimum Hasil Response Surface Methodology) --
    SEED = 42                           # Seed utama untuk reproducibility 100%
    MAKS_ITERASI = 2000                 # Jumlah iterasi pencarian ALNS
    SUHU_AWAL = 800.0                   # T0 optimum global (RSM) untuk seluruh instance
    LAJU_PENDINGINAN = 0.990            # Cooling rate c optimum global (RSM)
    REACTION_FACTOR = 0.31              # Reaction factor r optimum global (RSM)
    PANJANG_SEGMEN = 100                # Frekuensi pembaruan bobot operator
    TAMPILKAN_SETIAP = 500              # Log progres per N iterasi (0 untuk silent)

    # Skor performa operator adaptif
    SIGMA1 = 33.0                       # Rekor global baru ditemukan
    SIGMA2 = 9.0                        # Solusi lebih baik dari solusi saat ini
    SIGMA3 = 13.0                       # Solusi diterima (meski lebih buruk)

    # ---- 4. SAKELAR MODULAR (STUDI ABLASI 4 MODIFIKASI) ------------------
    # Modifikasi 1: Operator Destroy Baru (Shaw Removal)
    PAKAI_SHAW = True

    # Modifikasi 2: Operator Repair Baru (Regret-3 Insertion)
    PAKAI_REGRET3 = True

    # Modifikasi 3: Intensifikasi Local Search (2-Opt, Relocate, Swap)
    PAKAI_LS = True
   # Alias kompatibilitas
    OPERATOR_LS = ["two_opt", "relocate", "swap"]
    MAKS_ITERASI_LS = 30

    # Modifikasi 4: Mekanisme Diversifikasi & Anti-Stagnasi
    # (Reheating Suhu SA + Restart ke Solusi Terbaik saat stagnan)
    PAKAI_REHEATING = True
    AMBANG_REHEAT = 200                 # Iterasi tanpa rekor sebelum reheating

    # Opsi Tambahan: Gangguan Acak Terkendali (Controlled Noise) pada Repair
    PAKAI_NOISE = False
    TINGKAT_NOISE = 0.1

    # Opsi Adaptasi Parameter Dinamis berbasis Ukuran Instance
    PAKAI_ADAPTIF = True
