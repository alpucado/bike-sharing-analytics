from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Bike Sharing Analytics",
    page_icon="🚲",
    layout="wide",
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "Data"

DAY_PATH = DATA_DIR / "day.csv"
HOUR_PATH = DATA_DIR / "hour.csv"

SEASON_MAP = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
WEATHER_MAP = {
    1: "Clear",
    2: "Misty / Cloudy",
    3: "Light Rain / Snow",
    4: "Heavy Rain / Snow",
}


@st.cache_data(show_spinner="Memuat data Bike Sharing...")
def load_data():
    if not DAY_PATH.exists() or not HOUR_PATH.exists():
        missing = [p.name for p in [DAY_PATH, HOUR_PATH] if not p.exists()]
        raise FileNotFoundError(
            f"File berikut belum ditemukan di folder aplikasi: {', '.join(missing)}"
        )

    day = pd.read_csv(DAY_PATH, parse_dates=["dteday"])
    hour = pd.read_csv(HOUR_PATH, parse_dates=["dteday"])

    for frame in (day, hour):
        frame["season_label"] = frame["season"].map(SEASON_MAP)
        frame["weather_label"] = frame["weathersit"].map(WEATHER_MAP)
        frame["day_type"] = np.where(
            frame["workingday"].eq(1), "Working day", "Non-working day"
        )
        frame["year_label"] = frame["yr"].map({0: 2011, 1: 2012})

    # Untuk perbandingan per jam, hanya gunakan tanggal dengan 24 catatan jam.
    hours_per_day = hour.groupby("dteday")["hr"].nunique()
    complete_dates = hours_per_day[hours_per_day.eq(24)].index
    hour_complete = hour[hour["dteday"].isin(complete_dates)].copy()

    return day, hour_complete, len(complete_dates), len(hours_per_day)


st.title("🚲 Bike Sharing Analytics")
st.caption("Capital Bikeshare · Washington, D.C. · Data historis 2011–2012")

try:
    day_df, hour_df, complete_day_count, total_day_count = load_data()
except Exception as exc:
    st.error(str(exc))
    st.info("Letakkan `day.csv` dan `hour.csv` dalam folder yang sama dengan `app.py`, kemudian jalankan kembali aplikasi.")
    st.stop()

# ----------------------------- Sidebar filters -----------------------------
st.sidebar.header("Filter analisis")
available_years = sorted(day_df["year_label"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect(
    "Tahun", options=available_years, default=available_years
)

if not selected_years:
    st.warning("Pilih minimal satu tahun untuk menampilkan analisis.")
    st.stop()

base = day_df[day_df["year_label"].isin(selected_years)].copy()
min_date = base["dteday"].min().date()
max_date = base["dteday"].max().date()
selected_dates = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
elif isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 1:
    start_date = end_date = selected_dates[0]
else:
    start_date = end_date = selected_dates

season_options = sorted(base["season_label"].dropna().unique().tolist())
weather_options = sorted(base["weather_label"].dropna().unique().tolist())
selected_seasons = st.sidebar.multiselect(
    "Musim", options=season_options, default=season_options
)
selected_weather = st.sidebar.multiselect(
    "Kondisi cuaca", options=weather_options, default=weather_options
)

if not selected_seasons or not selected_weather:
    st.warning("Pilih minimal satu musim dan satu kondisi cuaca.")
    st.stop()

# Apply identical filters to daily and hourly datasets.
date_mask_day = day_df["dteday"].dt.date.between(start_date, end_date)
filtered_day = day_df[
    day_df["year_label"].isin(selected_years)
    & date_mask_day
    & day_df["season_label"].isin(selected_seasons)
    & day_df["weather_label"].isin(selected_weather)
].copy()

date_mask_hour = hour_df["dteday"].dt.date.between(start_date, end_date)
filtered_hour = hour_df[
    hour_df["year_label"].isin(selected_years)
    & date_mask_hour
    & hour_df["season_label"].isin(selected_seasons)
    & hour_df["weather_label"].isin(selected_weather)
].copy()

if filtered_day.empty:
    st.warning("Tidak ada data harian yang sesuai dengan kombinasi filter ini.")
    st.stop()

# ------------------------------- KPI section -------------------------------
registered_share = (
    filtered_day["registered"].sum() / filtered_day["cnt"].sum() * 100
    if filtered_day["cnt"].sum() > 0
    else 0
)
peak_row = filtered_day.loc[filtered_day["cnt"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", f"{filtered_day['cnt'].sum():,.0f}")
k2.metric("Rata-rata per hari", f"{filtered_day['cnt'].mean():,.0f}")
k3.metric("Porsi pengguna terdaftar", f"{registered_share:.1f}%")
k4.metric("Penyewaan harian tertinggi", f"{peak_row['cnt']:,.0f}", help=str(peak_row["dteday"].date()))

st.caption(
    f"Data terpilih: {len(filtered_day):,} hari. Profil per jam menggunakan tanggal lengkap saja "
    f"({complete_day_count:,} dari {total_day_count:,} tanggal pada keseluruhan dataset)."
)

# ---------------------------------- Tabs ------------------------------------
tab_overview, tab_hourly, tab_weather = st.tabs(
    ["Ringkasan", "Pola per Jam", "Musim & Cuaca"]
)

with tab_overview:
    st.subheader("Perkembangan penyewaan harian")
    trend = filtered_day.sort_values("dteday").copy()
    trend["rolling_7d"] = trend["cnt"].rolling(window=7, min_periods=1).mean()
    fig_trend = px.line(
        trend,
        x="dteday",
        y=["cnt", "rolling_7d"],
        labels={"dteday": "Tanggal", "value": "Jumlah penyewaan", "variable": "Seri"},
        title="Jumlah penyewaan harian dan rata-rata bergerak 7 hari",
    )
    fig_trend.update_layout(legend_title_text="Seri", hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)

    user_mix = pd.DataFrame(
        {
            "Jenis pengguna": ["Casual", "Registered"],
            "Jumlah penyewaan": [filtered_day["casual"].sum(), filtered_day["registered"].sum()],
        }
    )
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
            "Gunakan tren harian untuk melihat perubahan volume penyewaan, sementara komposisi "
            "pengguna membantu membedakan kebutuhan pengguna kasual dan terdaftar."
        )
        st.write(
            "Rata-rata bergerak 7 hari membantu mengurangi fluktuasi harian, tetapi tidak "
            "menghilangkan pengaruh kejadian khusus atau perubahan musiman."
        )

    csv_bytes = filtered_day.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Unduh data harian sesuai filter (CSV)",
        data=csv_bytes,
        file_name="bike_sharing_daily_filtered.csv",
        mime="text/csv",
    )

with tab_hourly:
    st.subheader("Rata-rata penyewaan berdasarkan jam")
    if filtered_hour.empty:
        st.info("Tidak tersedia catatan per jam lengkap untuk filter yang dipilih.")
    else:
        day_type_choice = st.radio(
            "Jenis hari",
            options=["Semua", "Working day", "Non-working day"],
            horizontal=True,
            key="day_type_choice",
        )
        chart_data = filtered_hour.copy()
        if day_type_choice != "Semua":
            chart_data = chart_data[chart_data["day_type"] == day_type_choice]

        hourly_avg = (
            chart_data.groupby(["day_type", "hr"], as_index=False)
            .agg(avg_rentals=("cnt", "mean"))
        )
        if hourly_avg.empty:
            st.info("Tidak ada observasi per jam untuk pilihan jenis hari tersebut.")
        else:
            fig_hourly = px.line(
                hourly_avg,
                x="hr",
                y="avg_rentals",
                color="day_type",
                markers=True,
                labels={
                    "hr": "Jam dalam sehari",
                    "avg_rentals": "Rata-rata penyewaan per jam",
                    "day_type": "Jenis hari",
                },
                title="Profil permintaan sepeda per jam",
            )
            fig_hourly.update_xaxes(dtick=1)
            fig_hourly.update_layout(hovermode="x unified")
            st.plotly_chart(fig_hourly, use_container_width=True)

            peak = hourly_avg.loc[hourly_avg.groupby("day_type")["avg_rentals"].idxmax()]
            st.markdown("**Jam puncak pada filter saat ini**")
            st.dataframe(
                peak.rename(
                    columns={
                        "day_type": "Jenis hari",
                        "hr": "Jam puncak",
                        "avg_rentals": "Rata-rata penyewaan",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )
        st.caption(
            "Catatan: hanya tanggal yang memiliki 24 catatan jam digunakan untuk grafik ini. "
            "Hari dengan catatan jam tidak lengkap tidak diimputasi."
        )

with tab_weather:
    st.subheader("Rata-rata penyewaan menurut musim dan cuaca")
    season_weather = (
        filtered_day.groupby(["season_label", "weather_label"], as_index=False)
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
        hover_data={"number_of_days": True, "avg_rentals": ":.1f"},
        category_orders={
            "season_label": ["Spring", "Summer", "Fall", "Winter"],
            "weather_label": list(WEATHER_MAP.values()),
        },
        labels={
            "season_label": "Musim",
            "avg_rentals": "Rata-rata penyewaan per hari",
            "weather_label": "Kondisi cuaca",
            "number_of_days": "Jumlah hari",
        },
        title="Perbandingan rata-rata penyewaan menurut musim dan cuaca",
    )
    st.plotly_chart(fig_weather, use_container_width=True)
    st.dataframe(
        season_weather.sort_values("avg_rentals", ascending=False).rename(
            columns={
                "season_label": "Musim",
                "weather_label": "Kondisi cuaca",
                "avg_rentals": "Rata-rata penyewaan",
                "number_of_days": "Jumlah hari",
            }
        ),
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
    "Fanaee-T & Gama (2013), https://doi.org/10.1007/s13748-013-0040-3"
)
