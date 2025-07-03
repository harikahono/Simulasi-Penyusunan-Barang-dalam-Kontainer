import streamlit as st
import pandas as pd
import os

def load_product_data():
    file_path = os.path.join("data", "produk.csv")
    try:
        produk_df = pd.read_csv(file_path)
        produk_df.columns = ['Nama', 'Panjang', 'Lebar', 'Berat', 'Tinggi', 'Volume']
        produk_df = produk_df.dropna()
        produk_df['Nama'] = produk_df['Nama'].str.strip()
        return produk_df
    except Exception as e:
        st.error(f"Gagal membaca produk.csv: {e}")
        return pd.DataFrame()

def render_sidebar_inputs():
    st.sidebar.header("📦 Input Barang")
    produk_df = load_product_data()
    valid_products = produk_df['Nama'].unique() if not produk_df.empty else []

    if 'items_count' not in st.session_state:
        st.session_state.items_count = 1

    selected_items = []
    for i in range(st.session_state.items_count):
        st.sidebar.subheader(f"Barang {i+1}")
        cols = st.sidebar.columns(4)
        with cols[0]:
            produk = st.selectbox("Produk", valid_products, key=f"produk_{i}")
        with cols[1]:
            customer = st.text_input("Customer", value="", placeholder="Masukkan nama customer", key=f"customer_{i}")
        with cols[2]:
            qty = st.number_input("Jumlah", min_value=1, value=1, key=f"qty_{i}")
        with cols[3]:
            urutan = st.selectbox("Urutan Pengiriman", list(range(1, 5)), key=f"urutan_{i}")  # bisa sampai 4
            
        selected_items.append({
            'produk': produk,
            'customer': customer,
            'quantity': qty,
            'urutan': urutan
        })

    for item in selected_items:
        if item['produk'] not in valid_products:
            st.sidebar.error(f"Produk '{item['produk']}' tidak valid!")

    if st.sidebar.button("➕ Tambah Barang"):
        st.session_state.items_count += 1
    if st.session_state.items_count > 1 and st.sidebar.button("➖ Kurang Barang"):
        st.session_state.items_count -= 1
        st.rerun()

    st.sidebar.header("🧬 Parameter Genetika")
    max_populasi = st.sidebar.number_input("Jumlah Populasi", min_value=5, max_value=100, value=30, step=5)
    max_generasi = st.sidebar.number_input("Jumlah Generasi", min_value=10, max_value=500, value=200, step=10)
    crossover_prob = st.sidebar.slider("Probabilitas Crossover", 0.0, 1.0, 0.95, 0.01)
    mutasi_prob = st.sidebar.slider("Probabilitas Mutasi", 0.0, 1.0, 0.01, 0.01)

    st.sidebar.header("🚛 Armada")
    jenis_truk = st.sidebar.selectbox("Jenis Truk", [
        "Truk Engkel Box",
        "Truk Engkel Bak",
        "L300 Box"
    ])
    ukuran_kontainer = {
        "Truk Engkel Box": (300, 150, 150),
        "Truk Engkel Bak": (300, 150, 150),
        "L300 Box": (250, 150, 125)
    }
    panjang, lebar, tinggi = ukuran_kontainer[jenis_truk]

    # Berat maksimal fix 5 ton (5000 kg) untuk semua truk
    max_berat = 5000

    return {
        "selected_items": selected_items,
        "max_populasi": max_populasi,
        "max_generasi": max_generasi,
        "crossover_prob": crossover_prob,
        "mutasi_prob": mutasi_prob,
        "jenis_truk": jenis_truk,
        "dimensi": (panjang, lebar, tinggi),
        "max_berat": max_berat
    }