import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit_plotly_events as plotly_events
import altair as alt
from streamlit_folium import st_folium
import folium
import requests
import re

GEOJSON_URL = 'https://raw.githubusercontent.com/naufalhajid/Dashboard-Ferizyan/refs/heads/main/data_pelabuhan.geojson'
GEOJSON_KAB_KEY = 'feature.properties.Nama Pelabuhan'

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Data Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* Main Background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
    [data-testid="stSidebar"] .css-1d391kg, [data-testid="stSidebar"] .st-emotion-cache-16idsys p {
        color: white;
    }
    
    /* Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;streamlit 
        color: white;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin: 10px 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .metric-value {
        font-size: 42px;
        font-weight: bold;
        margin: 10px 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .metric-label {
        font-size: 14px;
        opacity: 0.95;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .metric-delta {
        font-size: 18px;
        color: #4ade80;
        font-weight: 600;
        margin-top: 5px;
    }
    
    /* Chart Container */
    .chart-container {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
    }
    
    /* Section Header */
    .section-header {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
        border-left: 4px solid #4ade80;
    }
    
    /* Title Styling */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        padding: 10px 20px;
        font-size: 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* DataFrame Styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Info Box */
    .info-box {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
    }
    
    /* Progress Bar Custom */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    </style>
""", unsafe_allow_html=True)

# --- CUSTOM FUNCTIONS ---
@st.cache_data
def safe_date_conversion(df, date_cols):
    """Konversi kolom tanggal dengan aman"""
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

@st.cache_data
def to_csv(df):
    """Convert DataFrame to CSV"""
    return df.to_csv(index=False).encode('utf-8')

# --- HEADER ---
col_title1, col_title2 = st.columns([3, 1])
with col_title1:
    st.title("👥 Dashboard Demografi Karyawan FERIZYAN")
with col_title2:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/ASDP_Logo_2023.png/1199px-ASDP_Logo_2023.png", width=150)


# --- UPLOAD FILE ---
uploaded_file = st.file_uploader(
    "📂 Upload file data Anda",
    type=["csv", "xls", "xlsx"],
    help="Format yang didukung: CSV, Excel (.xls, .xlsx)"
)

if uploaded_file:
    try:
        file_name = uploaded_file.name.lower()
        
        with st.spinner("⏳ Memuat data..."):
            if file_name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # --- GANTI NAMA KOLOM ---
            df.rename(columns={
                'Status_Kepegawaian': 'Status Kepegawaian',
                'Sub_unker': 'Sub Unit Kerja',
                'Unit_Kerja': 'Unit Kerja',
                'TglLahir': 'Tanggal Lahir',
                'Keaktifan': 'Status Aktif',
                'Klasifikasi_Jabatan': 'Klasifikasi Jabatan',
                'Department_Name': 'Department Name',
                'Retirement_Date': 'Tanggal Pensiun',
                'Jenis_Kelamin': 'Jenis Kelamin',
                'Lokasi_Kerja': 'Lokasi Kerja',
                'Bulan': 'Tanggal Masuk',
                'Retirement Date': 'Tanggal Pensiun'
            }, inplace=True)
            
            # --- CLEANING DATA ---
            if 'Status Kepegawaian' in df.columns:
                df.loc[df['Status Kepegawaian'].str.contains(
                    r'^(CUTI|RESIGN|PENSIUN|TERMINATED)', na=False), 'Status Kepegawaian'] = 'Tidak Aktif'
                df['Status Kepegawaian'] = df['Status Kepegawaian'].astype(str).str.upper()
                df.loc[df['Status Kepegawaian'].str.contains('CONTRACT', na=False), 'Status Kepegawaian'] = 'PKWT'
                df.loc[df['Status Kepegawaian'].str.contains('EMPLOYEE', na=False), 'Status Kepegawaian'] = 'PKWTT'
            
            if 'Jenis Kelamin' in df.columns:
                df['Jenis Kelamin'] = df['Jenis Kelamin'].astype(str).str.strip()
                # --- CLEANING JENIS KELAMIN ---
                df['Jenis Kelamin'] = df['Jenis Kelamin'].astype(str).str.upper()
                df.loc[df['Jenis Kelamin'].str.contains(r'^(L)', na=False), 'Jenis Kelamin'] = 'Laki-laki'
                df.loc[df['Jenis Kelamin'].str.contains(r'^(P)', na=False), 'Jenis Kelamin'] = 'Perempuan'
            
            if 'Sub Unit Kerja' in df.columns:
                df['Sub Unit Kerja'] = df['Sub Unit Kerja'].astype(str).str.upper()
                
            # --- KONVERSI TANGGAL ---
            df = safe_date_conversion(df, ['Tanggal Masuk', 'Tanggal Keluar', 'Tanggal Lahir'])
        
        st.success(f"✅ Berhasil memuat: **{uploaded_file.name}**")
        st.markdown("### Analisis Komprehensif Data Karyawan")

        # --- TABS ---
        tab_analysis, tab_map, tab_raw_data = st.tabs([
            "Dashboard Analisis","Peta Lokasi Karyawan", 
            "Data Mentah"
        ])
        # ========================================
        # TAB: DATA MENTAH
        # ========================================
        with tab_raw_data:
            st.header("Data Asli")
            st.info("Data mentah setelah penggantian nama kolom dan *cleaning* karakter.")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv_raw = to_csv(df)
            st.download_button(
                label="Download Data Mentah (CSV)",
                data=csv_raw,
                file_name=f"cleanedrawdata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # ===============================
            # 1️⃣ ANALISIS MISSING VALUE
            # =============================== 
            missing_data = pd.DataFrame({
                'Missing Count': df.isnull().sum(),
                'Missing Percentage': (df.isnull().sum() / len(df)) * 100
            }).sort_values(by='Missing Percentage', ascending=False)
            
            df_cleaned = df.copy()
            to_drop = missing_data[missing_data['Missing Percentage'] == 100].index.tolist()
            
            if to_drop:
                df_cleaned.drop(columns=to_drop, inplace=True)
            
          # ===============================
        # 2️⃣ FILTER SIDEBAR
        # ===============================
        st.sidebar.markdown("## 🎛️ Filter Dashboard")
        st.sidebar.markdown("---")

        # Inisialisasi session state untuk filter
        if 'start_date' not in st.session_state:
            st.session_state['start_date'] = None
        if 'end_date' not in st.session_state:
            st.session_state['end_date'] = None
        if 'filter_values' not in st.session_state:
            st.session_state['filter_values'] = {}

        # Fungsi untuk reset filter
        def reset_filters():
            st.session_state['start_date'] = None
            st.session_state['end_date'] = None
            st.session_state['filter_values'] = {}

        df_filtered = df_cleaned.copy()
        today = pd.Timestamp(datetime.now().date())
        active_filters = []
        # Tangkap filter dari URL (klik peta)
        query_params = st.query_params  # st.experimental_get_query_params() untuk Streamlit <1.30
        filter_lokasi = query_params.get("filter_lokasi", [None])[0]

        if filter_lokasi and 'Lokasi Kerja' in df_cleaned.columns:
            # Simulasikan filter via sidebar state
            filter_key = 'filter_Lokasi Kerja'
            st.session_state['filter_values'][filter_key] = [filter_lokasi]
            # Opsional: tampilkan notifikasi
            st.success(f"✅ Filter aktif: **{filter_lokasi}**", icon="📍")
            # Bersihkan URL agar tidak berantakan
            st.markdown("""
            <script>
            if (window.history.replaceState) {
                const url = new URL(window.location);
                url.searchParams.delete('filter_lokasi');
                window.history.replaceState({}, '', url);
            }
            </script>
            """, unsafe_allow_html=True)
        # --- FILTER TANGGAL ---
        with st.sidebar.expander("📅 **Filter Tanggal Masuk**", expanded=True):
            if 'Tanggal Masuk' in df_cleaned.columns:
                valid_dates = df_cleaned[
                    (df_cleaned['Tanggal Masuk'] <= today) & 
                    (df_cleaned['Tanggal Masuk'].notna())
                ]['Tanggal Masuk']
                
                if not valid_dates.empty:
                    min_date = valid_dates.min().date()
                    max_date = today.date()
                    
                    # Gunakan session_state untuk menyimpan nilai date_input
                    if st.session_state['start_date'] is None:
                        st.session_state['start_date'] = min_date
                    if st.session_state['end_date'] is None:
                        st.session_state['end_date'] = max_date

                    col_date1, col_date2 = st.columns(2)
                    with col_date1:
                        start_date = st.date_input("Dari", st.session_state['start_date'], min_value=min_date, max_value=max_date, key="start_date_input")
                    with col_date2:
                        end_date = st.date_input("Sampai", st.session_state['end_date'], min_value=min_date, max_value=max_date, key="end_date_input")

                    # Update session state
                    st.session_state['start_date'] = start_date
                    st.session_state['end_date'] = end_date

                    if start_date > end_date:
                        st.error("❌ Tanggal mulai harus sebelum tanggal akhir")
                        st.stop()
                        
                    # Terapkan filter Tanggal Masuk
                    start_datetime = pd.to_datetime(start_date)
                    end_datetime = pd.to_datetime(end_date)
                    
                    df_filtered = df_filtered[
                        (df_filtered['Tanggal Masuk'] >= start_datetime) &
                        (df_filtered['Tanggal Masuk'] <= end_datetime)
                    ]
                    
                    active_filters.append(
                        f"📅 Tanggal: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
                    )
                else:
                    st.info("Tidak ada data tanggal valid")
            else:
                st.info("Kolom 'Tanggal Masuk' tidak ditemukan")

        # --- FILTER KATEGORI ---
        # Inisialisasi dictionary filter_selection
        filter_selection = {}

        # Definisi kolom di luar expander agar bisa diakses nanti
        core_columns = [
            ("Status Aktif", "✅"),
            ("Status Kepegawaian", "👤"),
            ("Unit Kerja", "🏭")
        ]

        detail_columns = [
            ("Klasifikasi Jabatan", "📑"),
            ("Jabatan", "💼"),
            ("Lokasi Kerja", "🗺️")
        ]

        internal_columns = [
            ("Sub Unit Kerja", "🧩"),
            ("Jenis", "⚙️"),
            ("Department Name", "🏷️")
        ]

        all_columns = core_columns + detail_columns + internal_columns

        with st.sidebar.expander("🔍 **Filter Kategori**", expanded=True):
            # Kelompok 1: Status & Unit
            st.markdown("##### 🏢 Organisasi & Status")
            for col_name, icon in core_columns:
                if col_name in df_cleaned.columns:
                    unique_values = sorted(
                        df_cleaned[col_name].dropna().astype(str).unique().tolist()
                    )
                    
                    if unique_values:
                        # Gunakan session_state untuk menyimpan nilai multiselect
                        key = f'filter_{col_name}'
                        if key not in st.session_state['filter_values']:
                            st.session_state['filter_values'][key] = []
                        
                        selected_values = st.multiselect(
                            f"{icon} {col_name}",
                            unique_values,
                            default=st.session_state['filter_values'][key],
                            key=key
                        )
                        
                        # Update session state
                        st.session_state['filter_values'][key] = selected_values
                        
                        if selected_values:
                            filter_selection[col_name] = selected_values
            
            # Kelompok 2: Posisi & Lokasi
            st.markdown("##### 📍 Posisi & Lokasi")
            for col_name, icon in detail_columns:
                if col_name in df_cleaned.columns:
                    unique_values = sorted(
                        df_cleaned[col_name].dropna().astype(str).unique().tolist()
                    )
                    
                    if unique_values:
                        # Gunakan session_state untuk menyimpan nilai multiselect
                        key = f'filter_{col_name}'
                        if key not in st.session_state['filter_values']:
                            st.session_state['filter_values'][key] = []
                        
                        selected_values = st.multiselect(
                            f"{icon} {col_name}",
                            unique_values,
                            default=st.session_state['filter_values'][key],
                            key=key
                        )
                        
                        # Update session state
                        st.session_state['filter_values'][key] = selected_values
                        
                        if selected_values:
                            filter_selection[col_name] = selected_values
            
            # Kelompok 3: Detail Internal
            with st.expander("Detail Internal"):
                for col_name, icon in internal_columns:
                    if col_name in df_cleaned.columns:
                        unique_values = sorted(
                            df_cleaned[col_name].dropna().astype(str).unique().tolist()
                        )
                        
                        if unique_values:
                            # Gunakan session_state untuk menyimpan nilai multiselect
                            key = f'filter_{col_name}'
                            if key not in st.session_state['filter_values']:
                                st.session_state['filter_values'][key] = []
                            
                            selected_values = st.multiselect(
                                f"{icon} {col_name}",
                                unique_values,
                                default=st.session_state['filter_values'][key],
                                key=key
                            )
                            
                            # Update session state
                            st.session_state['filter_values'][key] = selected_values
                            
                            if selected_values:
                                filter_selection[col_name] = selected_values

        # --- Terapkan Semua Filter Kategori ---
        for col_name, selected_values in filter_selection.items():
            if selected_values:
                df_filtered = df_filtered[
                    df_filtered[col_name].astype(str).isin(selected_values)
                ]
                # Cari icon yang sesuai
                icon = next((i for c, i in all_columns if c == col_name), "")
                active_filters.append(f"{icon} {col_name}: {', '.join(selected_values)}")
                
        # ========================================
        # TAB: Peta Lokasi Karyawan — INTERAKTIF (Plotly + plotly_events)
        # ========================================
        with tab_map:
            # Pastikan kolom lokasi dan jenis tersedia
            if 'Sub Unit Kerja' not in df_filtered.columns:
                st.error("❌ Kolom 'Sub Unit Kerja' tidak ditemukan.")
                st.stop()

            location_col = 'Sub Unit Kerja'
            jenis_col = 'Jenis' if 'Jenis' in df_filtered.columns else None

            # Hitung jumlah per lokasi
            lokasi_counts = df_filtered[location_col].value_counts().reset_index()
            lokasi_counts.columns = [location_col, 'Jumlah Karyawan']

            # Hitung breakdown laut/darat (jika kolom Jenis ada)
            if jenis_col:
                df_laut = df_filtered[df_filtered[jenis_col].str.contains('Laut', case=False, na=False)]
                df_darat = df_filtered[df_filtered[jenis_col].str.contains('Darat', case=False, na=False)]
                laut_counts = df_laut[location_col].value_counts().reindex(lokasi_counts[location_col], fill_value=0)
                darat_counts = df_darat[location_col].value_counts().reindex(lokasi_counts[location_col], fill_value=0)
                lokasi_counts['Laut'] = laut_counts.values
                lokasi_counts['Darat'] = darat_counts.values
            else:
                lokasi_counts['Laut'] = 0
                lokasi_counts['Darat'] = 0

            st.subheader(f"📊 Sebaran Karyawan berdasarkan {location_col}")

            # Statistik ringkas
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total Lokasi", len(lokasi_counts))
            with col_stat2:
                top_loc = lokasi_counts.iloc[0] if not lokasi_counts.empty else None
                st.metric("Lokasi Terbanyak", top_loc[location_col] if top_loc is not None else "N/A")
            with col_stat3:
                st.metric("Jumlah di Lokasi Tersebut", top_loc['Jumlah Karyawan'] if top_loc is not None else 0)

            # === Buat peta interaktif ===
            try:
                geojson = requests.get(GEOJSON_URL, timeout=10).json()

                # Plotly Choropleth Map — support klik event!
                fig = px.choropleth_map(
                    lokasi_counts,
                    geojson=geojson,
                    locations=location_col,
                    featureidkey="properties.Nama Pelabuhan",
                    color='Jumlah Karyawan',
                    color_continuous_scale='Blues',
                    range_color=(0, lokasi_counts['Jumlah Karyawan'].max()),
                    hover_name=location_col,
                    hover_data={
                        'Jumlah Karyawan': True,
                        'Laut': True,
                        'Darat': True,
                        location_col: False
                    },
                    custom_data=[location_col],  # ✅ kunci untuk event klik
                    zoom=4.8,
                    center={"lat": -2.5, "lon": 118.0},
                    map_style="carto-positron",
                    opacity=0.7,
                    height=550
                )

                fig.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    coloraxis_colorbar=dict(
                        title="Jumlah<br>Karyawan",
                        thickness=15,
                        len=0.6,
                        xanchor="left", x=0.01
                    )
                )
                fig.update_traces(
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        "👥 Total: %{customdata[1]}<br>"
                        "🚢 Laut: %{customdata[2]}<br>"
                        "🏢 Darat: %{customdata[3]}<extra></extra>"
                    ),
                    customdata=lokasi_counts[[location_col, 'Jumlah Karyawan', 'Laut', 'Darat']].values
                )

                # ✅ Tangkap klik
                clicked = plotly_events(
                    fig,
                    click_event=True,
                    hover_event=False,
                    select_event=False,
                    key="map_click"
                )

                st.plotly_chart(fig, use_container_width=True)

                # ✅ Handle klik → filter lokasi
                if clicked:
                    try:
                        custom = clicked[0].get('customdata', [])
                        if len(custom) >= 1:
                            lokasi_terpilih = str(custom[0])
                            # Update filter session state
                            filter_key = 'filter_Lokasi Kerja'
                            st.session_state['filter_values'][filter_key] = [lokasi_terpilih]
                            st.success(f"✅ Difilter ke: **{lokasi_terpilih}**", icon="📍")
                            st.rerun()
                    except Exception as e:
                        st.warning(f"⚠️ Gagal baca klik peta: {e}")

            except Exception as e:
                st.error(f"❌ Gagal memuat peta: {e}")
                st.info("Cek koneksi internet atau validitas GeoJSON.")
        # ========================================
        # TAB: DASHBOARD ANALISIS
        # ========================================
        with tab_analysis:    
            if df_filtered.empty:
                st.error("❌ Data kosong! Silakan sesuaikan filter Anda.")
                st.stop()
            
            # KPI CARDS
            total_karyawan = len(df_filtered)
            penempatan_laut = 0
            penempatan_darat = 0
            aktif = 0
            tidak_aktif = 0

            if 'Status Kepegawaian' in df_filtered.columns:
                aktif = (
                    (df_filtered['Status Kepegawaian'] == 'PKWTT') |
                    (df_filtered['Status Kepegawaian'] == 'PKWT')
                ).sum()
                tidak_aktif = (
                    (df_filtered['Status Kepegawaian'] == 'Cuti') |
                    (df_filtered['Status Kepegawaian'] == 'Resign') |
                    (df_filtered['Status Kepegawaian'] == 'Pensiun') |
                    (df_filtered['Status Kepegawaian'] == 'Terminated')
                ).sum()

            # Hitung penempatan laut/darat jika ada kolom Jenis
            if 'Jenis' in df_filtered.columns:
                penempatan_laut = df_filtered[df_filtered['Jenis'].str.contains('Laut', case=False, na=False)].shape[0]
                penempatan_darat = df_filtered[df_filtered['Jenis'].str.contains('Darat', case=False, na=False)].shape[0]

            # Hitung rata-rata masa kerja
            avg_masa_kerja = 0
            if 'Tanggal Masuk' in df_filtered.columns and not df_filtered['Tanggal Masuk'].isnull().all():
                df_filtered['Masa Kerja'] = (today - df_filtered['Tanggal Masuk']).dt.days / 365.25
                avg_masa_kerja = df_filtered['Masa Kerja'].mean()

            # Perhitungan persentase perubahan total karyawan
            current_period_total_employees = total_karyawan

            # Ambil data bulan lalu dari df_cleaned (bukan df_filtered)
            previous_period_total_employees = 0
            if 'Tanggal Masuk' in df_cleaned.columns:
                last_month = (pd.Timestamp.now() - pd.DateOffset(months=1)).to_period('M')
                last_month_data = df_cleaned[df_cleaned['Tanggal Masuk'].dt.to_period('M') == last_month]
                previous_period_total_employees = len(last_month_data)

            # Jika tidak ada data bulan lalu, gunakan nilai default
            if previous_period_total_employees == 0:
                previous_period_total_employees = 1  # Hindari pembagian dengan nol

            # Hitung persentase perubahan
            if previous_period_total_employees > 0:
                percentage_change = ((current_period_total_employees - previous_period_total_employees) / previous_period_total_employees) * 100
                delta_text = f"{'+' if percentage_change >= 0 else ''}{percentage_change:.1f}% vs periode lalu"
                delta_color_hex = "#4ade80" if percentage_change >= 0 else "#e74c3c"
            else:
                delta_text = "N/A"
                delta_color_hex = "rgba(255, 255, 255, 0.7)"

            # Layout KPI Cards
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">TOTAL KARYAWAN</div>
                        <div class="metric-value">{current_period_total_employees:,}</div>
                        <div class="metric-delta" style="color: {delta_color_hex};">
                           📊 {delta_text}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                pct_laut = (penempatan_laut / total_karyawan * 100) if total_karyawan > 0 else 0
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Penempatan Laut</div>
                        <div class="metric-value">{penempatan_laut:,}</div>
                        <div class="metric-delta" style="color: #4ade80;">
                            ⚓ {pct_laut:.1f}% dari total
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                pct_darat = (penempatan_darat / total_karyawan * 100) if total_karyawan > 0 else 0
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Penempatan Darat</div>
                        <div class="metric-value">{penempatan_darat:,}</div>
                        <div class="metric-delta" style="color: #4ade80;">
                            🏢 {pct_darat:.1f}% dari total
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Rata-rata Masa Kerja</div>
                        <div class="metric-value">{avg_masa_kerja:.1f} Tahun</div>
                        <div class="metric-delta" style="color: #a29bfe;">
                        <div class="metric-delta">📅 Tahun</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # ROW 2: DISTRIBUSI JABATAN & GENDER
            col_jab, col_gen, col_status = st.columns([1, 1, 1])

            with col_jab:
                st.markdown('<div class="section-header"><h3>🏫 Pendidikan</h3></div>', unsafe_allow_html=True)
            
                if 'Band Level' in df_filtered.columns:
                    level_df = df_filtered['Band Level'].value_counts().reset_index()
                    level_df.columns = ['Band Level', 'Jumlah']
                    
                    chart_jabatan = alt.Chart(level_df).mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10
                    ).encode(
                        x=alt.X('Band Level:N', title='Band Level', axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('Jumlah:Q', title='Jumlah Karyawan'),
                        color=alt.Color('Band Level:N', scale=alt.Scale(scheme='set2'), legend=None),
                        tooltip=['Band Level', 'Jumlah']
                    ).properties(height=350)
                    
                    text = chart_jabatan.mark_text(
                        dy=-10,
                        color='white',
                        fontSize=14,
                        fontWeight='bold'
                    ).encode(
                        text='Jumlah:Q'
                    )
                    
                    st.altair_chart(chart_jabatan + text, use_container_width=True)
                else:
                    st.info("Kolom 'Klasifikasi Jabatan' tidak ditemukan.")

            with col_gen:
                st.markdown('<div class="section-header"><h3>👨‍🦱👩‍🦰 Jenis Kelamin</h3></div>', unsafe_allow_html=True)
                
                # Kolom Jenis Kelamin
                if 'Jenis Kelamin' in df_filtered.columns:
                    gender_df = df_filtered['Jenis Kelamin'].value_counts().reset_index()
                    gender_df.columns = ['Jenis Kelamin', 'Jumlah']
                    
                    fig_pie = px.pie(
                        gender_df,
                        values='Jumlah',
                        names='Jenis Kelamin',
                        color='Jenis Kelamin',
                        color_discrete_map={
                            'Laki-laki': "#0084FF",
                            'Perempuan': "#FF0048",
                        },
                        hole=0.4,
                        height=400
                    )
                    
                    fig_pie.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        textfont_size=14
                    )
                    
                    fig_pie.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        )
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_status:
                if 'Status Kepegawaian' in df_filtered.columns:
                    st.markdown('<div class="section-header"><h3>👨‍💼 Distribusi Status Karyawan</h3></div>', unsafe_allow_html=True)
                    
                    keaktifan_df = df_filtered['Status Kepegawaian'].value_counts().reset_index()
                    keaktifan_df.columns = ['Status Aktif', 'Jumlah']
                    
                    fig_pie = px.pie(
                        keaktifan_df,
                        values='Jumlah',
                        names='Status Aktif',
                        color='Status Aktif',
                        color_discrete_map={
                            'PKWTT': "#00ff0d",
                            'PKWT': '#00d2ff',
                            'Cuti': "#fffb00",
                            'Resign': '#e74c3c',
                            'Pensiun': '#95a5a6',
                            'Terminated': '#c0392b'
                        },
                        hole=0.4,
                        height=400
                    )
                    
                    fig_pie.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        textfont_size=14
                    )
                    
                    fig_pie.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        )
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")
            if 'Status Kepegawaian' in df_filtered.columns:
                col_vis1, col_vis2 = st.columns([2, 1])
            
                with col_vis1:
                    st.markdown('<div class="section-header"><h3>📈 Tren Rekrutmen Bulanan</h3></div>', unsafe_allow_html=True)
        
                    if 'Tanggal Masuk' in df_filtered.columns:
                        df_filtered['Bulan Masuk'] = df_filtered['Tanggal Masuk'].dt.to_period('M').dt.to_timestamp()
                        monthly_hires = df_filtered.groupby('Bulan Masuk').size().reset_index(name='Jumlah Karyawan')
                        
                        chart_trend = alt.Chart(monthly_hires).mark_line(point=True).encode(
                            x=alt.X('Bulan Masuk:T', title='Bulan Masuk'),
                            y=alt.Y('Jumlah Karyawan:Q', title='Jumlah Karyawan'),
                            tooltip=['Bulan Masuk', 'Jumlah Karyawan']
                        ).properties(height=350)
                        
                        st.altair_chart(chart_trend, use_container_width=True)
                    else:
                        st.info("Kolom 'Tanggal Masuk' tidak ditemukan.")
                
                with col_vis2:
                    st.markdown('<div class="section-header"><h3>👨‍👩‍👧‍👦 Distribusi Generasi</h3></div>', unsafe_allow_html=True)
        
                    if 'Tanggal Lahir' in df_filtered.columns:
                        current_year = datetime.now().year
            
                        def classify_generation(dob):
                            if pd.isnull(dob):
                                return 'Unknown'
                            age = current_year - dob.year
                            if age >= 60:
                                return 'Boomers'
                            elif 44 <= age <= 59:
                                return 'Gen X'
                            elif 28 <= age <= 43:
                                return 'Millenials'
                            elif age <= 27:
                                return 'Gen Z'
                            else:
                                return 'Unknown'
            
                        df_filtered['Generasi'] = df_filtered['Tanggal Lahir'].apply(classify_generation)
            
                        # Filter out Unknown
                        generasi_df = df_filtered[df_filtered['Generasi'] != 'Unknown']['Generasi'].value_counts().reset_index()
                        generasi_df.columns = ['Generasi', 'Jumlah']
                        
                        # Calculate total and percentage
                        total_karyawan = generasi_df['Jumlah'].sum()
                        generasi_df['Persentase'] = (generasi_df['Jumlah'] / total_karyawan * 100).round(1)
                        
                        # Sort by a specific order
                        order = ['Boomers','Millenials', 'Gen X', 'Gen Z']
                        generasi_df['Generasi'] = pd.Categorical(generasi_df['Generasi'], categories=order, ordered=True)
                        generasi_df = generasi_df.sort_values('Generasi')
                        
                        emoji_map = {
                            'Millenials': '👨‍💻',
                            'Gen X': '👨‍💼',
                            'Gen Z': '🧑',
                            'Boomers': '👴'
                        }
                        
                        for idx, row in generasi_df.iterrows():
                            emoji = emoji_map.get(row['Generasi'], '👤')
                            
                            st.markdown(f"**{emoji} {row['Generasi']}**")
                            st.markdown(f"{row['Jumlah']:,} karyawan ({row['Persentase']}%)")
                            
                            # Progress bar
                            st.progress(row['Persentase'] / 100)
                            st.markdown("<br>", unsafe_allow_html=True)
                    else:
                        st.info("Kolom 'Tanggal Lahir' tidak ditemukan.")
            
            # ===============================
            # DATA AKHIR & DOWNLOAD
            # ===============================
            st.header("📑 Tabel Data Hasil Filter")
            
            st.dataframe(
                df_filtered,
                use_container_width=True,
                height=400
            )
            
            st.caption(f"Menampilkan {len(df_filtered):,} dari {len(df_cleaned):,} data setelah filter")
            
            # Download
            col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
            
            with col_dl1:
                csv_filtered = to_csv(df_filtered)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_filtered,
                    file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_dl2:
                if st.button("📊 Generate Report", use_container_width=True):
                    st.info("Fitur laporan akan segera tersedia!")

    except Exception as e:
        st.error(f"❗ Terjadi kesalahan saat memproses file:")
        st.exception(e)
        st.info("💡 Tips: Pastikan format tanggal di file Anda benar (DD/MM/YYYY atau YYYY-MM-DD)")
