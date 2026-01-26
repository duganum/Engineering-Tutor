import matplotlib.pyplot as plt
import numpy as np
import os
import io

def render_problem_diagram(prob_id):
    """Generates precise FBDs and geometric diagrams for all Statics categories."""
    pid = str(prob_id).strip()
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_aspect('equal')
    found = False

    # --- S_1.1: Free Body Diagrams (Equilibrium) ---
    if pid.startswith("S_1.1"):
        if pid == "S_1.1_1": # 50kg mass cables
            ax.plot(0, 0, 'ko', markersize=8)
            ax.annotate('', xy=(-1.5, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', color='blue'))
            ax.annotate('', xy=(1.2, 1.2), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', color='green'))
            ax.annotate('', xy=(0, -1.5), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color='red'))
            ax.text(-1.4, 0.2, 'A', color='blue'); ax.text(1.0, 1.3, 'B (45°)', color='green')
            found = True
        elif pid == "S_1.1_2": # Cylinder on Incline
            theta = np.radians(30)
            ax.plot([-2, 2], [2*np.tan(-theta), -2*np.tan(-theta)], 'k-', lw=2) # Incline
            ax.add_patch(plt.Circle((0, 0.5), 0.5, color='gray', alpha=0.5)) # Cylinder
            ax.annotate('', xy=(0.5*np.sin(theta), 0.5+0.5*np.cos(theta)), xytext=(0, 0.5), 
                        arrowprops=dict(arrowstyle='->', color='red')) # Normal Force
            found = True
        elif pid == "S_1.1_3": # Beam with Pin and Cable
            ax.plot([0, 3], [0, 0], 'brown', lw=6) # Beam
            ax.plot(0, 0, 'k^', markersize=10) # Pin A
            ax.annotate('', xy=(3, 2), xytext=(3, 0), arrowprops=dict(arrowstyle='-', ls='--')) # Cable B
            found = True

    # --- S_1.2: Truss Analysis ---
    elif pid.startswith("S_1.2"):
        if pid == "S_1.2_1": # Simple Bridge Truss
            pts = np.array([[0,0], [2,2], [4,0], [0,0]])
            ax.plot(pts[:,0], pts[:,1], 'k-o')
            ax.annotate('', xy=(2,-1), xytext=(2,2), arrowprops=dict(arrowstyle='->', color='red')) # Load
            found = True
        elif pid == "S_1.2_2": # Triangle Truss (60 deg)
            pts = np.array([[0,0], [1, 1.73], [2,0], [0,0]])
            ax.plot(pts[:,0], pts[:,1], 'k-o')
            ax.set_title("Equilateral Truss (60°)")
            found = True
        elif pid == "S_1.2_3": # Pratt Truss
            ax.plot([0,1,2,3], [0,1,1,0], 'k-o'); ax.plot([0,3], [0,0], 'k-o') # Bottom/Top chords
            ax.plot([1,1], [0,1], 'k-o'); ax.plot([2,2], [0,1], 'k-o') # Verticals
            found = True

    # --- S_1.3: Geometric Properties (Centroids/Inertia) ---
    elif pid.startswith("S_1.3"):
        if pid == "S_1.3_1": # Rectangle Centroid
            ax.add_patch(plt.Rectangle((0,0), 4, 6, fill=False, hatch='/'))
            ax.plot(2, 3, 'rx', markersize=10) # Centroid
            ax.set_xlim(-1, 5); ax.set_ylim(-1, 7)
            found = True
        elif pid == "S_1.3_2": # Square Inertia
            ax.add_patch(plt.Rectangle((-0.1, -0.1), 0.2, 0.2, color='orange', alpha=0.3))
            ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
            found = True
        elif pid == "S_1.3_3": # Circle Area
            ax.add_patch(plt.Circle((0,0), 0.25, color='blue', alpha=0.2))
            ax.plot([-0.25, 0.25], [0,0], 'k<->') # Diameter line
            found = True

    # --- S_1.4: Equilibrium (Moments/Levers) ---
    elif pid.startswith("S_1.4"):
        if pid == "S_1.4_1": # Pivot/Balance
            ax.plot([-2, 4], [0, 0], 'k', lw=4) # Bar
            ax.plot(0, -0.2, 'k^', markersize=15) # Pivot
            ax.annotate('', xy=(-2, -1), xytext=(-2, 0), arrowprops=dict(arrowstyle='->', color='red'))
            ax.annotate('', xy=(4, -0.5), xytext=(4, 0), arrowprops=dict(arrowstyle='->', color='blue'))
            found = True
        elif pid == "S_1.4_2": # Cantilever Beam
            ax.plot([0, 3], [0, 0], 'gray', lw=8) # Beam
            ax.axvline(0, color='black', lw=10) # Fixed Support
            ax.annotate('', xy=(3, -1), xytext=(3, 0), arrowprops=dict(arrowstyle='->', color='red'))
            found = True
        elif pid == "S_1.4_3": # Carrying a log
            ax.plot([0, 6], [0, 0], 'brown', lw=10) # Log
            ax.annotate('A', xy=(0, 1), xytext=(0, 0), arrowprops=dict(arrowstyle='<-'))
            ax.annotate('B', xy=(4, 1), xytext=(4, 0), arrowprops=dict(arrowstyle='<-'))
            found = True

    # --- Kinematics Image Loader ---
    elif pid.startswith("K"):
        try:
            clean_name = pid.replace("_", "").replace(".", "").lower()
            img_path = f'images/{clean_name}.png'
            if os.path.exists(img_path):
                img = plt.imread(img_path)
                ax.imshow(img)
                h, w = img.shape[:2]
                ax.set_xlim(0, w); ax.set_ylim(h, 0)
                found = True
        except: pass

    if not found:
        ax.text(0.5, 0.5, f"Diagram\n{pid}", color='gray', ha='center')
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    ax.axis('off')
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
