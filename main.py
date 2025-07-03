import random
import numpy as np
import streamlit as st
import pandas as pd
import os

# Global parameters
params = {
    'max_populasi': 30,
    'max_generasi': 200,
    'crossover_prob': 0.95,
    'mutasi_prob': 0.01,
    'dimensi': (300, 150, 150),  # Y (panjang), X (lebar), Z (tinggi)
    'max_berat': 5000
}

def set_params(new_params):
    global params
    params.update(new_params)

def load_data(selected_items):
    if not selected_items:
        st.error("Tidak ada input barang dari UI!")
        return []

    file_path = os.path.join("data", "produk.csv")
    try:
        produk = pd.read_csv(file_path)
        produk.columns = ['Nama', 'Panjang', 'Lebar', 'Berat', 'Tinggi', 'Volume']
        produk = produk.dropna()
        produk['Nama'] = produk['Nama'].str.strip()
    except Exception as e:
        st.error(f"Gagal membaca file CSV: {e}")
        return []

    box_instances = []
    for item in selected_items:
        try:
            produk_row = produk[produk['Nama'] == item['produk']].iloc[0]
            panjang = int(produk_row['Panjang'])
            lebar = int(produk_row['Lebar'])
            tinggi = int(produk_row['Tinggi'])

            # Cek apakah barang muat dalam kontainer
            if panjang > params['dimensi'][0] or lebar > params['dimensi'][1] or tinggi > params['dimensi'][2]:
                st.error(f"Produk '{item['produk']}' terlalu besar untuk kontainer!")
                return []

            for _ in range(item['quantity']):
                box_instances.append({
                    'produk': item['produk'],
                    'customer': item['customer'] or f"Customer {len(box_instances)+1}",
                    'panjang': panjang,
                    'lebar': lebar,
                    'tinggi': tinggi,
                    'berat': produk_row['Berat'],
                    'volume': produk_row['Volume'],
                    'urutan': item['urutan']
                })
        except IndexError:
            st.error(f"Produk '{item['produk']}' tidak ditemukan!")
            return []
    return box_instances



def true_lifo_packing(boxes, container_dims):
    """
    True LIFO packing: 
    - Urutan tertinggi (keluar terakhir) diletakkan dari belakang kontainer (Y max)
    - Urutan menengah dilanjutkan di depannya
    - Urutan terendah diletakkan paling depan (Y kecil)
    """
    panjang_container, lebar_container, tinggi_container = container_dims

    coords = []
    penalty = 0
    total_volume = 0
    total_berat = 0

    # Group boxes berdasarkan urutan
    urutan_groups = {}
    for box in boxes:
        urutan = box['urutan']
        if urutan not in urutan_groups:
            urutan_groups[urutan] = []
        urutan_groups[urutan].append(box)

    # Sort tiap grup berdasarkan volume terbesar dulu
    for urutan in urutan_groups:
        urutan_groups[urutan].sort(key=lambda x: x['volume'], reverse=True)

    # Debug awal
    if st.session_state.get('debug_mode', False):
        st.write(f"Container dims: {container_dims}")
        for urutan in sorted(urutan_groups.keys(), reverse=True):
            st.write(f"Urutan {urutan}: {len(urutan_groups[urutan])} boxes")

    # Tentukan awal Y dari belakang (untuk urutan tertinggi)
    max_urutan = max(urutan_groups.keys())
    max_box_length = max(b['panjang'] for b in urutan_groups[max_urutan])
    if max_box_length > panjang_container:
        st.warning(f"⚠️ Panjang box terbesar ({max_box_length}) melebihi panjang kontainer!")
        current_y_back = 0
    else:
        current_y_back = panjang_container

    # Proses per urutan (mulai dari tertinggi = paling belakang)
    for urutan in sorted(urutan_groups.keys(), reverse=True):
        boxes_in_urutan = urutan_groups[urutan]

        if st.session_state.get('debug_mode', False):
            st.write(f"=== Processing Urutan {urutan} ===")
            st.write(f"Starting from Y position: {current_y_back}")
            st.write(f"Boxes to place: {len(boxes_in_urutan)}")

        layer_z = 0
        layer_x = 0
        row_y = current_y_back

        for i, box in enumerate(boxes_in_urutan):
            dx, dy, dz = box['lebar'], box['panjang'], box['tinggi']
            placed = False

            for z_try in range(layer_z, tinggi_container - dz + 1, dz):
                start_y = max(0, row_y - dy)
                for y_try in range(start_y, -1, -dy):
                    for x_try in range(layer_x, lebar_container - dx + 1, dx):
                        if (x_try + dx > lebar_container or
                            y_try + dy > panjang_container or
                            z_try + dz > tinggi_container):
                            continue

                        conflict = False
                        for c in coords:
                            if not (x_try + dx <= c['x'] or x_try >= c['x'] + c['box']['lebar'] or
                                    y_try + dy <= c['y'] or y_try >= c['y'] + c['box']['panjang'] or
                                    z_try + dz <= c['z'] or z_try >= c['z'] + c['box']['tinggi']):
                                conflict = True
                                break

                        if not conflict:
                            coords.append({
                                'box': box,
                                'x': x_try,
                                'y': y_try,
                                'z': z_try
                            })
                            total_volume += dx * dy * dz
                            total_berat += box['berat']
                            placed = True

                            if st.session_state.get('debug_mode', False) and i < 5:
                                st.write(f"  Box {i+1}: {box['produk']} placed at ({x_try}, {y_try}, {z_try})")

                            if x_try + dx + dx <= lebar_container:
                                layer_x = x_try + dx
                            elif z_try + dz + dz <= tinggi_container:
                                layer_x = 0
                                layer_z = z_try + dz
                            else:
                                layer_x = 0
                                layer_z = 0
                                row_y = y_try

                            break
                    if placed:
                        break
                if placed:
                    break

            if not placed:
                if st.session_state.get('debug_mode', False):
                    st.error(f"FAILED to place: {box['produk']} (urutan {urutan})")
                penalty += 1000

        # Update posisi belakang untuk urutan berikutnya
        if coords:
            min_y_placed = min([c['y'] for c in coords])
            current_y_back = min_y_placed
            if st.session_state.get('debug_mode', False):
                st.write(f"Updated current_y_back to: {current_y_back}")

        if st.session_state.get('debug_mode', False):
            placed_count = len([c for c in coords if c['box']['urutan'] == urutan])
            st.write(f"Urutan {urutan} completed. Boxes placed: {placed_count}/{len(boxes_in_urutan)}")

    # Penalty berat berlebih
    if total_berat > params['max_berat']:
        penalty += 5000

    # Validasi posisi terhadap batas kontainer
    violations = 0
    for i, coord in enumerate(coords):
        box = coord['box']
        x, y, z = coord['x'], coord['y'], coord['z']
        if (x + box['lebar'] > lebar_container or
            y + box['panjang'] > panjang_container or
            z + box['tinggi'] > tinggi_container):
            violations += 1
            if st.session_state.get('debug_mode', False):
                st.error(f"ERROR: Box {i} keluar batas! {box['produk']} at ({x}, {y}, {z})")

    if violations > 0:
        penalty += violations * 10000
        if st.session_state.get('debug_mode', False):
            st.warning(f"{violations} box keluar dari batas kontainer.")
    elif st.session_state.get('debug_mode', False):
        st.success("✓ Semua box berada dalam batas kontainer.")

    # Hitung skor efisiensi akhir
    container_volume = panjang_container * lebar_container * tinggi_container
    volume_ratio = total_volume / container_volume if container_volume > 0 else 0
    stability_score = 1 / (1 + penalty * 0.001)
    fitness = volume_ratio * stability_score

    if st.session_state.get('debug_mode', False):
        st.write(f"=== Final Results ===")
        st.write(f"Total boxes placed: {len(coords)}/{len(boxes)}")
        st.write(f"Total volume used: {total_volume}")
        st.write(f"Volume ratio: {volume_ratio:.3f}")
        st.write(f"Penalty: {penalty}")
        st.write(f"Fitness: {fitness:.3f}")
        st.write(f"=== LIFO Validation ===")
        for urutan in sorted(urutan_groups.keys()):
            boxes_urutan = [c for c in coords if c['box']['urutan'] == urutan]
            if boxes_urutan:
                avg_y = sum([c['y'] + c['box']['panjang'] / 2 for c in boxes_urutan]) / len(boxes_urutan)
                st.write(f"Urutan {urutan}: {len(boxes_urutan)} boxes, avg Y position: {avg_y:.1f}")

    return fitness, coords


def simple_lifo_packing(boxes, container_dims):
    """
    Simplified LIFO: place all boxes of urutan 3 first, then 2, then 1
    Start from back of container and work forward
    """
    panjang_container, lebar_container, tinggi_container = container_dims
    
    coords = []
    penalty = 0
    total_volume = 0
    total_berat = 0
    
    # Sort: urutan 3 first (placed first, comes out last - LIFO)  
    sorted_boxes = sorted(boxes, key=lambda x: (-x['urutan'], -x['volume']))
    
    if st.session_state.get('debug_mode', False):
        st.write(f"Processing {len(sorted_boxes)} boxes in LIFO order")
    
    for i, box in enumerate(sorted_boxes):
        dx = box['lebar']
        dy = box['panjang'] 
        dz = box['tinggi']
        
        placed = False
        
        # Start from back of container (Y=300) and work forward
        # This ensures LIFO: first placed (urutan 3) will be at back
        for y_try in range(panjang_container - dy, -1, -5):  # step 5 for efficiency
            for z_try in range(0, tinggi_container - dz + 1, 5):
                for x_try in range(0, lebar_container - dx + 1, 5):
                    
                    # Check bounds
                    if (x_try + dx > lebar_container or 
                        y_try + dy > panjang_container or 
                        z_try + dz > tinggi_container):
                        continue
                    
                    # Check conflicts
                    conflict = False
                    for c in coords:
                        if not (x_try + dx <= c['x'] or x_try >= c['x'] + c['box']['lebar'] or
                                y_try + dy <= c['y'] or y_try >= c['y'] + c['box']['panjang'] or
                                z_try + dz <= c['z'] or z_try >= c['z'] + c['box']['tinggi']):
                            conflict = True
                            break
                    
                    if not conflict:
                        coords.append({
                            'box': box,
                            'x': x_try,
                            'y': y_try,
                            'z': z_try
                        })
                        total_volume += dx * dy * dz
                        total_berat += box['berat']
                        placed = True
                        
                        if st.session_state.get('debug_mode', False) and i % 10 == 0:  # print every 10th box
                            st.write(f"Box {i+1}: {box['produk']} (urutan {box['urutan']}) at ({x_try}, {y_try}, {z_try})")
                        break
                if placed:
                    break
            if placed:
                break
        
        if not placed:
            if st.session_state.get('debug_mode', False):
                st.error(f"Failed to place: {box['produk']} (urutan {box['urutan']})")
            penalty += 1000
    
    # Calculate fitness
    if total_berat > params['max_berat']:
        penalty += 5000
    
    container_volume = panjang_container * lebar_container * tinggi_container
    volume_ratio = total_volume / container_volume if container_volume > 0 else 0
    stability_score = 1 / (1 + penalty * 0.001)
    fitness = volume_ratio * stability_score
    
    if st.session_state.get('debug_mode', False):
        st.write(f"Simple LIFO Results:")
        st.write(f"Placed: {len(coords)}/{len(boxes)} boxes")
        st.write(f"Fitness: {fitness:.3f}, Penalty: {penalty}")
    
    return fitness, coords

def layer_by_layer_packing(boxes, container_dims):
    """
    Main packing function - uses True LIFO algorithm
    Replace the old zonasi-based approach with sequential LIFO placement
    """
    return true_lifo_packing(boxes, container_dims)

def evaluate(individual, boxes):
    sorted_boxes = [boxes[i] for i in individual]
    fitness, coords = layer_by_layer_packing(sorted_boxes, params['dimensi'])
    
    # Hitung penalty LIFO berdasarkan posisi Y - simplified
    lifo_penalty = 0
    for coord in coords:
        box = coord['box']
        y_center = coord['y'] + box['panjang'] / 2
        
        # Expected position: urutan 3 should be at back (high Y), urutan 1 at front (low Y)
        expected_y_ratio = (4 - box['urutan']) / 3  # urutan 3 -> 1/3, urutan 2 -> 2/3, urutan 1 -> 3/3
        expected_y = expected_y_ratio * params['dimensi'][0]
        
        lifo_penalty += abs(y_center - expected_y)
    
    lifo_score = 1 / (1 + lifo_penalty * 0.001)  # reduced penalty factor
    final_fitness = 0.7 * fitness + 0.3 * lifo_score  # prioritize packing efficiency
    
    return final_fitness, coords

def calculate_unloading_time(coords, panjang_container):
    Ws = 5
    Jk = 0
    Xkontainer = 0
    Zkontainer = 0
    total_time = 0
    unloading_details = []
    
    # Sort berdasarkan urutan unloading (urutan 1 keluar duluan, lalu posisi Y)
    sorted_coords = sorted(coords, key=lambda x: (x['box']['urutan'], x['y']))
    
    for i, coord in enumerate(sorted_coords):
        box = coord['box']
        x, y, z = coord['x'], coord['y'], coord['z']
        Xawal_box = x + box['lebar'] / 2
        Zawal_box = z + box['tinggi'] / 2
        jarak_horizontal = 2 * abs(Xkontainer - Xawal_box)
        jarak_vertikal = abs(Zawal_box - Zkontainer)
        jarak_tempuh = jarak_horizontal + jarak_vertikal + Jk
        waktu_unloading = jarak_tempuh * Ws / 100
        total_time += waktu_unloading
        
        unloading_details.append({
            'box_index': i + 1,
            'produk': box['produk'],
            'customer': box['customer'],
            'urutan': box['urutan'],
            'posisi': f"({x}, {y}, {z})",
            'jarak_horizontal_cm': round(jarak_horizontal, 2),
            'jarak_vertikal_cm': round(jarak_vertikal, 2),
            'jarak_tempuh_cm': round(jarak_tempuh, 2),
            'waktu_unloading_detik': round(waktu_unloading, 2)
        })
    
    return total_time, unloading_details

def generate_population(n):
    return [random.sample(range(n), n) for _ in range(params['max_populasi'])]

def roulette_selection(pop, fits):
    total = sum(fits)
    if total == 0:
        return random.choice(pop)
    pick = random.uniform(0, total)
    current = 0
    for p, f in zip(pop, fits):
        current += f
        if current > pick:
            return p
    return pop[0]

def crossover(p1, p2):
    if random.random() > params['crossover_prob']:
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
    if random.random() > params['mutasi_prob']:
        return ind
    a = random.randint(0, len(ind) - 1)
    b = min(a + random.randint(1, 3), len(ind) - 1)
    new_ind = ind.copy()
    new_ind[a], new_ind[b] = new_ind[b], new_ind[a]
    return new_ind

# Debug mode toggle (add this to your Streamlit UI)
def enable_debug_mode():
    """Call this function to enable debug output"""
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)

def export_coords_to_csv(coords, all_boxes, container_dims):
    panjang, lebar, tinggi = container_dims
    exported = []

    # Gunakan id untuk identifikasi unik
    placed_map = {id(c['box']): c for c in coords}

    for box in all_boxes:
        box_id = id(box)
        if box_id in placed_map:
            c = placed_map[box_id]
            x, y, z = c['x'], c['y'], c['z']
            dx, dy, dz = box['lebar'], box['panjang'], box['tinggi']


            if (x + dx > lebar or y + dy > panjang or z + dz > tinggi):
                status = "Keluar batas kontainer"
            else:
                status = "Valid"

            exported.append({
                "Produk": box['produk'],
                "Customer": box['customer'],
                "X": x,
                "Y": y,
                "Z": z,
                "Urutan": box['urutan'],
                "Berat (kg)": box['berat'],
                "Status": status
            })
        else:
            exported.append({
                "Produk": box['produk'],
                "Customer": box['customer'],
                "X": "-", "Y": "-", "Z": "-",
                "Urutan": box['urutan'],
                "Berat (kg)": box['berat'],
                "Status": "Tidak disusun"
            })

    return pd.DataFrame(exported)

