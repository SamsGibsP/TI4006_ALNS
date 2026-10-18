import cProfile
import io
import os
import pstats
import random
import sys

folder_tahap19 = os.path.dirname(os.path.abspath(__file__))
dir_root = os.path.dirname(folder_tahap19)
dir_hasil_final = os.path.join(dir_root, "hasil_final")
os.makedirs(dir_hasil_final, exist_ok=True)

if folder_tahap19 not in sys.path:
    sys.path.insert(0, folder_tahap19)

from alns import ALNS
from baca_data import baca_instance
from construction import ConstructionHeuristic
from cvrp_instance import CVRPInstance

random.seed(1)
path = os.path.join(folder_tahap19, "X", "X-n351-k40.vrp")

if not os.path.exists(path):
    raise FileNotFoundError(f"File instance tidak ditemukan di: {path}")

daftar_node, kapasitas, jumlah_kendaraan = baca_instance(path)
instance = CVRPInstance(daftar_node, kapasitas, jumlah_kendaraan)
solusi_awal = ConstructionHeuristic(instance).clarke_wright_savings()

pencari = ALNS(
    instance,
    maks_iterasi=500,
    pakai_ls=True,
    pakai_shaw=True,
    pakai_reheating=True,
    pakai_regret3=True,
    pakai_adaptif=True,
    tampilkan_setiap=0,
)

profiler = cProfile.Profile()
profiler.enable()

hasil = pencari.jalankan(solusi_awal)

profiler.disable()

output_buffer = io.StringIO()
stats = pstats.Stats(profiler, stream=output_buffer)
stats.strip_dirs()
stats.sort_stats("tottime")
stats.print_stats(30)

target_output = os.path.join(folder_tahap19, "profile_n351.txt")
with open(target_output, "w", encoding="utf-8") as f:
    f.write(output_buffer.getvalue())

print(f"Profiling selesai! Hasil disimpan di {target_output}")
print(f"Hasil jarak n351 (500 iter): {hasil.total_jarak} | Layak: {hasil.layak()}")
print("\n--- 15 FUNGSI TERATAS BERDASARKAN TOTTIME ---")
stats_short = pstats.Stats(profiler)
stats_short.strip_dirs()
stats_short.sort_stats("tottime")
stats_short.print_stats(15)