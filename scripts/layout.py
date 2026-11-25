"""layout.py — parámetros de la estación compartidos por todos los scripts.
Metros. X = largo, Y = ancho (0 = eje entre las dos vías), Z = altura (0 = piso del andén).
Cambiar un valor aquí lo cambia en todos los scripts.
"""
PLAT_L, PLAT_W, PLAT_H = 44.0, 4.5, 1.1   # andén: largo, ancho, alto sobre vía
PIT_HALF = 3.8                            # medio ancho del foso de vías
OUTER = PIT_HALF + PLAT_W                 # posición del muro del fondo
CEIL_H, WALL_T = 3.5, 0.3                 # techo bajo (como en las fotos)
TUNNEL_EXT = 30.0                         # túnel a cada extremo
TRACK_Y, GAUGE = 1.9, 1.5                 # eje de cada vía y ancho de vía
BEAM_STEP = 8.0                           # vigas y pilastras cada 8 m
ALC_X, ALC_W, ALC_D = 12.0, 5.0, 3.5      # nicho de acceso (andén Y+)
STAIR_W, STAIR_OPEN_H = 3.0, 2.4          # boca de la escalera en el fondo del nicho

# Derivados
WALL_H = CEIL_H + PLAT_H                  # del fondo de la vía al techo
WALL_ZC = (CEIL_H - PLAT_H) / 2           # centro vertical de los muros
X_END = PLAT_L / 2 + WALL_T               # donde empieza el túnel
TOTAL_L = PLAT_L + 2 * (WALL_T + TUNNEL_EXT)
SIDES = (1, -1)

# Animación
FPS, FRAMES = 24, 1500                    # 1500 frames a 24 fps ≈ 62 s
