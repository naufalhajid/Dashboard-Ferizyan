import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import re

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Data Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stMetric label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        color: rgba(255, 255, 255, 0.85) !important;
    }
    h1 {
        color: #1f77b4;
        font-weight: 700;
    }
    h2 {
        color: #2c3e50;
        font-weight: 600;
        margin-top: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
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

@st.cache_data
def clean_all_strings(df):
    """Menghilangkan semua karakter non-alfanumerik dari semua kolom string"""
    string_cols = df.select_dtypes(include=['object', 'string']).columns
    
    def clean_text(text):
        if pd.isna(text) or text is None:
            return text
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text)).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Hapus multiple spaces
        return cleaned

    for col in string_cols:
        df[col] = df[col].apply(clean_text)
        
    return df

# --- HEADER ---
st.title(" Dashboard Karyawan Ferizyan")
st.markdown("### Analisis Data Karyawan Interaktif")
st.markdown("---")

# --- UPLOAD FILE ---
uploaded_file = st.file_uploader(
    " Upload file data Anda",
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
                'Bulan' : 'Tanggal Masuk',
                
            }, inplace=True)

            # --- PEMBERSIHAN KARAKTER ---
            df = clean_all_strings(df.copy())

            # --- KONVERSI TANGGAL ---
            df = safe_date_conversion(df, ['Tanggal Masuk', 'Tanggal Keluar', 'Tanggal Pensiun', 'Tanggal Lahir'])
        
        st.success(f"✅ Berhasil memuat: **{uploaded_file.name}**")
        
        # Info file
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric(" Total Baris", f"{df.shape[0]:,}")
        with col_info2:
            st.metric(" Total Kolom", df.shape[1])
        with col_info3:
            st.metric(" Ukuran File", f"{uploaded_file.size / 1024:.1f} KB")
        
        st.markdown("---")

        # --- TABS ---
        tab_analysis, tab_raw_data = st.tabs([
            "Dashboard Analisis", 
            " Data Mentah"
        ])

        # ========================================
        # TAB: DATA MENTAH
        # ========================================
        with tab_raw_data:
            st.header(" Data Asli")
            st.info("Data mentah setelah penggantian nama kolom dan *cleaning* karakter.")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv_raw = to_csv(df)
            st.download_button(
                label=" Download Data Mentah (CSV)",
                data=csv_raw,
                file_name=f"cleaned_raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        # ========================================
        # TAB: DASHBOARD ANALISIS
        # ========================================
        with tab_analysis:
            # ===============================
            # 1️⃣ ANALISIS MISSING VALUE
            # ===============================
            st.header("1️⃣ Pra-pemrosesan Data")
            
            missing_data = pd.DataFrame({
                'Missing Count': df.isnull().sum(),
                'Missing Percentage': (df.isnull().sum() / len(df)) * 100
            }).sort_values(by='Missing Percentage', ascending=False)
            
            df_cleaned = df.copy()
            to_drop = missing_data[missing_data['Missing Percentage'] == 100].index.tolist()
            
            if to_drop:
                df_cleaned.drop(columns=to_drop, inplace=True)
                st.warning(f" Menghapus {len(to_drop)} kolom yang 100% kosong")
                
                with st.expander(" Lihat kolom yang dihapus"):
                    for col in to_drop:
                        st.text(f"• {col}")
                
                missing_data_partial = missing_data[
                    (missing_data['Missing Percentage'] < 100) & 
                    (missing_data['Missing Percentage'] > 0)
                ]
                
                if not missing_data_partial.empty:
                    st.subheader(" Visualisasi Sisa Missing Values")
                    fig_miss = px.bar(
                        missing_data_partial.reset_index(),
                        x='Missing Percentage',
                        y='index',
                        orientation='h',
                        title='Persentase Missing Values per Kolom',
                        labels={'index': 'Nama Kolom', 'Missing Percentage': 'Persentase (%)'},
                        color='Missing Percentage',
                        color_continuous_scale='Reds',
                        height=350
                    )
                    fig_miss.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=True, gridcolor='lightgray')
                    )
                    st.plotly_chart(fig_miss, use_container_width=True)

            
            st.markdown("---")
            
            # ===============================
            # 2️⃣ FILTER SIDEBAR
            # ===============================
            st.sidebar.markdown("##  Panel Filter")
            st.sidebar.markdown("Sesuaikan filter untuk analisis data")
            st.sidebar.markdown("---")
            
            df_filtered = df_cleaned.copy()
            today = pd.Timestamp(datetime.now().date())
            active_filters = []
            
            # --- FILTER TANGGAL ---
            with st.sidebar.expander(" **Filter Tanggal Masuk**", expanded=True):
                if 'Tanggal Masuk' in df_cleaned.columns:
                    valid_dates = df_cleaned[
                        (df_cleaned['Tanggal Masuk'] <= today) & 
                        (df_cleaned['Tanggal Masuk'].notna())
                    ]['Tanggal Masuk']
                    
                    if not valid_dates.empty:
                        min_date = valid_dates.min().date()
                        max_date = today.date()
                        
                        col_date1, col_date2 = st.columns(2)
                        with col_date1:
                            start_date = st.date_input(
                                "Dari",
                                min_date,
                                min_value=min_date,
                                max_value=max_date,
                                key="start_date"
                            )
                        with col_date2:
                            end_date = st.date_input(
                                "Sampai",
                                max_date,
                                min_value=min_date,
                                max_value=max_date,
                                key="end_date"
                            )

                        if start_date > end_date:
                            st.error(" Tanggal mulai harus sebelum tanggal akhir")
                            st.stop()
                        
                        # Terapkan filter Tanggal Masuk
                        start_datetime = pd.to_datetime(start_date)
                        end_datetime = pd.to_datetime(end_date)
                        
                        df_filtered = df_filtered[
                            (df_filtered['Tanggal Masuk'] >= start_datetime) &
                            (df_filtered['Tanggal Masuk'] <= end_datetime)
                        ]
                        
                        active_filters.append(
                            f" Tanggal: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
                        )
                    else:
                        st.info("Tidak ada data tanggal valid")
                else:
                    st.info("Kolom 'Tanggal Masuk' tidak ditemukan")

            # --- FILTER KATEGORI ---
            with st.sidebar.expander(" **Filter Kategori**", expanded=True):
                categorical_columns = [
                    ("Status Aktif", ""),
                    ("Status Kepegawaian", ""),
                    ("Unit Kerja", ""),
                    ("Sub Unit Kerja", ""),
                    ("Jenis", ""),
                    ("Klasifikasi Jabatan", ""),
                    ("Jabatan", ""),
                    ("Department Name", ""),
                    ("Lokasi Kerja", "")
                ]
                
                for col_name, icon in categorical_columns:
                    if col_name in df_filtered.columns:
                        unique_values = sorted(
                            df_filtered[col_name].dropna().astype(str).unique().tolist()
                        )
                        
                        if unique_values:
                            selected_value = st.selectbox(
                                f"{icon} {col_name}",
                                ['Semua'] + unique_values,
                                key=f'filter_{col_name}'
                            )
                            
                            if selected_value != 'Semua':
                                df_filtered = df_filtered[
                                    df_filtered[col_name].astype(str) == selected_value
                                ]
                                active_filters.append(f"{icon} {col_name}: {selected_value}")
            
            # --- TOMBOL RESET ---
            st.sidebar.markdown("---")
            if st.sidebar.button("🔄 Reset Semua Filter", use_container_width=True, type="primary"):
                st.rerun()
            
            # --- INFO FILTER AKTIF ---
            st.sidebar.markdown("---")
            st.sidebar.markdown("###  Filter Aktif")
            if active_filters:
                for f in active_filters:
                    st.sidebar.markdown(f"✓ {f}")
            else:
                st.sidebar.info("Tidak ada filter aktif")
            
            # ===============================
            # 3️⃣ HASIL FILTER & VISUALISASI
            # ===============================
            st.header("2️⃣ Hasil Analisis Data")
            
            if df_filtered.empty:
                st.error("❌ Data kosong! Silakan sesuaikan filter Anda.")
                st.stop()
            
            # KPI CARDS
            total_data = len(df_filtered)
            aktif = 0
            tidak_aktif = 0
            
            if 'Status Aktif' in df_filtered.columns:
                aktif = (df_filtered['Status Aktif'] == 'AKTIF').sum()
                tidak_aktif = (df_filtered['Status Aktif'] == 'TIDAK AKTIF').sum()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📊 Total Data",
                    value=f"{total_data:,}",
                    delta=f"{(total_data/len(df_cleaned)*100):.1f}% dari total"
                )
            
            with col2:
                pct_aktif = (aktif/total_data*100) if total_data > 0 else 0
                st.metric(
                    label="🟢 Karyawan Aktif",
                    value=f"{aktif:,}",
                    delta=f"{pct_aktif:.1f}%"
                )
            
            with col3:
                pct_tidak_aktif = (tidak_aktif/total_data*100) if total_data > 0 else 0
                st.metric(
                    label="🔴 Tidak Aktif",
                    value=f"{tidak_aktif:,}",
                    delta=f"{pct_tidak_aktif:.1f}%",
                    delta_color="inverse"
                )
            
            with col4:
                ratio = aktif / tidak_aktif if tidak_aktif > 0 else 0
                st.metric(
                    label="📈 Rasio",
                    value=f"{ratio:.2f}:1" if ratio > 0 else "N/A"
                )
            
            st.markdown("---")
            
            # VISUALISASI
            if 'Status Aktif' in df_filtered.columns:
                col_vis1, col_vis2 = st.columns([2, 1])
                
                with col_vis1:
                    st.subheader("📊 Distribusi Status Karyawan")
                    
                    keaktifan_df = df_filtered['Status Aktif'].value_counts().reset_index()
                    keaktifan_df.columns = ['Status Aktif', 'Jumlah']
                    
                    fig_pie = px.pie(
                        keaktifan_df,
                        values='Jumlah',
                        names='Status Aktif',
                        title='Komposisi Status Aktif Karyawan',
                        color='Status Aktif',
                        color_discrete_map={
                            'AKTIF': '#2ecc71',
                            'TIDAK AKTIF': '#e74c3c',
                            'CUTI': '#f39c12'
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
                
                with col_vis2:
                    st.subheader("📋 Detail Status")
                    st.dataframe(
                        keaktifan_df,
                        use_container_width=True,
                        hide_index=True,
                        height=300
                    )
            
            st.markdown("---")
            
            # ===============================
            # 4️⃣ DATA AKHIR & DOWNLOAD
            # ===============================
            st.header("3️⃣ Tabel Data Hasil Filter")
            
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