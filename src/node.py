"""
node.py  —  TAHAP 4
===============================================================================
Mulai tahap ini, kelas Node kita pindahkan ke filenya sendiri.

Alasannya: satu file untuk satu hal. Nanti akan ada banyak kelas, dan kalau
semuanya ditumpuk di satu file, mencari sesuatu jadi menyiksa.

File lain cukup menulis:  from node import Node
===============================================================================
"""

import math


class Node:
    """Satu titik pada peta: depot atau pelanggan."""

    def __init__(self, nomor, x, y, demand):
        self.nomor = nomor
        self.x = x
        self.y = y
        self.demand = demand

    def jarak_ke(self, lain):
        """Jarak lurus ke node lain, dibulatkan sesuai standar TSPLIB."""
        dx = self.x - lain.x
        dy = self.y - lain.y
        return round(math.sqrt(dx * dx + dy * dy))

    def adalah_depot(self):
        """Depot adalah node yang demand-nya nol."""
        return self.demand == 0

    def __repr__(self):
        return f"Node({self.nomor}, x={self.x}, y={self.y}, demand={self.demand})"
