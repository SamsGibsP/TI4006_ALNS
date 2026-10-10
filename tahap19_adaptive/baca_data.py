"""baca_data.py — TAHAP 4 (DIPERBAIKI)

Membaca file instance .vrp (kompatibel penuh dengan Set A dan Set X).
"""

import os
import re
from node import Node


def baca_instance(path):
  """Membaca file .vrp.

  Mengembalikan TIGA hal: daftar_node, kapasitas, jumlah_kendaraan
  """
  koordinat = {}
  permintaan = {}
  kapasitas = 0
  jumlah_kendaraan = 0
  bagian = None

  # Ambil cadangan nilai k langsung dari nama file jika di header bermasalah
  nama_file = os.path.basename(path)
  match_k_file = re.search(r"-k(\d+)", nama_file)
  if match_k_file:
    jumlah_kendaraan = int(match_k_file.group(1))

  with open(path, "r", encoding="utf-8", errors="ignore") as f:
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

      # --- bagian header/judul ---------------------------------
      if ":" in baris and bagian is None:
        kunci, nilai = baris.split(":", 1)
        kunci = kunci.strip()
        nilai = nilai.strip()

        if kunci == "CAPACITY":
          kapasitas = int(re.findall(r"\d+", nilai)[0])
        elif kunci == "NAME":
          match_k = re.search(r"-k(\d+)", nilai)
          if match_k:
            jumlah_kendaraan = int(match_k.group(1))
        continue

      # --- isi data numerik ------------------------------------
      potongan = baris.split()
      if bagian == "KOORDINAT" and len(potongan) >= 3:
        nomor = int(potongan[0])
        koordinat[nomor] = (int(potongan[1]), int(potongan[2]))
      elif bagian == "DEMAND" and len(potongan) >= 2:
        nomor = int(potongan[0])
        permintaan[nomor] = int(potongan[1])

  # --- ubah menjadi objek Node ---------------------------------
  daftar_node = []
  for nomor in sorted(koordinat.keys()):
    x, y = koordinat[nomor]
    demand = permintaan.get(nomor, 0)
    daftar_node.append(Node(nomor, x, y, demand))

  return daftar_node, kapasitas, jumlah_kendaraan