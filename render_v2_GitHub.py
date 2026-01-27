import matplotlib.pyplot as plt
import numpy as np
import os
import io

def render_problem_diagram(prob_id):
    """Generates precise FBDs and geometric diagrams for all Statics and Kinematics categories."""
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
            ax.text(-1.4, 0.2, '$T_A$', color='blue'); ax.text(1.0, 1.3, '$T_B (45^\circ)$', color='green')
            ax.set_xlim(-2, 2); ax.set_ylim(-2, 2)
            found = True
        elif pid == "S_1.1_2": # Cylinder on Incline
            theta = np.radians(30)
            ax.plot([-2, 2], [2*np.tan(-theta), -2*np.tan(-theta)], 'k-', lw=2) 
            ax.add_patch(plt.Circle((0, 0.5), 0.5, color='gray', alpha=0.5)) 
            ax.annotate('', xy=(0.5*np.sin(theta), 0.5+0.5*np.cos(theta)), xytext=(0, 0.5), 
                        arrowprops=dict(arrowstyle='->', color='red')) 
            ax.set_xlim(-2, 2); ax.set_ylim(-1, 2)
            found = True
        elif pid == "S_1.1_3": # Beam with Pin and Cable
            ax.plot([0, 3], [0, 0], 'brown', lw=6) 
            ax.plot(0, 0, 'k^', markersize=10) 
            ax.annotate('', xy=(3, 2), xytext=(3, 0), arrowprops=dict(arrowstyle='-', ls='--')) 
            ax.set_xlim(-0.5, 4); ax.set_ylim(-1, 3)
            found = True

    # --- S_1.2: Truss Analysis ---
    elif pid.startswith("S_1.2"):
        if pid == "S_1.2_1": # Simple Bridge Truss
            pts = np.array([[0,0], [2,2], [4,0], [0,0]])
            ax.plot(pts[:,0], pts[:,1], 'k-o')
            ax.annotate('', xy=(2,0.5), xytext=(2,2), arrowprops=dict(arrowstyle='->', color='red')) 
            ax.set_xlim(-0.5, 4.5); ax.set_ylim(-1, 3)
            found = True
        elif pid == "S_1.2_2": # Triangle Truss (60 deg)
            pts = np.array([[0,0], [1, 1.73], [2,0], [0,0]])
            ax.plot(pts[:,0], pts[:,1], 'k-o')
            ax.set_xlim(-0.5, 2.5); ax.set_ylim(-0.5, 2.5)
            found = True
        elif pid == "S_1.2_3": # Pratt Truss
            ax.plot([0,1,2,3], [0,1,1,0], 'k-o'); ax.plot([0,3], [0,0], 'k-o')
            ax.plot([1,1], [0,1], 'k-o'); ax.plot([2,2], [0,1], 'k-o')
            ax.set_xlim(-0.5, 3.5); ax.set_ylim(-0.5, 2)
            found = True

    # --- S_1.3: Geometric Properties (Centroids/Inertia) ---
    elif pid.startswith("S_1.3"):
        if pid == "S_1.3_1": # Rectangle Centroid
            ax.add_patch(plt.Rectangle((0,0), 4, 6, fill=False, hatch='/'))
            ax.plot(2, 3, 'rx', markersize=10) 
            ax.set_xlim(-1, 5); ax.set_ylim(-1, 7)
            found = True
        elif pid == "S_1.3_2": # Square Inertia
            ax.add_patch(plt.Rectangle((-0.1, -0.1), 0.2, 0.2, color='orange', alpha=0.3))
            ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
            ax.set_xlim(-0.2, 0.2); ax.set_ylim(-0.2, 0.2)
            found = True
        elif pid == "S_1.3_3": # Circle Area
            ax.add_patch(plt.Circle((0,0), 0.25, color='blue', alpha=0.2))
            ax.plot([-0.25, 0.25], [0,0], 'k<->') 
            ax.set_xlim(-0.5, 0.5); ax.set_ylim(-0.5, 0.5)
            found = True

    # --- S_1.4: Equilibrium (Moments/Levers) ---
    elif pid.startswith("S_1.4"):
        if pid == "S_1.4_1": # Pivot/Balance
            ax.plot([-2, 4], [0, 0], 'k', lw=4) 
            ax.plot(0, -0.2, 'k^', markersize=15) 
            ax.annotate('', xy=(-2, -1), xytext=(-2, 0), arrowprops=dict(arrowstyle='->', color='red'))
            ax.annotate('', xy=(4, -0.5), xytext=(4, 0), arrowprops=dict(arrowstyle='->', color='blue'))
            ax.set_xlim(-3, 5); ax.set_ylim(-2, 2)
            found = True
        elif pid == "S_1.4_2": # Cantilever Beam
            ax.plot([0, 3], [0, 0], 'gray', lw=8) 
            ax.axvline(0, color='black', lw=10) 
            ax.annotate('', xy=(3, -1), xytext=(3, 0), arrowprops=dict(arrowstyle='->', color='red'))
            ax.set_xlim(-1, 4); ax.set_ylim(-2, 2)
            found = True
        elif pid == "S_1.4_3": # Carrying a log
            ax.plot([0, 6], [0, 0], 'brown', lw=10) 
            ax.annotate('A', xy=(0, 1.2), xytext=(0, 0), arrowprops=dict(arrowstyle='<-'))
            ax.annotate('B', xy=(4, 1.2), xytext=(4, 0), arrowprops=dict(arrowstyle='<-'))
            ax.set_xlim(-1, 7); ax.set_ylim(-2, 2)
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
                ax.set_xlim(0, w); ax.set_ylim(h, 0) # Keeps image orientation standard
                found = True
        except: pass

    if not found:
        ax.text(0.5, 0.5, f"Diagram\n{pid}\n(Missing)", color='gray', ha='center', va='center')
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    ax.axis('off')
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def render_lecture_visual(topic, params=None):
    """Visualizes derivation components with a centered origin (0,0)."""
    fig, ax = plt.subplots(figsize=(5, 5), dpi=150)
    if params is None: params = {}
    
    # Force the origin (0,0) to be the center
    ax.axhline(0, color='black', lw=1.5, alpha=0.7)
    ax.axvline(0, color='black', lw=1.5, alpha=0.7)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.set_aspect('equal')
    
    if topic == "Projectile Motion":
        v0, angle = params.get('v0', 30), params.get('angle', 45)
        g, theta = 9.81, np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / g
        t = np.linspace(0, t_flight, 100)
        x = v0 * np.cos(theta) * t
        y = v0 * np.sin(theta) * t - 0.5 * g * t**2
        ax.plot(x, y, 'g-', lw=2, label='Trajectory')
        ax.set_xlim(-5, max(x)+5); ax.set_ylim(-5, max(y)+5)
        ax.set_title(r"Projectile Motion: $y = x\tan\theta - \frac{gx^2}{2v_0^2\cos^2\theta}$")

    elif topic == "Normal & Tangent":
        v, rho = params.get('v', 20), params.get('rho', 50)
        # Draw the curve path
        s = np.linspace(0, np.pi/2, 100)
        ax.plot(rho*np.cos(s), rho*np.sin(s), 'k--', lw=1)
        # Position of particle at 45 deg
        px, py = rho*np.cos(np.pi/4), rho*np.sin(np.pi/4)
        ax.plot(px, py, 'ro')
        an_mag = (v**2/rho)
        # Draw Normal Acceleration vector pointing to center (origin)
        ax.quiver(px, py, -px, -py, color='red', angles='xy', scale_units='xy', scale=1.5, label=r'$\vec{a}_n$')
        ax.set_title(r"Path Coordinates: $a_n = \frac{v^2}{\rho}$")
        ax.set_xlim(-10, rho+10); ax.set_ylim(-10, rho+10)

    elif topic == "Polar Coordinates":
        r, theta_deg = params.get('r', 20), params.get('theta', 45)
        theta_rad = np.radians(theta_deg)
        vx, vy = np.cos(theta_rad)*r, np.sin(theta_rad)*r
        ax.quiver(0, 0, vx, vy, color='blue', angles='xy', scale_units='xy', scale=1, label=r'$\vec{r}$')
        ax.set_title(r"Polar Vector: $\vec{r} = r\vec{u}_r$")
        limit = r + 5
        ax.set_xlim(-limit, limit); ax.set_ylim(-limit, limit)

    elif topic == "Relative Motion":
        vA = params.get('vA', [15, 5])
        vB = params.get('vB', [10, -5])
        
        # Calculate Relative Vector
        v_rel_x = vA[0] - vB[0]
        v_rel_y = vA[1] - vB[1]

        # Draw vA and vB from centered origin
        ax.quiver(0, 0, vA[0], vA[1], color='blue', angles='xy', scale_units='xy', scale=1, label=r'$\vec{v}_A$')
        ax.quiver(0, 0, vB[0], vB[1], color='red', angles='xy', scale_units='xy', scale=1, label=r'$\vec{v}_B$')
        
        # Draw vA/B starting at the tip of vB ending at tip of vA
        ax.quiver(vB[0], vB[1], v_rel_x, v_rel_y, color='green', angles='xy', scale_units='xy', scale=1, label=r'$\vec{v}_{A/B}$')
        
        ax.set_title(r"Relative Motion: $\vec{v}_A = \vec{v}_B + \vec{v}_{A/B}$")
        ax.legend(loc='upper right')
        
        # Symmetrize limits to keep (0,0) in the middle
        max_v = max(np.abs([vA[0], vA[1], vB[0], vB[1]])) + 10
        ax.set_xlim(-max_v, max_v); ax.set_ylim(-max_v, max_v)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
