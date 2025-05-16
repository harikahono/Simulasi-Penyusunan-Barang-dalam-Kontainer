import streamlit as st
import pandas as pd

def load_product_data():
    produk_df = pd.read_excel("data/EXCEL_NAMBAH_DATA.xlsx", sheet_name='DATA PRODUK', skiprows=2)
    produk_df.columns = ['Nama', 'Panjang', 'Lebar', 'Tinggi', 'Berat', 'Tinggi2', 'Volume']
    produk_df = produk_df[['Nama', 'Panjang', 'Lebar', 'Tinggi', 'Berat', 'Volume']].dropna()
    produk_df['Nama'] = produk_df['Nama'].str.strip()  # Bersihkan spasi
    return produk_df

def load_demand_data():
    demand_df = pd.read_excel("data/EXCEL_NAMBAH_DATA.xlsx", sheet_name='DATA DEMAND', skiprows=2, header=None)
    demand_df.columns = ['No_SO', 'Nama_Customer', 'Nama_Produk', 'Jumlah', 'Berat_Total']
    demand_df = demand_df[['Nama_Customer', 'Nama_Produk', 'Jumlah']].dropna()
    demand_df['Nama_Customer'] = demand_df['Nama_Customer'].str.strip()  # Bersihkan spasi
    demand_df['Jumlah'] = demand_df['Jumlah'].astype(str).str.extract('(\d+)')
    demand_df['Jumlah'] = pd.to_numeric(demand_df['Jumlah'], errors='coerce')
    return demand_df

def render_sidebar_inputs():
    st.sidebar.header("⚙️ Parameter Algoritma Genetika")
    
    # Load data
    produk_df = load_product_data()
    demand_df = load_demand_data()
    
    # Validasi produk dan customer
    valid_products = produk_df['Nama'].unique()
    valid_customers = demand_df['Nama_Customer'].unique()

    st.sidebar.header("📦 Pilih Barang untuk Dimuat")
    if 'items_count' not in st.session_state:
        st.session_state.items_count = 1
    
    selected_items = []
    for i in range(st.session_state.items_count):
        st.sidebar.subheader(f"Barang {i+1}")
        cols = st.sidebar.columns(4)
        with cols[0]:
            produk = st.selectbox("Produk", valid_products, key=f"produk_{i}")
        with cols[1]:
            customer = st.selectbox("Customer", valid_customers, key=f"customer_{i}")
        with cols[2]:
            quantity = st.number_input("Jumlah", min_value=1, value=1, key=f"qty_{i}")
        with cols[3]:
            urutan = st.number_input("Urutan Pengiriman", min_value=1, max_value=10, value=1, key=f"urutan_{i}")
        
        selected_items.append({
            'produk': produk,
            'customer': customer,
            'quantity': quantity,
            'urutan': urutan
        })
    
    # Validasi input
    for item in selected_items:
        if item['produk'] not in valid_products:
            st.sidebar.error(f"Produk '{item['produk']}' tidak ditemukan di data produk!")
        if item['customer'] not in valid_customers:
            st.sidebar.error(f"Customer '{item['customer']}' tidak ditemukan di data demand!")
    
    # Tombol untuk tambah barang
    if st.sidebar.button("➕ Tambah Barang Lain"):
        st.session_state.items_count += 1
    
    # Tombol untuk hapus barang terakhir
    if st.session_state.items_count > 1:
        if st.sidebar.button("➖ Hapus Barang Terakhir"):
            st.session_state.items_count -= 1
            st.rerun()

    # Parameter algoritma genetika
    max_populasi = st.sidebar.number_input("Max Populasi", min_value=10, max_value=500, value=30, step=10)
    max_generasi = st.sidebar.number_input("Max Iterasi", min_value=10, max_value=500, value=200, step=10)
    crossover_prob = st.sidebar.slider("Probabilitas Crossover", min_value=0.0, max_value=1.0, value=0.95, step=0.01)
    mutasi_prob = st.sidebar.slider("Probabilitas Mutasi", min_value=0.0, max_value=1.0, value=0.01, step=0.01)

    st.sidebar.markdown("---")
    st.sidebar.header("🚛 Pilih Armada Kontainer")
    jenis_truk = st.sidebar.selectbox("Jenis Truk", ["Colt Diesel Engkel (CDE)", "Engkel Box", "Double Engkel"])

    ukuran_kontainer = {
        "Colt Diesel Engkel (CDE)": (300, 150, 150),
        "Engkel Box": (400, 180, 180),
        "Double Engkel": (500, 200, 200)
    }
    panjang, lebar, tinggi = ukuran_kontainer[jenis_truk]

    return {
        "selected_items": selected_items,
        "max_populasi": max_populasi,
        "max_generasi": max_generasi,
        "crossover_prob": crossover_prob,
        "mutasi_prob": mutasi_prob,
        "jenis_truk": jenis_truk,
        "dimensi": (panjang, lebar, tinggi)
    }