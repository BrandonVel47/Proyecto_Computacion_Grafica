"""01_geometria_base.py
Estación "La Línea Cero": andén, vía, muros, techo y columnas.
Unidades: metros. Eje X = largo de la estación, Y = ancho, Z = altura.
Z=0 es la superficie del andén; el andén da hacia +Y y la vía hacia -Y.
"""
import bpy
import bmesh

# ---------- Parámetros del layout ----------
PLAT_L = 40.0        # largo del andén
PLAT_W = 4.0         # ancho del andén
PLAT_H = 1.1         # altura del andén sobre la vía
TUNNEL_EXT = 20.0    # túnel extra a cada lado (se pierde en la niebla)
CEIL_H = 4.5         # altura del techo medida desde el andén
WALL_T = 0.3         # grosor de muros y techo
TRACK_Y = -1.5       # eje de la vía
GAUGE = 1.5          # separación entre rieles (simplificada)
TRACK_WALL_Y = -5.5  # muro del lado de la vía
COL_SPACING = 8.0    # separación entre columnas
COL_SIZE = 0.5       # lado de la columna

TOTAL_L = PLAT_L + 2 * TUNNEL_EXT
WALL_H = CEIL_H + PLAT_H            # del fondo de la vía al techo
WALL_ZC = (CEIL_H - PLAT_H) / 2     # centro vertical de los muros


def fresh_collection(name):
    """Crea la colección o la vacía si ya existe (el script es repetible)."""
    col = bpy.data.collections.get(name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def box(name, size, center, col):
    """Caja de dimensiones `size` centrada en `center`.
    La escala se aplica a los vértices (no al objeto) para que
    las UV y la densidad de textura sean consistentes después."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = center
    col.objects.link(obj)
    return obj


scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
col = fresh_collection("Estacion_Base")

# ---------- Andén y franja de seguridad ----------
box("Anden", (PLAT_L, PLAT_W, PLAT_H), (0, PLAT_W / 2, -PLAT_H / 2), col)
box("Franja_Seguridad", (PLAT_L, 0.4, 0.02), (0, 0.25, 0.01), col)

# ---------- Fondo de vía (todo el largo, incluye túneles) ----------
bed_w = abs(TRACK_WALL_Y)
box("Fondo_Via", (TOTAL_L, bed_w, 0.3), (0, -bed_w / 2, -PLAT_H - 0.15), col)

# ---------- Rieles y durmientes ----------
for i, side in enumerate((-1, 1)):
    box(f"Riel_{i}", (TOTAL_L, 0.07, 0.15),
        (0, TRACK_Y + side * GAUGE / 2, -PLAT_H + 0.075), col)

sleeper = box("Durmientes", (0.25, 2.2, 0.12),
              (-TOTAL_L / 2 + 0.4, TRACK_Y, -PLAT_H + 0.06), col)
arr = sleeper.modifiers.new("Repetir", 'ARRAY')   # un solo objeto, N copias
arr.use_relative_offset = False
arr.use_constant_offset = True
arr.constant_offset_displace = (0.8, 0, 0)
arr.count = int(TOTAL_L / 0.8) - 1

# ---------- Muros ----------
box("Muro_Fondo", (PLAT_L, WALL_T, WALL_H),
    (0, PLAT_W + WALL_T / 2, WALL_ZC), col)
box("Muro_Via", (TOTAL_L, WALL_T, WALL_H),
    (0, TRACK_WALL_Y - WALL_T / 2, WALL_ZC), col)
for s in (-1, 1):
    # cierre del andén en cada extremo
    box(f"Cierre_Anden_{s}", (WALL_T, PLAT_W, WALL_H),
        (s * (PLAT_L / 2 + WALL_T / 2), PLAT_W / 2, WALL_ZC), col)
    # muro interior del túnel
    box(f"Muro_Tunel_{s}", (TUNNEL_EXT, WALL_T, WALL_H),
        (s * (PLAT_L / 2 + TUNNEL_EXT / 2), -WALL_T / 2, WALL_ZC), col)

# ---------- Techo ----------
box("Techo_Estacion", (PLAT_L, bed_w + PLAT_W, WALL_T),
    (0, (PLAT_W + TRACK_WALL_Y) / 2, CEIL_H + WALL_T / 2), col)
for s in (-1, 1):
    box(f"Techo_Tunel_{s}", (TUNNEL_EXT, bed_w, WALL_T),
        (s * (PLAT_L / 2 + TUNNEL_EXT / 2), -bed_w / 2, CEIL_H + WALL_T / 2), col)

# ---------- Columnas (a 0.5 m del borde del andén) ----------
n_cols = int(PLAT_L / COL_SPACING)
for i in range(n_cols):
    x = -PLAT_L / 2 + COL_SPACING / 2 + i * COL_SPACING
    box(f"Columna_{i}", (COL_SIZE, COL_SIZE, CEIL_H),
        (x, 0.5 + COL_SIZE / 2, CEIL_H / 2), col)

print(f"Estación creada: {len(col.objects)} objetos en 'Estacion_Base'")