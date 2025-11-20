import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from streamlit_folium import st_folium
import folium
import requests
import re
import time
from streamlit_gsheets import GSheetsConnection

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
col_title1, col_title2,  col_title3 = st.columns([3, 1, 1])
with col_title1:
    st.title("👥 Dashboard Demografi Karyawan FERIZYAN")
with col_title3:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/ASDP_Logo_2023.png/1199px-ASDP_Logo_2023.png", width=150)

st.markdown("Pastikan Anda sudah membuat file `.streamlit/secrets.toml` dengan benar.")

# Ganti dengan URL Google Sheet Anda
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1qDWIuC1Sc5QEIoujNkm8jb0_IxQZMsTypRdkZPkHdGU/edit?usp=sharing"

# Menggunakan "gsheets" sebagai nama koneksi
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=3600)
def load_and_clean_data(df_raw):
    """Memuat, membersihkan, dan mengubah data dari file yang diunggah."""
    df = df_raw.copy() # Buat salinan untuk menghindari modifikasi data asli di cache
    # --- 1. GANTI NAMA KOLOM ---
    rename_map = {
        'Status_Kepegawaian': 'Status Kepegawaian', 'Sub_unker': 'Sub Unit Kerja',
        'Unit_Kerja': 'Unit Kerja', 'TglLahir': 'Tanggal Lahir',
        'Keaktifan': 'Status Aktif', 'Klasifikasi_Jabatan': 'Klasifikasi Jabatan',
        'Department_Name': 'Department Name', 'Retirement Date': 'Tanggal Pensiun',
        'Jenis_Kelamin': 'Jenis Kelamin', 'Lokasi_Kerja': 'Lokasi Kerja',
        'Date of Joining': 'Tanggal Masuk', 'Date Of Exit': 'Tanggal Keluar',
        'Kelas_Kapal': 'Kelas Kapal'
    }
    df.rename(columns=rename_map, inplace=True)

    # --- 2. KONVERSI TANGGAL ---
    date_cols = ['Tanggal Masuk', 'Tanggal Keluar', 'Tanggal Lahir', 'Tanggal Pensiun']
    df = safe_date_conversion(df, date_cols)
    today = pd.Timestamp(datetime.now().date())

    # --- 3. CLEANING DATA ---
    if 'Status Kepegawaian' in df.columns:
        df['Status Kepegawaian'] = df['Status Kepegawaian'].astype(str).str.upper().str.strip()
        df.loc[df['Status Kepegawaian'].str.contains('CONTRACT', na=False), 'Status Kepegawaian'] = 'PKWT'
        df.loc[df['Status Kepegawaian'].str.contains('EMPLOYEE', na=False), 'Status Kepegawaian'] = 'PKWTT'

    if 'Jenis Kelamin' in df.columns:
        df['Jenis Kelamin'] = df['Jenis Kelamin'].astype(str).str.upper().str.strip()
        df.loc[df['Jenis Kelamin'].str.startswith('L', na=False), 'Jenis Kelamin'] = 'Laki-laki'
        df.loc[df['Jenis Kelamin'].str.startswith('P', na=False), 'Jenis Kelamin'] = 'Perempuan'

    if 'Sub Unit Kerja' in df.columns:
        df['Sub Unit Kerja'] = df['Sub Unit Kerja'].astype(str).str.upper().str.strip()

    # --- 4. UPDATE STATUS BERDASARKAN TANGGAL ---
    if 'Tanggal Pensiun' in df.columns:
        df.loc[(df['Tanggal Pensiun'] <= today) & df['Tanggal Pensiun'].notna(), 'Status Kepegawaian'] = 'PENSIUN'
    if 'Tanggal Keluar' in df.columns:
        df.loc[(df['Tanggal Keluar'] <= today) & df['Tanggal Keluar'].notna(), 'Status Kepegawaian'] = 'RESIGN'

    # --- 5. TENTUKAN STATUS AKTIF/TIDAK AKTIF ---
    if 'Status Kepegawaian' in df.columns:
        exit_statuses = ['PENSIUN', 'RESIGN', 'TERMINATED', 'CUTI']
        df['Status Aktif'] = 'Aktif'
        df.loc[df['Status Kepegawaian'].isin(exit_statuses), 'Status Aktif'] = 'Tidak Aktif'

    # --- 6. HAPUS KOLOM KOSONG ---
    missing_perc = (df.isnull().sum() / len(df)) * 100
    cols_to_drop = missing_perc[missing_perc == 100].index
    df.drop(columns=cols_to_drop, inplace=True)
    
    return df

def filter_active_only(df, today=pd.Timestamp(datetime.now().date())):
    """Dari DataFrame apa pun, ambil hanya karyawan yang AKTIF HARI INI."""
    if df.empty:
        return df

    # 1. Karyawan harus sudah masuk
    mask = (df['Tanggal Masuk'].notna()) & (df['Tanggal Masuk'] <= today)

    # 2. Karyawan harus belum keluar (Tanggal Keluar >= Hari Ini ATAU kosong)
    if 'Tanggal Keluar' in df.columns:
        mask &= (df['Tanggal Keluar'].isna()) | (df['Tanggal Keluar'] >= today)
    if 'Tanggal Pensiun' in df.columns:
        mask &= (df['Tanggal Pensiun'].isna()) | (df['Tanggal Pensiun'] >= today)

    # 3. Status kepegawaian bukan merupakan status keluar
    if 'Status Kepegawaian' in df.columns:
        exit_statuses = ['RESIGN', 'PENSIUN', 'TERMINATED']
        mask &= ~df['Status Kepegawaian'].isin(exit_statuses)

    return df[mask]

try:
    with st.spinner("⏳ Menghubungkan ke Google Sheets..."):
        df_raw = conn.read(spreadsheet=spreadsheet_url, ttl=3600)
    
    st.success(f"✅ Berhasil memuat data dari Google Sheets!")
    
    with st.spinner("⏳ Membersihkan dan memproses data..."):
        df_cleaned = load_and_clean_data(df_raw)

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
        st.dataframe(df_cleaned, use_container_width=True, height=500)
        
        csv_raw = to_csv(df_cleaned)
        st.download_button(
            label="Download Data Mentah (CSV)",
            data=csv_raw,
            file_name=f"cleaned_raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
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

    def create_multiselect_filter(col_name, icon, df):
        if col_name in df.columns:
            unique_values = sorted(df[col_name].dropna().astype(str).unique().tolist())
            if unique_values:
                key = f'filter_{col_name}'
                if key not in st.session_state['filter_values']:
                    st.session_state['filter_values'][key] = []
                
                selected = st.multiselect(
                    f"{icon} {col_name}", unique_values,
                    default=st.session_state['filter_values'][key], key=key
                )
                if selected:
                    filter_selection[col_name] = selected

    with st.sidebar.expander("🔍 **Filter Kategori**", expanded=True):
        st.markdown("##### 🏢 Organisasi")
        for col_name, icon in core_columns:
            create_multiselect_filter(col_name, icon, df_cleaned)
        st.markdown("##### 📍 Posisi & Lokasi")
        for col_name, icon in detail_columns:
            create_multiselect_filter(col_name, icon, df_cleaned)
        with st.expander("Detail Internal"):
            for col_name, icon in internal_columns:
                create_multiselect_filter(col_name, icon, df_cleaned)

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
    # TAB: Peta Lokasi Karyawan
    # ========================================
    with tab_map:
        if 'Lokasi Kerja' in df_filtered.columns or 'Sub Unit Kerja' in df_filtered.columns:
            location_col = 'Lokasi Kerja' if 'Lokasi Kerja' in df_filtered.columns else 'Sub Unit Kerja'
            Jenis_col = 'Jenis' if 'Jenis' in df_filtered.columns else None

            # --- Agregasi Data untuk Peta (Lebih Efisien) ---
            lokasi_counts = df_filtered[location_col].value_counts().reset_index()
            lokasi_counts.columns = [location_col, 'Jumlah Karyawan']

            # Pre-calculate counts for 'Laut' and 'Darat'
            if Jenis_col:
                jenis_agg = df_filtered.groupby(location_col)[Jenis_col].apply(
                    lambda x: pd.Series({
                        'Laut': x.str.contains('Laut', case=False, na=False).sum(),
                        'Darat': x.str.contains('Darat', case=False, na=False).sum()
                    })
                ).unstack(fill_value=0)
                lokasi_counts = pd.merge(lokasi_counts, jenis_agg, on=location_col, how='left')
                lokasi_counts[['Laut', 'Darat']] = lokasi_counts[['Laut', 'Darat']].fillna(0).astype(int)

            st.subheader(f"📊 Sebaran Karyawan berdasarkan {location_col}")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total Lokasi", len(lokasi_counts))
            with col_stat2:
                st.metric("Lokasi Terbanyak", lokasi_counts.iloc[0][location_col] if not lokasi_counts.empty else "N/A")
            with col_stat3:
                st.metric("Jumlah di Lokasi Tersebut", lokasi_counts.iloc[0]['Jumlah Karyawan'] if not lokasi_counts.empty else 0)

            # --- Fungsi Helper untuk Peta ---
            def create_map_popup_html(name, jumlah, laut, darat):
                return f"""
                <div style="font-family: 'Segoe UI', sans-serif; min-width: 280px; padding: 10px; background: #fff; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                    <h4 style="margin: 0 0 10px 0; color: #2a5298; border-bottom: 2px solid #667eea; padding-bottom: 5px;">📍 {name}</h4>
                    <div style="font-size: 14px;">
                        <p style="margin: 5px 0;"><strong>👥 Total Karyawan:</strong> <span style="float: right; font-weight: bold;">{jumlah}</span></p>
                        <p style="margin: 5px 0;"><strong>🚢 Penempatan Laut:</strong> <span style="float: right; font-weight: bold;">{laut}</span></p>
                        <p style="margin: 5px 0;"><strong>🏢 Penempatan Darat:</strong> <span style="float: right; font-weight: bold;">{darat}</span></p>
                    </div>
                </div>
                """

            def get_marker_style(count):
                if count > 50: return 'red', 'star'
                if count > 20: return 'orange', 'info-sign'
                if count > 0: return 'blue', 'user'
                return 'gray', 'map-marker'

            # --- Render Peta ---
            m = folium.Map(
                location=[-2.5, 118.0], 
                zoom_start=5, 
                tiles='OpenStreetMap'
            )
                    
            with st.spinner("Memuat data peta..."):
                try:
                    response = requests.get(GEOJSON_URL, timeout=10)
                    geojson_data = response.json()

                    # Buat dictionary lookup untuk data karyawan
                    lokasi_data = lokasi_counts.set_index(location_col).to_dict('index')

                    for feature in geojson_data.get('features', []):
                        props = feature.get('properties', {})
                        name = props.get('Nama Pelabuhan', 'Unknown')
                        data = lokasi_data.get(name)

                        if data and 'geometry' in feature and feature['geometry']['type'] == 'Point':
                            coords = feature['geometry']['coordinates']
                            jumlah = data.get('Jumlah Karyawan', 0)
                            laut = data.get('Laut', 0)
                            darat = data.get('Darat', 0)

                            if jumlah > 0:
                                color, icon = get_marker_style(jumlah)
                                popup_html = create_map_popup_html(name, jumlah, laut, darat)
                                
                                folium.Marker(
                                    location=[coords[1], coords[0]],
                                    popup=folium.Popup(popup_html, max_width=300),
                                    tooltip=f"{name} ({jumlah} karyawan)",
                                    icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
                                ).add_to(m)

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error saat mengunduh GeoJSON: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error saat memproses GeoJSON: {str(e)}")
            
            st_folium(m, width=None, height=600, returned_objects=[])
                    
                    
    # ========================================
    # TAB: DASHBOARD ANALISIS
    # ========================================
    with tab_analysis:    
        if df_filtered.empty:
            st.error("❌ Data kosong! Silakan sesuaikan filter Anda.")
            st.stop()
        
        # =================================================================
        # UTAMA: Filter dashboard ini HANYA untuk karyawan aktif
        # =================================================================
        df_analysis = filter_active_only(df_filtered.copy())

        if df_analysis.empty:
            st.warning("Tidak ada karyawan aktif yang cocok dengan filter yang Anda pilih.")
            st.stop()
        
        # --- 1. PERHITUNGAN KPI ---
        total_karyawan = len(df_analysis)
        penempatan_laut = 0
        penempatan_darat = 0
        avg_masa_kerja = 0
        
        # Hitung penempatan
        if 'Jenis' in df_analysis.columns:
            penempatan_laut = df_analysis[
                df_analysis['Jenis'].str.contains('Laut', case=False, na=False)
            ].shape[0]
            penempatan_darat = total_karyawan - penempatan_laut

        # Hitung masa kerja
        if 'Tanggal Masuk' in df_analysis.columns and not df_analysis['Tanggal Masuk'].isnull().all():
            df_analysis['Masa Kerja'] = (today - df_analysis['Tanggal Masuk']).dt.days / 365.25
            avg_masa_kerja = df_analysis['Masa Kerja'].mean()

        # Hitung perubahan vs periode lalu
        last_month_end = (pd.Timestamp.now().to_period('M').to_timestamp() - pd.Timedelta(days=1))
        df_last_month_active = filter_active_only(df_cleaned, today=last_month_end)
        previous_period_total_employees = len(df_last_month_active)
        current_period_total_employees = total_karyawan
        
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

        # --- 2. RENDER KPI CARDS ---
        def render_metric_card(label, value, delta_text="", delta_color="#4ade80", icon=""):
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-delta" style="color: {delta_color};">
                       {icon} {delta_text}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        col1, col2, col3, col4= st.columns(4)
        with col1:
            render_metric_card("Total Karyawan Aktif", f"{total_karyawan:,}", delta_text, delta_color_hex, "📊")
        with col2:
            pct_laut = (penempatan_laut / total_karyawan * 100) if total_karyawan > 0 else 0
            render_metric_card("Penempatan Laut", f"{penempatan_laut:,}", f"{pct_laut:.1f}% dari total", icon="⚓")
        with col3:
            pct_darat = (penempatan_darat / total_karyawan * 100) if total_karyawan > 0 else 0
            render_metric_card("Penempatan Darat", f"{penempatan_darat:,}", f"{pct_darat:.1f}% dari total", icon="🏢")
        with col4:
            render_metric_card("Rata-rata Masa Kerja", f"{avg_masa_kerja:.1f} Tahun", "Tahun", "#a29bfe", "📅")

        st.markdown("<br>", unsafe_allow_html=True)
        
        #ROW 1: Distribusi Status, Jenis Kelamin, Generasi
        col_status, col_gen, col_hirarchy  = st.columns([1, 1, 1])

        with col_hirarchy:
            st.markdown('<div class="section-header"><h3>👨‍👩‍👧‍👦 Distribusi Generasi</h3></div>', unsafe_allow_html=True)
    
            if 'Tanggal Lahir' in df_analysis.columns:
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
    
                df_analysis['Generasi'] = df_analysis['Tanggal Lahir'].apply(classify_generation)
    
                # Filter out Unknown 
                generasi_df = df_analysis[df_analysis['Generasi'] != 'Unknown']['Generasi'].value_counts().reset_index()
                generasi_df.columns = ['Generasi', 'Jumlah']
                
                # Calculate total and percentage
                generasi_df['Persentase'] = (generasi_df['Jumlah'] / len(df_analysis) * 100).round(1)
                
                # Sort by a specific order
                order = ['Boomers', 'Gen X', 'Millenials', 'Gen Z'] # Urutan kronologis
                generasi_df['Generasi'] = pd.Categorical(generasi_df['Generasi'], categories=order, ordered=True) # Terapkan urutan
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

        with col_gen:
            st.markdown('<div class="section-header"><h3>👨‍🦱👩‍🦰 Jenis Kelamin</h3></div>', unsafe_allow_html=True)
            if 'Jenis Kelamin' in df_analysis.columns:
                # Hitung distribusi
                gender_counts = df_analysis['Jenis Kelamin'].value_counts()
                total = gender_counts.sum()
                laki = 0
                perempuan = 0

                if total > 0:
                    laki = gender_counts.get('Laki-laki', 0)
                    perempuan = gender_counts.get('Perempuan', 0)
                
                gender_df = gender_counts.reset_index()
                gender_df.columns = ['Jenis Kelamin', 'Jumlah']

                fig_pie = px.pie(
                    gender_df,
                    values='Jumlah',
                    names='Jenis Kelamin',
                    hole=0.35,
                    height=400,
                    color='Jenis Kelamin',
                    color_discrete_map={
                        'Laki-laki': '#1e3c72',
                        'Perempuan': '#f75196'
                    }
                )
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    pull=[0.05, 0]
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
            else:
                st.info("Tidak ada data jenis kelamin untuk ditampilkan.")
                
            col_num1, col_num2 = st.columns(2)
            with col_num1:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 16px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    color: white;
                ">
                    <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">Laki-laki</div>
                    <div style="font-size: 28px; font-weight: bold;">{laki:,}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_num2:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f75196 0%, #ff7aa2 100%);
                    padding: 16px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    color: white;
                ">
                    <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">Perempuan</div>
                    <div style="font-size: 28px; font-weight: bold;">{perempuan:,}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_status:
            if 'Status Kepegawaian' in df_analysis.columns:
                st.markdown('<div class="section-header"><h3>👨‍💼 Distribusi Status Karyawan</h3></div>', unsafe_allow_html=True)
                
                keaktifan_df = df_analysis['Status Kepegawaian'].value_counts().reset_index()
                keaktifan_df.columns = ['Status Aktif', 'Jumlah']
                
                fig_pie = px.pie(
                    keaktifan_df,
                    values='Jumlah',
                    names='Status Aktif',
                    hole=0.35,
                    height=400,
                    color='Status Aktif',
                    color_discrete_map={
                        'PKWTT': "#9d00fffb",
                        'PKWT': '#00d2ff',
                        'Cuti': "#fffb00",
                        'Resign': '#e74c3c',
                        'Pensiun': '#95a5a6',
                        'Terminated': '#c0392b'
                    }
                )
                
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    pull=[0.05, 0]
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
                
                col_num3, col_num4 = st.columns(2)
                with col_num3:
                    pkwtt_count = keaktifan_df.loc[keaktifan_df['Status Aktif'] == 'PKWTT', 'Jumlah'].values
                    pkwtt_count = pkwtt_count[0] if len(pkwtt_count) > 0 else 0
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #9d00fffb 0%, #6a00ff 100%);
                        padding: 16px;
                        border-radius: 12px;
                        text-align: center;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                        color: white;
                    ">
                        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">PKWTT</div>
                        <div style="font-size: 28px; font-weight: bold;">{pkwtt_count:,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_num4:
                    pkwt_count = keaktifan_df.loc[keaktifan_df['Status Aktif'] == 'PKWT', 'Jumlah'].values
                    pkwt_count = pkwt_count[0] if len(pkwt_count) > 0 else 0
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #00d2ff 0%, #0066ff 100%);
                        padding: 16px;
                        border-radius: 12px;
                        text-align: center;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                        color: white;
                    ">
                        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">PKWT</div>
                        <div style="font-size: 28px; font-weight: bold;">{pkwt_count:,}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        if 'Status Kepegawaian' in df_analysis.columns:
            col_vis1, col_vis2 = st.columns([2, 1])
        
            with col_vis1:
                st.markdown('<div class="section-header"><h3>🏫 Klasifikasi Jabatan</h3></div>', unsafe_allow_html=True)
                
                st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
                if 'Band Level' in df_analysis.columns:
                    level_df = df_analysis['Band Level'].value_counts().reset_index()
                    level_df.columns = ['Band Level', 'Jumlah']
                    
                    chart_band = alt.Chart(level_df).mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10
                    ).encode(
                        x=alt.X('Band Level:N', title='Klasifikasi Jabatan', axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('Jumlah:Q', title='Jumlah Karyawan'),
                        color=alt.Color('Band Level:N', scale=alt.Scale(scheme='blues'), legend=None),
                        tooltip=['Band Level', 'Jumlah']
                    ).properties(height=400)
                    
                    text = chart_band.mark_text(
                        dy=-10,
                        color='white',
                        fontSize=14,
                        fontWeight='bold'
                    ).encode(
                        text='Jumlah:Q'
                    )
                    
                    st.altair_chart(chart_band + text, use_container_width=True)
                else:
                    st.info("Kolom 'Klasifikasi Band Level' tidak ditemukan.")
            
            with col_vis2:
                st.markdown('<div class="section-header"><h3> Kantor Pusat Vs Cabang</h3></div>', unsafe_allow_html=True)
                if 'Unit Kerja' in df_analysis.columns:
                    kantor_df = df_analysis['Unit Kerja'].value_counts().reset_index()
                    kantor_df.columns = ['Unit Kerja', 'Jumlah']
                    
                    # Fungsi untuk mengklasifikasikan tipe kantor dengan lebih baik
                    def classify_office_type(unit_kerja):
                        unit_kerja_upper = str(unit_kerja).upper()
                        if 'HO' in unit_kerja_upper:
                            return 'Kantor Pusat'
                        elif 'REGIONAL' in unit_kerja_upper:
                            return 'Regional'
                        else:
                            return 'Kantor Cabang'
                    
                    kantor_df['Tipe Kantor'] = kantor_df['Unit Kerja'].apply(classify_office_type)
                    
                    kantor_summary = kantor_df.groupby('Tipe Kantor')['Jumlah'].sum().reset_index()
                    
                    fig_pie = px.pie(
                        kantor_summary,
                        values='Jumlah',
                        names='Tipe Kantor',
                        color='Tipe Kantor',
                        color_discrete_map={
                            'Kantor Pusat': "#0d47a1",  # Biru paling gelap
                            'Regional': '#42a5f5',      # Biru tengah
                            'Kantor Cabang': '#bbdefb', # Biru paling terang
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
                    
            #ROW 3: DISTRIBUSI KARYAWAN AKTIF
            st.markdown('<div class="section-header"><h3>📊 Analisis Detail per Lokasi Penempatan</h3></div>', unsafe_allow_html=True)

            if 'Jenis' in df_filtered.columns:
                col_laut, col_darat = st.columns(2)

                def render_summary_card(title, value, icon, background_gradient):
                    st.markdown(f"""
                    <div style="
                        background: {background_gradient};
                        border-radius: 15px;
                        padding: 25px;
                        color: white;
                        position: relative;
                        overflow: hidden;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
                        margin-bottom: 20px;
                    ">
                        <div style="font-size: 80px; position: absolute; top: -20px; right: -10px; opacity: 0.15;">{icon}</div>
                        <h3 style="margin: 0; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">{title}</h3>
                        <p style="font-size: 48px; font-weight: bold; margin: 5px 0 0 0;">{value:,}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                def create_breakdown_barchart(df, column_name, title, color_range):
                    """Membuat grafik batang"""
                    if column_name not in df.columns or df.empty:
                        st.info(f"Kolom '{column_name}' tidak tersedia.")
                        return

                    data = df[column_name].value_counts().nlargest(7).reset_index()
                    data.columns = [column_name, 'Jumlah']

                    chart = alt.Chart(data).mark_bar(
                        cornerRadius=5,
                        height=25
                    ).encode(
                        x=alt.X('Jumlah:Q', title=None, axis=None),
                        y=alt.Y(f'{column_name}:N', sort='-x', title=None, axis=alt.Axis(labelPadding=10), scale=alt.Scale(paddingInner=1)),
                        color=alt.Color('Jumlah:Q', scale=alt.Scale(range=color_range), legend=None),
                        tooltip=[alt.Tooltip(column_name, title=column_name), alt.Tooltip('Jumlah', title='Jumlah')]
                    ).properties(
                        title=alt.TitleParams(text=title, anchor='start', fontSize=20, fontWeight='bold', dy=-10)
                    )

                    text = chart.mark_text(
                        align='left', baseline='middle', dx=5, color='white', fontWeight='bold'
                    ).encode(text='Jumlah:Q')

                    st.altair_chart(chart + text, use_container_width=True)

                with col_laut:
                    laut_df = df_analysis[df_analysis['Jenis'].str.contains('Laut', case=False, na=False)]
                    render_summary_card("Total Karyawan Laut", len(laut_df), "⚓", "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)")
                    
                    create_breakdown_barchart(laut_df, 'Klasifikasi Jabatan', 'Breakdown Jabatan', ['#667eea', '#2a5298'])
                    st.markdown("---")
                    create_breakdown_barchart(laut_df, 'Tingkat Pendidikan', 'Tingkat Pendidikan', ['#89f7fe', '#66a6ff'])

                with col_darat:
                    darat_df = df_analysis[df_analysis['Jenis'].str.contains('Darat', case=False, na=False)]
                    render_summary_card("Total Karyawan Darat", len(darat_df), "🏢", "linear-gradient(135deg, #15803d 0%, #22c55e 100%)")
                    
                    create_breakdown_barchart(darat_df, 'Klasifikasi Jabatan', 'Breakdown Jabatan', ['#34d399', '#059669'])
                    st.markdown("---")
                    create_breakdown_barchart(darat_df, 'Tingkat Pendidikan', 'Tingkat Pendidikan', ['#a7f3d0', '#34d399'])

            else:
                st.info("Kolom 'Jenis' tidak ditemukan. Bagian ini tidak akan ditampilkan.")

            st.markdown("---")
            
            col_kelas, col_kapal = st.columns(2)
            
            with col_kelas:
                st.markdown('<div class="section-header"><h3>🚢 Distribusi Kelas Kapal</h3></div>', unsafe_allow_html=True)
                if 'Kelas Kapal' in df_analysis.columns:
                    kelas_df = df_analysis['Kelas Kapal'].value_counts().reset_index()
                    kelas_df.columns = ['Kelas Kapal', 'Jumlah']
                    
                    chart_kelas = alt.Chart(kelas_df).mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10
                    ).encode(
                        x=alt.X('Kelas Kapal:N', title='Kelas Kapal', axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('Jumlah:Q', title='Jumlah Karyawan'),
                        color=alt.Color('Kelas Kapal:N', scale=alt.Scale(scheme='tealblues'), legend=None),
                        tooltip=['Kelas Kapal', 'Jumlah']
                    ).properties(height=400)
                    
                    text = chart_kelas.mark_text(
                        dy=-10,
                        color='white',
                        fontSize=14,
                        fontWeight='bold'
                    ).encode(
                        text='Jumlah:Q'
                    )
                    
                    st.altair_chart(chart_kelas + text, use_container_width=True)
                else:
                    st.info("Kolom 'Kelas Kapal' tidak ditemukan.")
                    
            with col_kapal:
                st.markdown('<div class="section-header"><h3>🚢 Distribusi Tipe Kapal</h3></div>', unsafe_allow_html=True)
                if 'Segmen' in df_analysis.columns:
                    tipe_df = df_analysis['Segmen'].value_counts().reset_index()
                    tipe_df.columns = ['Segmen', 'Jumlah']
                    
                    chart_tipe = alt.Chart(tipe_df).mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10
                    ).encode(
                        x=alt.X('Segmen:N', title='Segmen', axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('Jumlah:Q', title='Jumlah Karyawan'),
                        color=alt.Color('Segmen:N', scale=alt.Scale(scheme='reds'), legend=None),
                        tooltip=['Segmen', 'Jumlah']
                    ).properties(height=400)
                    
                    text = chart_tipe.mark_text(
                        dy=-10,
                        color='white',
                        fontSize=14,
                        fontWeight='bold'
                    ).encode(
                        text='Jumlah:Q'
                    )
                    
                    st.altair_chart(chart_tipe + text, use_container_width=True)
                else:
                    st.info("Kolom 'Segmen' tidak ditemukan.")
                    
            st.markdown("---")
            col_pensiun1, col_resign1 = st.columns(2) # Membuat dua kolom utama

            with col_pensiun1:
                st.markdown('<div class="section-header"><h3>⚠️ Karyawan Pensiun</h3></div>', unsafe_allow_html=True)
                
                # Filter karyawan yang pensiun dari data yang sudah difilter sidebar
                pensiun_df = df_filtered[df_filtered['Status Kepegawaian'] == 'PENSIUN']
                
                # Buat dua kolom di dalam kolom pensiun
                col_pensiun_laut, col_pensiun_darat = st.columns(2)

                if 'Jenis' in pensiun_df.columns:
                    pensiun_laut_count = pensiun_df[pensiun_df['Jenis'].str.contains('Laut', na=False)].shape[0]
                    pensiun_darat_count = pensiun_df[pensiun_df['Jenis'].str.contains('Darat', na=False)].shape[0]

                    with col_pensiun_laut:
                        render_summary_card("Pensiun Laut", pensiun_laut_count, "⚓", "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)")
                    with col_pensiun_darat:
                        render_summary_card("Pensiun Darat", pensiun_darat_count, "🏢", "linear-gradient(135deg, #15803d 0%, #22c55e 100%)")
                else:
                    st.info("Data 'Jenis' tidak tersedia untuk menampilkan breakdown pensiun.")

            with col_resign1:
                st.markdown('<div class="section-header"><h3>👋 Karyawan Resign</h3></div>', unsafe_allow_html=True)

                # Filter karyawan yang resign
                resign_df = df_filtered[df_filtered['Status Kepegawaian'] == 'RESIGN']

                # Buat dua kolom di dalam kolom resign
                col_resign_laut, col_resign_darat = st.columns(2)

                if 'Jenis' in resign_df.columns:
                    resign_laut_count = resign_df[resign_df['Jenis'].str.contains('Laut', na=False)].shape[0]
                    resign_darat_count = resign_df[resign_df['Jenis'].str.contains('Darat', na=False)].shape[0]

                    with col_resign_laut:
                        render_summary_card("Resign Laut", resign_laut_count, "⚓", "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)")
                    with col_resign_darat:
                        render_summary_card("Resign Darat", resign_darat_count, "🏢", "linear-gradient(135deg, #15803d 0%, #22c55e 100%)")
                else:
                    st.info("Data 'Jenis' tidak tersedia untuk menampilkan breakdown resign.")
                    
            col_pensiun, col_resign = st.columns(2)
            
            with col_pensiun:
                st.markdown('<div class="section-header"><h3>🎯 Karyawan Mendekati Pensiun (Dalam 12 Bulan)</h3></div>', unsafe_allow_html=True)
                if 'Tanggal Lahir' in df_filtered.columns:
                    df_filtered['Usia'] = df_filtered['Tanggal Lahir'].apply(
                        lambda dob: (today.year - dob.year) - ((today.month, today.day) < (dob.month, dob.day)) if pd.notnull(dob) else None
                    )
                    df_filtered['Bulan Menuju Pensiun'] = df_filtered['Tanggal Lahir'].apply(
                        lambda dob: ((dob.replace(year=dob.year + 60) - today).days // 30) if pd.notnull(dob) else None
                    )
                    nearing_pension_df = df_filtered[
                        (df_filtered['Bulan Menuju Pensiun'] >= 0) & 
                        (df_filtered['Bulan Menuju Pensiun'] <= 12)
                    ]
                    
                    if not nearing_pension_df.empty:
                        st.dataframe(
                            nearing_pension_df[['Nama', 'Tanggal Lahir', 'Usia', 'Bulan Menuju Pensiun']],
                            use_container_width=True,
                        )
                    else:
                        st.info("Tidak ada karyawan yang mendekati masa pensiun dalam 12 bulan ke depan.")
                else:
                    st.info("Kolom 'Tanggal Lahir' tidak ditemukan.")
                    
            with col_resign:
                st.markdown('<div class="section-header"><h3>❗ Karyawan Mendekati Resign (Dalam 1 Bulan)</h3></div>', unsafe_allow_html=True)
                if 'Tanggal Resign' in df_filtered.columns:
                    df_filtered['Bulan Menuju Resign'] = df_filtered['Tanggal Resign'].apply(
                        lambda dor: ((dor - today).days // 30) if pd.notnull(dor) else None
                    )
                    nearing_resign_df = df_filtered[
                        (df_filtered['Bulan Menuju Resign'] >= 0) & 
                        (df_filtered['Bulan Menuju Resign'] <= 1)
                    ]
                    
                    if not nearing_resign_df.empty:
                        st.dataframe(
                            nearing_resign_df[['Nama', 'Jenis', 'Department Name', 'Tanggal Resign', 'Bulan Menuju Resign']],
                            use_container_width=True,
                        )
                    else:
                        st.info("Tidak ada karyawan yang mendekati masa resign dalam 1 bulan ke depan.")
            
        # ===============================
        # DATA AKHIR & DOWNLOAD
        # ===============================
        st.header("📑 Tabel Data Hasil Filter")
        st.info("Tabel di bawah ini menampilkan karyawan yang aktif berdasarkan filter yang dipilih.")
        st.dataframe(
            df_analysis,
            use_container_width=True,
            height=400
        )
        
        st.caption(f"Menampilkan {len(df_analysis):,} karyawan aktif dari total {len(df_cleaned):,} data.")
        
        # Download
        col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
        
        with col_dl1:
            csv_filtered = to_csv(df_analysis)
            st.download_button(
                label="💾 Download CSV",
                data=csv_filtered,
                file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

except Exception as e:
    st.error(f"❗ Terjadi kesalahan saat memproses data:")
    st.exception(e)
    st.info("💡 Tips: Pastikan koneksi internet Anda stabil dan URL Google Sheet serta file `secrets.toml` sudah benar.")


