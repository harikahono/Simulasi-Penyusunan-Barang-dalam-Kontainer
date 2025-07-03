def visualisasi_penyusunan(coords, panjang, lebar, tinggi):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim([0, lebar])
    ax.set_ylim([0, panjang])
    ax.set_zlim([0, tinggi])
    ax.set_xlabel('X (Lebar)')
    ax.set_ylabel('Y (Panjang)')
    ax.set_zlabel('Z (Tinggi)')

    # Warna berdasarkan urutan (1-4), dan 'red' untuk keluar batas
    warna_urutan = {
        1: "cyan",
        2: "magenta",
        3: "yellow",
        4: "lime"
    }

    for coord in coords:
        box = coord['box']
        x, y, z = coord['x'], coord['y'], coord['z']
        dx, dy, dz = box['lebar'], box['panjang'], box['tinggi']
        urutan = box.get('urutan', 1)

        # Cek keluar batas
        if (x + dx > lebar or y + dy > panjang or z + dz > tinggi):
            color = "red"
        else:
            color = warna_urutan.get(urutan, "gray")

        ax.bar3d(x, y, z, dx, dy, dz, color=color, edgecolor="black", alpha=0.7)

    ax.text(-10, 0, tinggi + 10, "Pintu", color='red')
    return fig
