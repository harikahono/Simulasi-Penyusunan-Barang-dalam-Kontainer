import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from matplotlib.patches import Patch
import matplotlib.colors as mcolors

def get_color(urutan):
    """Get color based on delivery order priority."""
    color_map = {
        1: 'cyan',  # First delivery - front
        2: 'magenta',  # Second delivery - middle
        3: 'yellow',  # Third delivery - back
    }
    return color_map.get(urutan, 'lightgrey')

def draw_container_outline(ax, panjang, lebar, tinggi):
    """Draw transparent container outline with grid."""
    # Draw container edges
    edges = [
        # Bottom face
        [(0, 0, 0), (lebar, 0, 0)],
        [(lebar, 0, 0), (lebar, panjang, 0)],
        [(lebar, panjang, 0), (0, panjang, 0)],
        [(0, panjang, 0), (0, 0, 0)],
        
        # Top face
        [(0, 0, tinggi), (lebar, 0, tinggi)],
        [(lebar, 0, tinggi), (lebar, panjang, tinggi)],
        [(lebar, panjang, tinggi), (0, panjang, tinggi)],
        [(0, panjang, tinggi), (0, 0, tinggi)],
        
        # Vertical edges
        [(0, 0, 0), (0, 0, tinggi)],
        [(lebar, 0, 0), (lebar, 0, tinggi)],
        [(lebar, panjang, 0), (lebar, panjang, tinggi)],
        [(0, panjang, 0), (0, panjang, tinggi)]
    ]
    
    for edge in edges:
        ax.plot3D(*zip(*edge), color='black', linewidth=1.5, alpha=0.7)

def draw_box(ax, x, y, z, dx, dy, dz, color, alpha=0.8, is_container=False):
    """Draw a 3D box with specified dimensions and color."""
    # Define the 8 vertices of the box
    vertices = np.array([
        [x, y, z],
        [x+dx, y, z],
        [x+dx, y+dy, z],
        [x, y+dy, z],
        [x, y, z+dz],
        [x+dx, y, z+dz],
        [x+dx, y+dy, z+dz],
        [x, y+dy, z+dz]
    ])
    
    # Define the 6 faces using vertex indices
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
        [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
    ]
    
    # Create a Poly3DCollection
    edge_color = 'black' if not is_container else None
    edge_width = 0.5 if not is_container else 0
    
    # Add lighting effect to make boxes look 3D
    face_colors = [mcolors.to_rgba(color, alpha)] * 6
    
    # Create slightly darker color for edges
    darker = mcolors.to_rgba(color, alpha*0.7)
    
    # Apply slightly different shading to faces
    for i in range(6):
        # Adjust shading based on face orientation
        if i == 0:  # bottom face
            face_colors[i] = darker
        elif i == 1:  # top face
            face_colors[i] = mcolors.to_rgba(color, alpha*1.1)
    
    collection = Poly3DCollection(
        faces, facecolors=face_colors, edgecolors=edge_color, linewidths=edge_width
    )
    
    # Add some ambient lighting
    collection.set_alpha(alpha)
    ax.add_collection3d(collection)

def visualisasi_penyusunan(coords, panjang_container, lebar_container, tinggi_container, show=True):
    """Create a 3D visualization of container loading."""
    # Create figure and 3D axis
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Draw container outline
    draw_container_outline(ax, panjang_container, lebar_container, tinggi_container)
    
    # Draw invisible container to set bounds
    draw_box(ax, 0, 0, 0, lebar_container, panjang_container, tinggi_container, 
             'white', alpha=0.0, is_container=True)
    
    # Sort boxes by position to help with rendering
    coords_sorted = sorted(coords, key=lambda c: (c['z'], c['y'], c['x']))
    
    # Draw boxes
    for coord in coords_sorted:
        box = coord['box']
        x, y, z = coord['x'], coord['y'], coord['z']
        dx, dy, dz = box['lebar'], box['panjang'], box['tinggi']
        urutan = box['urutan'] if 'urutan' in box else 1
        color = get_color(urutan)
        
        draw_box(ax, x, y, z, dx, dy, dz, color)
    
    # Set axis labels and limits
    ax.set_xlabel('Lebar (cm) (Kiri-Kanan)', fontsize=12)
    ax.set_ylabel('Panjang (cm) (Depan-Belakang, Urutan: 1->3)', fontsize=12)
    ax.set_zlabel('Tinggi (cm)', fontsize=12)
    
    # Set consistent limits
    ax.set_xlim([0, lebar_container])
    ax.set_ylim([0, panjang_container])
    ax.set_zlim([0, tinggi_container])
    
    # Add container dimensions text
    dimension_text = f"Kontainer: {panjang_container}cm × {lebar_container}cm × {tinggi_container}cm"
    fig.text(0.5, 0.02, dimension_text, ha='center', fontsize=10)
    
    # Add labels for door and back
    ax.text(0, 0, -5, "PINTU", color='red', fontsize=14, weight='bold')
    ax.text(lebar_container/2, panjang_container, -5, "BELAKANG", color='black', fontsize=12)
    
    # Add legend for delivery order
    legend_elements = [
        Patch(facecolor='cyan', edgecolor='black', label='Tujuan Lokasi ke-1 (CYAN)'),
        Patch(facecolor='magenta', edgecolor='black', label='Tujuan Lokasi ke-2 (MAGENTA)'),
        Patch(facecolor='yellow', edgecolor='black', label='Tujuan Lokasi ke-3 (KUNING)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    # Set view angle to match reference
    ax.view_init(elev=20, azim=-135)
    
    # Set title
    ax.set_title('Penyusunan Barang (LIFO: 1 = dikirim pertama, dekat pintu)', fontsize=14, y=1.05)
    
    # Remove grid for cleaner look
    ax.grid(False)
    
    # Layout and display
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    if show:
        plt.show()
    
    return fig