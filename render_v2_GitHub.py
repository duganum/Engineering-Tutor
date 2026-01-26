import matplotlib.pyplot as plt
import numpy as np
import os
import io

def render_problem_diagram(prob_id):
    """Generates diagrams or loads images for practice problems."""
    pid = str(prob_id).strip()
    fig, ax = plt.subplots(figsize=(4, 3), dpi=200)
    ax.set_aspect('equal')
    found = False

    # 1. Statics Logic (Manual drawing)
    if pid.startswith("S_1"):
        if pid == "S_1.1_1":
            ax.plot(0, 0, 'ks', markersize=15)
            ax.annotate('', xy=(-1.5, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', lw=2, color='blue'))
            ax.annotate('', xy=(1.2, 1.2), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', lw=2, color='green'))
            ax.annotate('', xy=(0, -1.5), xytext=(0, 0), arrowprops=dict(arrowstyle='->', lw=2, color='red'))
            found = True
        # Add other statics cases as needed...

    # 2. Kinematics Logic (Image Loading)
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
        ax.text(0.5, 0.5, f"Diagram\n{pid}", color='red', ha='center')
        ax.set_xlim(-2.5, 2.5); ax.set_ylim(-2.5, 2.5)

    ax.axis('off')
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def render_lecture_visual(topic, params=None):
    """Visualizes velocity and acceleration components for interactive English lectures."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    
    if topic == "Projectile Motion":
        v0, angle = params.get('v0', 30), params.get('angle', 45)
        g, theta = 9.81, np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / g
        t = np.linspace(0, t_flight, 100)
        x = v0 * np.cos(theta) * t
        y = v0 * np.sin(theta) * t - 0.5 * g * t**2
        ax.plot(x, y, 'g-', lw=2, label='Path')
        ax.set_title(f"Projectile: v0={v0}m/s, θ={angle}°")

    elif topic == "Normal & Tangent":
        v, rho = params.get('v', 20), params.get('rho', 50)
        s = np.linspace(0, np.pi/2, 100)
        ax.plot(rho*np.cos(s), rho*np.sin(s), 'k--', lw=1)
        px, py = rho*np.cos(np.pi/4), rho*np.sin(np.pi/4)
        ax.plot(px, py, 'ro')
        an_val = (v**2/rho)
        ax.quiver(px, py, -np.cos(np.pi/4)*an_val*2, -np.sin(np.pi/4)*an_val*2, color='red', scale=50, label='an = v²/ρ')
        ax.set_title(f"Normal Acceleration: {an_val:.2f} m/s²")

    elif topic == "Polar Coordinates":
        r_val, theta_deg = params.get('r', 20), params.get('theta', 45)
        theta_rad = np.radians(theta_deg)
        ax.quiver(0, 0, np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, color='black', scale=20)
        ax.set_title("Polar: Radial Vector r")

    ax.legend(); ax.grid(True, alpha=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf
