import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import time
from main import (
    load_data, evaluate, generate_population,
    crossover, mutate, roulette_selection, set_params
)
from visualisasi import visualisasi_penyusunan
from ui_input import render_sidebar_inputs

def get_unloading_map():
    df = pd.read_excel("data/EXCEL_NAMBAH_DATA.xlsx", sheet_name='UNLOADING', skiprows=3, header=None)
    df = df[[1, 2, 9, 10]].copy()
    df.columns = ['No_SO', 'Produk', 'jarak_cm', 'waktu_dtk']
    df[['No_SO', 'Produk']] = df[['No_SO', 'Produk']].fillna(method='ffill')
    df = df[~df['Produk'].isin(['Produk', 'Koordinat Akhir'])]
    df = df.dropna(subset=['jarak_cm', 'waktu_dtk'])
    df['Produk'] = df['Produk'].str.strip().str.lower()
    return df.groupby('Produk')[['jarak_cm', 'waktu_dtk']].mean().to_dict('index')

def validate_result(best_coords, panjang, lebar, tinggi):
    total_volume = 0
    jumlah_box_valid = 0
    volume_kontainer = panjang * lebar * tinggi
    invalid_boxes = []

    for b in best_coords:
        box = b['box']
        x, y, z = b['x'], b['y'], b['z']
        dx, dy, dz = box['panjang'], box['lebar'], box['tinggi']
        if x + dx > panjang or y + dy > lebar or z + dz > tinggi:
            invalid_boxes.append({
                "Produk": box['produk'],
                "Posisi akhir": f"({x + dx}, {y + dy}, {z + dz})",
                "Status": "Keluar dari batas kontainer"
            })
        else:
            volume_box = dx * dy * dz
            total_volume += volume_box
            jumlah_box_valid += 1

    efisiensi = total_volume / volume_kontainer * 100
    return {
        "valid_count": jumlah_box_valid,
        "used_volume": total_volume,
        "total_volume": volume_kontainer,
        "empty_volume": volume_kontainer - total_volume,
        "efficiency": round(efisiensi, 2),
        "invalid_boxes": pd.DataFrame(invalid_boxes)
    }

st.set_page_config(page_title="Simulasi Kontainer V2", layout="wide")
st.title("🚛 Simulasi Penyusunan Barang dalam Kontainer")

params = render_sidebar_inputs()
set_params(params)
dimensi = params['dimensi']
# Debugging pindah ke terminal
print(f"Debugging: Dimensi kontainer dari UI: {dimensi}")

if st.button("Mulai Optimasi"):
    with st.spinner("Sedang menjalankan algoritma genetika..."):
        boxes = load_data(selected_items=params['selected_items'])
        if not boxes:
            st.error("Tidak ada data barang yang valid untuk diproses!")
        else:
            # Debugging pindah ke terminal
            print("Data barang yang diproses:")
            print(pd.DataFrame(boxes))
            print(f"Total kotak: {len(boxes)}")

            pop = generate_population(len(boxes))
            best, best_fit, best_coords = None, -1e9, []
            print(f"Total kotak: {len(boxes)}")

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
                end_time = time.time()
                st.write(f"Generasi {gen + 1}/{params['max_generasi']}, Fitness terbaik: {best_fit:.4f}, Waktu: {end_time - start_time:.2f} detik")

            st.success(f"✅ Optimasi selesai. Fitness terbaik: {best_fit:.4f}")

            # Debugging pindah ke terminal
            print("Debugging: Isi best_coords")
            print(best_coords)

            st.subheader("📦 Visualisasi 3D Penyusunan")
            fig = visualisasi_penyusunan(best_coords, *dimensi, show=False)
            st.pyplot(fig)

            unloading_map = get_unloading_map()
            final_output = []
            for b in best_coords:
                produk_name = b['box']['produk'].strip().lower()
                waktu = unloading_map.get(produk_name, {'jarak_cm': None, 'waktu_dtk': None})
                final_output.append({
                    "Produk": b['box']['produk'],
                    "Customer": b['box']['customer'],
                    "X": b['x'], "Y": b['y'], "Z": b['z'],
                    "Urutan": b['box']['urutan'],
                    "Berat": b['box']['berat'],
                    "Jarak ke Pintu (cm)": waktu['jarak_cm'],
                    "Waktu Unloading (detik)": waktu['waktu_dtk']
                })
            df_result = pd.DataFrame(final_output)
            total_time = df_result['Waktu Unloading (detik)'].dropna().sum()

            st.subheader("⏱️ Total Waktu Unloading")
            st.metric("Waktu Total Unloading (detik)", f"{total_time:.2f}")

            st.subheader("📋 Detail Penyusunan Barang dan Waktu Bongkar")
            st.dataframe(df_result, use_container_width=True)

            st.subheader("🧠 Ringkasan & Validasi Penyusunan")
            validasi = validate_result(best_coords, *dimensi)
            st.write(f"📦 Jumlah box valid: {validasi['valid_count']}")
            st.write(f"🧮 Total volume terpakai: {validasi['used_volume']} cm³")
            st.write(f"📭 Ruang kosong: {validasi['empty_volume']} cm³")
            st.write(f"📏 Efisiensi pemakaian ruang: {validasi['efficiency']}%")
            if not validasi["invalid_boxes"].empty:
                st.error("❗ Ada box yang keluar dari batas kontainer!")
                st.dataframe(validasi["invalid_boxes"])
            else:
                st.success("✅ Tidak ada box yang keluar dari batas kontainer.")