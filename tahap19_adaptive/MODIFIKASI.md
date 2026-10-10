# Modifikasi ALNS

Implementasi tahap 19 diperluas dengan enam modifikasi berikut.

1. **Shaw removal** (`destroy.py`) menghapus kelompok pelanggan yang dekat
   secara spasial dan mirip demand-nya. Pemilihan berbias acak tetap memberi
   variasi eksplorasi. Rujukan: Shaw (1998).
2. **Regret-3 insertion** (`repair.py`) memprioritaskan pelanggan berdasarkan
   selisih kumulatif tiga alternatif penyisipan terbaik. Rujukan: Ropke &
   Pisinger (2006).
3. **Noise pada repair** (`repair.py`) menambahkan gangguan terkontrol pada
   nilai pembanding biaya penyisipan. Jarak solusi yang sebenarnya tidak
   diubah. Rujukan: Ropke & Pisinger (2006).
4. **Bobot pasangan operator** (`alns.py`) mempelajari kombinasi
   `(destroy, repair)`, bukan menganggap kontribusi keduanya saling bebas.
   Rujukan: Turkes et al. (2021).
5. **Reheating saat stagnasi** (`alns.py`) menaikkan suhu kembali ke sebagian
   suhu awal setelah sejumlah iterasi tanpa rekor baru. Rujukan: Ropke &
   Pisinger (2006).
6. **Local search pada calon rekor** (`alns.py`) menjalankan relocate/swap
   sebagai pemoles sebelum calon solusi terbaik diterima. Rujukan: Pisinger &
   Ropke (2007).

Tersedia pula `batas_stagnasi` sebagai stopping criterion opsional. Semua
fitur dapat diatur melalui argumen konstruktor `ALNS`; nilai `None` pada
`batas_stagnasi` mempertahankan jumlah iterasi tetap.

Contoh konfigurasi:

```python
pencari = ALNS(
    instance,
    maks_iterasi=2000,
    tingkat_noise=0.10,
    stagnasi_reheat=250,
    faktor_reheat=0.50,
    gunakan_local_search=True,
    iterasi_local_search=3,
    batas_stagnasi=None,
)
```

