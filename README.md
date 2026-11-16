# Bike Sharing Analytics Project

## Isi folder
- `Proyek_Analisis_Data_Bike_Sharing.ipynb`: notebook analisis yang mengikuti struktur template proyek.
- `app.py`: dashboard interaktif berbasis Streamlit.
- `day.csv`: data penyewaan yang diagregasi per hari.
- `hour.csv`: data penyewaan yang diagregasi per jam.
- `requirements.txt`: dependensi Python.

## Menjalankan notebook
1. Unggah `Proyek_Analisis_Data_Bike_Sharing.ipynb`, `day.csv`, dan `hour.csv` ke Google Colab atau letakkan di direktori kerja Jupyter yang sama.
2. Jalankan cell secara berurutan.
3. Isi nama, email, dan ID Dicoding pada bagian awal notebook.

## Menjalankan dashboard secara lokal
Pastikan Python telah terpasang. Dari terminal, masuk ke direktori proyek, lalu jalankan:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Pastikan `day.csv` dan `hour.csv` berada dalam folder yang sama dengan `app.py`.

## Catatan metodologis
- `day.csv` dan `hour.csv` adalah agregasi berbeda dari sistem dan periode yang sama. Jangan menjumlahkan kedua file.
- Terdapat 165 kombinasi tanggal-jam yang tidak tercatat pada 76 tanggal di `hour.csv`. Perbandingan profil per jam menggunakan 655 tanggal yang memiliki 24 observasi jam lengkap.
- Potensi outlier `cnt` di `hour.csv` ditandai dengan aturan IQR, tetapi tidak dihapus otomatis karena dapat mencerminkan lonjakan permintaan yang nyata.
- Hasil bersifat deskriptif dan terbatas pada data Capital Bikeshare Washington, D.C. tahun 2011–2012.

## Referensi
Fanaee-T, H., & Gama, J. (2013). *Event labeling combining ensemble detectors and background knowledge*. Progress in Artificial Intelligence. https://doi.org/10.1007/s13748-013-0040-3
