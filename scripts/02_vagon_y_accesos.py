"""02_vagon_y_accesos.py
Vagón naranja (estilo de las fotos de referencia), torniquetes y escalera de acceso.
Requiere haber ejecutado antes 01_geometria_base.py: las posiciones salen de los
empties ANCLA_* de la escena. Metros; ver layout.py para el sistema de coordenadas.
"""
import sys
import importlib
import math

import bpy

_scripts_dir = bpy.path.abspath("//scripts")
if _scripts_dir not in sys.path:
    sys.path.append(_scripts_dir)
import layout
import lib_bpy
importlib.reload(layout)
importlib.reload(lib_bpy)
from layout import WALL_T, SIDES, STAIR_W, PLAT_H, GAUGE
from lib_bpy import fresh_collection, box, pipe, repeat, anchor_location

if "Estacion_Base" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01_geometria_base.py")
root = bpy.data.collections["Estacion_Base"]
VAG = fresh_collection("Vagon", root)
ACC = fresh_collection("Accesos", root)

# =====================================================================
# VAGÓN (sobre la vía del andén Y+, centrado en ANCLA_Vagon)
# =====================================================================
CAR_L, CAR_W = 15.0, 2.6
DOOR_STEP = CAR_L / 4                 # 4 puertas por lado, separadas 3.75 m
cx, cy, _ = anchor_location("ANCLA_Vagon")


def car_box(name, size, local):
    """Caja en coordenadas locales del vagón (x largo, y lateral, z altura)."""
    return box(name, size, (cx + local[0], cy + local[1], local[2]), VAG)


# Capas del cuerpo: faldón oscuro, carrocería naranja y techo (un objeto por material)
car_box("Vagon_Faldon", (CAR_L - 0.4, CAR_W - 0.2, 0.8), (0, 0, -0.05))
car_box("Vagon_Carroceria", (CAR_L, CAR_W, 2.55), (0, 0, 1.625))
car_box("Vagon_Techo", (CAR_L - 0.4, CAR_W - 0.6, 0.1), (0, 0, 2.95))

# Ruedas: 2 bogies con 4 ruedas apoyadas sobre los rieles. El faldón las tapa en parte,
# pero asoman por debajo y el vagón deja de verse flotando.
RIEL_TOP = -PLAT_H + 0.27                # altura de la cara superior del riel
RADIO_RUEDA = 0.42
for b in SIDES:                          # bogie delantero y trasero
    for a in (-0.9, 0.9):                # dos ejes por bogie
        for s in SIDES:                  # una rueda sobre cada riel
            rueda = pipe(f"Vagon_Rueda_{b}_{a:+.1f}_{s}", RADIO_RUEDA, 0.25,
                         (cx + b * 5.0 + a, cy + s * GAUGE / 2, RIEL_TOP + RADIO_RUEDA),
                         VAG, segments=16)
            rueda.rotation_euler = (0, 0, math.pi / 2)   # eje de la rueda a lo largo de Y

for s in SIDES:
    face = s * CAR_W / 2              # plano lateral del vagón
    # puertas: marco + dos cristales angostos (se repiten con Array)
    marco = car_box(f"Puerta_Marco_{s}", (1.5, 0.06, 2.2), (-1.5 * DOOR_STEP, face + s * 0.03, 1.45))
    repeat(marco, 4, DOOR_STEP)
    for j in (-1, 1):
        cristal = car_box(f"Puerta_Cristal_{s}_{j}", (0.45, 0.08, 1.3),
                          (-1.5 * DOOR_STEP + j * 0.38, face + s * 0.05, 1.75))
        repeat(cristal, 4, DOOR_STEP)
    # ventanas entre puertas: marco, cristal y rejillas de ventilación arriba
    ventana = car_box(f"Ventana_Marco_{s}", (1.2, 0.05, 1.0), (-DOOR_STEP, face + s * 0.025, 1.9))
    repeat(ventana, 3, DOOR_STEP)
    vidrio = car_box(f"Ventana_Cristal_{s}", (1.05, 0.07, 0.85), (-DOOR_STEP, face + s * 0.035, 1.9))
    repeat(vidrio, 3, DOOR_STEP)
    rejilla = car_box(f"Ventila_{s}", (0.9, 0.06, 0.22), (-DOOR_STEP, face + s * 0.03, 2.7))
    repeat(rejilla, 3, DOOR_STEP)

# frentes: parabrisas y faros
for e in SIDES:
    car_box(f"Parabrisas_{e}", (0.08, 1.8, 0.9), (e * (CAR_L / 2 + 0.02), 0, 1.9))
    for s in SIDES:
        car_box(f"Faro_{e}_{s}", (0.08, 0.25, 0.15), (e * (CAR_L / 2 + 0.02), s * 0.8, 0.8))

# =====================================================================
# TORNIQUETES (4 en el nicho de acceso, de tres brazos)
# =====================================================================
tx, ty, _ = anchor_location("ANCLA_Torniquetes")
PITCH, ARM_LEN = 0.9, 0.5
for i in range(4):
    x = tx + (i - 1.5) * PITCH
    box(f"Torniquete_Cuerpo_{i}", (0.25, 0.9, 1.05), (x, ty, 0.525), ACC)
    box(f"Torniquete_Lector_{i}", (0.2, 0.25, 0.1), (x, ty - 0.2, 1.1), ACC)
    hub = (x, ty + 0.1, 0.9)
    for a in (0, 120, 240):           # tres brazos a 120° alrededor del eje Y
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        arm = pipe(f"Torniquete_Brazo_{i}_{a}", 0.02, ARM_LEN,
                   (hub[0] + d[0] * ARM_LEN / 2, hub[1], hub[2] + d[1] * ARM_LEN / 2), ACC)
        arm.rotation_euler = (0, -math.radians(a), 0)

# =====================================================================
# ESCALERA (sube por la boca del fondo del nicho y se pierde en la oscuridad)
# =====================================================================
sx, sy, _ = anchor_location("ANCLA_Escalera")   # cara interior del muro del fondo
RUN, RISE, STEPS = 0.3, 0.18, 10
y0 = ty + PITCH                                 # empieza justo después de los torniquetes
for k in range(STEPS):
    box(f"Escalon_{k}", (STAIR_W, RUN, (k + 1) * RISE),
        (sx, y0 + RUN * (k + 0.5), (k + 1) * RISE / 2), ACC)

# caja de la escalera detrás del muro: paredes, techo y fondo
y_in, y_end = sy + WALL_T, y0 + STEPS * RUN + 0.2
depth = y_end - y_in
for k in SIDES:
    box(f"Escalera_Pared_{k}", (0.2, depth, 3.2), (sx + k * (STAIR_W / 2 + 0.1), y_in + depth / 2, 1.6), ACC)
box("Escalera_Techo", (STAIR_W + 0.4, depth, 0.2), (sx, y_in + depth / 2, 3.1), ACC)
box("Escalera_Fondo", (STAIR_W + 0.4, 0.2, 3.2), (sx, y_end + 0.1, 1.6), ACC)

print("Vagón, torniquetes y escalera creados:",
      len(VAG.objects), "+", len(ACC.objects), "objetos")
