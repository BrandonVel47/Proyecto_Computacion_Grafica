"""04_iluminacion.py
Luces fluorescentes (unas fijas, unas parpadeantes y unas apagadas), lámparas del túnel,
luz al fondo del túnel, faros del vagón, niebla volumétrica, mundo oscuro y motor EEVEE.
Requiere 01 y 02 (03 es opcional). Es repetible: reconstruye su colección "Iluminacion".
"""
import sys
import importlib
import math
import random

import bpy

_scripts_dir = bpy.path.abspath("//scripts")
if _scripts_dir not in sys.path:
    sys.path.append(_scripts_dir)
import layout
import lib_bpy
import lib_materiales as lm
for _m in (layout, lib_bpy, lm):
    importlib.reload(_m)
from layout import CEIL_H, WALL_H, WALL_ZC, OUTER, TOTAL_L, X_END, TUNNEL_EXT
from lib_bpy import fresh_collection, box

SEED = 26                  # misma semilla = mismo patrón de parpadeo
FRAMES = 1500              # duración de la animación (24 fps ≈ 62 s)
P_FIJA, P_PARPADEO = 0.40, 0.70   # <0.40 fija, <0.70 parpadea, el resto apagada
E_TUBO = 160.0             # potencia (W) de cada luminaria encendida

if "Estacion_Base" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01_geometria_base.py")
root = bpy.data.collections["Estacion_Base"]
ILU = fresh_collection("Iluminacion", root)
sc = bpy.context.scene
rng = random.Random(SEED)


def add_light(name, kind, energy, color, loc, rot=(0, 0, 0)):
    """Crea una luz y la deja en la colección Iluminacion."""
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    obj = bpy.data.objects.new(name, data)
    obj.location, obj.rotation_euler = loc, rot
    ILU.objects.link(obj)
    return obj


def flicker_pattern(frames):
    """Lista (frame, encendida): luz estable, tartamudeo y apagones breves."""
    t, out = 1, [(1, True)]
    while t < frames:
        t += rng.randint(30, 140)
        for _ in range(rng.randint(2, 6)):
            out.append((t, False)); t += rng.randint(1, 3)
            out.append((t, True)); t += rng.randint(1, 4)
        if rng.random() < 0.3:
            out.append((t, False)); t += rng.randint(8, 36)
            out.append((t, True))
    return out


def keyframe_step(patron, fijar):
    """Inserta llaves 'escalón': mantiene el valor anterior hasta justo antes del cambio."""
    previo = None
    for f, on in patron:
        if previo is not None:
            fijar(previo, f - 1)
        fijar(on, f)
        previo = on


# ---------- Luminarias del andén ----------
mat_on = lm.emision("Luz_Fluorescente_On", (0.85, 1.0, 0.92), 14.0)
mat_off = lm.emision("Luz_Fluorescente_Off", (0.85, 1.0, 0.92), 0.02)
cuenta = {"fija": 0, "parpadea": 0, "apagada": 0}

tubos = sorted((o for o in bpy.data.collections["Luminarias"].objects
                if o.name.startswith("Luminaria_")), key=lambda o: o.name)
for tubo in tubos:
    r = rng.random()
    tubo.data.materials.clear()
    if r >= P_PARPADEO:
        tubo.data.materials.append(mat_off)
        cuenta["apagada"] += 1
        continue
    # spot con sombra dura (radio casi 0): proyecta círculos de luz como en las fotos
    luz = add_light(f"Luz_{tubo.name}", 'SPOT', E_TUBO, (0.82, 1.0, 0.92),
                    (tubo.location.x, tubo.location.y, tubo.location.z - 0.06))
    luz.data.spot_size, luz.data.spot_blend = math.radians(115), 0.7
    luz.data.shadow_soft_size = 0.03
    if r < P_FIJA:
        tubo.data.materials.append(mat_on)
        cuenta["fija"] += 1
        continue
    mat = lm.emision(f"Luz_Parpadeo_{tubo.name}", (0.85, 1.0, 0.92), 14.0)
    tubo.data.materials.append(mat)
    fuerza = mat.node_tree.nodes['Emision'].inputs['Strength']

    def fijar(on, frame, luz=luz, fuerza=fuerza):
        luz.data.energy = E_TUBO if on else 0.0
        luz.data.keyframe_insert('energy', frame=frame)
        fuerza.default_value = 14.0 if on else 0.02
        fuerza.keyframe_insert('default_value', frame=frame)

    keyframe_step(flicker_pattern(FRAMES), fijar)
    cuenta["parpadea"] += 1

# ---------- Lámparas cálidas del túnel ----------
mat_calida = lm.emision("Luz_Calida", (1.0, 0.55, 0.2), 8.0)
for lamp in (o for o in bpy.data.collections["Luminarias"].objects
             if o.name.startswith("Lampara_Tunel")):
    lamp.data.materials.clear()
    lamp.data.materials.append(mat_calida)
    mod = lamp.modifiers["Repetir"]
    sign_y = 1 if lamp.location.y > 0 else -1
    for i in range(mod.count):
        loc = (lamp.location.x + i * mod.constant_offset_displace[0],
               lamp.location.y - sign_y * 0.3, lamp.location.z)
        add_light(f"Luz_{lamp.name}_{i}", 'POINT', 60.0, (1.0, 0.55, 0.2), loc)

# ---------- Luz del fondo del túnel (+X) y faros del vagón ----------
fondo_x = X_END + TUNNEL_EXT - 0.5
fondo = add_light("Luz_Fondo_Tunel", 'AREA', 1500.0, (1.0, 0.97, 0.9),
                  (fondo_x, 0, 1.5), (0, math.radians(90), 0))
fondo.data.shape, fondo.data.size, fondo.data.size_y = 'RECTANGLE', 5.0, 3.5

for s in (1, -1):
    faro = bpy.data.objects.get(f"Faro_1_{s}")
    if faro is not None:
        f = add_light(f"Luz_Faro_{s}", 'SPOT', 600.0, (1.0, 0.9, 0.7),
                      faro.location, (0, math.radians(-90), 0))
        f.data.spot_size, f.data.spot_blend = math.radians(55), 0.5
        f.data.shadow_soft_size = 0.05

# ---------- Niebla volumétrica ----------
fog = box("Niebla", (TOTAL_L - 1.0, 2 * OUTER - 0.4, WALL_H - 0.3), (0, 0, WALL_ZC), ILU)
fog.display_type = 'WIRE'
fog.data.materials.append(lm.niebla("Niebla_Volumen"))

# ---------- Mundo oscuro y render ----------
mundo = bpy.data.worlds.get("Mundo") or bpy.data.worlds.new("Mundo")
mundo.use_nodes = True
fondo_nodo = mundo.node_tree.nodes.get("Background") or mundo.node_tree.nodes.new("ShaderNodeBackground")
fondo_nodo.inputs['Color'].default_value = (0.004, 0.006, 0.01, 1)
fondo_nodo.inputs['Strength'].default_value = 1.0
sc.world = mundo

motores = bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in motores else 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1920, 1080, 24
sc.frame_start, sc.frame_end = 1, FRAMES
if hasattr(sc.eevee, "volumetric_end"):
    sc.eevee.volumetric_end = 120.0

print("Iluminación lista:", cuenta, "| luces:", sum(o.type == 'LIGHT' for o in ILU.objects))
