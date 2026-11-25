"""05_camara.py
Recorrido guiado: una cámara que sigue una spline (Bezier) mientras un empty, que
sigue otra spline, le marca hacia dónde mirar. La distancia focal cambia a lo largo
del recorrido y se agregan marcadores de escena en la línea de tiempo.

Ruta: túnel oscuro → sube al andén → recorre el vagón → entra al nicho → escalera.
Requiere los scripts 01 y 02. Es repetible.
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
from layout import FRAMES
from lib_bpy import fresh_collection

if "Estacion_Base" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01_geometria_base.py")
REC = fresh_collection("Recorrido", bpy.data.collections["Estacion_Base"])
sc = bpy.context.scene

# Puntos de control (x, y, z) en metros. Cada punto de la cámara tiene su punto de mira
# en la misma posición de la lista, para que ambas curvas avancen sincronizadas.
POS_CAMARA = [
    (-48, -1.9, 0.6),   # dentro del túnel, sobre la vía sur
    (-34, -1.9, 0.6),
    (-24, -0.5, 1.0),   # empieza a subir hacia el andén
    (-16, 4.6, 1.6),    # ya en el andén norte, a la altura de los ojos
    (-8, 6.0, 1.6),
    (0, 6.0, 1.6),      # frente al vagón
    (6, 6.4, 1.6),
    (10.5, 7.8, 1.6),   # entrada al nicho de acceso
    (12, 8.9, 1.6),     # frente a los torniquetes, con la escalera al fondo
]
POS_MIRA = [
    (-30, -1.9, 1.2),   # mira hacia la luz del fondo del túnel
    (-16, -1.0, 1.3),
    (-8, 2.6, 1.4),
    (-3, 3.0, 1.4),
    (0, 2.4, 1.6),      # puertas y ventanas del vagón
    (8.5, 1.9, 1.0),    # faros del vagón
    (12, 9.5, 1.2),
    (12, 12.5, 1.0),
    (12, 13.5, 1.8),    # la escalera que se pierde en la oscuridad
]
# (frame, distancia focal en mm): gran angular en el túnel, más cerrada al final
LENTES = [(1, 20), (560, 24), (900, 35), (1200, 28), (1500, 35)]
# (frame, nombre) para la línea de tiempo y para el documento
ESCENAS = [(1, "Tunel"), (520, "Anden"), (750, "Vagon"), (1100, "Acceso"), (1400, "Escalera")]


def make_path(name, points):
    """Curva Bezier 3D con manijas automáticas (trayectoria suave) animada de 0 a 1."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions, cu.use_path, cu.path_duration = '3D', True, FRAMES
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, cu)
    REC.objects.link(obj)
    cu.eval_time = 0
    cu.keyframe_insert('eval_time', frame=1)       # recorre la curva en todo el rango
    cu.eval_time = FRAMES
    cu.keyframe_insert('eval_time', frame=FRAMES)
    return obj


def follow(obj, path):
    c = obj.constraints.new('FOLLOW_PATH')
    c.target, c.use_curve_follow = path, False


ruta_cam = make_path("Ruta_Camara", POS_CAMARA)
ruta_mira = make_path("Ruta_Mira", POS_MIRA)

mira = bpy.data.objects.new("Mira_Camara", None)
mira.empty_display_type = 'SPHERE'
REC.objects.link(mira)
follow(mira, ruta_mira)

cam_data = bpy.data.cameras.new("Camara_Recorrido")
cam_data.clip_start, cam_data.clip_end = 0.1, 300
cam = bpy.data.objects.new("Camara_Recorrido", cam_data)
REC.objects.link(cam)
follow(cam, ruta_cam)
track = cam.constraints.new('TRACK_TO')            # la cámara siempre mira al empty
track.target, track.track_axis, track.up_axis = mira, 'TRACK_NEGATIVE_Z', 'UP_Y'

for frame, mm in LENTES:
    cam_data.lens = mm
    cam_data.keyframe_insert('lens', frame=frame)

sc.camera = cam
sc.timeline_markers.clear()
for frame, nombre in ESCENAS:
    sc.timeline_markers.new(nombre, frame=frame)

# Salida: secuencia de PNG (si el render se interrumpe, se retoma sin repetir frames)
sc.render.filepath = "//renders/frames/frame_"
sc.render.image_settings.file_format = 'PNG'
sc.render.use_overwrite = False
sc.render.use_placeholder = True
sc.frame_set(1)

print("Cámara lista: recorrido de", FRAMES, "frames con", len(POS_CAMARA), "puntos de control")
