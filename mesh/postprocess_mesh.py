"""Generate mesh images: full domain slice, 3D boundary, wing close-up."""
import os
os.environ["DISPLAY"] = ":99"
from paraview.simple import *

case_dir = "/home/andrew/openfoam_jobs/openfoam-agard445/mesh"
img_dir  = "/home/andrew/openfoam_jobs/openfoam-agard445/images"
os.makedirs(img_dir, exist_ok=True)

BG   = [0.12, 0.12, 0.18]   # dark blue-grey
FACE = [0.55, 0.70, 0.90]   # light blue cells
EDGE = [0.05, 0.05, 0.05]   # near-black edges

foam = OpenFOAMReader(FileName=case_dir + "/mesh.foam")
foam.MeshRegions = ["internalMesh"]
foam.CellArrays  = []
foam.UpdatePipeline()

def new_view(w, h):
    v = CreateRenderView()
    v.ViewSize = [w, h]
    v.Background = BG
    v.OrientationAxesVisibility = 1
    return v

def wire_show(src, view, lw=0.6):
    d = Show(src, view)
    d.Representation = "Surface With Edges"
    d.EdgeColor        = EDGE
    d.AmbientColor     = FACE
    d.DiffuseColor     = FACE
    d.ColorArrayName   = ['POINTS', '']
    d.LineWidth        = lw
    return d

# ── 1. Full domain — XY slice at mid-span ─────────────────────────────────────
sl_domain = Slice(Input=foam)
sl_domain.SliceType        = "Plane"
sl_domain.SliceType.Origin = [0, 0, 0.38]
sl_domain.SliceType.Normal = [0, 0, 1]
sl_domain.UpdatePipeline()

v1 = new_view(1400, 1000)
wire_show(sl_domain, v1)
v1.CameraParallelProjection = 1
v1.CameraPosition   = [0, 0, 60]
v1.CameraFocalPoint = [0, 0, 0.38]
v1.CameraViewUp     = [0, 1, 0]
ResetCamera(v1)
v1.CameraParallelScale *= 1.02
Render(v1)
SaveScreenshot(img_dir + "/mesh_domain_slice.png", v1, ImageResolution=[1400,1000])
print("Saved mesh_domain_slice.png")

# ── 2. Wing region — XY slice, zoomed in ──────────────────────────────────────
sl_wing = Slice(Input=foam)
sl_wing.SliceType        = "Plane"
sl_wing.SliceType.Origin = [0, 0, 0.30]
sl_wing.SliceType.Normal = [0, 0, 1]
sl_wing.UpdatePipeline()

v2 = new_view(1400, 700)
wire_show(sl_wing, v2, lw=0.4)
v2.CameraParallelProjection = 1
v2.CameraPosition   = [0.6, 0, 60]
v2.CameraFocalPoint = [0.6, 0, 0.30]
v2.CameraViewUp     = [0, 1, 0]
v2.CameraParallelScale = 0.90   # tight zoom on wing
Render(v2)
SaveScreenshot(img_dir + "/mesh_wing_closeup.png", v2, ImageResolution=[1400,700])
print("Saved mesh_wing_closeup.png")

# ── 3. XZ slice (top view, spanwise cut at y=0) ────────────────────────────────
sl_xz = Slice(Input=foam)
sl_xz.SliceType        = "Plane"
sl_xz.SliceType.Origin = [0, 0, 0]
sl_xz.SliceType.Normal = [0, 1, 0]
sl_xz.UpdatePipeline()

v3 = new_view(1400, 800)
wire_show(sl_xz, v3)
v3.CameraParallelProjection = 1
v3.CameraPosition   = [0, -60, 5]
v3.CameraFocalPoint = [0,   0, 5]
v3.CameraViewUp     = [1,   0, 0]  # x right, z up when looking -Y
ResetCamera(v3)
v3.CameraParallelScale *= 1.02
Render(v3)
SaveScreenshot(img_dir + "/mesh_xz_slice.png", v3, ImageResolution=[1400,800])
print("Saved mesh_xz_slice.png")

# ── 4. 3D perspective — boundary surface only ─────────────────────────────────
surf = ExtractSurface(Input=foam)
surf.UpdatePipeline()

v4 = new_view(1400, 900)
wire_show(surf, v4, lw=0.3)
v4.CameraParallelProjection = 0
v4.CameraPosition   = [12, -16, 9]
v4.CameraFocalPoint = [0,   0,  4]
v4.CameraViewUp     = [0,   0,  1]
ResetCamera(v4)
Render(v4)
SaveScreenshot(img_dir + "/mesh_domain_3d.png", v4, ImageResolution=[1400,900])
print("Saved mesh_domain_3d.png")

# ── 5. 3D wing close-up ────────────────────────────────────────────────────────
v5 = new_view(1400, 900)
wire_show(surf, v5, lw=0.5)
v5.CameraParallelProjection = 0
v5.CameraPosition   = [0.4, -1.8, 0.6]
v5.CameraFocalPoint = [0.55, 0.0, 0.35]
v5.CameraViewUp     = [0,    0,   1]
Render(v5)
SaveScreenshot(img_dir + "/mesh_wing_3d.png", v5, ImageResolution=[1400,900])
print("Saved mesh_wing_3d.png")

print("All done.")
