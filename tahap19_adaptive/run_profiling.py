import cProfile
import io
import os
import pstats
import sys

# Tentukan path direktori
folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
root_folder = os.path.dirname(folder_tahap19)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance

# Path file instance yang benar berada di dalam subfolder X
path = os.path.join(folder_tahap19, "X", "X-n101-k25.vrp")

if not os.path.exists(path):
    raise FileNotFoundError(f"File instance tidak ditemukan di: {path}")

daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path)
instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
solusi_awal = ConstructionHeuristic(instance).nearest_neighbor()

pencari = ALNS(instance, maks_iterasi=500, tampilkan_setiap=0)

profiler = cProfile.Profile()
profiler.enable()

pencari.jalankan(solusi_awal)

profiler.disable()

output_buffer = io.StringIO()
stats = pstats.Stats(profiler, stream=output_buffer)
stats.strip_dirs()
stats.sort_stats("tottime")
stats.print_stats(30)

target_output = os.path.join(root_folder, "profile_result.txt")
with open(target_output, "w", encoding="utf-8") as f:
    f.write(output_buffer.getvalue())

print(f"Profiling selesai! Hasil disimpan di {target_output}")