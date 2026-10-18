"""
tuning.py  —  TAHAP 20
===============================================================================
PARAMETER TUNING dengan GRID SEARCH.

ALNS kita punya banyak parameter. Sampai sekarang nilainya kita tebak saja:

    suhu_awal          = 100
    laju_pendinginan   = 0.995
    reaction_factor    = 0.3
    panjang_segmen     = 100
    rho_min, rho_maks  = 4, 12

Dari mana angka-angka itu? Jujur saja: karangan. Tahap ini mencari
angka yang lebih baik secara sistematis.

GRID SEARCH artinya: buat daftar nilai yang ingin dicoba untuk tiap
parameter, lalu coba SEMUA kombinasinya.

    suhu_awal       : 3 pilihan
    laju_pendinginan: 3 pilihan
    reaction_factor : 3 pilihan
    ------------------------------- x
    total             27 kombinasi

Kelebihan : sederhana, menyeluruh, mudah dijelaskan di laporan
Kekurangan: jumlah kombinasi meledak. Menambah satu parameter dengan
            3 pilihan langsung mengalikan waktu dengan 3.

ATURAN PENTING: setiap kombinasi harus diuji dengan BEBERAPA SEED,
lalu dilihat RATA-RATANYA. Algoritma acak tidak boleh dinilai dari
satu kali jalan.
===============================================================================
"""

import itertools
import random
import time

from alns import ALNS


class GridSearch:
    """Mencari kombinasi parameter terbaik dengan mencoba semuanya."""

    def __init__(self, instance, solusi_awal,
                 maks_iterasi=1000, daftar_seed=(1, 2, 3)):
        self.instance = instance
        self.solusi_awal = solusi_awal
        self.maks_iterasi = maks_iterasi
        self.daftar_seed = daftar_seed
        self.hasil = []

    # =====================================================================
    def uji_satu_kombinasi(self, parameter):
        """
        Menjalankan ALNS beberapa kali dengan satu kombinasi parameter.
        Mengembalikan (rata_rata, terbaik, terburuk).
        """
        nilai = []
        for seed in self.daftar_seed:
            random.seed(seed)
            pencari = ALNS(self.instance,
                           maks_iterasi=self.maks_iterasi,
                           tampilkan_setiap=0,
                           **parameter)
            hasil = pencari.jalankan(self.solusi_awal)
            nilai.append(hasil.total_jarak)

        return (sum(nilai) / len(nilai), min(nilai), max(nilai))

    # =====================================================================
    def jalankan(self, kisi):
        """
        kisi : dictionary {nama_parameter: [daftar nilai yang dicoba]}

        Mencoba SEMUA kombinasi, mencatat hasilnya.
        """
        nama_parameter = list(kisi.keys())
        semua_nilai = [kisi[n] for n in nama_parameter]
        kombinasi = list(itertools.product(*semua_nilai))

        print(f"  Jumlah kombinasi : {len(kombinasi)}")
        print(f"  Seed per kombinasi: {len(self.daftar_seed)}")
        print(f"  Total percobaan  : "
              f"{len(kombinasi) * len(self.daftar_seed)}\n")

        self.hasil = []
        mulai = time.time()

        for ke, nilai in enumerate(kombinasi, start=1):
            parameter = dict(zip(nama_parameter, nilai))
            rata, terbaik, terburuk = self.uji_satu_kombinasi(parameter)

            self.hasil.append({
                "parameter": parameter,
                "rata": rata,
                "terbaik": terbaik,
                "terburuk": terburuk,
            })

            ringkas = ", ".join(f"{k}={v}" for k, v in parameter.items())
            print(f"  [{ke:>3}/{len(kombinasi)}] {ringkas:<58} "
                  f"rata {rata:>7.1f}")

        print(f"\n  Waktu total: {time.time() - mulai:.1f} detik")
        return self.hasil

    # =====================================================================
    def cetak_peringkat(self, berapa=10):
        """Menampilkan kombinasi terbaik, diurutkan berdasarkan rata-rata."""
        urut = sorted(self.hasil, key=lambda h: h["rata"])

        print("\n" + "=" * 78)
        print(f" {berapa} KOMBINASI TERBAIK (diurutkan dari rata-rata terkecil)")
        print("=" * 78)
        print(f"  {'#':>3} | {'Rata':>7} | {'Terbaik':>8} | {'Terburuk':>9} "
              f"| Parameter")
        print("  " + "-" * 74)

        for i, h in enumerate(urut[:berapa], start=1):
            ringkas = ", ".join(f"{k}={v}" for k, v in h["parameter"].items())
            print(f"  {i:>3} | {h['rata']:>7.1f} | {h['terbaik']:>8} | "
                  f"{h['terburuk']:>9} | {ringkas}")

        print("  " + "-" * 74)
        return urut[0]

    # =====================================================================
    def pengaruh_satu_parameter(self, nama):
        """
        Melihat pengaruh SATU parameter saja, dengan merata-ratakan
        seluruh kombinasi lain. Berguna untuk menjawab pertanyaan
        "sebenarnya parameter mana yang paling berpengaruh?"
        """
        kelompok = {}
        for h in self.hasil:
            nilai = h["parameter"][nama]
            kelompok.setdefault(nilai, []).append(h["rata"])

        print(f"\n  Pengaruh {nama}:")
        print(f"    {'Nilai':>10} | {'Rata-rata hasil':>16} | "
              f"{'Jumlah kombinasi':>17}")
        print("    " + "-" * 50)
        for nilai in sorted(kelompok):
            daftar = kelompok[nilai]
            print(f"    {str(nilai):>10} | {sum(daftar) / len(daftar):>16.1f} "
                  f"| {len(daftar):>17}")

    # =====================================================================
    def simpan_csv(self, path_csv):
        """Menyimpan seluruh hasil uji grid search ke format CSV."""
        import csv
        if not self.hasil:
            return
        param_names = list(self.hasil[0]["parameter"].keys())
        urut = sorted(self.hasil, key=lambda h: h["rata"])
        with open(path_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["peringkat", "rata_rata", "terbaik", "terburuk"] + param_names)
            for rank, item in enumerate(urut, start=1):
                p = item["parameter"]
                row = [rank, f"{item['rata']:.2f}", item["terbaik"], item["terburuk"]]
                row += [p[k] for k in param_names]
                writer.writerow(row)
        print(f"  [CSV] Hasil grid search tersimpan di: {path_csv}")


if __name__ == "__main__":
    import os
    import sys
    folder = os.path.dirname(os.path.abspath(__file__))
    if folder not in sys.path:
        sys.path.insert(0, folder)

    from baca_data import baca_instance
    from cvrp_instance import CVRPInstance
    from construction import ConstructionHeuristic

    path = os.path.join(folder, "X", "X-n101-k25.vrp")
    daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path)
    instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
    solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

    kisi = {
        "suhu_awal": [500.0, 1500.0, 3500.0],
        "laju_pendinginan": [0.990, 0.995, 0.998],
        "reaction_factor": [0.1, 0.3, 0.5],
    }

    tuner = GridSearch(instance, solusi_awal, maks_iterasi=500, daftar_seed=(1, 2, 3))
    tuner.jalankan(kisi)
    tuner.cetak_peringkat(berapa=10)

    for p in kisi:
        tuner.pengaruh_satu_parameter(p)

    dir_hasil_final = os.path.join(os.path.dirname(folder), "hasil_final")
    os.makedirs(dir_hasil_final, exist_ok=True)
    csv_out = os.path.join(dir_hasil_final, "hasil_grid_search.csv")
    tuner.simpan_csv(csv_out)

