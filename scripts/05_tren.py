"""05_tren.py
Tren de tres vagones que cruza la estación por la vía sur sin detenerse, con faros,
calaveras rojas y luz interior. Se arma copiando la geometría del vagón del script 02
(cada copia con su propia malla) y emparentando todo a un empty, "Tren_Rig", que es lo
único que se anima: posición en X con interpolación lineal (velocidad constante).
Requiere 02. Repetible: reconstruye su colección "Tren".
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
from layout import TRACK_Y, X_END, TUNNEL_EXT, FPS, TREN_F0, TREN_V
from lib_bpy import fresh_collection, box, anchor_location

if "Vagon" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01 y 02 (falta la colección Vagon)")
root = bpy.data.collections["Estacion_Base"]
VAG = bpy.data.collections["Vagon"]
TREN = fresh_collection("Tren", root)

CAR_L, GAP, N_CARS = 15.0, 0.6, 3          # mismo largo que el vagón del script 02
RELLENO = 25.0      # W por vagón de luz de relleno sobre el costado que ve la cámara
                    # (0 = el tren pasa como silueta negra con las ventanas encendidas)
PASO = CAR_L + GAP
LARGO = N_CARS * CAR_L + (N_CARS - 1) * GAP
cx, cy, _ = anchor_location("ANCLA_Vagon")  # centro del vagón original

# El rig va sobre la vía sur. Su origen es el centro del primer vagón; el tren avanza hacia -X.
rig = bpy.data.objects.new("Tren_Rig", None)
rig.empty_display_type, rig.empty_display_size = 'ARROWS', 2.0
TREN.objects.link(rig)


def hijo(obj, local):
    """Emparenta un objeto al rig y lo coloca en coordenadas locales del tren."""
    obj.parent = rig
    obj.location = local
    if obj.name not in TREN.objects:
        TREN.objects.link(obj)
    return obj


# ---------- Vagones: copias de la geometría del vagón estacionado ----------
for k in range(N_CARS):
    for o in VAG.objects:
        partes = o.name.split("_")
        frente = trasero = False
        if partes[0] in ("Parabrisas", "Faro"):      # cabina solo en las puntas del tren
            e = int(partes[1])
            frente, trasero = (k == 0 and e == -1), (k == N_CARS - 1 and e == 1)
            if not (frente or trasero):
                continue
        c = o.copy()
        c.data = o.data.copy()
        if partes[0] == "Faro":
            c.name = f"Tren_Faro{'Del' if frente else 'Tras'}_{partes[2]}"
        else:
            c.name = f"Tren{k}_{o.name}"
        hijo(c, (o.location.x - cx + k * PASO, o.location.y - cy, o.location.z))
# fuelles entre vagones
for k in range(N_CARS - 1):
    f = box(f"Tren_Fuelle_{k}", (GAP + 0.3, 2.0, 2.3), (0, 0, 0), TREN)
    hijo(f, (k * PASO + CAR_L / 2 + GAP / 2, 0, 1.55))


# ---------- Luces del tren (viajan con él) ----------
def luz(nombre, tipo, energia, color, local, rot=(0, 0, 0)):
    data = bpy.data.lights.new(nombre, tipo)
    data.energy, data.color = energia, color
    obj = bpy.data.objects.new(nombre, data)
    obj.rotation_euler = rot
    return hijo(obj, local)


for s in (1, -1):                                   # faros: spots hacia -X
    f = luz(f"Luz_Tren_Faro_{s}", 'SPOT', 900.0, (1.0, 0.92, 0.75),
            (-CAR_L / 2 - 0.15, s * 0.8, 0.8), (0, math.radians(90), 0))
    f.data.spot_size, f.data.spot_blend, f.data.shadow_soft_size = math.radians(50), 0.4, 0.05
for k in range(N_CARS):                             # interior: luz fría que sale por las ventanas
    for dx in (-5.0, 0.0, 5.0):
        i = luz(f"Luz_Tren_Interior_{k}_{dx:+.0f}", 'POINT', 90.0, (0.85, 0.95, 1.0),
                (k * PASO + dx, 0, 1.7))
        i.data.use_shadow = False                   # atraviesa la carrocería: ilumina andén y vía
        i.data.shadow_soft_size = 1.0
        if hasattr(i.data, "use_custom_distance"):  # EEVEE: alcance limitado a 7 m
            i.data.use_custom_distance, i.data.cutoff_distance = True, 7.0
# Relleno: EEVEE no tiene rebote de luz, y las luces del andén casi no alcanzan el centro de
# las vías, así que el costado del tren quedaría negro. Un panel de luz por vagón, entre las
# dos vías y mirando hacia el tren (-Y), deja ver el naranja sin iluminar nada más.
if RELLENO > 0:
    for k in range(N_CARS):
        r = luz(f"Luz_Tren_Relleno_{k}", 'AREA', RELLENO, (1.0, 0.95, 0.9),
                (k * PASO, TRACK_Y, 1.5), (math.radians(-90), 0, 0))
        r.data.shape, r.data.size, r.data.size_y = 'RECTANGLE', CAR_L - 1.0, 2.6
        r.data.use_shadow = False
        if hasattr(r.data, "use_custom_distance"):
            r.data.use_custom_distance, r.data.cutoff_distance = True, 9.0   # cubre el vagón entero
cola = luz("Luz_Tren_Cola", 'POINT', 25.0, (1.0, 0.05, 0.02),
           ((N_CARS - 1) * PASO + CAR_L / 2 + 0.3, 0, 0.8))
cola.data.use_shadow = False

# ---------- Animación: velocidad constante de un extremo del túnel al otro ----------
FIN_TUNEL = X_END + TUNNEL_EXT
x_ini = FIN_TUNEL + 22.0 + CAR_L / 2               # la punta arranca 22 m más allá del túnel
x_fin = -FIN_TUNEL - LARGO - 1.0 + CAR_L / 2       # la cola termina fuera del túnel opuesto
f_fin = round(TREN_F0 + (x_ini - x_fin) / TREN_V * FPS)
rig.location = (x_ini, -TRACK_Y, 0)

prefs = bpy.context.preferences.edit                # interpolación lineal solo para estas llaves
previa = prefs.keyframe_new_interpolation_type
prefs.keyframe_new_interpolation_type = 'LINEAR'
try:
    rig.keyframe_insert('location', index=0, frame=TREN_F0)
    rig.location.x = x_fin
    rig.keyframe_insert('location', index=0, frame=f_fin)
finally:
    prefs.keyframe_new_interpolation_type = previa
bpy.context.scene.frame_set(bpy.context.scene.frame_current)


def frame_punta_en(x):
    """Frame en que la punta del tren pasa por la coordenada x."""
    return round(TREN_F0 + (x_ini - CAR_L / 2 - x) / TREN_V * FPS)


print(f"Tren: {N_CARS} vagones, {len(TREN.objects)} objetos, {TREN_V * 3.6:.0f} km/h,"
      f" frames {TREN_F0}-{f_fin}; entra a la estación en {frame_punta_en(X_END - 0.3)}"
      f" y sale del andén en {frame_punta_en(-X_END + 0.3)}")
