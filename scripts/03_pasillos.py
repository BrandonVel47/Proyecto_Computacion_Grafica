"""03_pasillos.py
Nivel superior de la estación: escalera de dos tramos con descanso, pasillo largo con un
extremo tapiado y vestíbulo con taquilla, columnas y la cortina metálica de la salida,
por donde se cuela la luz del día. Requiere 01. Repetible: reconstruye sus colecciones.
Metros; ver layout.py para las medidas y el sistema de coordenadas.
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
from layout import (WALL_T as T, OUTER, ALC_X, ALC_D, ALC_CEIL, STAIR_W, STAIR_OPEN_H,
                    STEP_RUN, STEP_RISE, STEPS, LANDING, STAIR_Y0, STAIR_Y1, STAIR_Y2,
                    STAIR_TOP, Z_PAS, PAS_H, PB_Y0, PB_Y1, PB_YC, PB_X0, PB_X1,
                    VB_X1, VB_Y0, VB_Y1, VB_H, SALIDA_H, CORTINA_GAP)
from lib_bpy import fresh_collection, box, cylinder, tube_between, text, repeat

if "Estacion_Base" not in bpy.data.collections:
    raise RuntimeError("Ejecuta primero 01_geometria_base.py")
root = bpy.data.collections["Estacion_Base"]
PAS = fresh_collection("Pasillos", root)
LUZP = fresh_collection("Luminarias_Pasillo", root)   # 07_iluminacion les pone luz

XL, XR = ALC_X - STAIR_W / 2, ALC_X + STAIR_W / 2     # caras interiores de la escalera
Z_TECHO = Z_PAS + PAS_H                                # techo del pasillo (6.5 m)


def muro(tag, eje, a0, a1, cara, s, z0, alto, acabados=True, ext=(T, T)):
    """Muro recto de a0 a a1 a lo largo de `eje` ('X' o 'Y').
    `cara` es la coordenada de su cara interior y `s` (+1/-1) apunta hacia dentro del
    espacio. `ext` alarga solo la estructura para cerrar esquinas. Acabados como en los
    pasillos del Metro: zoclo, azulejo hasta 2.2 m y una franja de color."""
    def capa(nombre, grosor, off, dz, h, b0=a0, b1=a1):
        c = cara + s * off                   # off > 0: hacia el espacio; < 0: dentro del muro
        ln, bc = b1 - b0, (b0 + b1) / 2
        if eje == 'X':
            return box(nombre, (ln, grosor, h), (bc, c, z0 + dz + h / 2), PAS)
        return box(nombre, (grosor, ln, h), (c, bc, z0 + dz + h / 2), PAS)

    capa(f"Muro_Pas_{tag}", T, -T / 2, -0.3, alto + 0.6, a0 - ext[0], a1 + ext[1])
    if acabados:
        capa(f"Zoclo_Pas_{tag}", 0.04, 0.02, 0.0, 0.15)
        capa(f"Azulejo_{tag}", 0.02, 0.01, 0.15, 2.05)
        capa(f"Banda_Pas_{tag}", 0.03, 0.015, 2.2, 0.25)


def losa(tag, x0, x1, y0, y1, z, arriba):
    """Piso (la losa queda bajo `z`) o techo (la losa queda sobre `z`)."""
    zc = z + T / 2 if arriba else z - T / 2
    nombre = f"Techo_Pas_{tag}" if arriba else f"Piso_Pas_{tag}"
    return box(nombre, (x1 - x0, y1 - y0, T), ((x0 + x1) / 2, (y0 + y1) / 2, zc), PAS)


def luminaria(nombre, loc, largo=1.6, rot=(0, 0, 0)):
    o = box(nombre, (largo, 0.3, 0.08), loc, LUZP)
    o.rotation_euler = rot
    return o


def letrero(tag, cuerpo, centro, ancho, alto, cara, nombre="Letrero_Pasillo", size=0.18):
    """Letrero plano con texto, pegado a un muro o colgado (cara = hacia dónde mira)."""
    eje_x = cara in ('+Y', '-Y')
    dims = (ancho, 0.04, alto) if eje_x else (0.04, ancho, alto)
    box(f"{nombre}_{tag}", dims, centro, PAS)
    d = {'-Y': (0, -1), '+Y': (0, 1), '-X': (-1, 0), '+X': (1, 0)}[cara]
    text(f"Texto_{tag}", cuerpo, size,
         (centro[0] + d[0] * 0.025, centro[1] + d[1] * 0.025, centro[2]), cara, PAS)


# =====================================================================
# ESCALERA: dos tramos de 10 escalones con descanso (sube Z_PAS = 3.6 m)
# =====================================================================
for t, (y_ini, z_ini) in enumerate(((STAIR_Y0, 0.0), (STAIR_Y2, STEPS * STEP_RISE)), 1):
    for k in range(STEPS):
        top = z_ini + (k + 1) * STEP_RISE
        box(f"Escalon_{t}_{k:02d}", (STAIR_W, STEP_RUN, top),
            (ALC_X, y_ini + STEP_RUN * (k + 0.5), top / 2), PAS)
    # cinta antiderrapante en la orilla de cada escalón (un objeto con Array por tramo)
    nariz = box(f"Nariz_Escalon_{t}", (STAIR_W - 0.1, 0.05, 0.012),
                (ALC_X, y_ini + 0.03, z_ini + STEP_RISE + 0.006), PAS)
    repeat(nariz, STEPS, 0.0, STEP_RUN, STEP_RISE)
z_desc = STEPS * STEP_RISE
box("Descanso", (STAIR_W, LANDING, z_desc), (ALC_X, STAIR_Y1 + LANDING / 2, z_desc / 2), PAS)
losa("A", XL, XR, STAIR_TOP, PB_Y0, Z_PAS, False)

# Caja de la escalera detrás del nicho: muros forrados de azulejo y techo inclinado
YS0 = OUTER + ALC_D + T                                 # cara trasera del muro del nicho
for tag, cara, s in (("Esc_O", XL, 1), ("Esc_E", XR, -1)):
    muro(tag, 'Y', YS0, PB_Y0, cara, s, 0.0, Z_TECHO, acabados=False, ext=(0, 0))
    box(f"Azulejo_{tag}", (0.02, PB_Y0 - YS0, Z_TECHO - 0.15),
        (cara + s * 0.01, (YS0 + PB_Y0) / 2, 0.15 + (Z_TECHO - 0.15) / 2), PAS)

# techo inclinado: de la boca de la escalera (STAIR_OPEN_H) al techo del pasillo
dy, dz = STAIR_TOP - YS0, Z_TECHO - STAIR_OPEN_H
theta = math.atan2(dz, dy)                              # pendiente (~31°)
largo = math.hypot(dy, dz) + 0.3
mid_y, mid_z = (YS0 + STAIR_TOP) / 2, (STAIR_OPEN_H + Z_TECHO) / 2
mid_y += 0.15 * math.cos(theta) - (T / 2) * math.sin(theta)
mid_z += 0.15 * math.sin(theta) + (T / 2) * math.cos(theta)
techo_esc = box("Techo_Pas_Escalera", (STAIR_W + 2 * T, largo, T), (ALC_X, mid_y, mid_z), PAS)
techo_esc.rotation_euler = (theta, 0, 0)
losa("A", XL - T, XR + T, STAIR_TOP, PB_Y0, Z_TECHO, True)


def z_techo_esc(y):
    """Altura del techo inclinado en la posición y."""
    return STAIR_OPEN_H + (y - YS0) * math.tan(theta)


def z_escalon(y):
    """Altura de la línea de los escalones (para pasamanos y franja)."""
    if y <= STAIR_Y1:
        return (y - STAIR_Y0) / STEP_RUN * STEP_RISE
    if y <= STAIR_Y2:
        return z_desc
    return z_desc + (min(y, STAIR_TOP) - STAIR_Y2) / STEP_RUN * STEP_RISE


# franja de color sobre los escalones (sube de 1.8 a 2.2 m para no chocar con el techo
# inclinado y empatar con la del pasillo) y pasamanos a 0.9 m, en ambos muros
BANDA = ((YS0, 1.8), (STAIR_Y1, 1.8), (STAIR_Y2, 1.9), (STAIR_TOP, 2.2), (PB_Y0, 2.2))
for lado, cara, s in (("O", XL, 1), ("E", XR, -1)):
    for i in range(len(BANDA) - 1):
        (ya, ha), (yb, hb) = BANDA[i], BANDA[i + 1]
        za, zb = z_escalon(ya) + ha, z_escalon(yb) + hb
        b = box(f"Banda_Pas_Esc_{lado}{i}", (0.03, math.hypot(yb - ya, zb - za), 0.25),
                (cara + s * 0.015, (ya + yb) / 2, (za + zb) / 2 + 0.125), PAS)
        b.rotation_euler = (math.atan2(zb - za, yb - ya), 0, 0)
    xp = cara + s * 0.09
    puntos = [STAIR_Y0, STAIR_Y1, STAIR_Y2, STAIR_TOP, PB_Y0 - 0.2]
    for i in range(len(puntos) - 1):
        ya, yb = puntos[i], puntos[i + 1]
        tube_between(f"Pasamanos_{lado}{i}", (xp, ya, z_escalon(ya) + 0.9),
                     (xp, yb, z_escalon(yb) + 0.9), 0.025, PAS)
    for y in (STAIR_Y0 + 0.15, YS0 - 0.4):         # postes en el tramo que asoma al nicho
        tube_between(f"Poste_Pasamanos_{lado}_{y:.1f}", (xp, y, z_escalon(y)),
                     (xp, y, z_escalon(y) + 0.9), 0.025, PAS)

# luminarias: una en el nicho (sobre los torniquetes) y dos bajo el techo inclinado
luminaria("Luminaria_A_00", (ALC_X, STAIR_Y0 - 0.4, ALC_CEIL - 0.04), 2.0)
for i, y in enumerate((STAIR_Y0 + 2.6, STAIR_Y2 + 1.4)):
    luminaria(f"Luminaria_E_{i:02d}", (ALC_X, y, z_techo_esc(y) - 0.06), 2.0, (theta, 0, 0))

# =====================================================================
# PASILLO LARGO (a lo largo de X): la escalera desemboca en su muro sur
# =====================================================================
losa("B", PB_X0 - T, PB_X1, PB_Y0 - T, PB_Y1 + T, Z_PAS, False)
losa("B", PB_X0 - T, PB_X1, PB_Y0 - T, PB_Y1 + T, Z_TECHO, True)
muro("PN", 'X', PB_X0, PB_X1 - T, PB_Y1, -1, Z_PAS, PAS_H, ext=(T, 0))
muro("PS1", 'X', PB_X0, XL, PB_Y0, 1, Z_PAS, PAS_H, ext=(T, 0))
muro("PS2", 'X', XR, PB_X1 - T, PB_Y0, 1, Z_PAS, PAS_H, ext=(0, 0))

# extremo oeste: correspondencia clausurada, tapiada con tablones
HUECO_W, HUECO_H = 2.6, 2.5
y_a, y_b = PB_YC - HUECO_W / 2, PB_YC + HUECO_W / 2
muro("PO1", 'Y', PB_Y0, y_a, PB_X0, 1, Z_PAS, PAS_H, ext=(T, 0))
muro("PO2", 'Y', y_b, PB_Y1, PB_X0, 1, Z_PAS, PAS_H, ext=(0, T))
box("Muro_Pas_PO_Dintel", (T, HUECO_W, PAS_H - HUECO_H + 0.3),
    (PB_X0 - T / 2, PB_YC, Z_PAS + HUECO_H + (PAS_H - HUECO_H + 0.3) / 2), PAS)
x_fin = PB_X0 - T - 3.0                                 # pasaje oscuro detrás de los tablones
box("Pasaje_Piso", (3.0, HUECO_W, 0.2), (x_fin + 1.5, PB_YC, Z_PAS - 0.1), PAS)
box("Pasaje_Techo", (3.0, HUECO_W, 0.2), (x_fin + 1.5, PB_YC, Z_PAS + HUECO_H + 0.1), PAS)
box("Pasaje_Fondo", (0.2, HUECO_W, HUECO_H), (x_fin - 0.1, PB_YC, Z_PAS + HUECO_H / 2), PAS)
for k, y in ((1, y_a - 0.1), (2, y_b + 0.1)):
    box(f"Pasaje_Muro_{k}", (3.0, 0.2, HUECO_H), (x_fin + 1.5, y, Z_PAS + HUECO_H / 2), PAS)
for i, (z, giro, dyy) in enumerate(((0.35, 0.05, 0.0), (0.8, -0.07, 0.1), (1.3, 0.02, -0.05),
                                     (1.75, 0.09, 0.05), (2.25, -0.04, 0.0))):
    tab = box(f"Tablon_{i}", (0.035, HUECO_W + 0.5, 0.2), (PB_X0 + 0.03, PB_YC + dyy, Z_PAS + z), PAS)
    tab.rotation_euler = (giro, 0, 0)
text("TextoRojo_NoPasar", "NO PASAR", 0.5, (PB_X0 + 0.09, PB_YC, Z_PAS + 1.3), '+X', PAS)
letrero("Corr", "CORRESPONDENCIA", (PB_X0 + 0.03, PB_YC, Z_PAS + HUECO_H + 0.2), 2.6, 0.32, '+X')

# letreros colgantes con flechas y anuncios vacíos en los muros
for i, x in enumerate((19.0, 30.0)):
    zc = Z_TECHO - 0.5
    letrero(f"Salida_{i}", "SALIDA  →", (x, PB_YC, zc), 2.0, 0.4, '-X', size=0.22)
    text(f"Texto_Anden_{i}", "←  ANDENES", 0.22, (x + 0.025, PB_YC, zc), '+X', PAS)
    for r in (-0.8, 0.8):
        box(f"Varilla_Pas_{i}_{r}", (0.03, 0.03, 0.3), (x, PB_YC + r, Z_TECHO - 0.15), PAS)
for i, (x, cara, s) in enumerate(((17.0, PB_Y1, -1), (23.0, PB_Y1, -1), (29.0, PB_Y1, -1),
                                  (20.0, PB_Y0, 1), (26.0, PB_Y0, 1))):
    box(f"Marco_Anuncio_P_{i}", (2.0, 0.06, 1.3), (x, cara + s * 0.05, Z_PAS + 1.5), PAS)
    box(f"Cartel_P_{i}", (1.8, 0.04, 1.1), (x, cara + s * 0.07, Z_PAS + 1.5), PAS)
for i in range(4):                                      # rejillas de ventilación altas
    box(f"Rejilla_Vent_{i}", (0.8, 0.05, 0.3), (9.0 + 7.0 * i, PB_Y0 + 0.03, Z_TECHO - 0.35), PAS)
box("Puerta_Servicio", (1.0, 0.06, 2.1), (32.5, PB_Y0 + 0.03, Z_PAS + 1.05), PAS)
letrero("Servicio", "SOLO PERSONAL\nAUTORIZADO", (32.5, PB_Y0 + 0.03, Z_PAS + 2.45),
        1.0, 0.32, '+Y', nombre="Letrero_Rojo", size=0.09)
for i in range(10):                                     # una luminaria cada 3 m
    luminaria(f"Luminaria_P_{i:02d}", (PB_X0 + 1.5 + 3.0 * i, PB_YC, Z_TECHO - 0.04))

# =====================================================================
# VESTÍBULO: taquilla, columnas, reloj y cortina metálica de la salida
# =====================================================================
Z_TV = Z_PAS + VB_H
losa("V", PB_X1 - T, VB_X1 + T, VB_Y0 - T, VB_Y1 + T, Z_PAS, False)
losa("V", PB_X1 - T, VB_X1 + T, VB_Y0 - T, VB_Y1 + T, Z_TV, True)
muro("VN", 'X', PB_X1, VB_X1, VB_Y1, -1, Z_PAS, VB_H)
muro("VS", 'X', PB_X1, VB_X1, VB_Y0, 1, Z_PAS, VB_H)
for lado, cara, s in (("VO", PB_X1, 1), ("VE", VB_X1, -1)):
    muro(f"{lado}1", 'Y', VB_Y0, PB_Y0, cara, s, Z_PAS, VB_H, ext=(0, 0))
    muro(f"{lado}2", 'Y', PB_Y1, VB_Y1, cara, s, Z_PAS, VB_H, ext=(0, 0))
for lado, cara, s, z_hueco in (("VO", PB_X1, 1, Z_TECHO), ("VE", VB_X1, -1, Z_PAS + SALIDA_H)):
    h = Z_TV + T - z_hueco
    box(f"Muro_Pas_{lado}_Dintel", (T, PB_Y1 - PB_Y0, h),
        (cara - s * T / 2, PB_YC, z_hueco + h / 2), PAS)
for i, (x, y) in enumerate(((39.5, PB_Y0 - 1.0), (44.5, PB_Y0 - 1.0),
                            (39.5, PB_Y1 + 1.0), (44.5, PB_Y1 + 1.0))):
    box(f"Columna_{i}", (0.6, 0.6, VB_H), (x, y, Z_PAS + VB_H / 2), PAS)
    box(f"Zoclo_Pas_Col_{i}", (0.64, 0.64, 0.15), (x, y, Z_PAS + 0.075), PAS)

# taquilla contra el muro norte, con su ventanilla iluminada desde dentro
TX0, TX1, TQ_D = 40.0, 44.0, 2.0
ty_f = VB_Y1 - TQ_D                                     # frente de la taquilla
box("Taquilla_Cuerpo", (TX1 - TX0, TQ_D, 2.6), ((TX0 + TX1) / 2, VB_Y1 - TQ_D / 2, Z_PAS + 1.3), PAS)
box("Taquilla_Cristal", (2.6, 0.04, 1.0), ((TX0 + TX1) / 2, ty_f - 0.02, Z_PAS + 1.6), PAS)
box("Taquilla_Mostrador", (3.0, 0.35, 0.05), ((TX0 + TX1) / 2, ty_f - 0.17, Z_PAS + 1.05), PAS)
letrero("Taquilla", "TAQUILLA", ((TX0 + TX1) / 2, ty_f - 0.02, Z_PAS + 2.35), 2.0, 0.35, '-Y',
        size=0.24)

# reloj detenido a las 11:58 sobre la taquilla
rc = ((TX0 + TX1) / 2, VB_Y1 - 0.06, Z_PAS + 3.0)
cylinder("Reloj_Caja", 0.36, 0.08, rc, PAS, 32, 'Y')
cylinder("Reloj_Cara", 0.32, 0.02, (rc[0], rc[1] - 0.045, rc[2]), PAS, 32, 'Y')
for h in range(12):
    a = math.radians(30 * h)
    box(f"Reloj_Marca_{h}", (0.02, 0.01, 0.06),
        (rc[0] + 0.27 * math.sin(a), rc[1] - 0.06, rc[2] + 0.27 * math.cos(a)), PAS).rotation_euler = (0, a, 0)
for nombre, largo_m, grados in (("H", 0.16, 359.0), ("M", 0.26, 348.0)):
    a = math.radians(grados)
    box(f"Reloj_Manecilla_{nombre}", (0.02, 0.01, largo_m),
        (rc[0] + largo_m / 2 * math.sin(a), rc[1] - 0.065, rc[2] + largo_m / 2 * math.cos(a)),
        PAS).rotation_euler = (0, a, 0)

# salida: cortina metálica casi cerrada, guías, caja del rollo y letrero verde
cx_c = VB_X1 + T / 2
box("Cortina", (0.05, PB_Y1 - PB_Y0, SALIDA_H - CORTINA_GAP),
    (cx_c, PB_YC, Z_PAS + CORTINA_GAP + (SALIDA_H - CORTINA_GAP) / 2), PAS)
for k, y in ((0, PB_Y0 + 0.04), (1, PB_Y1 - 0.04)):
    box(f"Cortina_Guia_{k}", (0.12, 0.08, SALIDA_H), (cx_c, y, Z_PAS + SALIDA_H / 2), PAS)
box("Cortina_Caja", (0.3, PB_Y1 - PB_Y0 + 0.3, 0.24), (VB_X1 - 0.15, PB_YC, Z_PAS + SALIDA_H + 0.12), PAS)
box("Salida_Caja", (0.06, 1.2, 0.3), (VB_X1 - 0.03, PB_YC, Z_TV - 0.2), PAS)
text("Texto_Salida_V", "SALIDA", 0.2, (VB_X1 - 0.065, PB_YC, Z_TV - 0.2), '-X', PAS)
# recinto detrás de la cortina (07_iluminacion pone ahí la luz del día)
RX0, RX1 = VB_X1 + T, VB_X1 + T + 2.0
box("Salida_Recinto_Piso", (RX1 - RX0 + T, PB_Y1 - PB_Y0 + 2 * T, T),
    ((RX0 + RX1 + T) / 2, PB_YC, Z_PAS - T / 2), PAS)
box("Salida_Recinto_Techo", (RX1 - RX0 + T, PB_Y1 - PB_Y0 + 2 * T, T),
    ((RX0 + RX1 + T) / 2, PB_YC, Z_PAS + SALIDA_H + 0.2 + T / 2), PAS)
box("Salida_Recinto_Fondo", (T, PB_Y1 - PB_Y0 + 2 * T, SALIDA_H + 0.2),
    (RX1 + T / 2, PB_YC, Z_PAS + (SALIDA_H + 0.2) / 2), PAS)
for k, y in ((0, PB_Y0 - T / 2), (1, PB_Y1 + T / 2)):
    box(f"Salida_Recinto_Muro_{k}", (RX1 - RX0, T, SALIDA_H + 0.2),
        ((RX0 + RX1) / 2, y, Z_PAS + (SALIDA_H + 0.2) / 2), PAS)

for r, y in enumerate((PB_YC - 2.0, PB_YC + 2.0)):      # 2 hileras de 3 luminarias
    for i, x in enumerate((38.0, 42.0, 46.0)):
        luminaria(f"Luminaria_V_{r}_{i}", (x, y, Z_TV - 0.04), 2.0)

print("Pasillos creados:", len(PAS.objects), "objetos y", len(LUZP.objects), "luminarias")
