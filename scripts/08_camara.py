"""08_camara.py
Recorrido guiado: una cámara que sigue una spline (Bezier) mientras un empty, que sigue
otra spline, le marca hacia dónde mirar (restricción Track To). Cada punto de control
tiene su frame: el avance sobre cada curva se anima por longitud de arco, así que cámara
y mirada llegan juntas a cada punto y la velocidad cambia suave entre tramos (pausas
incluidas). La distancia focal cambia y hay marcadores de escena en la línea de tiempo.

Ruta: túnel → andén (pasa el tren) → vagón → nicho y torniquetes → escalera →
pasillo con el extremo tapiado → vestíbulo, taquilla y cortina de salida.
Requiere 01 a 05. Es repetible.
"""
import sys
import importlib

import bpy

_scripts_dir = bpy.path.abspath("//scripts")
if _scripts_dir not in sys.path:
    sys.path.append(_scripts_dir)
import layout
import lib_bpy
importlib.reload(layout)
importlib.reload(lib_bpy)
from layout import FRAMES, Z_PAS, PB_YC
from lib_bpy import fresh_collection

if "Estacion_Base" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01_geometria_base.py")
REC = fresh_collection("Recorrido", bpy.data.collections["Estacion_Base"])
sc = bpy.context.scene
OJO = Z_PAS + 1.6                  # altura de los ojos en el nivel de pasillos (5.2 m)
Y = PB_YC                          # eje del pasillo

# (frame, posición de la cámara, punto al que mira). Metros; ver layout.py.
PUNTOS = [
    # túnel oscuro sobre la vía sur, hacia la luz del fondo
    (1,    (-48.0, -1.9, 0.6),  (-30.0, -1.9, 1.2)),
    (200,  (-38.0, -1.9, 0.6),  (-20.0, -1.6, 1.3)),
    (330,  (-28.0, -1.0, 0.8),  (-12.0, 1.0, 1.4)),
    # sube al andén norte y voltea hacia la vía sur: ahí pasará el tren (05_tren.py)
    (460,  (-17.5, 4.6, 1.6),   (-8.0, -1.4, 1.3)),
    (600,  (-16.8, 5.4, 1.6),   (-7.0, -1.9, 1.4)),
    (660,  (-16.6, 5.6, 1.6),   (-12.0, -1.9, 1.4)),
    (720,  (-16.4, 5.7, 1.6),   (-18.0, -1.9, 1.4)),
    (790,  (-16.2, 5.8, 1.6),   (-25.0, -2.1, 1.2)),
    (860,  (-14.5, 5.8, 1.6),   (-20.0, 1.0, 1.3)),
    # el vagón estacionado
    (960,  (-10.0, 5.9, 1.6),   (-3.0, 2.6, 1.4)),
    (1070, (-2.0, 6.0, 1.6),    (2.0, 2.4, 1.6)),
    (1160, (4.0, 6.2, 1.6),     (14.0, 2.2, 1.1)),
    # nicho de acceso, torniquetes y escalera
    (1250, (9.0, 6.6, 1.6),     (12.0, 10.0, 1.4)),
    (1340, (11.6, 8.4, 1.6),    (12.0, 13.0, 2.0)),
    (1420, (12.0, 9.3, 1.62),   (12.0, 14.5, 3.0)),
    (1480, (12.0, 10.3, 1.75),  (12.0, 15.0, 3.6)),
    (1560, (12.0, 11.8, 2.4),   (12.0, 16.5, 4.4)),
    (1630, (12.0, 13.3, 3.3),   (12.0, 18.0, 5.0)),
    (1680, (12.0, 14.3, 3.4),   (12.0, 19.0, 5.3)),
    (1760, (12.0, 16.3, 4.4),   (12.0, 21.0, 5.3)),
    (1840, (12.0, 18.3, OJO),   (8.0, 22.0, 5.0)),
    # pasillo: mira el extremo tapiado y luego gira hacia la salida
    (1910, (12.1, 19.9, OJO),   (6.5, Y, 4.8)),
    (1970, (12.4, 20.4, OJO),   (9.0, Y + 1.8, 4.9)),
    (2010, (13.2, Y, OJO),      (16.0, Y + 2.2, 5.1)),
    (2050, (14.5, Y, OJO),      (24.0, Y, 5.1)),
    (2190, (25.0, Y, OJO),      (36.0, Y, 5.0)),
    (2290, (33.0, Y, OJO),      (42.0, Y + 1.0, 5.0)),
    # vestíbulo: la taquilla y, al final, la luz que se cuela bajo la cortina
    (2360, (38.5, Y, OJO),      (42.5, Y + 5.6, 5.3)),
    (2420, (40.5, Y - 0.3, OJO), (45.0, Y + 3.0, 5.0)),
    (2470, (42.0, Y - 0.2, 5.05), (48.0, Y, 4.3)),
    (FRAMES, (44.0, Y, 4.9),    (48.3, Y, 3.85)),
]
# (frame, distancia focal en mm): gran angular en el túnel y la escalera, más cerrada al final
LENTES = [(1, 20), (430, 24), (860, 24), (1000, 32), (1250, 28), (1460, 24),
          (1840, 24), (2050, 28), (FRAMES, 35)]
# (frame, nombre) para la línea de tiempo y para el documento
ESCENAS = [(1, "Tunel"), (400, "Anden"), (560, "Tren"), (880, "Vagon"), (1250, "Acceso"),
           (1440, "Escalera"), (1840, "Pasillo"), (2300, "Vestibulo")]


def make_path(name, points):
    """Curva Bezier 3D con manijas automáticas (trayectoria suave por los puntos)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions, cu.use_path, cu.path_duration = '3D', True, FRAMES
    cu.resolution_u = 32
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, cu)
    REC.objects.link(obj)
    return obj


def arc_lengths(obj, n_points):
    """Distancia acumulada sobre la curva hasta cada punto de control."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    vs = [v.co.copy() for v in me.vertices]
    ev.to_mesh_clear()
    acum = [0.0]
    for a, b in zip(vs, vs[1:]):
        acum.append(acum[-1] + (b - a).length)
    res = obj.data.resolution_u                    # muestras por segmento de la Bezier
    return [acum[min(i * res, len(acum) - 1)] for i in range(n_points)], acum[-1]


def animate_path(obj, frames):
    """Anima eval_time para que la curva pase por cada punto en su frame.
    Follow Path recorre la curva por longitud: eval_time / path_duration = fracción."""
    largos, total = arc_lengths(obj, len(frames))
    cu = obj.data
    for f, l in zip(frames, largos):
        cu.eval_time = FRAMES * l / total
        cu.keyframe_insert('eval_time', frame=f)


def follow(obj, path):
    c = obj.constraints.new('FOLLOW_PATH')
    c.target, c.use_curve_follow = path, False


frames = [p[0] for p in PUNTOS]
ruta_cam = make_path("Ruta_Camara", [p[1] for p in PUNTOS])
ruta_mira = make_path("Ruta_Mira", [p[2] for p in PUNTOS])
for ruta in (ruta_cam, ruta_mira):
    animate_path(ruta, frames)

mira = bpy.data.objects.new("Mira_Camara", None)
mira.empty_display_type = 'SPHERE'
REC.objects.link(mira)
follow(mira, ruta_mira)

cam_data = bpy.data.cameras.new("Camara_Recorrido")
cam_data.clip_start, cam_data.clip_end = 0.05, 300
cam = bpy.data.objects.new("Camara_Recorrido", cam_data)
REC.objects.link(cam)
follow(cam, ruta_cam)
track = cam.constraints.new('TRACK_TO')            # la cámara siempre mira al empty
track.target, track.track_axis, track.up_axis = mira, 'TRACK_NEGATIVE_Z', 'UP_Y'

for frame, mm in LENTES:
    cam_data.lens = mm
    cam_data.keyframe_insert('lens', frame=frame)

sc.camera = cam
sc.frame_start, sc.frame_end = 1, FRAMES
sc.timeline_markers.clear()
for frame, nombre in ESCENAS:
    sc.timeline_markers.new(nombre, frame=frame)

# Salida: secuencia de PNG (si el render se interrumpe, se retoma sin repetir frames)
sc.render.filepath = "//renders/frames/frame_"
sc.render.image_settings.file_format = 'PNG'
sc.render.use_overwrite = False
sc.render.use_placeholder = True
sc.frame_set(1)

print("Cámara lista: recorrido de", FRAMES, "frames con", len(PUNTOS), "puntos de control")
