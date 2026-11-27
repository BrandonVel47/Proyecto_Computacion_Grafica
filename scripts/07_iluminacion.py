"""07_iluminacion.py
Luces fluorescentes de estación, escalera, pasillo y vestíbulo (unas fijas, unas que
parpadean y unas apagadas), lámparas del túnel, semáforos, letreros de salida, luz del día
que se cuela bajo la cortina, faros del vagón estacionado, niebla volumétrica, mundo
oscuro y ajustes de EEVEE. Requiere 01 a 05 (06 es opcional). Repetible: reconstruye su
colección "Iluminacion". Las luces del tren en marcha viven en 05_tren.py.
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
from layout import (WALL_H, WALL_ZC, WALL_T, OUTER, ALC_D, TOTAL_L, X_END, TUNNEL_EXT, FPS,
                    FRAMES, Z_PAS, VB_H, PB_X0, PB_YC, PB_Y0, PB_Y1, VB_X1, VB_Y1)
from lib_bpy import fresh_collection, box

SEED = 26                          # cambia la semilla para otro reparto de luces
P_FIJA, P_PARPADEO = 0.40, 0.70    # <0.40 fija, <0.70 parpadea, el resto apagada
# Potencia (W) según la zona: el prefijo del nombre de la luminaria decide
POTENCIA = {"Luminaria_N": 160.0, "Luminaria_S": 160.0, "Luminaria_V": 150.0,
            "Luminaria_P": 110.0, "Luminaria_E": 90.0, "Luminaria_A": 90.0}
# Estados fijados a mano para dirigir la mirada (el resto sale al azar con la semilla)
FORZAR = {
    "Luminaria_A_00": "parpadea",     # nicho: la luz que tartamudea antes de subir
    "Luminaria_E_00": "fija", "Luminaria_E_01": "parpadea",
    "Luminaria_P_02": "fija", "Luminaria_P_06": "parpadea",   # la desprendida
    "Luminaria_V_1_1": "fija",        # frente a la taquilla
    "Luminaria_V_0_2": "apagada", "Luminaria_V_1_2": "apagada",  # junto a la cortina: oscuro
    "Luminaria_N_1_00": "fija", "Luminaria_N_0_01": "fija",   # andén donde se ve pasar el tren
}
RENDER_SAMPLES = 64                # muestras de EEVEE por frame (menos = más rápido)
AMBIENTE = (0.012, 0.015, 0.022)   # luz mínima del mundo: EEVEE no rebota la luz, así que lo
                                   # que ninguna lámpara toca queda negro; esto lo levanta un poco
REFLEJOS = False                   # raytracing de EEVEE: reflejos más fieles en pisos y charcos,
                                   # pero deja puntos blancos (ruido) y alarga el render

if "Estacion_Base" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01_geometria_base.py")
root = bpy.data.collections["Estacion_Base"]
ILU = fresh_collection("Iluminacion", root)
sc = bpy.context.scene


def add_light(name, kind, energy, color, loc, rot=(0, 0, 0), sombra=True, alcance=None):
    """Crea una luz en la colección Iluminacion. `alcance` limita su radio de influencia."""
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    data.use_shadow = sombra
    if alcance and hasattr(data, "use_custom_distance"):
        data.use_custom_distance, data.cutoff_distance = True, alcance
    obj = bpy.data.objects.new(name, data)
    obj.location, obj.rotation_euler = loc, rot
    ILU.objects.link(obj)
    return obj


def flicker_pattern(frames, rng):
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


# ---------- Luminarias (estación, nicho, escalera, pasillo y vestíbulo) ----------
mat_on = lm.emision("Luz_Fluorescente_On", (0.85, 1.0, 0.92), 14.0)
mat_off = lm.emision("Luz_Fluorescente_Off", (0.85, 1.0, 0.92), 0.02)
cuenta = {"fija": 0, "parpadea": 0, "apagada": 0}

tubos = []
for nombre_col in ("Luminarias", "Luminarias_Pasillo"):
    col = bpy.data.collections.get(nombre_col)
    if col:
        tubos += sorted((o for o in col.objects if o.name.startswith("Luminaria_")),
                        key=lambda o: o.name)
for tubo in tubos:
    # cada luminaria tiene su propio generador: agregar o quitar una no altera a las demás
    rng = random.Random(f"{SEED}-{tubo.name}")
    r = rng.random()
    estado = FORZAR.get(tubo.name) or ("fija" if r < P_FIJA else
                                       "parpadea" if r < P_PARPADEO else "apagada")
    cuenta[estado] += 1
    tubo.data.materials.clear()
    if estado == "apagada":
        tubo.data.materials.append(mat_off)
        continue
    energia = next((e for p, e in POTENCIA.items() if tubo.name.startswith(p)), 150.0)
    # spot con sombra dura (radio casi 0): proyecta círculos de luz como en las fotos
    # alcance de 8 m: EEVEE no calcula esta luz (ni reserva sus sombras) fuera de su zona
    luz = add_light(f"Luz_{tubo.name}", 'SPOT', energia, (0.82, 1.0, 0.92),
                    (tubo.location.x, tubo.location.y, tubo.location.z - 0.06), alcance=8.0)
    luz.data.spot_size, luz.data.spot_blend = math.radians(115), 0.7
    luz.data.shadow_soft_size = 0.03
    luz.data.shadow_maximum_resolution = 0.02   # texel más grueso: ahorra memoria de sombras
    if estado == "fija":
        tubo.data.materials.append(mat_on)
        continue
    mat = lm.emision(f"Luz_Parpadeo_{tubo.name}", (0.85, 1.0, 0.92), 14.0)
    tubo.data.materials.append(mat)
    fuerza = mat.node_tree.nodes['Emision'].inputs['Strength']

    def fijar(on, frame, luz=luz, fuerza=fuerza, energia=energia):
        luz.data.energy = energia if on else 0.0
        luz.data.keyframe_insert('energy', frame=frame)
        fuerza.default_value = 14.0 if on else 0.02
        fuerza.keyframe_insert('default_value', frame=frame)

    keyframe_step(flicker_pattern(FRAMES, rng), fijar)

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
        add_light(f"Luz_{lamp.name}_{i}", 'POINT', 60.0, (1.0, 0.55, 0.2), loc, alcance=10.0)

# ---------- Luz del fondo del túnel (+X) y faros del vagón estacionado ----------
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

# ---------- Semáforos y letreros de salida: brillos pequeños sin sombra ----------
for o in bpy.data.objects:
    if o.name.startswith("Semaforo_Rojo"):
        hacia = -1 if o.location.x > 0 else 1          # el semáforo mira a la estación
        add_light(f"Luz_{o.name}", 'POINT', 12.0, (1.0, 0.05, 0.02),
                  (o.location.x + hacia * 0.2, o.location.y, o.location.z), sombra=False, alcance=4.0)
for nombre, (dx, dy) in (("Salida_Caja_Nicho", (0, -0.3)), ("Salida_Caja", (-0.3, 0))):
    o = bpy.data.objects.get(nombre)
    if o:
        add_light(f"Luz_{nombre}", 'POINT', 10.0, (0.1, 1.0, 0.35),
                  (o.location.x + dx, o.location.y + dy, o.location.z), sombra=False, alcance=3.0)

# ---------- Luz del día detrás de la cortina: baja, para que se cuele por la rendija ----------
dia = add_light("Luz_Exterior", 'AREA', 400.0, (0.8, 0.88, 1.0),
                (VB_X1 + WALL_T + 1.8, PB_YC, Z_PAS + 0.3), (0, math.radians(90), 0))
dia.data.shape, dia.data.size, dia.data.size_y = 'RECTANGLE', 0.6, PB_Y1 - PB_Y0 - 0.2

# ---------- Niebla volumétrica (estación y nivel de pasillos) ----------
mat_niebla = lm.niebla("Niebla_Volumen")
fog = box("Niebla", (TOTAL_L - 1.0, 2 * OUTER - 0.4, WALL_H - 0.3), (0, 0, WALL_ZC), ILU)
y0p = OUTER + ALC_D + WALL_T
z1p = Z_PAS + VB_H
fog2 = box("Niebla_Pasillos", (VB_X1 - PB_X0, VB_Y1 - y0p, z1p),
           ((PB_X0 + VB_X1) / 2, (y0p + VB_Y1) / 2, z1p / 2), ILU)
for f in (fog, fog2):
    f.display_type = 'WIRE'
    f.data.materials.append(mat_niebla)

# ---------- Mundo oscuro y render ----------
mundo = bpy.data.worlds.get("Mundo") or bpy.data.worlds.new("Mundo")
mundo.use_nodes = True
fondo_nodo = mundo.node_tree.nodes.get("Background") or mundo.node_tree.nodes.new("ShaderNodeBackground")
fondo_nodo.inputs['Color'].default_value = (*AMBIENTE, 1)
fondo_nodo.inputs['Strength'].default_value = 1.0
sc.world = mundo

motores = bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in motores else 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1920, 1080, FPS
sc.frame_start, sc.frame_end = 1, FRAMES
ee = sc.eevee
if hasattr(ee, "taa_render_samples"):
    ee.taa_render_samples = RENDER_SAMPLES
if hasattr(ee, "volumetric_end"):
    ee.volumetric_end = 120.0
if hasattr(ee, "use_volumetric_shadows"):        # la niebla respeta las sombras (haces de luz)
    ee.use_volumetric_shadows = True
if hasattr(ee, "use_raytracing"):                 # ver REFLEJOS arriba
    ee.use_raytracing = REFLEJOS
    if REFLEJOS:
        try:                                      # resolución completa y sin destellos
            ee.ray_tracing_method = 'SCREEN'
            ee.ray_tracing_options.resolution_scale = '1'
            ee.ray_tracing_options.use_denoise = True
            ee.clamp_surface_indirect = 3.0
        except (AttributeError, TypeError):
            pass
if hasattr(sc.render, "use_motion_blur"):         # desenfoque de movimiento (tren y cámara)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
if hasattr(ee, "shadow_pool_size"):               # evita "Shadow buffer full" con muchas luces
    # el tamaño máximo del pool cambia entre versiones de Blender: se toma el mayor disponible
    opciones = list(ee.bl_rna.properties['shadow_pool_size'].enum_items.keys())
    ee.shadow_pool_size = opciones[-1]
    ee.shadow_resolution_scale = 0.5

print("Iluminación lista:", cuenta, "| luces:", sum(o.type == 'LIGHT' for o in ILU.objects))
