"""
visit.py  —  TAHAP 6
===============================================================================
Kelas Visit: satu kali KUNJUNGAN ke sebuah node.

Mengapa perlu kelas baru? Bukankah Node sudah ada?

  Node  = TEMPAT.
          Ada 32, tidak pernah berubah. Node 5 tetap node 5 selamanya.

  Visit = PERISTIWA mengunjungi tempat itu.
          Berubah terus. Kunjungan ke node 5 bisa berada di rute 2 urutan
          ke-4 pada satu solusi, dan di rute 5 urutan ke-0 pada solusi lain.

Analogi: "Bandung" adalah tempat (Node).
         "Saya ke Bandung hari Selasa, jadi tujuan ketiga" adalah kunjungan
         (Visit). Bandungnya sama, kunjungannya bisa banyak dan berbeda-beda.
===============================================================================
"""


class Visit:
    """Satu kunjungan ke sebuah node di dalam sebuah rute."""

    def __init__(self, node, urutan=0, muatan_sesudah=0):
        # PENTING: kita simpan RUJUKAN ke objek Node, bukan menyalin isinya.
        # Jangan menulis self.x = node.x dan seterusnya. Kalau disalin,
        # data node jadi ada di dua tempat dan bisa saling bertentangan.
        self.node = node

        self.urutan = urutan                  # kunjungan ke berapa dalam rute
        self.muatan_sesudah = muatan_sesudah  # isi truk setelah melayani node ini

    # -------------------------------------------------------------------
    # Jalan pintas supaya penulisan lebih singkat
    # -------------------------------------------------------------------
    @property
    def nomor(self):
        """visit.nomor sama dengan visit.node.nomor, hanya lebih pendek."""
        return self.node.nomor

    @property
    def demand(self):
        """Diambil dari objek Node, bukan disimpan ulang di sini."""
        return self.node.demand

    def copy(self):
        """
        Salinan kunjungan ini.
        Objek Node TIDAK disalin, cukup dirujuk, karena isinya tidak
        pernah berubah. Menyalinnya hanya memboroskan memori.
        """
        return Visit(self.node, self.urutan, self.muatan_sesudah)

    def __repr__(self):
        return (f"Visit(urutan={self.urutan}, node={self.nomor}, "
                f"demand={self.demand}, muatan={self.muatan_sesudah})")
