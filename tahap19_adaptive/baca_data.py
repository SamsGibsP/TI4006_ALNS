"""
baca_data.py  —  TAHAP 4
===============================================================================
Membaca file instance .vrp dan mengubahnya menjadi banyak objek Node.

Di tahap ini kita pakai FUNGSI biasa dulu, belum kelas. Tujuannya supaya
terlihat jelas: kelas hanya dipakai kalau memang ada gunanya.
===============================================================================
"""

from node import Node


def baca_instance(path):
    """
    Membaca file .vrp.

    Mengembalikan TIGA hal sekaligus:
        daftar_node, kapasitas, jumlah_kendaraan
    """
    koordinat = {}          # nomor -> (x, y)
    permintaan = {}         # nomor -> demand
    kapasitas = 0
    jumlah_kendaraan = 0
    bagian = None           # penanda: sedang membaca bagian apa

    with open(path, "r") as f:
        for baris in f:
            baris = baris.strip()
            if not baris:
                continue

            # --- deteksi pergantian bagian ---------------------------
            if baris.startswith("NODE_COORD_SECTION"):
                bagian = "KOORDINAT"
                continue
            if baris.startswith("DEMAND_SECTION"):
                bagian = "DEMAND"
                continue
            if baris.startswith("DEPOT_SECTION"):
                bagian = None
                continue
            if baris.startswith("EOF"):
                break

            # --- bagian judul, bentuknya "KUNCI : NILAI" -------------
            if ":" in baris:
                kunci, nilai = baris.split(":", 1)
                kunci, nilai = kunci.strip(), nilai.strip()
                if kunci == "CAPACITY":
                    kapasitas = int(nilai)
                elif kunci == "NAME":
                    # nama file berbentuk A-n32-k5, huruf k menandakan
                    # jumlah kendaraan
                    jumlah_kendaraan = int(nilai.split("-k")[1])
                continue

            # --- isi bagian ------------------------------------------
            potongan = baris.split()
            if bagian == "KOORDINAT":
                nomor = int(potongan[0])
                koordinat[nomor] = (int(potongan[1]), int(potongan[2]))
            elif bagian == "DEMAND":
                nomor = int(potongan[0])
                permintaan[nomor] = int(potongan[1])

    # --- ubah menjadi objek Node ---------------------------------------
    daftar_node = []
    for nomor in sorted(koordinat):
        x, y = koordinat[nomor]
        daftar_node.append(Node(nomor, x, y, permintaan[nomor]))

    return daftar_node, kapasitas, jumlah_kendaraan
