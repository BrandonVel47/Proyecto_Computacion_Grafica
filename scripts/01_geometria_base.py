"""01_geometria_base.py (v2)
Estación "La Línea Cero" basada en fotos de estaciones del Metro CDMX.
Metros. X = largo, Y = ancho (0 = eje entre las dos vías), Z = altura.
Z=0 es el piso del andén. Andenes laterales (Y+ y Y-), 2 vías al centro.
"""
import sys
import importlib

import bpy

# Los módulos compartidos viven junto a este script (carpeta scripts/ del repo).
_scripts_dir = bpy.path.abspath("//scripts")
if _scripts_dir not in sys.path:
    sys.path.append(_scripts_dir)
import layout
import lib_bpy
importlib.reload(layout)       # recarga por si se editaron entre ejecuciones
importlib.reload(lib_bpy)
from layout import (PLAT_L, PLAT_W, PLAT_H, PIT_HALF, OUTER, CEIL_H, WALL_T,
                    TUNNEL_EXT, TRACK_Y, GAUGE, BEAM_STEP, ALC_X, ALC_W, ALC_D, ALC_CEIL,
                    STAIR_W, STAIR_OPEN_H, WALL_H, WALL_ZC, X_END, TOTAL_L, SIDES, TORN_DY)
from lib_bpy import fresh_collection, box, pipe, repeat, anchor


# ---------- Colecciones ----------
root = fresh_collection("Estacion_Base", bpy.context.scene.collection)
EST, VIA, DET, LUZ, ANC = (fresh_collection(n, root) for n in
                           ("Estructura", "Via", "Detalles", "Luminarias", "Anclas"))
bpy.context.scene.unit_settings.system = 'METRIC'


def wall_layers(s, x0, x1, tag):
    """Muro de fondo en capas: muro, zócalo, travertino y banda de color."""
    xc, ln = (x0 + x1) / 2, x1 - x0
    box(f"Muro_{tag}", (ln, WALL_T, WALL_H), (xc, s * (OUTER + WALL_T / 2), WALL_ZC), EST)
    box(f"Zoclo_{tag}", (ln, 0.06, 0.2), (xc, s * (OUTER - 0.03), 0.1), DET)
    box(f"Travertino_{tag}", (ln, 0.05, 2.3), (xc, s * (OUTER - 0.025), 1.35), DET)
    box(f"Banda_Linea_{tag}", (ln, 0.05, 0.45), (xc, s * (OUTER - 0.025), 2.725), DET)


# ---------- Andenes, borde de seguridad y piso ----------
for s in SIDES:
    n = "N" if s > 0 else "S"
    box(f"Anden_{n}", (PLAT_L, PLAT_W, PLAT_H),
        (0, s * (PIT_HALF + PLAT_W / 2), -PLAT_H / 2), EST)
    box(f"Borde_Gris_{n}", (PLAT_L, 0.55, 0.02), (0, s * (PIT_HALF + 0.275), 0.01), DET)
    box(f"Franja_Amarilla_{n}", (PLAT_L, 0.3, 0.02), (0, s * (PIT_HALF + 0.7), 0.01), DET)
    fw = PLAT_W - 0.85
    box(f"Piso_Marmol_{n}", (PLAT_L, fw, 0.02), (0, s * (PIT_HALF + 0.85 + fw / 2), 0.01), DET)
    # rejillas oscuras en la cara del andén (hacia la vía)
    g = box(f"Rejillas_Foso_{n}", (0.9, 0.04, 0.22),
            (-PLAT_L / 2 + 0.8, s * (PIT_HALF - 0.02), -0.55), DET)
    repeat(g, int(PLAT_L / 1.6), 1.6)

# ---------- Foso de vías (concreto en estación, balasto en túnel) ----------
box("Foso_Concreto", (PLAT_L, 2 * PIT_HALF, 0.3), (0, 0, -PLAT_H - 0.15), VIA)
for sx in SIDES:
    box(f"Balasto_{sx}", (TUNNEL_EXT, 2 * PIT_HALF, 0.5),
        (sx * (X_END + TUNNEL_EXT / 2), 0, -PLAT_H - 0.15), VIA)

for i, ty in enumerate((TRACK_Y, -TRACK_Y)):
    for j, side in enumerate((-1, 1)):
        box(f"Riel_{i}_{j}", (TOTAL_L, 0.07, 0.15),
            (0, ty + side * GAUGE / 2, -PLAT_H + 0.195), VIA)
    d = box(f"Durmientes_{i}", (0.25, 2.2, 0.12),
            (-TOTAL_L / 2 + 0.4, ty, -PLAT_H + 0.06), VIA)
    repeat(d, int(TOTAL_L / 0.8) - 1, 0.8)

# ---------- Muros de fondo (con nicho de acceso en el andén N) ----------
wall_layers(-1, -PLAT_L / 2, PLAT_L / 2, "S")
wall_layers(1, -PLAT_L / 2, ALC_X - ALC_W / 2, "N1")
wall_layers(1, ALC_X + ALC_W / 2, PLAT_L / 2, "N2")

# cierres de andén en los extremos + nichos naranjas (fotos 1 y 6)
for sx in SIDES:
    for s in SIDES:
        yc = s * (PIT_HALF + PLAT_W / 2)
        box(f"Cierre_{sx}_{s}", (WALL_T, PLAT_W, WALL_H),
            (sx * (PLAT_L / 2 + WALL_T / 2), yc, WALL_ZC), EST)
        box(f"Nicho_Fondo_{sx}_{s}", (0.15, 2.0, 2.6),
            (sx * (PLAT_L / 2 - 0.075), yc, 1.3), DET)

# nicho de acceso: torniquetes (script 02) y escalera hacia los pasillos (script 03)
oy = OUTER + ALC_D / 2
box("Acceso_Piso", (ALC_W, ALC_D, PLAT_H), (ALC_X, oy, -PLAT_H / 2), EST)
for k in SIDES:
    box(f"Acceso_Muro_{k}", (WALL_T, ALC_D + WALL_T, WALL_H),
        (ALC_X + k * (ALC_W / 2 + WALL_T / 2), OUTER + (ALC_D + WALL_T) / 2, WALL_ZC), EST)
# fondo del nicho con boca de escalera al centro (la escalera se modela en el script 03)
yb = OUTER + ALC_D + WALL_T / 2
side_w = (ALC_W + 2 * WALL_T - STAIR_W) / 2
for k in SIDES:
    box(f"Acceso_Fondo_{k}", (side_w, WALL_T, WALL_H),
        (ALC_X + k * (STAIR_W / 2 + side_w / 2), yb, WALL_ZC), EST)
box("Acceso_Fondo_Bajo", (STAIR_W, WALL_T, PLAT_H), (ALC_X, yb, -PLAT_H / 2), EST)
box("Acceso_Fondo_Dintel", (STAIR_W, WALL_T, CEIL_H - STAIR_OPEN_H),
    (ALC_X, yb, (CEIL_H + STAIR_OPEN_H) / 2), EST)
box("Acceso_Techo", (ALC_W, ALC_D, 0.2), (ALC_X, oy, ALC_CEIL + 0.1), EST)
box("Acceso_Dintel", (ALC_W, WALL_T, CEIL_H - 2.9),
    (ALC_X, OUTER + WALL_T / 2, (CEIL_H + 2.9) / 2), EST)

# ---------- Techo, vigas y pilastras ----------
box("Techo_Estacion", (PLAT_L, 2 * OUTER, WALL_T), (0, 0, CEIL_H + WALL_T / 2), EST)
v = box("Viga", (0.5, 2 * OUTER, 0.4), (-2 * BEAM_STEP, 0, CEIL_H - 0.2), EST)
repeat(v, 5, BEAM_STEP)
for s in SIDES:
    p = box(f"Pilastra_{s}", (0.6, 0.25, CEIL_H),
            (-2 * BEAM_STEP, s * (OUTER - 0.125), CEIL_H / 2), EST)
    repeat(p, 5, BEAM_STEP)

# ---------- Túneles (caja con charolas de cables y lámparas) ----------
for sx in SIDES:
    xc = sx * (X_END + TUNNEL_EXT / 2)
    box(f"Techo_Tunel_{sx}", (TUNNEL_EXT, 2 * PIT_HALF, WALL_T),
        (xc, 0, CEIL_H + WALL_T / 2), EST)
    for s in SIDES:
        box(f"Muro_Tunel_{sx}_{s}", (TUNNEL_EXT, WALL_T, WALL_H),
            (xc, s * (PIT_HALF + WALL_T / 2), WALL_ZC), EST)
    for i in range(4):  # charola de cables en el muro Y+ (foto 2)
        pipe(f"Cable_{sx}_{i}", 0.05, TUNNEL_EXT,
             (xc, PIT_HALF - 0.12, 1.7 + 0.22 * i), DET)
    lamp = box(f"Lampara_Tunel_{sx}", (0.5, 0.12, 0.16),
               (sx * (X_END + 5), -(PIT_HALF - 0.06), 1.8), LUZ)
    repeat(lamp, int(TUNNEL_EXT / 10), sx * 10.0)

# ---------- Detalles del andén ----------
for s in SIDES:
    n = "N" if s > 0 else "S"
    for i in range(3):  # tuberías bajo el techo, junto al muro
        pipe(f"Tuberia_{n}_{i}", 0.05, PLAT_L,
             (0, s * (OUTER - 0.35 - 0.14 * i), CEIL_H - 0.55), DET)
    box(f"Rotulo_Estacion_{n}", (3.2, 0.03, 0.32), (-4, s * (OUTER - 0.065), 2.725), DET)
    for k, yoff in enumerate((1.3, 3.3)):  # 2 hileras de 10 luminarias por andén
        for i in range(10):                # una por una: cada tubo tendrá su propio estado
            box(f"Luminaria_{n}_{k}_{i:02d}", (2.4, 0.25, 0.08),
                (-18 + 4.0 * i, s * (PIT_HALF + yoff), CEIL_H - 0.04), LUZ)

# letreros colgantes "Dirección ..." (foto 1)
for s, x in ((1, -10.0), (-1, 6.0)):
    yc = s * (PIT_HALF + PLAT_W / 2)
    box(f"Letrero_Colgante_{s}", (0.25, 3.0, 0.55), (x, yc, CEIL_H - 0.675), DET)
    for r in SIDES:
        box(f"Varilla_{s}_{r}", (0.03, 0.03, 0.4), (x, yc + r * 1.2, CEIL_H - 0.2), DET)

# ---------- Anclas para los scripts siguientes ----------
anchor("ANCLA_Vagon", (0, TRACK_Y, -PLAT_H), ANC)
anchor("ANCLA_Torniquetes", (ALC_X, OUTER + TORN_DY, 0), ANC)
anchor("ANCLA_Escalera", (ALC_X, OUTER + ALC_D, 0), ANC)

print("Estación v2 creada:", sum(len(c.objects) for c in root.children_recursive), "objetos")