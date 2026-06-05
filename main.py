import pandas as pd
from solver import ShipyardSolver
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
import time

def load_data(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 10:
        data = {
            'id': list(range(1, 51)),
            'width': [random.randint(5, 20) for _ in range(50)],
            'height': [random.randint(5, 20) for _ in range(50)]
        }
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        return df.to_dict('records')
    
    df = pd.read_csv(file_path)
    return df.to_dict('records')

def visualize_layout(shipyard_width, shipyard_height, placed_blocks, utilization, output_filename='shipyard_layout.png'):
    fig, ax = plt.subplots(1, figsize=(14, 14))
    ax.set_xlim(0, shipyard_width)
    ax.set_ylim(0, shipyard_height)
    ax.set_aspect('equal', adjustable='box')
    
    title = f'Hybrid Optimized Shipyard Layout\nMaxRects + GA + Local Search | Utilization: {utilization:.2%}'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Width (meters)', fontsize=12)
    ax.set_ylabel('Height (meters)', fontsize=12)

    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(vmin=0, vmax=len(placed_blocks))
    
    for i, block in enumerate(placed_blocks):
        color = cmap(norm(i))
        rect = patches.Rectangle(
            (block['x'], block['y']),
            block['w'],
            block['h'],
            linewidth=1.5, edgecolor='white', facecolor=color, alpha=0.85
        )
        ax.add_patch(rect)
        if block['w'] > 3 and block['h'] > 3:
            ax.text(block['x'] + block['w']/2, block['y'] + block['h']/2, 
                    f"B{block['id']}", color='white', ha='center', va='center', 
                    fontsize=8, fontweight='bold', path_effects=[])

    plt.grid(True, which='both', color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    plt.savefig(output_filename, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"High-quality visualization saved to {output_filename}")

def main():
    print("--- Shipyard Block Packing Optimizer (Hybrid: GA + Local Search + MaxRects) ---")
    
    SHIPYARD_WIDTH = 100
    SHIPYARD_HEIGHT = 100
    
    if os.path.exists('data.csv'): os.remove('data.csv')
    blocks_data = load_data('data.csv')
    formatted_blocks = [{'id': int(b['id']), 'w': int(b['width']), 'h': int(b['height'])} for b in blocks_data]
    
    start_time = time.time()
    solver = ShipyardSolver(SHIPYARD_WIDTH, SHIPYARD_HEIGHT)
    results = solver.solve_hybrid(formatted_blocks, iterations=1000)
    end_time = time.time()
    
    utilization = solver.get_utilization()
    print(f"\nFinal Optimization Results:")
    print(f"  - Total blocks: {len(formatted_blocks)}")
    print(f"  - Blocks placed: {len(results)}")
    print(f"  - Execution time: {end_time - start_time:.2f} seconds")
    print(f"  - Shipyard Utilization: {utilization:.2%}")
    
    with open('output_layout.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("Layout saved to output_layout.json")

    visualize_layout(SHIPYARD_WIDTH, SHIPYARD_HEIGHT, results, utilization)

if __name__ == "__main__":
    main()
