import matplotlib.pyplot as plt
import numpy as np
import io

def render_lecture_visual(topic, params=None):
    """학생들이 속도와 가속도의 성분을 직관적으로 이해할 수 있도록 시각화합니다."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    
    if topic == "Projectile Motion":
        # x, y 성분 분해 중심 시각화
        v0, angle = params.get('v0', 50), params.get('angle', 45)
        g, theta = 9.81, np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / g
        t = np.linspace(0, t_flight, 100)
        x = v0 * np.cos(theta) * t
        y = v0 * np.sin(theta) * t - 0.5 * g * t**2
        ax.plot(x, y, 'g-', lw=2)
        # 특정 지점에서 속도 벡터 분해 표시
        ti = t_flight * 0.3
        xi, yi = v0*np.cos(theta)*ti, v0*np.sin(theta)*ti - 0.5*g*ti**2
        ax.quiver(xi, yi, v0*np.cos(theta), 0, color='blue', scale=200, label='vx (Constant)')
        ax.quiver(xi, yi, 0, v0*np.sin(theta)-g*ti, color='red', scale=200, label='vy (Changing)')
        ax.set_title("Velocity Components in Projectile Motion")

    elif topic == "Normal & Tangent":
        # an = v^2/rho 유도를 위한 곡률 반경 시각화
        rho = params.get('rho', 20)
        v = params.get('v', 10)
        s = np.linspace(0, np.pi/2, 100)
        ax.plot(rho*np.cos(s), rho*np.sin(s), 'k--', lw=1)
        # 입자와 가속도 벡터
        px, py = rho*np.cos(np.pi/4), rho*np.sin(np.pi/4)
        ax.plot(px, py, 'ro', markersize=8)
        ax.quiver(px, py, -np.sin(np.pi/4)*10, np.cos(np.pi/4)*10, color='blue', scale=50, label='vt (Tangent)')
        ax.quiver(px, py, -np.cos(np.pi/4)*(v**2/rho)*2, -np.sin(np.pi/4)*(v**2/rho)*2, color='red', scale=50, label='an = v²/ρ')
        ax.set_title(f"Normal Accel: {v**2/rho:.2f} m/s² (v={v}, ρ={rho})")
        

    elif topic == "Polar Coordinates":
        # r, theta 성분 및 속도 유도 시각화
        r_val, theta_deg = params.get('r', 10), params.get('theta', 30)
        theta_rad = np.radians(theta_deg)
        ax.quiver(0, 0, np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, color='black', scale=20, label='r vector')
        ax.quiver(np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, np.cos(theta_rad), np.sin(theta_rad), color='blue', scale=10, label='er (Radial)')
        ax.quiver(np.cos(theta_rad)*r_val, np.sin(theta_rad)*r_val, -np.sin(theta_rad), np.cos(theta_rad), color='red', scale=10, label='eθ (Transverse)')
        ax.set_title("Radial and Transverse Components")
        

    ax.legend(); ax.grid(True, alpha=0.3)
    buf = io.BytesIO(); fig.savefig(buf, format='png'); plt.close(fig); buf.seek(0)
    return buf
