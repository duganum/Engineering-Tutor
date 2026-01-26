import matplotlib.pyplot as plt
import numpy as np
import os
import io

def render_problem_diagram(prob_id):
    pid = str(prob_id).strip()
    
    # Initialize Figure
    fig, ax = plt.subplots(figsize=(4, 3), dpi=200)
    ax.set_aspect('equal')
    found = False

    # ---------------------------------------------------------
    # 1. Statics (S_1.1 ~ S_1.4) - Hand-drawn/Generated
    # ---------------------------------------------------------
    if pid == "S_1.1_1": # Suspended Mass
        ax.plot(0, 0, 'ks', markersize=15)
        ax.annotate('', xy=(-1.5, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', lw=2, color='blue'))
        ax.annotate('', xy=(1.2, 1.2), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', lw=2, color='green'))
        ax.annotate('', xy=(0, -1.5), xytext=(0, 0), arrowprops=dict(arrowstyle='->', lw=2, color='red'))
        found = True
    elif pid == "S_1.1_2": # Cylinder on Incline
        t = np.radians(30); ax.plot([-2, 2], [-2*np.tan(t), 2*np.tan(t)], 'k-', lw=2)
        ax.add_patch(plt.Circle((0, 0.58), 0.5, color='orange', alpha=0.7))
        ax.annotate('', xy=(0.5, 1.45), xytext=(0, 0.58), arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.annotate('', xy=(0, -0.8), xytext=(0, 0.58), arrowprops=dict(arrowstyle='->', color='red', lw=2))
        found = True
    elif pid == "S_1.1_3": # Beam with Pin/Cable
        ax.plot([-1.5, 1.5], [0, 0], 'k-', lw=4); ax.plot(-1.5, -0.2, 'k^')
        ax.annotate('', xy=(1.5, 1.5), xytext=(1.5, 0), arrowprops=dict(arrowstyle='<-', color='blue', lw=2))
        found = True
    elif pid == "S_1.2_1": # Symmetric Truss
        ax.plot([0, 2, 4], [0, 1.5, 0], 'k-o'); ax.plot([0, 4], [0, 0], 'k-')
        ax.annotate('', xy=(2, -1), xytext=(2, 0), arrowprops=dict(arrowstyle='->', color='red', lw=2))
        found = True
    elif pid == "S_1.2_2": # Triangle Truss
        ax.plot([0, 2, 1, 0], [0, 0, 1.73, 0], 'k-o', lw=2)
        ax.annotate('', xy=(1, 0.7), xytext=(1, 1.73), arrowprops=dict(arrowstyle='->', color='red', lw=2))
        found = True
    elif pid == "S_1.2_3": # Zero Force Members
        for x in range(3): ax.plot([x, x+1], [0, 0], 'k-o')
        ax.plot([0, 1, 1, 0], [0, 1, 0, 0], 'k-'); found = True
    elif "S_1.3" in pid: # Centroids/Geometry
        if "1" in pid: ax.add_patch(plt.Rectangle((-1, 0), 2, 3, fill=False, lw=2))
        elif "2" in pid: ax.add_patch(plt.Rectangle((-1, -1), 2, 2, fill=False, lw=2))
        elif "3" in pid: ax.add_patch(plt.Circle((0, 0), 1, fill=False, lw=2))
        found = True
    elif pid == "S_1.4_1": # Seesaw Balance
        ax.plot([-2, 4], [0, 0], 'k-', lw=4); ax.plot(0, -0.2, 'k^')
        ax.annotate('', xy=(-2, -1), xytext=(-2, 0), arrowprops=dict(arrowstyle='->', color='red'))
        ax.annotate('', xy=(4, 0.5), xytext=(4, 0), arrowprops=dict(arrowstyle='->', color='blue'))
        found = True
    elif pid == "S_1.4_2": # Cantilever
        ax.fill_between([-2.2, -2], -1, 1, color='gray'); ax.plot([-2, 1.5], [0, 0], 'k-', lw=4)
        ax.annotate('', xy=(1.5, -1), xytext=(1.5, 0), arrowprops=dict(arrowstyle='->', color='red'))
        found = True
    elif pid == "S_1.4_3": # Log Carry
        ax.plot([-2, 2], [0, 0], color='brown', lw=8)
        ax.annotate('', xy=(-2, 1), xytext=(-2, 0), arrowprops=dict(arrowstyle='->', color='green'))
        ax.annotate('', xy=(0.67, 1), xytext=(0.67, 0), arrowprops=dict(arrowstyle='->', color='blue'))
        found = True

    # ---------------------------------------------------------
    # 2. Kinematics (K_2.1 ~ K_2.4) - Image Based
    # ---------------------------------------------------------
    # This logic handles IDs like K_2.2_1, K_2.3_2, etc. 
    # and matches them to filenames like k221.png, k232.png
    elif pid.startswith("K"):
        try:
            # Format: 'K_2.2_1' -> 'k221.png'
            clean_name = pid.replace("_", "").replace(".", "").lower()
            img_path = f'images/{clean_name}.png'
            
            if os.path.exists(img_path):
                img = plt.imread(img_path)
                ax.imshow(img)
                h, w = img.shape[:2]
                ax.set_xlim(0, w)
                ax.set_ylim(h, 0)
                ax.set_aspect('equal')
                found = True
            else:
                # Fallback for Kinematics without images
                ax.text(0.5, 0.5, f"Image {clean_name}.png\nnot found in /images", ha='center')
                found = True
        except Exception as e:
            ax.text(0.5, 0.5, f"Error loading image:\n{str(e)}", ha='center')
            found = True

    # --- Final Processing ---
    if not found:
        ax.text(0.5, 0.5, f"Diagram\n{pid}", color='red', ha='center')
        ax.set_xlim(-2.5, 2.5); ax.set_ylim(-2.5, 2.5)

    ax.axis('off')
    plt.tight_layout()

    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
