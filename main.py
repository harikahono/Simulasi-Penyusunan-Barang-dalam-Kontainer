import pandas as pd
import numpy as np
import random
import os
import streamlit as st

# Parameter global
MAX_BERAT = 5000
PANJANG_CONTAINER = None
LEBAR_CONTAINER = None
TINGGI_CONTAINER = None
MAX_GENERATIONS = None
POPULATION_SIZE = None
CROSSOVER_PROB = None
MUTATION_PROB = None

def set_params(params):
    global MAX_GENERATIONS, POPULATION_SIZE, CROSSOVER_PROB, MUTATION_PROB, PANJANG_CONTAINER, LEBAR_CONTAINER, TINGGI_CONTAINER
    MAX_GENERATIONS = params['max_generasi']
    POPULATION_SIZE = params['max_populasi']
    CROSSOVER_PROB = params['crossover_prob']
    MUTATION_PROB = params['mutasi_prob']
    PANJANG_CONTAINER, LEBAR_CONTAINER, TINGGI_CONTAINER = params['dimensi']
    # Validasi dimensi
    if not all(d > 0 for d in [PANJANG_CONTAINER, LEBAR_CONTAINER, TINGGI_CONTAINER]):
        raise ValueError(f"Dimensi kontainer tidak valid: {params['dimensi']}")

def load_data(selected_items=None):
    file_path = os.path.join("data", "EXCEL_NAMBAH_DATA.xlsx")
    produk = pd.read_excel(file_path, sheet_name='DATA PRODUK', skiprows=2)
    produk.columns = ['Nama', 'Panjang', 'Lebar', 'Tinggi', 'Berat', 'Tinggi2', 'Volume']
    produk = produk[['Nama', 'Panjang', 'Lebar', 'Tinggi', 'Berat', 'Volume']].dropna()
    produk['Nama'] = produk['Nama'].str.strip()

    box_instances = []
    if selected_items:
        for item in selected_items:
            try:
                produk_row = produk[produk['Nama'] == item['produk']].iloc[0]
                # Validasi urutan
                if not isinstance(item['urutan'], (int, float)) or item['urutan'] < 1:
                    st.error(f"Urutan untuk produk '{item['produk']}' tidak valid: {item['urutan']}")
                    return []
                for _ in range(item['quantity']):
                    box_instances.append({
                        'produk': item['produk'],
                        'customer': item['customer'],
                        'panjang': int(produk_row['Panjang']),
                        'lebar': int(produk_row['Lebar']),
                        'tinggi': int(produk_row['Tinggi']),
                        'berat': produk_row['Berat'],
                        'volume': produk_row['Volume'],
                        'urutan': item['urutan']
                    })
            except IndexError:
                st.error(f"Produk '{item['produk']}' tidak ditemukan di data produk!")
                return []
    else:
        demand = pd.read_excel(file_path, sheet_name='DATA DEMAND', skiprows=2, header=None)
        demand.columns = ['No_SO', 'Nama_Customer', 'Nama_Produk', 'Jumlah', 'Berat_Total']
        demand = demand[['Nama_Customer', 'Nama_Produk', 'Jumlah']].dropna()
        demand['Nama_Customer'] = demand['Nama_Customer'].str.strip()
        demand['Nama_Produk'] = demand['Nama_Produk'].str.strip()
        demand['Jumlah'] = demand['Jumlah'].astype(str).str.extract('(\d+)')
        demand['Jumlah'] = pd.to_numeric(demand['Jumlah'], errors='coerce')

        urutan = pd.read_excel(file_path, sheet_name='URUTAN PENGIRIMANN', skiprows=2, header=None)
        urutan = urutan[[1, 2]]
        urutan.columns = ['Urutan', 'Customer']
        urutan = urutan.dropna()
        urutan['Customer'] = urutan['Customer'].str.strip()
        urutan['Urutan'] = pd.to_numeric(urutan['Urutan'], errors='coerce')
        urutan_map = dict(zip(urutan['Customer'], urutan['Urutan']))

        box_df = pd.merge(demand, produk, left_on='Nama_Produk', right_on='Nama', how='inner')
        for _, row in box_df.iterrows():
            for _ in range(int(row['Jumlah'])):
                urutan_val = urutan_map.get(row['Nama_Customer'], 99)
                if not isinstance(urutan_val, (int, float)) or urutan_val < 1:
                    print(f"Urutan untuk customer '{row['Nama_Customer']}' tidak valid: {urutan_val}")
                    urutan_val = 99
                box_instances.append({
                    'produk': row['Nama_Produk'],
                    'customer': row['Nama_Customer'],
                    'panjang': int(row['Panjang']),
                    'lebar': int(row['Lebar']),
                    'tinggi': int(row['Tinggi']),
                    'berat': row['Berat'],
                    'volume': row['Volume'],
                    'urutan': urutan_val
                })

    # Validasi dimensi kotak
    for box in box_instances:
        if not all(isinstance(d, (int, float)) and d > 0 for d in [box['panjang'], box['lebar'], box['tinggi']]):
            print(f"Kotak {box['produk']} memiliki dimensi tidak valid: {box['panjang']}, {box['lebar']}, {box['tinggi']}")
            return []
    return box_instances

def generate_population(n):
    return [random.sample(range(n), n) for _ in range(POPULATION_SIZE)]

def evaluate(ind, boxes, lebar_container=150, panjang_container=300, tinggi_container=150, max_berat=1000):
    sorted_boxes = sorted([boxes[i] for i in ind], key=lambda x: x['urutan'])
    vol_used = total_berat = penalty = 0
    coords = []
    grid = np.zeros((lebar_container, panjang_container), dtype=int)  # X=lebar, Y=panjang
    fail_count = 0  # Hitung kegagalan

    # Batas Y per urutan (panjang 0-300 cm, bagi 3)
    Y_LIMITS = {
        1: (0, 150),    # Urutan 1: Y=0 sampai Y=150 (depan, pintu)
        2: (150, 225),  # Urutan 2: Y=150 sampai Y=225 (tengah)
        3: (225, 300)   # Urutan 3: Y=225 sampai Y=300 (belakang)
    }

    # Track posisi per urutan
    current_positions = {
        1: {'x': 0, 'y': 0, 'z': 0, 'max_x': 0, 'max_z': 0},
        2: {'x': 0, 'y': 150, 'z': 0, 'max_x': 0, 'max_z': 0},
        3: {'x': 0, 'y': 225, 'z': 0, 'max_x': 0, 'max_z': 0}
    }

    for b in sorted_boxes:
        if not isinstance(b['urutan'], (int, float)) or b['urutan'] < 1:
            print(f"Kotak {b['produk']} memiliki urutan tidak valid: {b['urutan']}")
            penalty += 1000
            fail_count += 1
            if fail_count > 2:
                print("Terlalu banyak kegagalan, stop evaluasi")
                return 0, []
            continue

        urutan = int(b['urutan'])
        if urutan > 3:
            print(f"Kotak {b['produk']} memiliki urutan lebih dari 3: {urutan}. Hanya urutan 1-3 yang diperbolehkan.")
            penalty += 1000000
            fail_count += 1
            if fail_count > 2:
                print("Terlalu banyak kegagalan, stop evaluasi")
                return 0, []
            continue

        # Orientasi asli (X=lebar, Y=panjang, Z=tinggi)
        dx, dy, dz = b['lebar'], b['panjang'], b['tinggi']
        print(f"Memproses kotak: {b['produk']}, Orientasi: ({dx}, {dy}, {dz}), Urutan: {urutan}")

        # Ambil posisi saat ini untuk urutan ini
        x, y, z = current_positions[urutan]['x'], current_positions[urutan]['y'], current_positions[urutan]['z']
        max_x, max_z = current_positions[urutan]['max_x'], current_positions[urutan]['max_z']

        # Tentukan batas Y berdasarkan urutan
        y_min, y_max = Y_LIMITS.get(urutan, (0, panjang_container))

        placed = False
        # Coba taruh barang sepanjang sumbu Y dalam rentang Y_LIMITS
        while not placed:
            # Cek apakah Y masih dalam batas
            if y + dy > y_max or y < y_min:
                y = y_min  # Reset Y ke y_min
                x += max_x  # Pindah ke kanan (tambah X)
                max_x = 0
            if x + dx > lebar_container:
                x = 0  # Kembali ke kiri (X=0)
                z += max_z  # Tumpuk ke atas (tambah Z)
                max_z = 0
                y = y_min  # Reset Y ke y_min

            # Cek apakah posisi valid terhadap batas kontainer
            if x + dx > lebar_container or y + dy > panjang_container or z + dz > tinggi_container:
                print(f"Posisi ({x}, {y}, {z}) di luar batas: X={x+dx}/{lebar_container}, Y={y+dy}/{panjang_container}, Z={z+dz}/{tinggi_container}")
                # Pindah ke X atau Z
                y = y_min
                x += max_x
                max_x = 0
                if x + dx > lebar_container:
                    x = 0
                    z += max_z
                    max_z = 0
                    if z + dz > tinggi_container:
                        print(f"Kotak {b['produk']} gagal ditempatkan: Z penuh")
                        penalty += 1000
                        fail_count += 1
                        if fail_count > 2:
                            print("Terlalu banyak kegagalan, stop evaluasi")
                            return 0, []
                        break
                continue

            # Coba tumpuk di Z, prioritas Z kecil (mulai dari 0)
            for test_z in range(0, tinggi_container - dz + 1, dz):
                z = test_z
                if z + dz > tinggi_container:
                    continue

                # Cek apakah area kosong di Z ini
                can_place = True
                for i in range(int(x), int(x + dx)):
                    for j in range(int(y), int(y + dy)):
                        if i >= lebar_container or j >= panjang_container:
                            can_place = False
                            print(f"Indeks di luar batas: i={i}/{lebar_container}, j={j}/{panjang_container}")
                            break
                        if grid[i, j] > z:
                            can_place = False
                            print(f"Area tidak kosong di ({i}, {j}): grid[{i}, {j}]={grid[i, j]} > z={z}")
                            break
                    if not can_place:
                        break

                if can_place:
                    coords.append({'box': b, 'x': x, 'y': y, 'z': z})
                    vol_used += dx * dy * dz
                    total_berat += b['berat']

                    # Penalti kalau di luar batas Y
                    if y < y_min or y + dy > y_max:
                        penalty += 100000 * urutan
                        print(f"Kotak {b['produk']} di luar batas Y untuk urutan {urutan}: ({y}, {y+dy})")

                    # Penalti deviasi Y dari posisi ideal
                    ideal_y = (y_min + y_max) / 2
                    y_deviation = abs(y - ideal_y) / panjang_container
                    penalty += urutan * y_deviation * 100000

                    # Penalti Z: semua urutan prioritas Z kecil dulu
                    penalty += (z / tinggi_container) * 150000

                    # Penalti tambahan: urutan 3 nggak boleh di Y kecil
                    if urutan >= 3 and y < 225:
                        penalty += 200000
                        print(f"Kotak {b['produk']} urutan {urutan} salah posisi: Y={y}, seharusnya Y>=225")

                    # Penalti tambahan: urutan 2 nggak boleh di Y belakang
                    if urutan == 2 and y >= 225:
                        penalty += 200000
                        print(f"Kotak {b['produk']} urutan {urutan} salah posisi: Y={y}, seharusnya Y<225")

                    print(f"Kotak {b['produk']} ditempatkan di: ({x}, {y}, {z}) dengan orientasi ({dx}, {dy}, {dz})")

                    for i in range(int(x), int(x + dx)):
                        for j in range(int(y), int(y + dy)):
                            if i < lebar_container and j < panjang_container:
                                grid[i, j] = z + dz

                    y += dy  # Maju ke belakang (tambah Y)
                    max_x = max(max_x, dx)
                    max_z = max(max_z, dz)
                    placed = True
                    break

            if not placed:
                # Kalau ga muat di Z, pindah ke X atau Z
                y = y_min
                x += max_x
                max_x = 0
                if x + dx > lebar_container:
                    x = 0
                    z += max_z
                    max_z = 0
                    if z + dz > tinggi_container:
                        print(f"Kotak {b['produk']} gagal ditempatkan: Z penuh")
                        penalty += 1000
                        fail_count += 1
                        if fail_count > 2:
                            print("Terlalu banyak kegagalan, stop evaluasi")
                            return 0, []
                        break

        # Update posisi untuk urutan ini
        current_positions[urutan]['x'] = x
        current_positions[urutan]['y'] = y
        current_positions[urutan]['z'] = z
        current_positions[urutan]['max_x'] = max_x
        current_positions[urutan]['max_z'] = max_z

    if total_berat > max_berat:
        penalty += 10000
        print(f"Total berat ({total_berat}) melebihi MAX_BERAT ({max_berat})")

    volume_ratio = vol_used / (lebar_container * panjang_container * tinggi_container)
    stability_score = 1 / (1 + penalty * 0.00001)
    print(f"Evaluasi selesai. Volume ratio: {volume_ratio}, Stability score: {stability_score}, Coords: {len(coords)}")
    return volume_ratio * stability_score, coords

def roulette_selection(pop, fits):
    total = sum(fits)
    pick = random.uniform(0, total)
    current = 0
    for p, f in zip(pop, fits):
        current += f
        if current > pick:
            return p
    return pop[0]

def crossover(p1, p2):
    if random.random() > CROSSOVER_PROB:
        return p1[:]
    child = [-1] * len(p1)
    for i in range(len(p1)):
        if random.random() < 0.5:
            child[i] = p1[i]
    pointer = 0
    for i in p2:
        if i not in child:
            while child[pointer] != -1:
                pointer += 1
            child[pointer] = i
    return child

def mutate(ind):
    if random.random() > MUTATION_PROB:
        return ind
    a = random.randint(0, len(ind) - 1)
    b = min(a + random.randint(1, 3), len(ind) - 1)
    new_ind = ind.copy()
    new_ind[a], new_ind[b] = new_ind[b], new_ind[a]
    return new_ind