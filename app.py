import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
from main import (
    load_data, evaluate, generate_population,
    crossover, mutate, roulette_selection, set_params, calculate_unloading_time
)
from visualisasi import visualisasi_penyusunan
from ui_input import render_sidebar_inputs

# HARUS DI ATAS
st.set_page_config(page_title="Simulasi Penyusunan Barang", layout="wide")

def highlight_status(row):
    if row["Status"] == "Valid":
        return [""] * len(row)
    elif row["Status"] == "Keluar batas kontainer":
        return ["background-color: #e3bf00"] * len(row)
    elif row["Status"] == "Tidak disusun":
        return ["background-color: #ff0000"] * len(row)
    return [""] * len(row)

st.title("🚛 Simulasi Penyusunan Barang di Kontainer")

params = render_sidebar_inputs()
set_params(params)
panjang, lebar, tinggi = params['dimensi']

if st.button("Jalankan Simulasi"):
    with st.spinner("Menjalankan algoritma genetika..."):
        boxes = load_data(params['selected_items'])
        if not boxes:
            st.error("Tidak ada data barang yang valid!")
        else:
            pop = generate_population(len(boxes))
            best, best_fit, best_coords = None, -1e9, []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for gen in range(params['max_generasi']):
                start_time = time.time()
                results = [evaluate(ind, boxes) for ind in pop]
                fitnesses = [r[0] for r in results]
                coords_list = [r[1] for r in results]

                for i, f in enumerate(fitnesses):
                    if f > best_fit:
                        best_fit = f
                        best = pop[i]
                        best_coords = coords_list[i]

                pop = [mutate(crossover(roulette_selection(pop, fitnesses), roulette_selection(pop, fitnesses))) for _ in range(params['max_populasi'])]

                progress = (gen + 1) / params['max_generasi']
                progress_bar.progress(progress)
                status_text.text(f"Generasi {gen + 1}/{params['max_generasi']}, Fitness: {best_fit:.4f}, Waktu: {time.time() - start_time:.2f} detik")

            st.success(f"✅ Simulasi selesai. Fitness terbaik: {best_fit:.4f}")

            total_unloading_time, unloading_details = calculate_unloading_time(best_coords, panjang)

            coord_map = {(c['box']['produk'], c['box']['customer']): c for c in best_coords}

            final_output = []
            for i, box in enumerate(boxes):
                key = (box['produk'], box['customer'])
                detail = next((d for d in unloading_details if d['produk'] == box['produk'] and d['customer'] == box['customer']), {})

                if key in coord_map:
                    c = coord_map[key]
                    x, y, z = c['x'], c['y'], c['z']
                    dx, dy, dz = box['lebar'], box['panjang'], box['tinggi']
                    status = "Keluar batas kontainer" if (x + dx > lebar or y + dy > panjang or z + dz > tinggi) else "Valid"
                else:
                    x = y = z = "-"
                    status = "Tidak disusun"

                final_output.append({
                    "#": i + 1,
                    "Produk": box['produk'],
                    "Customer": box['customer'],
                    "X": x, "Y": y, "Z": z,
                    "Urutan": box['urutan'],
                    "Berat (kg)": box['berat'],
                    "Jarak Horizontal (cm)": detail.get("jarak_horizontal_cm", "-"),
                    "Jarak Vertikal (cm)": detail.get("jarak_vertikal_cm", "-"),
                    "Jarak Tempuh (cm)": detail.get("jarak_tempuh_cm", "-"),
                    "Waktu Unloading (detik)": detail.get("waktu_unloading_detik", "-"),
                    "Status": status
                })

            df_result = pd.DataFrame(final_output)

            st.session_state.simulasi_selesai = True
            st.session_state.df_result = df_result
            st.session_state.df_coords = best_coords
            st.session_state.df_fig = visualisasi_penyusunan(best_coords, panjang, lebar, tinggi)
            st.session_state.total_unloading_time = total_unloading_time

if st.session_state.get("simulasi_selesai", False):
    df_result = st.session_state.df_result
    best_coords = st.session_state.df_coords
    fig = st.session_state.df_fig
    total_unloading_time = st.session_state.total_unloading_time

    st.subheader("📦 Visualisasi 3D")
    st.pyplot(fig)

    if "Waktu Unloading (detik)" in df_result.columns:
        df_result["Waktu Unloading (detik)"] = pd.to_numeric(df_result["Waktu Unloading (detik)"], errors='coerce')
        df_result["Unloading Rank"] = df_result["Waktu Unloading (detik)"].rank(method="min", ascending=False).fillna("-").astype(str)

    st.subheader("📋 Filter Tabel Penyusunan")
    status_filter = st.selectbox("Tampilkan berdasarkan status:", ["Semua", "Valid", "Keluar batas kontainer", "Tidak disusun"])
    df_display = df_result.copy()
    if status_filter != "Semua":
        df_display = df_display[df_display["Status"] == status_filter]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏲️ Total Waktu Unloading", f"{total_unloading_time:.2f} detik")
    with col2:
        st.metric("⏲️ Total Waktu (menit)", f"{total_unloading_time/60:.2f} menit")
    with col3:
        st.metric("📦 Total Barang", f"{len(best_coords)} box")

    st.subheader("📋 Detail Penyusunan & Waktu Unloading")
    st.dataframe(df_display.style.apply(highlight_status, axis=1), use_container_width=True)

    st.subheader("📊 Ringkasan Status Box")
    summary = {
        "valid_count": len(df_result[df_result["Status"] == "Valid"]),
        "used_volume": df_result[df_result["Status"] == "Valid"]["Berat (kg)"].sum(),
        "total_volume": panjang * lebar * tinggi,
        "empty_volume": 0,
        "efficiency": 0
    }
    summary["efficiency"] = round(summary["used_volume"] / summary["total_volume"] * 100, 2)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Valid", summary['valid_count'])
    col2.metric("⚠️ Keluar batas", len(df_result[df_result["Status"] == "Keluar batas kontainer"]))
    col3.metric("❌ Tidak disusun", len(df_result[df_result["Status"] == "Tidak disusun"]))
    col4.metric("📦 Total Box", len(df_result))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📏 Volume Terpakai", f"{summary['used_volume']:,}")
    col2.metric("🌀 Ruang Kosong", f"{summary['total_volume'] - summary['used_volume']:,}")
    col3.metric("📈 Efisiensi", f"{summary['efficiency']}%")

    with st.expander("ℹ️ Informasi Rumus Perhitungan Waktu Unloading"):
        st.write("""
        **Rumus yang digunakan:**
        - Koordinat pintu kontainer: (0, 0, 0)
        - Waktu standar (Ws): 5 detik per meter
        - Jarak tempuh = 2 × |Xkontainer - Xawal_box| + |Zawal_box - Zkontainer| + Jk
        - Waktu unloading = Jarak tempuh × Ws

        **Keterangan:**
        - Xawal_box: Koordinat X tengah box
        - Zawal_box: Koordinat Z tengah box  
        - Jk: Jarak ketinggian kontainer ke tanah (diasumsikan 0)
        - Faktor 2 pada jarak horizontal karena operator harus bolak-balik
        """)

    st.download_button(
        label="📅 Download Hasil CSV",
        data=df_result.to_csv(index=False).encode('utf-8'),
        file_name="hasil_simulasi.csv",
        mime="text/csv"
    )
