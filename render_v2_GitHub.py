import matplotlib.pyplot as plt
import numpy as np
import os
import io

def render_problem_diagram(prob_id):
    """연습 문제 풀이 세션에서 각 문제 번호(ID)에 맞는 다이어그램을 생성하거나 이미지를 로드합니다."""
    pid = str(prob_id).strip()
    
    # Figure 초기화
    fig, ax = plt.subplots(figsize=(4, 3), dpi=200)
    ax.set_aspect('equal')
    found = False

    # 1. Statics (S_1.1 ~ S_1.4) - 수치 기반 다이어그램 생성
    if pid == "S_1.1_1": 
        ax.plot(0, 0, 'ks', markersize=15)
        ax.annotate('', xy=(-1.5, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', lw=2, color='blue'))
        ax.annotate('', xy=(1.2, 1.2), xytext=(0, 0), arrowprops=dict(arrowstyle='<-', lw=2, color='green'))
        ax.annotate('', xy=(0, -1.5), xytext=(0, 0), arrowprops=dict(arrowstyle='->', lw=2, color='red'))
        found = True
    elif pid == "S_1.1_2": 
        t = np.radians(30); ax.plot([-2, 2], [-2*np.tan(t), 2*np.tan(t)], 'k-', lw=2)
        ax.add_patch(plt.Circle((0, 0.58), 0.5, color='orange', alpha=0.7))
        ax.annotate('', xy=(0.5, 1.45), xytext=(0, 0.58), arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.annotate('', xy=(0, -0.8), xytext=(0, 0.58), arrowprops=dict(arrowstyle='->', color='red', lw=2))
        found = True
    elif pid == "S_1.1_3": 
        ax.plot([-1.5, 1.5], [0, 0], 'k-', lw=4); ax.plot(-1.5, -0.2, 'k^')
        ax.annotate('', xy=(1.5, 1.5), xytext=(1.5, 0), arrowprops=dict(arrowstyle='<-', color='blue', lw=2))
        found = True
    elif pid == "S_1.2_1": 
        ax.plot([0, 2, 4], [0, 1.5, 0], 'k-o'); ax.plot([0, 4], [0, 0], 'k-')
        ax.annotate('', xy=(2, -1), xytext=(2, 0), arrowprops=dict(arrowstyle='->', color='red', lw=2))
        found = True
    elif pid == "S_1.4_1": 
        ax.plot([-2, 4], [0, 0], 'k-', lw=4); ax.plot(0, -0.2, 'k^')
        ax.annotate('', xy=(-2, -1), xytext=(-2, 0), arrowprops=dict(arrowstyle='->', color='red'))
        ax.annotate('', xy=(4, 0.5), xytext=(4, 0), arrowprops=dict(arrowstyle='->', color='blue'))
        found = True

    # 2. Kinematics (K_2.1 ~ K_2.4) - 이미지 기반 로드
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
    """강의 세션에서 학생들이 슬라이더를 조절할 때 실시간으로 물리적 성분을 시각화합니다."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    
    if topic == "Projectile Motion":
        v0, angle = params.get('v0', 30), params.get('angle', 45)
        g, theta = 9.81, np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / g
        t = np.linspace(0, t_flight, 100)
        x = v0 * np.cos(theta) * t
        y = v0 * np.sin(theta) * t - 0.5 * g * t**2
        ax.plot(x, y, 'g-', lw=2, label='Trajectory')
        # 특정 시점의 속도 벡터 표시
        ti = t_flight * 0.4
        xi, yi = v0*np.cos(theta)*ti, v0*np.sin(theta)*ti - 0.5*g*ti**2
        ax.quiver(xi, yi, v0*np.cos(theta), 0, color='blue', scale=200, label='vx')
        ax.quiver(xi, yi, 0, v0*np.sin(theta)-g*ti, color='red', scale=200, label='vy')
        ax.set_title(f"Projectile Motion (v0={v0}, theta={angle})")
        

    elif topic == "Normal & Tangent":
        v, rho = params.get('v', 20), params.get('rho', 50)
        s = np.linspace(0, np.pi/2, 100)
        ax.plot(rho*np.cos(s), rho*np.sin(s), 'k--', lw=1, label='Path')
        # 입자 위치 및 가속도 벡터
        px, py = rho*np.cos(np.pi/4), rho*np.sin(np.pi/4)
        ax.plot(px, py, 'ro')
        ax.quiver(px, py, -np.sin(np.pi/4)*10, np.cos(np.pi/4)*10, color='blue', scale=50, label='at')
        an_val = (v**2/rho)
        ax.quiver(px, py, -np.cos(np.pi/4)*an_val*2, -np.sin(np.pi/4)*an_val*2, color='red', scale=50, label='an = v²/ρ')
        ax.set_title(f"Acceleration: an = {an_val:.2f} m/s²")
        

    elif topic == "Polar Coordinates":
        r_val, theta_deg = params.get('r', 20), params.get('theta', 45)
        theta_rad = np.radians(theta_deg)
        ax.quiver(0, 0, np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, color='black', scale=20, label='r vector')
        ax.quiver(np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, np.cos(theta_rad), np.sin(theta_rad), color='blue', scale=10, label='er')
        ax.quiver(np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, -np.sin(theta_rad), np.cos(theta_rad), color='red', scale=10, label='etheta')
        ax.set_title("Polar Coordinates: er & etheta")
        

    ax.legend(); ax.grid(True, alpha=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf
