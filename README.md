# Bike Sharing Analytics — Proyek Analisis Data

Dashboard publik: https://bike-sharing-analytics-cbneyotthvmyxmgbcfdfet.streamlit.app/

Proyek ini menganalisis pola penyewaan sepeda Capital Bikeshare di Washington, D.C. selama 1 Januari 2011–31 Desember 2012. Analisis menggunakan dua tingkat agregasi: `day.csv` (harian) dan `hour.csv` (per jam). Kedua file tidak dijumlahkan karena merepresentasikan periode layanan yang sama pada tingkat agregasi berbeda.

## Struktur direktori

```text
Submission_Bike_Sharing_Analytics/
├── Dashboard/
│   └── dashboard.py
├── Data/
│   ├── day.csv                         # data sumber harian
│   ├── hour.csv                        # data sumber per jam
│   └── processed/
│       ├── day_clean.csv               # hasil preprocessing/cleaning notebook
│       └── hour_clean.csv              # hasil cleaning, tanggal dengan 24 jam lengkap
├── Proyek_Analisis_Data_Bike_Sharing.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Persyaratan sistem

- Python 3.10 atau lebih baru (disarankan Python 3.11/3.12).
- `pip`.
- Koneksi internet untuk mengunduh library saat instalasi.

## Menyiapkan environment — Windows PowerShell

Buka terminal pada direktori utama proyek, lalu jalankan:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jika PowerShell memblokir aktivasi script, izinkan hanya untuk sesi terminal saat ini, kemudian aktifkan kembali:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Menyiapkan environment — Anaconda

```bash
conda create --name bike-sharing python=3.11 -y
conda activate bike-sharing
python -m pip install -r requirements.txt
```

## Menyiapkan environment — macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Menjalankan preprocessing dan notebook

1. Buka `Proyek_Analisis_Data_Bike_Sharing.ipynb` dengan Jupyter Notebook, JupyterLab, VS Code, atau Google Colab.
2. Pastikan data sumber `day.csv` dan `hour.csv` tersedia di folder `Data/`.
3. Jalankan seluruh cell notebook dari atas ke bawah.
4. Pada tahap Cleaning Data, notebook akan menghasilkan `Data/processed/day_clean.csv` dan `Data/processed/hour_clean.csv`.
5. Dashboard membaca **hanya dataset hasil cleaning** di folder `Data/processed/`, bukan CSV mentah. Jika data sumber diperbarui atau proses cleaning berubah, jalankan ulang notebook untuk memperbarui kedua file processed tersebut.

## Menjalankan dashboard Streamlit secara lokal

Dari direktori utama proyek, pastikan environment aktif dan dataset hasil cleaning sudah tersedia. Jalankan:

```bash
python -m streamlit run Dashboard/dashboard.py
```

Streamlit biasanya menampilkan alamat lokal `http://localhost:8501`. Buka alamat tersebut di browser dan biarkan terminal tetap berjalan selama dashboard digunakan. Untuk menghentikan aplikasi, tekan `Ctrl + C` pada terminal.

Dashboard publik: https://bike-sharing-analytics-cbneyotthvmyxmgbcfdfet.streamlit.app/

### Konfigurasi Streamlit Community Cloud

- Repository: `alpucado/bike-sharing-analytics`
- Branch: `main`
- Main file path: `Dashboard/dashboard.py`

Pastikan folder `Data/processed/` ikut berada di repository agar aplikasi cloud membaca data hasil cleaning yang sama.

## Ringkasan tahapan analisis

- **Gathering Data:** memuat 731 observasi harian dan 17.379 observasi per jam.
- **Assessing Data:** memeriksa struktur dan tipe data (`info()`/`dtypes`), missing value, duplikasi, konsistensi `cnt`, rentang variabel ternormalisasi, kelengkapan tanggal–jam, nilai `hum = 0`, serta konteks potential outlier.
- **Cleaning Data:** mengubah `dteday` menjadi datetime; mengimputasi nilai `hum = 0` memakai median kelompok pembanding; menambahkan label kategori; mempertahankan potential outlier dengan penanda; dan menggunakan 655 tanggal dengan 24 jam lengkap untuk profil per jam. Hasil cleaning diekspor ke `Data/processed/`.
- **EDA dan visualisasi:** membandingkan profil penyewaan menurut jam dan jenis hari serta rata-rata harian menurut kombinasi musim–cuaca.
- **Analisis lanjutan:** menerapkan binning kuantil untuk merangkum tingkat permintaan harian menurut musim.
- **Conclusion & Recommendation:** menyusun implikasi operasional untuk jadwal redistribusi dan perencanaan kapasitas.

## Catatan interpretasi

Hasil merupakan analisis deskriptif historis Capital Bikeshare di Washington, D.C. pada 2011–2012. Korelasi dan perbedaan rata-rata tidak membuktikan sebab-akibat. Kombinasi Spring–Light Rain / Snow hanya memiliki empat hari observasi sehingga perlu ditafsirkan secara hati-hati.

## Referensi dataset

Fanaee-T, H., & Gama, J. (2013). *Event labeling combining ensemble detectors and background knowledge*. Progress in Artificial Intelligence. https://doi.org/10.1007/s13748-013-0040-3
