from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# Konfigurasi halaman
st.set_page_config(
    page_title="Bike Sharing Analytics",
    page_icon="🚲",
    layout="wide",
)

# Dashboard hanya membaca dataset hasil preprocessing dan cleaning notebook.
PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "Data" / "processed"
DAY_CLEAN_PATH = PROCESSED_DIR / "day_clean.csv"
HOUR_CLEAN_PATH = PROCESSED_DIR / "hour_clean.csv"

SEASON_ORDER = ["Spring", "Summer", "Fall", "Winter"]
WEATHER_ORDER = [
    "Clear",
    "Misty / Cloudy",
    "Light Rain / Snow",
    "Heavy Rain / Snow",
]
DAY_TYPE_ORDER = ["Working day", "Non-working day"]

REQUIRED_DAY_COLUMNS = {
    "dteday", "cnt", "casual", "registered", "season_label",
    "weather_label", "workingday_label", "day_type", "year_label", "hum",
}
REQUIRED_HOUR_COLUMNS = {
    "dteday", "hr", "cnt", "season_label", "weather_label",
    "workingday_label", "day_type", "year_label", "hum",
    "potential_outlier_cnt",
}


@st.cache_data(show_spinner="Memuat dataset hasil preprocessing dan cleaning...")
def load_cleaned_data():
    """Muat dan validasi hasil cleaning yang diekspor oleh notebook.

    Tidak membaca CSV mentah dan tidak memetakan ulang kode numerik kategori.
    """
    missing_files = [
        path.relative_to(PROJECT_DIR).as_posix()
        for path in (DAY_CLEAN_PATH, HOUR_CLEAN_PATH)
        if not path.exists()
    ]
    if missing_files:
        raise FileNotFoundError(
            "Dataset hasil cleaning belum tersedia: " + ", ".join(missing_files)
            + ". Jalankan seluruh notebook sampai bagian ekspor dataset hasil "
            "preprocessing untuk membuat file di Data/processed/."
        )

    day = pd.read_csv(DAY_CLEAN_PATH, parse_dates=["dteday"])
    hour = pd.read_csv(HOUR_CLEAN_PATH, parse_dates=["dteday"])

    missing_day_columns = REQUIRED_DAY_COLUMNS.difference(day.columns)
    missing_hour_columns = REQUIRED_HOUR_COLUMNS.difference(hour.columns)
    if missing_day_columns or missing_hour_columns:
        details = []
        if missing_day_columns:
            details.append("day_clean.csv: " + ", ".join(sorted(missing_day_columns)))
        if missing_hour_columns:
            details.append("hour_clean.csv: " + ", ".join(sorted(missing_hour_columns)))
        raise ValueError(
            "Kolom dataset hasil cleaning tidak sesuai: " + "; ".join(details)
            + ". Ekspor ulang dataset dari notebook versi terbaru."
        )

    # Validasi hasil cleaning; label kategori yang sudah dibuat notebook digunakan langsung.
    for name, frame in (("day_clean", day), ("hour_clean", hour)):
        if frame["dteday"].isna().any():
            raise ValueError(f"{name}: terdapat tanggal kosong setelah parsing datetime.")
        label_columns = [
            "season_label", "weather_label", "workingday_label", "day_type", "year_label"
        ]
        if frame[label_columns].isna().any().any():
            raise ValueError(f"{name}: terdapat label kategori atau tahun yang kosong.")
        if (frame["hum"] == 0).any():
            raise ValueError(f"{name}: masih terdapat hum = 0; jalankan ulang cleaning notebook.")
        if not frame["hum"].between(0, 1).all():
            raise ValueError(f"{name}: nilai hum berada di luar rentang normalisasi 0–1.")
        if not (frame["cnt"] == frame["casual"] + frame["registered"]).all():
            raise ValueError(f"{name}: ditemukan ketidaksesuaian cnt dengan casual + registered.")
        if not set(frame["season_label"].unique()).issubset(SEASON_ORDER):
            raise ValueError(f"{name}: ditemukan label musim yang tidak dikenal.")
        if not set(frame["weather_label"].unique()).issubset(WEATHER_ORDER):
            raise ValueError(f"{name}: ditemukan label cuaca yang tidak dikenal.")
        if not set(frame["workingday_label"].unique()).issubset(DAY_TYPE_ORDER):
            raise ValueError(f"{name}: ditemukan label jenis hari yang tidak dikenal.")

    if day.duplicated(subset=["dteday"]).any():
        raise ValueError("day_clean: terdapat tanggal duplikat.")
    if hour.duplicated(subset=["dteday", "hr"]).any():
        raise ValueError("hour_clean: terdapat kombinasi tanggal-jam duplikat.")

    # hour_clean.csv harus hanya memuat tanggal dengan 24 observasi jam lengkap.
    hours_per_day = hour.groupby("dteday")["hr"].nunique()
    if hours_per_day.ne(24).any():
        raise ValueError(
            "hour_clean.csv harus hanya berisi tanggal dengan 24 catatan jam. "
            "Ekspor ulang dari notebook versi terbaru."
        )

    # Konversi eksplisit tipe numerik yang dipakai oleh filter dan agregasi.
    day["year_label"] = pd.to_numeric(day["year_label"], errors="raise").astype(int)
    hour["year_label"] = pd.to_numeric(hour["year_label"], errors="raise").astype(int)
    hour["hr"] = pd.to_numeric(hour["hr"], errors="raise").astype(int)

    return day, hour


st.title("🚲 Bike Sharing Analytics")
st.caption("Capital Bikeshare · Washington, D.C. · Data historis 2011–2012")
st.markdown(
    "Dashboard menggunakan **`day_clean.csv` dan `hour_clean.csv`**, yaitu dataset "
    "hasil preprocessing, validasi, dan cleaning pada notebook. CSV mentah tidak "
    "digunakan langsung sebagai sumber visualisasi, dan label musim, cuaca, serta "
    "jenis hari digunakan langsung dari hasil pengolahan notebook."
)

try:
    day_df, hour_df = load_cleaned_data()
except Exception as exc:
    st.error(str(exc))
    st.stop()

# ----------------------------- Filter tahun -----------------------------
st.sidebar.header("Filter analisis")
available_years = sorted(day_df["year_label"].unique().tolist())
selected_years = st.sidebar.multiselect(
    "Tahun",
    options=available_years,
    default=available_years,
)
if not selected_years:
    st.warning("Pilih minimal satu tahun untuk menampilkan analisis.")
    st.stop()

# Rentang tanggal mengikuti tahun yang dipilih dan diterapkan identik pada dua dataset.
base_by_year = day_df[day_df["year_label"].isin(selected_years)].copy()
min_date = base_by_year["dteday"].min().date()
max_date = base_by_year["dteday"].max().date()
year_key = "_".join(str(year) for year in selected_years)
selected_dates = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key=f"date_range_{year_key}",
)
if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected_dates

# Filter tahun dan tanggal sama persis untuk day_clean dan hour_clean.
day_mask = (
    day_df["year_label"].isin(selected_years)
    & day_df["dteday"].dt.date.between(start_date, end_date)
)
hour_mask = (
    hour_df["year_label"].isin(selected_years)
    & hour_df["dteday"].dt.date.between(start_date, end_date)
)
filtered_day = day_df.loc[day_mask].copy()
filtered_hour = hour_df.loc[hour_mask].copy()

if filtered_day.empty:
    st.warning("Tidak ada data harian pada tahun dan rentang tanggal yang dipilih.")
    st.stop()

# ------------------------------- KPI section -------------------------------
registered_share = (
    filtered_day["registered"].sum() / filtered_day["cnt"].sum() * 100
    if filtered_day["cnt"].sum() > 0 else 0
)
peak_row = filtered_day.loc[filtered_day["cnt"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", f"{filtered_day['cnt'].sum():,.0f}")
k2.metric("Rata-rata per hari", f"{filtered_day['cnt'].mean():,.0f}")
k3.metric("Porsi pengguna terdaftar", f"{registered_share:.1f}%")
k4.metric(
    "Penyewaan harian tertinggi",
    f"{peak_row['cnt']:,.0f}",
    help=str(peak_row["dteday"].date()),
)

st.caption(
    f"Data harian terpilih: {len(filtered_day):,} hari. Data per jam terpilih: "
    f"{len(filtered_hour):,} observasi dari {filtered_hour['dteday'].nunique():,} "
    "tanggal dengan 24 jam lengkap. Filter tahun dan tanggal diterapkan pada kedua dataset."
)

# ---------------------------------- Tabs ------------------------------------
tab_overview, tab_hourly, tab_weather = st.tabs(
    ["Ringkasan", "Pertanyaan 1 · Pola per Jam", "Pertanyaan 2 · Musim & Cuaca"]
)

with tab_overview:
    st.subheader("Perkembangan penyewaan harian")
    trend = filtered_day.sort_values("dteday").copy()
    trend["rolling_7d"] = trend["cnt"].rolling(window=7, min_periods=1).mean()
    fig_trend = px.line(
        trend,
        x="dteday",
        y=["cnt", "rolling_7d"],
        labels={
            "dteday": "Tanggal",
            "value": "Jumlah penyewaan (sepeda)",
            "variable": "Seri",
        },
        title="Jumlah penyewaan harian dan rata-rata bergerak 7 hari",
    )
    fig_trend.update_layout(legend_title_text="Seri", hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)

    user_mix = pd.DataFrame({
        "Jenis pengguna": ["Casual", "Registered"],
        "Jumlah penyewaan": [filtered_day["casual"].sum(), filtered_day["registered"].sum()],
    })
    mix_col, info_col = st.columns([1, 1])
    with mix_col:
        fig_mix = px.pie(
            user_mix,
            names="Jenis pengguna",
            values="Jumlah penyewaan",
            hole=0.45,
            title="Komposisi penyewaan menurut jenis pengguna",
        )
        st.plotly_chart(fig_mix, use_container_width=True)
    with info_col:
        st.markdown("#### Catatan interpretasi")
        st.write(
            "Ringkasan harian dan komposisi pengguna dihitung dari dataset yang sudah "
            "melewati tahap cleaning notebook. Rata-rata bergerak 7 hari membantu "
            "melihat kecenderungan tanpa menghilangkan seluruh fluktuasi harian."
        )

    st.download_button(
        "Unduh data harian cleaned sesuai filter (CSV)",
        data=filtered_day.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8"),
        file_name="bike_sharing_day_clean_filtered.csv",
        mime="text/csv",
    )

with tab_hourly:
    st.subheader("Pertanyaan 1 — Rata-rata penyewaan per jam menurut jenis hari")
    if filtered_hour.empty:
        st.info("Tidak tersedia tanggal dengan 24 catatan jam pada rentang tanggal yang dipilih.")
    else:
        day_type_choice = st.radio(
            "Jenis hari",
            options=["Semua", *DAY_TYPE_ORDER],
            horizontal=True,
            key="day_type_choice",
        )
        chart_data = filtered_hour.copy()
        if day_type_choice != "Semua":
            chart_data = chart_data[chart_data["workingday_label"] == day_type_choice]

        hourly_avg = (
            chart_data.groupby(["workingday_label", "hr"], as_index=False)
            .agg(
                avg_rentals=("cnt", "mean"),
                observations=("cnt", "size"),
            )
            .rename(columns={"workingday_label": "Jenis hari"})
        )
        if hourly_avg.empty:
            st.info("Tidak ada observasi untuk pilihan jenis hari tersebut.")
        else:
            fig_hourly = px.line(
                hourly_avg,
                x="hr",
                y="avg_rentals",
                color="Jenis hari",
                color_discrete_sequence=px.colors.qualitative.Safe,
                markers=True,
                labels={
                    "hr": "Jam dalam sehari (waktu lokal)",
                    "avg_rentals": "Rata-rata penyewaan (sepeda/jam)",
                    "Jenis hari": "Jenis hari",
                },
                title=(
                    "Profil rata-rata penyewaan sepeda per jam | "
                    "Washington, D.C. (2011–2012)"
                ),
            )
            fig_hourly.update_xaxes(dtick=1, tickmode="linear")
            fig_hourly.update_layout(hovermode="x unified")
            st.plotly_chart(fig_hourly, use_container_width=True)

            peak = hourly_avg.loc[
                hourly_avg.groupby("Jenis hari")["avg_rentals"].idxmax()
            ]
            peak_display = peak.rename(columns={
                "hr": "Jam puncak",
                "avg_rentals": "Rata-rata penyewaan (sepeda/jam)",
                "observations": "Jumlah observasi per jam",
            })
            st.markdown("**Jam puncak pada filter saat ini**")
            st.dataframe(peak_display, hide_index=True, use_container_width=True)

        st.caption(
            "Dashboard menggunakan hour_clean.csv dari notebook: hanya tanggal dengan "
            "24 observasi jam lengkap yang disertakan. Potential outlier tidak dihapus; "
            "penanda potential_outlier_cnt tetap tersedia pada dataset."
        )

with tab_weather:
    st.subheader("Pertanyaan 2 — Rata-rata penyewaan harian menurut musim dan cuaca")
    season_weather = (
        filtered_day.groupby(
            ["season_label", "weather_label"],
            as_index=False,
            observed=True,
        )
        .agg(
            avg_rentals=("cnt", "mean"),
            number_of_days=("cnt", "size"),
        )
    )
    fig_weather = px.bar(
        season_weather,
        x="season_label",
        y="avg_rentals",
        color="weather_label",
        barmode="group",
        category_orders={
            "season_label": SEASON_ORDER,
            "weather_label": WEATHER_ORDER,
        },
        color_discrete_sequence=px.colors.qualitative.Safe,
        hover_data={"number_of_days": True, "avg_rentals": ":.1f"},
        labels={
            "season_label": "Musim",
            "avg_rentals": "Rata-rata penyewaan (sepeda/hari)",
            "weather_label": "Kondisi cuaca",
            "number_of_days": "Jumlah hari pengamatan",
        },
        title=(
            "Rata-rata penyewaan sepeda harian pada kombinasi musim–cuaca | "
            "Washington, D.C. (2011–2012)"
        ),
    )
    st.plotly_chart(fig_weather, use_container_width=True)

    if not season_weather.empty:
        highest = season_weather.loc[season_weather["avg_rentals"].idxmax()]
        lowest = season_weather.loc[season_weather["avg_rentals"].idxmin()]
        gap = highest["avg_rentals"] - lowest["avg_rentals"]
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Kombinasi tertinggi",
            f"{highest['avg_rentals']:,.1f} /hari",
            help=(
                f"{highest['season_label']} – {highest['weather_label']} | "
                f"{int(highest['number_of_days'])} hari"
            ),
        )
        m2.metric(
            "Kombinasi terendah",
            f"{lowest['avg_rentals']:,.1f} /hari",
            help=(
                f"{lowest['season_label']} – {lowest['weather_label']} | "
                f"{int(lowest['number_of_days'])} hari"
            ),
        )
        m3.metric("Selisih rata-rata", f"{gap:,.1f} /hari")

    st.dataframe(
        season_weather.sort_values("avg_rentals", ascending=False).rename(columns={
            "season_label": "Musim",
            "weather_label": "Kondisi cuaca",
            "avg_rentals": "Rata-rata penyewaan (sepeda/hari)",
            "number_of_days": "Jumlah hari",
        }),
        hide_index=True,
        use_container_width=True,
    )
    st.caption(
        "Rata-rata kelompok dengan jumlah hari sedikit perlu ditafsirkan hati-hati. "
        "Perbandingan ini bersifat deskriptif dan tidak membuktikan hubungan sebab-akibat."
    )

st.divider()
st.caption(
    "Sumber: Bike Sharing Dataset, Capital Bikeshare (Washington, D.C.), 2011–2012. "
    "Dashboard menggunakan hasil preprocessing/cleaning notebook dari Data/processed/. "
    "Referensi: Fanaee-T & Gama (2013), https://doi.org/10.1007/s13748-013-0040-3"
)
