# AGARD 445.6 Aeroelastic Flutter — OpenFOAM 13 + hisa

Transonic flutter prediction for the AGARD 445.6 wing benchmark using hisa (High Speed Aerodynamic solver) on OpenFOAM 13 (Foundation). Two-phase workflow: steady aerodynamic solution → transient modal flutter.

---

## Background

The AGARD 445.6 wing is a standard aeroelastic benchmark from Yates (1988). It is a 45° swept, NACA 64A004 wing with an aspect ratio of 1.65 and a taper ratio of 0.66. Experimental flutter boundaries were measured at subsonic through supersonic Mach numbers in the NASA Langley Transonic Dynamics Tunnel, making it the most widely used validation case for computational aeroelasticity.

**Key geometry parameters:**

| Parameter | Value |
|-----------|-------|
| Airfoil | NACA 64A004 |
| Root chord | 0.558 m |
| Tip chord | 0.368 m |
| Semi-span | 0.762 m |
| Sweep (quarter-chord) | 45° |
| Aspect ratio | 1.65 |
| Taper ratio | 0.659 |

The wing model in this case has:
- X: [0, 1.1785] m (streamwise, root to tip in chord coordinates)
- Y: [−0.011, +0.011] m (thickness, max ~2.2% chord = NACA 64A004)
- Z: [0, 0.762] m (spanwise, root at symmetry plane)

---

## Freestream Conditions

Test point: Mach 1.072 (weakly supersonic), matching one of the Yates experimental conditions.

| Quantity | Value |
|----------|-------|
| Mach number | 1.072 |
| Velocity | (344.7, 0, 0) m/s |
| Static pressure | 7084.3 Pa |
| Static temperature | 257.3 K |
| Density | 0.0959 kg/m³ |
| Speed of sound | 321.5 m/s |
| Dynamic pressure | 5699 Pa |
| γ | 1.4 |
| Fluid | Air (perfect gas, μ = 0 — inviscid Euler) |

---

## Mesh

Generated with snappyHexMesh on a structured blockMesh background.

**Background block:** −10 m to +10 m in X and Y, 0 to 10 m in Z (half-domain, symmetry at Z=0).

**Refinement:**
- Global refinement box around wing: (−0.5, −0.5, −0.1) → (2.0, 0.5, 1.0), level 3
- Wing surface: levels 5–6 (cell size ~10–20 mm near surface)
- Feature edges extracted at 150° included angle, snapped at level 5

**Result:** ~98,000 cells, all hex-dominant, zero quality violations.

**Patches:**

| Patch | Type | BC |
|-------|------|----|
| `wing` | patch | inviscid wall (slip / characteristic) |
| `symmetry` | symmetryPlane | symmetryPlane |
| `farfield` | patch | characteristic farfield |
| `redistributeHelper` | internal | (parallel redistribution only) |

Mesh workflow:
```
cd mesh/
blockMesh
surfaceFeatures
snappyHexMesh -overwrite
createPatch -overwrite
checkMesh
```

---

## Solver: hisa

[hisa](https://hisa.gitlab.io) is a density-based compressible Euler/RANS solver for OpenFOAM. It uses:
- AUSM+Up flux scheme
- GMRES linear solver
- Local time stepping (pseudo-time) for steady runs
- Dual time stepping for transient runs

Flow is treated as **inviscid** (Euler, `simulationType laminar`, `mu 0`). This matches the original Yates experimental conditions, which used a lightweight flutter model where viscous effects are secondary to the pressure-driven aeroelastic response.

**Flux scheme:** AUSMPlusUp  
**Gradient scheme:** face least squares (linear)  
**Reconstruction:** weighted Van Leer limiter on ρ, U, T

---

## Boundary Conditions

### `wing` (inviscid wall)
| Field | Type |
|-------|------|
| U | `slip` |
| p | `characteristicWallPressure` |
| T | `characteristicWallTemperature` |

### `farfield`
| Field | Type |
|-------|------|
| U | `characteristicFarfieldVelocity` |
| p | `characteristicFarfieldPressure` |
| T | `characteristicFarfieldTemperature` |

### `symmetry`
All fields: `symmetryPlane`

---

## Two-Phase Workflow

### Phase 1 — Fixed (Steady Aerodynamics)

Pseudo-time marching to converge the steady aerodynamic solution on the rigid wing. Provides the initial flow field for the transient flutter run.

```
cd simulation/fixed/
cp -r 0.org 0
hisa
```

**Settings:**
- `endTime 500` pseudo-steps, `deltaT 1`
- `ddtSchemes: bounded dualTime rPseudoDeltaT steadyState`
- `writeInterval 50`, `purgeWrite 2`

### Phase 2 — Transient (Flutter)

Coupled fluid–structure simulation. The wing mesh deforms each time step according to the modal equations of motion; aerodynamic pressure feeds back into the modal accelerations.

```
cd simulation/transient/
cp -r 0.org 0
# Copy converged flow field from fixed run first
hisa
```

**Settings:**
- Physical time integration
- `maxDeltaT 2e-3` s (≈ 1/12 of mode-2 period at 38.2 Hz)
- Mesh motion: `displacementLaplacian` with `inverseFaceDistance` diffusivity on wing patch

---

## Mode Shapes

Four structural modes from Yates (1988) experimental GVT data. Stored in `modeShape/yates/`.

| Mode | Natural frequency (Hz) | Description |
|------|------------------------|-------------|
| 1 | 9.56 | First bending |
| 2 | 38.2 | First torsion |
| 3 | 48.3 | Second bending |
| 4 | 91.5 | Second torsion |

All modal masses normalized to 1. Mode shapes are defined at discrete spanwise stations and interpolated onto the CFD mesh by `genModeShape.py`.

---

## Validation

The AGARD 445.6 flutter boundary is one of the most cited aeroelastic benchmarks. Expected flutter dynamic pressure ratio (q/q_flutter) varies with Mach number. At M = 1.072 the wing is near the transonic dip — the most challenging region where flutter speed is lowest.

Published CFD results (inviscid Euler, similar mesh resolution) typically match the Yates experimental flutter boundary to within 5–15% across the Mach range 0.5–1.14.

**Reference:**  
Yates, E.C. (1988). *AGARD Standard Aeroelastic Configurations for Dynamic Response — Wing 445.6.* AGARD Report 765.

---

## Repository Structure

```
openfoam-agard445/
├── mesh/
│   ├── Allmesh                  # Mesh generation script
│   ├── constant/triSurface/     # wing.stl geometry
│   └── system/                  # blockMeshDict, snappyHexMeshDict, ...
├── modeShape/
│   ├── genModeShape.py          # Interpolates Yates modes onto CFD mesh
│   └── yates/                   # Raw Yates mode shape data
└── simulation/
    ├── fixed/                   # Steady rigid-wing Euler run
    │   ├── 0.org/               # Initial conditions template
    │   ├── constant/            # thermophysicalProperties, turbulenceProperties
    │   └── system/              # controlDict, fvSchemes, fvSolution, decomposeParDict
    └── transient/               # Coupled aeroelastic flutter run
        ├── 0.org/               # Initial conditions + modal variables
        ├── constant/modal/      # Mass, stiffness, damping matrices + mode shapes
        └── system/              # controlDict, fvSchemes, fvSolution
```

---

## Software

| Component | Version |
|-----------|---------|
| OpenFOAM | 13 (Foundation) |
| hisa | latest (gitlab.com/hisa/hisa) |
| OS | Ubuntu 22.04 (WSL2) |
