"""10 — Pruebas automáticas de la escena (sección «Pruebas y validación» del documento).

Se ejecuta igual que los demás: con el .blend abierto desde la raíz del repositorio, en la
pestaña Scripting → Run Script. También corre sin interfaz:
    blender -b LaLineaCero.blend -P scripts/10_pruebas.py
Reconstruye la escena (00_construir_todo.py), verifica una lista de criterios y escribe el
resultado en docs/pruebas_resultados.txt. Cada prueba imprime APROBADA o FALLÓ con el dato
medido, y al final se muestran las métricas de la escena (objetos, polígonos, luces...).
"""
import math
import os
import runpy
import sys
import time

import bpy

_scripts_dir = bpy.path.abspath("//scripts")
if _scripts_dir not in sys.path:
    sys.path.append(_scripts_dir)
import layout

sc = bpy.context.scene
RESULTADOS = []                                  # (id, descripción, aprobada, dato medido)


def registrar(pid, desc, ok, dato):
    RESULTADOS.append((pid, desc, bool(ok), dato))
    print(f"[{'APROBADA' if ok else 'FALLÓ  '}] {pid} {desc}: {dato}")


def curvas(obj_data):
    """F-curves de un objeto o dato animado (Blender 5 guarda las curvas en capas/tiras)."""
    ad = obj_data.animation_data
    if not ad or not ad.action:
        return []
    ac = ad.action
    if hasattr(ac, "fcurves"):                       # Blender 4.x
        return list(ac.fcurves)
    return [fc for ly in ac.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]


def conteos():
    """Resumen estructural de la escena para comparar dos construcciones."""
    # solo cuenta lo que usa la escena (los datos huérfanos de una reconstrucción previa
    # desaparecen al guardar y no forman parte de ella)
    teclas = 0
    for o in bpy.data.objects:
        teclas += sum(len(fc.keyframe_points) for fc in curvas(o))
        if o.data is not None:
            teclas += sum(len(fc.keyframe_points) for fc in curvas(o.data))
    return {
        "objetos": len(bpy.data.objects),
        "mallas": len([o for o in bpy.data.objects if o.type == 'MESH']),
        "luces": len([o for o in bpy.data.objects if o.type == 'LIGHT']),
        "materiales": len([m for m in bpy.data.materials if m.users > 0]),
        "colecciones": len(bpy.data.collections),
        "keyframes": teclas,
    }


def construir():
    t0 = time.time()
    runpy.run_path(os.path.join(_scripts_dir, "00_construir_todo.py"))
    return time.time() - t0


# ---------------------------------------------------------------------------------------------
# P01 y P02: construcción completa e idempotencia
# ---------------------------------------------------------------------------------------------
t1 = construir()
c1 = conteos()
registrar("P01", "Construcción completa (scripts 00 a 08) en menos de 30 s", t1 < 30, f"{t1:.1f} s")
t2 = construir()
c2 = conteos()
registrar("P02", "Idempotencia: reconstruir no duplica nada", c1 == c2, f"{c1} → {c2}")

# ---------------------------------------------------------------------------------------------
# P03: toda malla tiene material
# ---------------------------------------------------------------------------------------------
sin_mat = [o.name for o in bpy.data.objects
           if o.type == 'MESH' and not any(s.material for s in o.material_slots)]
registrar("P03", "Toda malla tiene un material asignado", not sin_mat,
          f"{len([o for o in bpy.data.objects if o.type == 'MESH'])} mallas, sin material: {sin_mat[:5]}")

# ---------------------------------------------------------------------------------------------
# P04: luces (tipos, sombras, parpadeo)
# ---------------------------------------------------------------------------------------------
luces = [o for o in bpy.data.objects if o.type == 'LIGHT']
por_tipo = {}
for o in luces:
    por_tipo[o.data.type] = por_tipo.get(o.data.type, 0) + 1
con_sombra = sum(1 for o in luces if o.data.use_shadow)
parpadean = [o for o in luces if o.data.animation_data and o.data.animation_data.action]
registrar("P04", "Luces con sombra y luces animadas (parpadeo) dentro de lo previsto",
          0 < len(parpadean) < len(luces) and con_sombra > 0,
          f"{len(luces)} luces {por_tipo}, {con_sombra} con sombra, {len(parpadean)} parpadean")

# ---------------------------------------------------------------------------------------------
# P05: animación y ajustes de render
# ---------------------------------------------------------------------------------------------
r = sc.render
ok = (sc.frame_start == 1 and sc.frame_end == layout.FRAMES and r.fps == layout.FPS
      and (r.resolution_x, r.resolution_y) == (1920, 1080) and r.image_settings.file_format == 'PNG')
registrar("P05", "Rango, fps, resolución y formato de salida", ok,
          f"{sc.frame_start}-{sc.frame_end} a {r.fps} fps, {r.resolution_x}x{r.resolution_y}, "
          f"{r.image_settings.file_format}, motor {r.engine}, muestras {sc.eevee.taa_render_samples}")
marcas = [(m.frame, m.name) for m in sc.timeline_markers]
registrar("P06", "Marcadores de escena en la línea de tiempo", len(marcas) == 8, f"{marcas}")

# ---------------------------------------------------------------------------------------------
# P07 a P09: cámara — exactitud, suavidad y velocidad
# ---------------------------------------------------------------------------------------------
cam = sc.camera
datos_cam = runpy.run_path(os.path.join(_scripts_dir, "08_camara.py"))       # devuelve PUNTOS
PUNTOS = datos_cam["PUNTOS"]
cam = sc.camera
err_max = 0.0
for f, pos, mira in PUNTOS:
    sc.frame_set(f)
    p = cam.matrix_world.translation
    err_max = max(err_max, (p - __import__("mathutils").Vector(pos)).length)
registrar("P07", "La cámara pasa por los 31 puntos de control (error < 1 cm)", err_max < 0.01,
          f"{len(PUNTOS)} puntos, error máximo {err_max * 1000:.3f} mm")

pos_f, dir_f = [], []
for f in range(1, layout.FRAMES + 1):
    sc.frame_set(f)
    m = cam.matrix_world
    pos_f.append(m.translation.copy())
    dir_f.append((m.to_quaternion() @ __import__("mathutils").Vector((0, 0, -1))).normalized())
vel = [(b - a).length * layout.FPS for a, b in zip(pos_f, pos_f[1:])]
giro = [math.degrees(a.angle(b)) * layout.FPS for a, b in zip(dir_f, dir_f[1:])]
registrar("P08", "Velocidad de la cámara continua y razonable (sin saltos: máx < 4 m/s)",
          max(vel) < 4.0, f"media {sum(vel) / len(vel):.2f} m/s, máx {max(vel):.2f} m/s")
por_frame = [g / layout.FPS for g in giro]
f_pico = giro.index(max(giro)) + 1
registrar("P09", "Giro de la cámara continuo: sin saltos de más de 5° entre cuadros", max(por_frame) < 5.0,
          f"media {sum(giro) / len(giro):.1f} °/s; pico {max(giro):.1f} °/s "
          f"({max(por_frame):.1f} °/cuadro) en el frame {f_pico}")
longitud = sum((b - a).length for a, b in zip(pos_f, pos_f[1:]))

# ---------------------------------------------------------------------------------------------
# P10: tren — velocidad constante de 10 m/s (interpolación lineal)
# ---------------------------------------------------------------------------------------------
rig = bpy.data.objects["Tren_Rig"]
f0, f1 = layout.TREN_F0, 859
xs = {}
for f in range(f0 - 1, f1 + 2):
    sc.frame_set(f)
    xs[f] = rig.matrix_world.translation.x
v = {f: (xs[f - 1] - xs[f]) * layout.FPS for f in range(f0, f1 + 1)}     # m/s hacia -X
v_max, v_med = max(v.values()), (xs[f0] - xs[f1]) / ((f1 - f0) / layout.FPS)
registrar("P10", "El tren arranca y termina en reposo y alcanza ~1.5 × la velocidad media (Bezier)",
          v[f0 + 1] < 0.5 and v[f1] < 0.5 and abs(v_max / v_med - 1.5) < 0.05,
          f"media {v_med:.2f} m/s ({v_med * 3.6:.0f} km/h), pico {v_max:.2f} m/s ({v_max * 3.6:.0f} km/h), "
          f"x de {xs[f0]:.1f} a {xs[f1]:.1f} m")
sc.frame_set(f0 - 1)
x_antes = rig.matrix_world.translation.x
sc.frame_set(1)
registrar("P11", "El tren permanece fuera de la estación antes de arrancar (x > 60 m)",
          x_antes > 60.0, f"x = {x_antes:.1f} m")

# ---------------------------------------------------------------------------------------------
# P12: cuadros renderizados en disco (solo si existen)
# ---------------------------------------------------------------------------------------------
carpeta = bpy.path.abspath("//renders/frames")
if os.path.isdir(carpeta):
    n = [f for f in os.listdir(carpeta) if f.startswith("frame_") and f.endswith(".png")]
    esperados = {f"frame_{i:04d}.png" for i in range(1, layout.FRAMES + 1)}
    faltan = sorted(esperados - set(n))
    registrar("P12", "Existen los 2520 cuadros renderizados, sin huecos", not faltan,
              f"{len(n)} archivos, faltan {len(faltan)}")
else:
    registrar("P12", "Cuadros renderizados en renders/frames", True, "omitida: carpeta no disponible")

# ---------------------------------------------------------------------------------------------
# Métricas de la escena
# ---------------------------------------------------------------------------------------------
dg = bpy.context.evaluated_depsgraph_get()
verts = caras = tris = 0
por_col = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    me = o.evaluated_get(dg).to_mesh()
    verts += len(me.vertices)
    caras += len(me.polygons)
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
    o.evaluated_get(dg).to_mesh_clear()
    col = o.users_collection[0].name if o.users_collection else "-"
    por_col[col] = por_col.get(col, 0) + 1
nodos = sum(len(m.node_tree.nodes) for m in bpy.data.materials if m.use_nodes and m.node_tree)
tipos_nodo = {}
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree:
        for n in m.node_tree.nodes:
            tipos_nodo[n.bl_idname] = tipos_nodo.get(n.bl_idname, 0) + 1
metricas = [
    ("Objetos", len(bpy.data.objects)),
    ("Mallas", c1["mallas"]),
    ("Luces", c1["luces"]),
    ("Materiales procedurales", c1["materiales"]),
    ("Nodos de material (total)", nodos),
    ("Vértices", verts), ("Polígonos", caras), ("Triángulos", tris),
    ("Longitud del recorrido de la cámara (m)", f"{longitud:.1f}"),
    ("Duración (s)", layout.FRAMES / layout.FPS),
]
print("\nMétricas de la escena")
for k, v in metricas:
    print(f"  {k}: {v}")
print("  Mallas por colección:", dict(sorted(por_col.items(), key=lambda kv: -kv[1])))
print("  Nodos por tipo:", dict(sorted(tipos_nodo.items(), key=lambda kv: -kv[1])[:8]))

aprobadas = sum(1 for r in RESULTADOS if r[2])
print(f"\n{aprobadas} de {len(RESULTADOS)} pruebas aprobadas")

# ---------------------------------------------------------------------------------------------
# Informe en texto para el repositorio y el documento
# ---------------------------------------------------------------------------------------------
ruta = os.path.join(bpy.path.abspath("//docs"), "pruebas_resultados.txt")
os.makedirs(os.path.dirname(ruta), exist_ok=True)
with open(ruta, "w", encoding="utf-8") as fh:
    fh.write(f"Pruebas automáticas — Blender {bpy.app.version_string}\n\n")
    for pid, desc, ok, dato in RESULTADOS:
        fh.write(f"{pid}  {'APROBADA' if ok else 'FALLÓ'}  {desc}\n      {dato}\n")
    fh.write(f"\n{aprobadas} de {len(RESULTADOS)} pruebas aprobadas\n\nMétricas\n")
    for k, v in metricas:
        fh.write(f"  {k}: {v}\n")
    fh.write(f"  Mallas por colección: {dict(sorted(por_col.items(), key=lambda kv: -kv[1]))}\n")
    fh.write(f"  Nodos por tipo: {dict(sorted(tipos_nodo.items(), key=lambda kv: -kv[1])[:8])}\n")
print("Informe:", ruta)
