"""
visit.py — TAHAP 6 (TEROPTIMASI)
===============================================================================
Kelas Visit: satu kali KUNJUNGAN ke sebuah node.
Optimasi: Hapus @property agar akses nomor dan demand bersifat langsung O(1).
===============================================================================
"""


class Visit:
    """Satu kunjungan ke sebuah node di dalam sebuah rute."""

    def __init__(self, node, urutan=0, muatan_sesudah=0):
        self.node = node
        # Akses langsung tanpa @property untuk menghindari jutaan overhead call
        self.nomor = node.nomor
        self.demand = node.demand

        self.urutan = urutan
        self.muatan_sesudah = muatan_sesudah

    def copy(self):
        """Salinan kunjungan ini."""
        return Visit(self.node, self.urutan, self.muatan_sesudah)

    def __repr__(self):
        return (f"Visit(urutan={self.urutan}, node={self.nomor}, "
                f"demand={self.demand}, muatan={self.muatan_sesudah})")