"""
parameters.py  —  TAHAP 12
===============================================================================
Semua angka dan pilihan percobaan dikumpulkan di SATU tempat.

Alasannya sederhana: saat bereksperimen, yang berubah hanyalah isi file ini.
Kode algoritma tidak perlu disentuh sama sekali. Dengan begitu percobaan
mudah diulang, dan Anda tidak akan bingung "tadi settingannya apa ya?"

Ubah nilainya di sini, lalu jalankan main.py lagi.
===============================================================================
"""


class Parameter:

    # ---- data instance --------------------------------------------------
    FOLDER_INSTANCE = "A"
    NAMA_FILE = "A-n32-k5.vrp"
    NILAI_OPTIMAL = 784                 # dari literatur, sebagai pembanding

    # ---- cara menyusun solusi awal --------------------------------------
    # pilihan: "sequential"  atau  "nearest_neighbor"
    METODE_KONSTRUKSI = "nearest_neighbor"

    # ---- local search ---------------------------------------------------
    GUNAKAN_LOCAL_SEARCH = True

    # operator yang dipakai, sekaligus urutan pemakaiannya
    # pilihan: "relocate", "swap"
    OPERATOR = ["relocate", "swap"]

    MAKS_ITERASI = 100                  # pengaman agar tidak berputar selamanya
