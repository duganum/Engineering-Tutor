import matplotlib.pyplot as plt
import numpy as np
import os
import io

def render_problem_diagram(prob_id):
    pid = str(prob_id).strip()
    fig, ax = plt.subplots(figsize=(4, 3), dpi=200)
    ax.set_aspect('equal')
    found = False

    # Kinematics Image Logic
    if pid.startswith("K"):
        try:
            clean_name = pid.replace("_", "").replace(".", "").lower()
            img_path = f'images/{clean_name}.png'
            if os.path.exists(img_path):
                img = plt.imread(img_path)
                ax.imshow(img); ax.axis('off'); found = True
        except: pass

    if not found:
        ax.text(0.5, 0.5, f"Diagram {pid}", ha='center')
        ax.axis('off')
    
    buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig); buf.seek(0)
    return buf

def render_lecture_visual(topic, params=None):
    fig, ax = plt.subplots(figsize=(5, 3), dpi=150)
    if topic == "Projectile Motion":
        v0, angle = params.get('v0', 50), params.get('angle', 45)
        theta = np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / 9.81
        t = np.linspace(0, t_flight, 100)
        x = v0 * np.cos(theta) * t
        y = v0 * np.sin(theta) * t - 0.5 * 9.81 * t**2
        ax.plot(x, y, 'g-', lw=2); ax.set_title("Projectile Path")
        ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
        ax.grid(True, alpha=0.3)
    elif topic == "Normal & Tangent":
        
        ax.text(0.5, 0.5, "Curvilinear Motion Concept", ha='center')
    elif topic == "Polar Coordinates":
        
        ax.text(0.5, 0.5, "Polar Coordinates Concept", ha='center')
    
    buf = io.BytesIO(); fig.savefig(buf, format='png'); plt.close(fig); buf.seek(0)
    return buf
