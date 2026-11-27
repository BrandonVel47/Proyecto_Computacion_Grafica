"""layout.py — parámetros de la escena compartidos por todos los scripts.
Metros. X = largo, Y = ancho (0 = eje entre las dos vías), Z = altura (0 = piso del andén).
Cambiar un valor aquí lo cambia en todos los scripts.
"""
# ---------- Estación ----------
PLAT_L, PLAT_W, PLAT_H = 44.0, 4.5, 1.1   # andén: largo, ancho, alto sobre vía
PIT_HALF = 3.8                            # medio ancho del foso de vías
OUTER = PIT_HALF + PLAT_W                 # posición del muro del fondo
CEIL_H, WALL_T = 3.5, 0.3                 # techo bajo (como en las fotos)
TUNNEL_EXT = 30.0                         # túnel a cada extremo
TRACK_Y, GAUGE = 1.9, 1.5                 # eje de cada vía y ancho de vía
BEAM_STEP = 8.0                           # vigas y pilastras cada 8 m
ALC_X, ALC_W, ALC_D = 12.0, 5.0, 3.5      # nicho de acceso (andén Y+)
ALC_CEIL = 3.2                            # altura del plafón del nicho
STAIR_W, STAIR_OPEN_H = 3.0, 3.2          # boca de la escalera en el fondo del nicho

# Derivados
WALL_H = CEIL_H + PLAT_H                  # del fondo de la vía al techo
WALL_ZC = (CEIL_H - PLAT_H) / 2           # centro vertical de los muros
X_END = PLAT_L / 2 + WALL_T               # donde empieza el túnel
TOTAL_L = PLAT_L + 2 * (WALL_T + TUNNEL_EXT)
SIDES = (1, -1)

# Textos de la señalización (se pueden cambiar libremente)
NOMBRE_ESTACION = "ESTACIÓN CERO"
DIRECCION = {1: "TERMINAL NORTE", -1: "TERMINAL SUR"}   # por andén (Y+ / Y-)

# ---------- Escalera y pasillos (nivel superior, detrás del nicho) ----------
TORN_DY = 1.2                             # torniquetes: distancia desde la entrada del nicho
STEP_RUN, STEP_RISE, STEPS = 0.30, 0.18, 10   # huella, peralte y escalones por tramo
LANDING = 1.2                             # descanso entre los dos tramos
STAIR_Y0 = OUTER + TORN_DY + 0.9          # la escalera empieza detrás de los torniquetes
STAIR_Y1 = STAIR_Y0 + STEPS * STEP_RUN    # fin del tramo 1 = inicio del descanso
STAIR_Y2 = STAIR_Y1 + LANDING             # inicio del tramo 2
STAIR_TOP = STAIR_Y2 + STEPS * STEP_RUN   # llegada al nivel superior
Z_PAS = 2 * STEPS * STEP_RISE             # piso de pasillo y vestíbulo (3.6 m)
PAS_H, PAS_W = 2.9, 4.0                   # altura libre y ancho del pasillo largo
PB_Y0 = STAIR_TOP + 1.0                   # cara interior del muro sur del pasillo
PB_Y1 = PB_Y0 + PAS_W                     # cara interior del muro norte
PB_YC = (PB_Y0 + PB_Y1) / 2               # eje del pasillo (y del recorrido)
PB_X0, PB_X1 = ALC_X - 6.0, 36.0          # extremo tapiado (oeste) y entrada al vestíbulo
VB_X1 = PB_X1 + 12.0                      # muro del vestíbulo con la cortina de salida
VB_Y0, VB_Y1 = PB_Y0 - 4.0, PB_Y1 + 4.0   # muros sur y norte del vestíbulo
VB_H = 3.6                                # altura libre del vestíbulo
SALIDA_H, CORTINA_GAP = 3.0, 0.28         # hueco de la salida y rendija bajo la cortina

# ---------- Animación ----------
FPS, FRAMES = 24, 2520                    # 2520 frames a 24 fps = 105 s
TREN_F0, TREN_V = 442, 10.0               # frame en que arranca el tren y velocidad (m/s)
