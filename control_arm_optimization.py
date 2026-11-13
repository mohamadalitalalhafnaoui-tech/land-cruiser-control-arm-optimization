import numpy as np
import matplotlib.pyplot as plt

# 1. Vehicle & Load Parameters (2026 Toyota Land Cruiser EXR - GVW)
F_lateral = 14391.27       # N (Simplified: peak lateral tire load applied directly along arm axis)
L = 0.340                  # m (340 mm pin-to-pin bolt span)
K = 1.0                    # Pinned-pinned effective length factor for buckling
rho_al6061 = 2700.0        # kg/m^3 (Aluminum 6061-T6 density)
E = 68.9e9                 # Pa (Young's Modulus)
sigma_y = 276e6            # Pa (Yield Strength of Al 6061-T6)

# 2. Parametric Design Iterations: [Name, Outer Width b (m), Thickness h (m), Pocket Width b_p (m), Pocket Depth h_p (m)]
designs = [
    ("Baseline Solid Bar",      0.060, 0.015, 0.000, 0.000),
    ("Iteration 1 (Narrowed)",  0.048, 0.015, 0.000, 0.000),
    ("Iteration 2 (Pocketed)",  0.046, 0.015, 0.026, 0.008),
    ("Iteration 3 (Optimized)", 0.044, 0.015, 0.026, 0.009)
]

results = []

print(f"{'Design Iteration':24s} | {'Analytical Mass':15s} | {'Max Stress':10s} | {'Yield FoS':9s} | {'Buckling FoS':12s}")
print("-" * 82)

for name, b, h, b_p, h_p in designs:
    # Analytical Volume & Mass (400 mm total length, two 16 mm bolt holes, 240 mm central pocket)
    hole_vol = 2 * np.pi * (0.008**2) * h
    pocket_vol = b_p * h_p * 0.240
    net_vol = (0.400 * b * h) - hole_vol - pocket_vol
    mass_g = net_vol * rho_al6061 * 1000

    # Cross-sectional Area & In-Plane Moment of Inertia (I_z for lateral bending)
    A_net = (b * h) - (b_p * h_p)
    I_z = (h * (b**3) - h_p * (b_p**3)) / 12.0

    # Weak-Axis (Out-of-Plane) Moment of Inertia (I_y) using Parallel Axis Theorem for T-channel pocket
    if b_p > 0:
        # Web under pocket: width b_p, height (h - h_p); Two side flanges: width (b - b_p)/2, height h
        A_web = b_p * (h - h_p)
        y_web = (h - h_p) / 2.0
        A_flanges = (b - b_p) * h
        y_flanges = h / 2.0
        y_bar = (A_web * y_web + A_flanges * y_flanges) / A_net

        I_web = (b_p * (h - h_p)**3) / 12.0 + A_web * (y_bar - y_web)**2
        I_flanges = ((b - b_p) * (h**3)) / 12.0 + A_flanges * (y_bar - y_flanges)**2
        I_min = I_web + I_flanges
    else:
        I_min = (b * (h**3)) / 12.0

    # Euler Critical Buckling Load (Pinned-Pinned, K = 1.0)
    P_cr = (np.pi**2 * E * I_min) / ((K * L)**2)
    fos_buckling = P_cr / F_lateral

    # Combined Axial Compression + Eccentric Bending Stress (15 mm load offset, nominal without SCF)
    eccentricity = 0.015
    M_max = F_lateral * eccentricity
    sigma_axial = F_lateral / A_net
    sigma_bending = (M_max * (b / 2.0)) / I_z
    nominal_stress_mpa = (sigma_axial + sigma_bending) / 1e6

    fos_yield = (sigma_y / 1e6) / nominal_stress_mpa
    results.append((name, mass_g, nominal_stress_mpa, fos_yield, fos_buckling))
    print(f"{name:24s} | {mass_g:13.1f} g | {nominal_stress_mpa:6.2f} MPa | {fos_yield:9.2f} | {fos_buckling:12.2f}")

# 3. Plot Analytical Mass vs. Yield & Buckling Safety Factors
names = [r[0] for r in results]
masses = [r[1] for r in results]
fos_y_vals = [r[3] for r in results]
fos_b_vals = [r[4] for r in results]

fig, ax1 = plt.subplots(figsize=(9.5, 5.0))
x = np.arange(len(names))
ax1.bar(x - 0.18, masses, width=0.35, color='#2b5c8f', label='Analytical Mass (g)')
ax1.set_ylabel('Component Mass (g)', color='#2b5c8f', fontweight='bold')
ax1.set_ylim(0, 1150)
ax1.set_xticks(x)
ax1.set_xticklabels(names, rotation=10)

ax2 = ax1.twinx()
ax2.plot(x + 0.15, fos_y_vals, color='#d9534f', marker='o', linewidth=2.5, markersize=8, label='Yield FoS (Nominal)')
ax2.plot(x + 0.15, fos_b_vals, color='#f0ad4e', marker='s', linewidth=2.5, markersize=7, label='Euler Buckling FoS')
ax2.axhline(2.0, color='green', linestyle='--', linewidth=1.5, label='Min Target FoS (2.0)')
ax2.set_ylabel('Factor of Safety (FoS)', color='#d9534f', fontweight='bold')
ax2.set_ylim(0, 9.5)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

plt.title('2026 Land Cruiser Control Arm: Parametric Mass & Safety Factor Optimization (14.4 kN)')
fig.tight_layout()
plt.savefig('control_arm_optimization.png', dpi=300)
plt.show()