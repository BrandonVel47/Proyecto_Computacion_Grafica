"""04_detalles.py
Detalles que cuentan el abandono y dan escala: bancas, botes, gabinetes contra incendio,
cámaras de vigilancia, señalización con texto, anuncios, semáforos en los túneles, mapa
de la red, charcos, papeles, cajas, un plafón caído con cables colgando y una luminaria
desprendida. Requiere 01, 02 y 03. Repetible: reconstruye su colección "Detalles_Extra".
Las posiciones aleatorias usan una semilla fija: siempre salen iguales.
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
from layout import (PLAT_L, PIT_HALF, OUTER, CEIL_H, X_END, ALC_X, SIDES, NOMBRE_ESTACION,
                    DIRECCION, Z_PAS, PAS_H, PB_Y0, PB_Y1, PB_YC, PB_X0, PB_X1, VB_X1,
                    VB_Y0, VB_Y1, VB_H)
from lib_bpy import fresh_collection, box, cylinder, tube_between, blob, text, cable

for req in ("Estacion_Base", "Vagon", "Pasillos"):
    if req not in bpy.data.collections:
        raise RuntimeError("Ejecuta antes 01, 02 y 03 (falta la colección %s)" % req)
root = bpy.data.collections["Estacion_Base"]
DX = fresh_collection("Detalles_Extra", root)
rng = random.Random(7)
Z_TECHO = Z_PAS + PAS_H
CARA = {1: '-Y', -1: '+Y'}          # hacia dónde mira algo pegado al muro de cada andén


def banca(tag, x, y_muro, s, z0=0.0, eje='X'):
    """Banca metálica pegada a un muro. s apunta del muro hacia el espacio."""
    def b(n, size, off, dz):
        if eje == 'X':
            return box(n, size, (x, y_muro + s * off, z0 + dz), DX)
        return box(n, (size[1], size[0], size[2]), (y_muro + s * off, x, z0 + dz), DX)
    b(f"Banca_Asiento_{tag}", (1.8, 0.45, 0.05), 0.35, 0.45)
    b(f"Banca_Respaldo_{tag}", (1.8, 0.05, 0.4), 0.13, 0.78)
    for k in (-0.8, 0.8):
        if eje == 'X':
            box(f"Banca_Pata_{tag}_{k}", (0.05, 0.45, 0.45), (x + k, y_muro + s * 0.35, z0 + 0.22), DX)
        else:
            box(f"Banca_Pata_{tag}_{k}", (0.45, 0.05, 0.45), (y_muro + s * 0.35, x + k, z0 + 0.22), DX)


def bote(tag, x, y, z0=0.0):
    cylinder(f"Bote_Basura_{tag}", 0.22, 0.7, (x, y, z0 + 0.35), DX, 16)
    cylinder(f"Bote_Tapa_{tag}", 0.24, 0.05, (x, y, z0 + 0.72), DX, 16)


def anuncio(tag, x, y_muro, s, z, eje='X'):
    """Marco publicitario con un cartel viejo y roto."""
    if eje == 'X':
        box(f"Marco_Anuncio_{tag}", (2.0, 0.06, 1.3), (x, y_muro + s * 0.03, z), DX)
        box(f"Cartel_{tag}", (1.8, 0.04, 1.1), (x, y_muro + s * 0.05, z), DX)


def segmento(nombre, p0, p1, y, ancho, col):
    """Barra delgada sobre un plano vertical X-Z (líneas del mapa)."""
    dx, dz = p1[0] - p0[0], p1[1] - p0[1]
    o = box(nombre, (math.hypot(dx, dz) + ancho, 0.01, ancho),
            ((p0[0] + p1[0]) / 2, y, (p0[1] + p1[1]) / 2), col)
    o.rotation_euler = (0, -math.atan2(dz, dx), 0)
    return o


# =====================================================================
# ANDENES
# =====================================================================
for s in SIDES:
    n = "N" if s > 0 else "S"
    y_muro = s * (OUTER - 0.05)                       # cara del travertino
    for x in ((-12.0, -4.0, 4.0) if s > 0 else (-12.0, -4.0, 4.0, 12.0)):
        banca(f"{n}{x:+.0f}", x, y_muro, -s)
    bote(f"{n}1", -13.6, s * (OUTER - 0.4))
    bote(f"{n}2", 5.6, s * (OUTER - 0.4))
    for x in ((-12.0, 4.0) if s > 0 else (-4.0, 12.0)):
        anuncio(f"E_{n}{x:+.0f}", x, y_muro, -s, 1.65)
    # gabinete contra incendio con su vidrio
    gx = -20.0 * s
    box(f"Gabinete_{n}", (0.7, 0.15, 0.9), (gx, s * (OUTER - 0.125), 1.3), DX)
    box(f"Gabinete_Vidrio_{n}", (0.55, 0.02, 0.7), (gx, s * (OUTER - 0.21), 1.3), DX)
    # cámaras de vigilancia bajo el techo
    for k, x in enumerate((-21.0, 21.0)):
        tube_between(f"Camara_CCTV_Soporte_{n}{k}", (x, s * 7.6, CEIL_H), (x, s * 7.6, CEIL_H - 0.25), 0.02, DX)
        cam = box(f"Camara_CCTV_{n}{k}", (0.32, 0.12, 0.12), (x - 0.1 * math.copysign(1, x), s * 7.6, CEIL_H - 0.3), DX)
        cam.rotation_euler = (0, 0.35 * math.copysign(1, x), 0)
    # nombre de la estación sobre los rótulos azules (y un rótulo extra por andén)
    extra_x = 16.0 if s > 0 else -18.0
    box(f"Rotulo_Estacion_{n}2", (3.2, 0.03, 0.32), (extra_x, s * (OUTER - 0.065), 2.725), DX)
    for k, x in enumerate((-4.0, extra_x)):
        text(f"Texto_Estacion_{n}{k}", NOMBRE_ESTACION, 0.2, (x, s * (OUTER - 0.085), 2.725), CARA[s], DX)
    # letreros colgantes "Dirección ..." (las cajas verdes vienen del script 01)
    letrero = bpy.data.objects.get(f"Letrero_Colgante_{s}")
    if letrero:
        lx, ly, lz = letrero.location
        for cara, dx in (('+X', 0.13), ('-X', -0.13)):
            text(f"Texto_Direccion_{n}{cara}", f"DIRECCIÓN\n{DIRECCION[s]}", 0.17,
                 (lx + dx, ly, lz), cara, DX)
    # charcos y papeles tirados
    for k, (x, y, rx, ry) in enumerate(((-6.0, 5.6, 1.2, 0.6), (13.0, 6.6, 1.0, 0.7))
                                       if s > 0 else ((-14.0, -6.0, 1.3, 0.7), (8.0, -5.3, 0.9, 0.5))):
        blob(f"Charco_{n}{k}", rx, ry, (x, y, 0.024), DX, seed=k + (0 if s > 0 else 10))
    for k in range(16):
        p = box(f"Papel_{n}{k}", (0.21, 0.28, 0.003),
                (rng.uniform(-21, 21), s * rng.uniform(4.6, 7.9), 0.024), DX)
        p.rotation_euler = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), rng.uniform(0, math.pi))

# letrero verde de SALIDA sobre la entrada del nicho
box("Salida_Caja_Nicho", (1.0, 0.06, 0.3), (ALC_X, OUTER - 0.03, 3.2), DX)
text("Texto_Salida_Nicho", "SALIDA", 0.2, (ALC_X, OUTER - 0.065, 3.2), '-Y', DX)
# cajas de cartón abandonadas al fondo del andén sur
for k, (x, y, z, r) in enumerate(((-21.0, -7.7, 0.2, 0.2), (-20.3, -7.8, 0.2, -0.3), (-20.7, -7.75, 0.6, 0.6))):
    box(f"Caja_Carton_S{k}", (0.6, 0.45, 0.4), (x, y, z), DX).rotation_euler = (0, 0, r)

# semáforos en rojo a la salida de cada túnel (miran hacia la estación)
for sx in SIDES:
    for sy in SIDES:
        x, y = sx * (X_END + 3.0), sy * (PIT_HALF - 0.16)
        box(f"Semaforo_Caja_{sx}_{sy}", (0.14, 0.28, 0.65), (x, y, 1.4), DX)
        cylinder(f"Semaforo_Rojo_{sx}_{sy}", 0.07, 0.04, (x - sx * 0.08, y, 1.58), DX, 16, 'X')
        cylinder(f"Semaforo_Verde_{sx}_{sy}", 0.07, 0.04, (x - sx * 0.08, y, 1.24), DX, 16, 'X')

# =====================================================================
# PASILLO
# =====================================================================
for k, (x, y, rx, ry) in enumerate(((15.0, PB_YC + 0.4, 1.6, 0.8), (26.5, PB_YC + 0.7, 1.2, 0.6))):
    blob(f"Charco_P{k}", rx, ry, (x, y, Z_PAS + 0.004), DX, seed=20 + k)
for k in range(16):
    p = box(f"Papel_P{k}", (0.21, 0.28, 0.003),
            (rng.uniform(PB_X0 + 1, PB_X1 - 1), rng.uniform(PB_Y0 + 0.2, PB_Y1 - 0.2), Z_PAS + 0.004), DX)
    p.rotation_euler = (0, 0, rng.uniform(0, math.pi))
for k, (x, y, z, r) in enumerate(((PB_X0 + 0.5, PB_Y0 + 0.45, 0.2, 0.1), (PB_X0 + 1.2, PB_Y0 + 0.4, 0.2, -0.2),
                                  (PB_X0 + 0.8, PB_Y0 + 0.45, 0.6, 0.4), (PB_X0 + 0.45, PB_Y1 - 0.5, 0.25, 0.7))):
    box(f"Caja_Carton_P{k}", (0.6, 0.45, 0.4 if k != 3 else 0.5), (x, y, Z_PAS + z), DX).rotation_euler = (0, 0, r)
bote("P1", 22.0, PB_Y1 - 0.35, Z_PAS)
box("Gabinete_P", (0.7, 0.15, 0.9), (34.2, PB_Y1 - 0.075, Z_PAS + 1.3), DX)
box("Gabinete_Vidrio_P", (0.55, 0.02, 0.7), (34.2, PB_Y1 - 0.16, Z_PAS + 1.3), DX)

# plafón caído: un hueco negro en el techo, el panel colgando de una orilla y cables
hx, hy = 26.5, PB_Y1 - 0.6
box("Hueco_Techo", (1.2, 0.6, 0.01), (hx, hy, Z_TECHO - 0.004), DX)
fi = math.radians(50)
panel = box("Panel_Caido", (1.2, 0.6, 0.03),
            (hx, hy + 0.3 - 0.3 * math.cos(fi), Z_TECHO - 0.01 - 0.3 * math.sin(fi)), DX)
panel.rotation_euler = (fi, 0, 0)
for k, (dx, largo, giro) in enumerate(((-0.35, 0.9, 0.15), (0.05, 0.6, -0.2), (0.4, 1.1, 0.1))):
    z0 = Z_TECHO - 0.01
    cable(f"Cable_Colgante_{k}", [(hx + dx, hy, z0), (hx + dx + giro, hy - 0.1, z0 - largo * 0.5),
                                  (hx + dx + giro * 0.5, hy - 0.2, z0 - largo)], 0.012, DX)

# luminaria desprendida: cuelga inclinada de un solo lado
lum = bpy.data.objects.get("Luminaria_P_06")
if lum:
    lum.rotation_euler = (0, 0.35, 0)
    lum.location.z = Z_TECHO - 0.34                  # valor absoluto: repetir el script no la baja más
    ex = lum.location.x + 0.75 * math.cos(0.35)        # extremo que sigue sujeto
    cable("Cable_Colgante_Lum", [(ex, PB_YC, Z_TECHO - 0.01), (ex + 0.05, PB_YC, Z_TECHO - 0.2),
                                 (ex, PB_YC, lum.location.z - 0.75 * math.sin(0.35) + 0.04)], 0.01, DX)

# =====================================================================
# VESTÍBULO
# =====================================================================
banca("V1", 39.0, VB_Y0, 1, Z_PAS)
banca("V2", 45.0, VB_Y0, 1, Z_PAS)
bote("V1", 37.0, VB_Y0 + 0.4, Z_PAS)
anuncio("V1", 37.6, VB_Y1, -1, Z_PAS + 1.6)
anuncio("V2", 46.4, VB_Y1, -1, Z_PAS + 1.6)
blob("Charco_V0", 1.5, 0.9, (41.0, PB_YC - 1.3, Z_PAS + 0.004), DX, seed=31)
blob("Charco_V1", 0.7, 0.5, (40.5, PB_YC + 1.2, Z_PAS + 0.004), DX, seed=32)
for k in range(12):
    p = box(f"Papel_V{k}", (0.21, 0.28, 0.003),
            (rng.uniform(36.5, 47.5), rng.uniform(VB_Y0 + 0.4, VB_Y1 - 2.3), Z_PAS + 0.004), DX)
    p.rotation_euler = (0, 0, rng.uniform(0, math.pi))
for k, (x, y, z, r) in enumerate(((47.3, VB_Y0 + 0.5, 0.2, 0.3), (46.7, VB_Y0 + 0.45, 0.2, -0.1))):
    box(f"Caja_Carton_V{k}", (0.6, 0.45, 0.4), (x, y, Z_PAS + z), DX).rotation_euler = (0, 0, r)
# letrero que se cayó del techo y quedó recargado en una columna
caido = box("Letrero_Caido", (1.6, 0.05, 0.4), (44.5, PB_Y0 - 0.55, Z_PAS + 0.55), DX)
caido.rotation_euler = (math.radians(-12), math.radians(8), 0)
t_caido = text("Texto_Caido", "ANDENES  ←", 0.16, (0, 0.03, 0), '+Y', DX)
t_caido.parent = caido                          # el texto sigue la inclinación del letrero

# mapa de la red en el muro sur, con una "Línea 0" punteada que no existe
MX, MZ, MY = 42.0, Z_PAS + 1.75, VB_Y0 + 0.02
box("Marco_Mapa", (2.5, 0.04, 1.7), (MX, MY, MZ), DX)
box("Mapa_Panel", (2.4, 0.03, 1.6), (MX, MY + 0.01, MZ), DX)
LINEAS = {   # color, puntos (u, v) en [-1, 1]
    "L1": ((0.85, 0.3, 0.5), [(-1.0, 0.25), (-0.3, 0.2), (0.4, 0.15), (1.0, 0.05)]),
    "L2": ((0.05, 0.25, 0.75), [(-0.8, -0.9), (-0.25, -0.15), (0.2, 0.35), (0.85, 0.9)]),
    "L3": ((0.45, 0.55, 0.1), [(-0.35, 1.0), (-0.3, 0.2), (-0.3, -1.0)]),
    "L5": ((0.95, 0.78, 0.05), [(0.55, 1.0), (0.4, 0.15), (0.45, -0.3), (0.85, -0.95)]),
    "L7": ((0.9, 0.4, 0.05), [(-1.0, -0.55), (0.3, -0.6), (1.0, -0.35)]),
}
y_lin = MY + 0.03
for nombre, (color, pts) in LINEAS.items():
    mat = lm.pintura(f"Mapa_{nombre}", color, rough=0.5, wear_at=0.75)
    xz = [(MX + u * 1.08, MZ + v * 0.7) for u, v in pts]
    for i in range(len(xz) - 1):
        o = segmento(f"Mapa_{nombre}_{i}", xz[i], xz[i + 1], y_lin, 0.035, DX)
        o.data.materials.append(mat)
        o["mat_propio"] = True                  # 06_materiales respeta este material
negro = lm.mate("Mapa_Negro", (0.01, 0.01, 0.01), 0.7)
p_l0 = [(MX - 0.95, MZ + 0.6), (MX - 0.55, MZ + 0.45), (MX - 0.1, MZ + 0.5)]
for i in range(len(p_l0) - 1):                  # trazo punteado de la Línea 0
    a, b = p_l0[i], p_l0[i + 1]
    for t in range(4):
        f0, f1 = t / 4, t / 4 + 0.15
        o = segmento(f"Mapa_L0_{i}_{t}", (a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0),
                     (a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1), y_lin, 0.03, DX)
        o.data.materials.append(negro)
        o["mat_propio"] = True
for k, (u, v) in enumerate(((-0.3, 0.2), (0.4, 0.15), (-0.27, -0.15), (0.43, -0.32), (-0.1, 0.5))):
    cylinder(f"Mapa_Estacion_{k}", 0.035, 0.012, (MX + u * 1.08, y_lin + 0.006, MZ + v * 0.7), DX, 16, 'Y')
text("TextoNegro_Mapa", "RED DEL METRO", 0.09, (MX, MY + 0.035, MZ + 0.7), '+Y', DX)
text("TextoNegro_Mapa_L0", "0", 0.1, (MX - 1.02, MY + 0.035, MZ + 0.6), '+Y', DX)

print("Detalles agregados:", len(DX.objects), "objetos")
