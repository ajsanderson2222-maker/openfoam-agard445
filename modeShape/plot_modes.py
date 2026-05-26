"""Plot AGARD 445.6 Yates mode shapes (tip deflection vs span)."""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

data_dir = Path(__file__).parent / "yates"
img_dir  = Path(__file__).parent.parent / "images"
img_dir.mkdir(exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
def load(fname):
    rows = []
    for line in (data_dir / fname).read_text().splitlines():
        parts = line.split()
        if len(parts) == 4:
            rows.append([float(p) for p in parts])
    return np.array(rows)   # [idx, x, y, z_disp_at_col4] — columns per vertex file

verts = load("vertices")   # col1=idx, col2=x(chord), col3=y(span inches), col4=0
freqs = {}
for line in (data_dir / "frequency").read_text().splitlines():
    parts = line.split()
    if len(parts) == 2:
        freqs[int(parts[0])] = float(parts[1])

modes_raw = {}
for i in range(1, 5):
    modes_raw[i] = load(f"mode{i}")   # dx dy dz per vertex

# Span stations (column 3 of vertices = y in model inches, 0..30)
# Use leading-edge points only (first point per span station = smallest x per y)
span_vals = sorted(set(verts[:, 2]))   # unique y values

def le_disp(mode_data, verts, span_vals, col=3):
    """Pick leading-edge vertex per span station, return (span, disp)."""
    pts = []
    for y in span_vals:
        mask = np.isclose(verts[:, 2], y)
        idxs = np.where(mask)[0]
        # leading edge = smallest x
        le = idxs[np.argmin(verts[idxs, 1])]
        pts.append((y, mode_data[le, col]))
    return np.array(pts)

def te_disp(mode_data, verts, span_vals, col=3):
    """Pick trailing-edge vertex per span station."""
    pts = []
    for y in span_vals:
        mask = np.isclose(verts[:, 2], y)
        idxs = np.where(mask)[0]
        te = idxs[np.argmax(verts[idxs, 1])]
        pts.append((y, mode_data[te, col]))
    return np.array(pts)

# ── Figure: 2×2 grid, one mode per panel ─────────────────────────────────────
fig = plt.figure(figsize=(12, 9))
fig.patch.set_facecolor("#0f0f18")
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32)

titles = {
    1: "Mode 1 — First Bending\n9.56 Hz",
    2: "Mode 2 — First Torsion\n38.2 Hz",
    3: "Mode 3 — Second Bending\n48.3 Hz",
    4: "Mode 4 — Second Torsion\n91.5 Hz",
}
colors_le = ["#4fc3f7", "#81c784", "#ffb74d", "#f06292"]
colors_te = ["#0288d1", "#388e3c", "#e65100", "#880e4f"]

axes = []
for i, (mode_num, title) in enumerate(titles.items()):
    ax = fig.add_subplot(gs[i // 2, i % 2])
    ax.set_facecolor("#1a1a2e")

    le = le_disp(modes_raw[mode_num], verts, span_vals)
    te = te_disp(modes_raw[mode_num], verts, span_vals)

    span_norm = le[:, 0] / le[-1, 0]   # normalise 0→1

    # Normalise displacement to max abs of LE/TE combined
    scale = max(np.max(np.abs(le[:, 1])), np.max(np.abs(te[:, 1])))
    if scale < 1e-20:
        scale = 1.0

    ax.plot(span_norm, le[:, 1] / scale, "o-", color=colors_le[i],
            lw=2, ms=4, label="Leading edge")
    ax.plot(span_norm, te[:, 1] / scale, "s--", color=colors_te[i],
            lw=2, ms=4, label="Trailing edge")

    ax.axhline(0, color="#555", lw=0.8, ls=":")
    ax.set_title(title, color="white", fontsize=11, pad=6)
    ax.set_xlabel("Normalised span (η)", color="#aaa", fontsize=9)
    ax.set_ylabel("Normalised out-of-plane\ndisplacement", color="#aaa", fontsize=9)
    ax.tick_params(colors="#aaa", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.legend(fontsize=8, facecolor="#22223b", edgecolor="#555",
              labelcolor="white", loc="upper left")
    ax.set_xlim(0, 1)
    axes.append(ax)

fig.suptitle("AGARD 445.6 Wing — Yates Experimental Mode Shapes",
             color="white", fontsize=14, y=0.98)

plt.savefig(img_dir / "mode_shapes.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("Saved images/mode_shapes.png")
