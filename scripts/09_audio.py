"""09 — Banda sonora procedural del recorrido (sin audios de terceros).

Se ejecuta FUERA de Blender, con Python normal:   python scripts/09_audio.py
Requiere numpy y scipy. Escribe renders/audio_ambiente.wav (estéreo, 44.1 kHz) con la
misma duración que la animación (FRAMES / FPS). Luego se une al video con ffmpeg:

    ffmpeg -i renders/LaLineaCero_mudo.mp4 -i renders/audio_ambiente.wav \
           -c:v copy -c:a aac -b:a 192k -shortest renders/LaLineaCero.mp4

Todo se sintetiza con ruido filtrado y senoidales; la semilla fija el resultado.
Los volúmenes (VOL_*) están arriba para ajustarlos de oído sin tocar el resto.
"""
import os
import numpy as np
from scipy import signal
from scipy.io import wavfile

# --- datos de la animación (los mismos de layout.py / 05_tren.py / 08_camara.py) -----------
FPS, FRAMES = 24, 2520
DUR = FRAMES / FPS                      # 105 s
SR = 44100
SEED = 26
rng = np.random.default_rng(SEED)

# marcadores de la cámara (frame -> segundo)
T_TUNEL, T_TREN_ARRANCA = 1 / FPS, 442 / FPS
T_TREN_FIN = 859 / FPS
T_ESCALERA, T_PASILLO, T_VESTIBULO = 1440 / FPS, 1840 / FPS, 2300 / FPS

# --- el tren y la cámara en el tramo del tren (de 05_tren.py y 08_camara.py) -----------------
# El volumen del tren sale de la distancia REAL entre la cámara y el tren, no de una curva a ojo.
TREN_X0 = 22.3 + 30.0 + 22.0 + 7.5      # x del rig al arrancar (FIN_TUNEL + 22 + CAR_L/2)
TREN_X1 = -92.0                         # x del rig al terminar (05_tren.py)
TREN_F0, TREN_F1 = 442, 859             # el movimiento es Bezier (suave), no de velocidad constante
TREN_ADELANTE, TREN_ATRAS = 7.5, 7.5 + 2 * 15.6   # la punta va 7.5 m delante del rig, la cola 38.7 m detrás
TREN_Y, TREN_Z = -1.9, 1.5
# (frame, posición de la cámara, punto al que mira) de los puntos de control de 08_camara.py
CAM = [(442, (-17.9, 4.2, 1.6), (-8.0, -1.4, 1.3)), (460, (-17.5, 4.6, 1.6), (-8.0, -1.4, 1.3)),
       (600, (-16.8, 5.4, 1.6), (-7.0, -1.9, 1.4)), (660, (-16.6, 5.6, 1.6), (-12.0, -1.9, 1.4)),
       (720, (-16.4, 5.7, 1.6), (-18.0, -1.9, 1.4)), (790, (-16.2, 5.8, 1.6), (-25.0, -2.1, 1.2)),
       (860, (-14.5, 5.8, 1.6), (-20.0, 1.0, 1.3))]
D_REF, EXP_DIST = 8.0, 0.35             # a 8 m (pasando junto a la cámara) ganancia 1; ~1/d^0.35
                                        # (el túnel conduce el sonido: cae menos que al aire libre)

# --- mezcla (0..1) -------------------------------------------------------------------------
VOL_DRONE, VOL_VIENTO, VOL_ZUMBIDO = 0.55, 0.35, 0.16
VOL_TREN, VOL_GOTAS, VOL_GOLPES, VOL_CHISPAS, VOL_TENSION = 0.9, 0.30, 0.45, 0.22, 0.30
VOL_AIRE = 0.55                         # ráfagas del tren, corrientes y silbidos

N = int(DUR * SR)
t = np.arange(N) / SR


def env(puntos):
    """Envolvente lineal por tramos: lista de (segundo, ganancia)."""
    xs, ys = zip(*puntos)
    return np.interp(t, xs, ys)


def ruido(color="blanco"):
    r = rng.standard_normal(N)
    if color == "marron":                       # ruido browniano: retumbo grave
        r = np.cumsum(r)
        r -= np.convolve(r, np.ones(SR) / SR, mode="same")   # quita la deriva
        r /= np.max(np.abs(r))
    return r


def paso_banda(x, f0, f1, orden=2):
    sos = signal.butter(orden, [f0, f1], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def paso_bajo(x, fc, orden=2):
    return signal.sosfilt(signal.butter(orden, fc, btype="low", fs=SR, output="sos"), x)


def rig_x_en(f):
    """x del tren en el frame f: Bezier con manijas planas entre dos llaves = smoothstep."""
    u = min(max((f - TREN_F0) / (TREN_F1 - TREN_F0), 0.0), 1.0)
    return TREN_X0 + (TREN_X1 - TREN_X0) * (3 * u * u - 2 * u ** 3)


def frame_cuando(x_punta=None, x_cola=None):
    """Primer frame en que la punta (o la cola) del tren llega a la coordenada x dada."""
    for f in np.arange(TREN_F0, TREN_F1, 0.25):
        if x_punta is not None and rig_x_en(f) - TREN_ADELANTE <= x_punta:
            return f
        if x_cola is not None and rig_x_en(f) + TREN_ATRAS <= x_cola:
            return f
    return TREN_F1


T_TREN_ESTACION = frame_cuando(x_punta=22.0) / FPS    # la punta entra al andén (x = 22 m)
X_CAMARA = -16.6                                      # x de la cámara junto al tren
T_PUNTA = frame_cuando(x_punta=X_CAMARA) / FPS         # la punta pasa frente a la cámara
T_COLA = frame_cuando(x_cola=X_CAMARA) / FPS           # la cola pasa frente a la cámara


def velocidad_tren(seg):
    """Rapidez del tren (m/s): derivada del smoothstep; 0 al arrancar y al parar, pico de 15 m/s."""
    u = min(max((seg * FPS - TREN_F0) / (TREN_F1 - TREN_F0), 0.0), 1.0)
    return (TREN_X0 - TREN_X1) / ((TREN_F1 - TREN_F0) / FPS) * 6 * u * (1 - u)


def tren_vs_camara(seg):
    """Distancia (m) de la cámara al punto más cercano del tren y panorama (-1 izq .. 1 der)
    en el instante `seg`. El tren es un segmento de 46 m sobre la vía sur que avanza hacia -X."""
    f = seg * FPS
    cam = np.array([np.interp(f, [c[0] for c in CAM], [c[1][i] for c in CAM]) for i in range(3)])
    mira = np.array([np.interp(f, [c[0] for c in CAM], [c[2][i] for c in CAM]) for i in range(3)])
    rig_x = rig_x_en(f)
    x_punta, x_cola = rig_x - TREN_ADELANTE, rig_x + TREN_ATRAS
    px = min(max(cam[0], x_punta), x_cola)           # punto del tren más cercano a la cámara
    v = np.array([px, TREN_Y, TREN_Z]) - cam
    h = (mira - cam)[:2]
    h = h / np.linalg.norm(h)
    cruz = h[0] * v[1] - h[1] * v[0]                 # >0: el tren queda a la izquierda
    pan = float(np.clip(-cruz / max(np.linalg.norm(v[:2]), 1e-6), -1, 1)) * 0.8
    return float(np.linalg.norm(v)), pan


def ganancia_tren(seg):
    d, _ = tren_vs_camara(seg)
    g = min(1.0, (D_REF / d) ** EXP_DIST)
    # el tren se detiene en el frame 859: el sonido muere despacio, ya dentro del túnel
    return g * float(np.interp(seg, [T_TREN_FIN, T_TREN_FIN + 3.5], [1.0, 0.0]))


def reverb(x, seg=2.2, mezcla=0.35):
    """Reverberación de túnel: convolución con ruido de caída exponencial."""
    n = int(seg * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.28 * SR))
    ir = paso_bajo(ir, 3500)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = signal.fftconvolve(x, ir)[: len(x)]
    return (1 - mezcla) * x + mezcla * wet


def evento(x, t0, muestras, ganancia=1.0, pan=0.0):
    """Suma `muestras` (mono) en el instante t0 con panorama pan (-1 izq .. 1 der)."""
    i = int(t0 * SR)
    if i >= len(x[0]):
        return
    seg = muestras[: len(x[0]) - i] * ganancia
    x[0][i:i + len(seg)] += seg * (1 - max(pan, 0))
    x[1][i:i + len(seg)] += seg * (1 + min(pan, 0))


# =============================================================================================
# 1) Drone grave: tres senoidales desafinadas con vibrato lento + retumbo browniano
# =============================================================================================
def drone():
    base = np.zeros(N)
    for f, a, lfo in ((41.2, 1.0, 0.07), (55.0, 0.7, 0.05), (82.4, 0.4, 0.09), (61.7, 0.35, 0.03)):
        fase = 2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * lfo * t)
        base += a * np.sin(fase) * (0.75 + 0.25 * np.sin(2 * np.pi * lfo * 1.7 * t + f))
    base /= np.max(np.abs(base))
    rum = paso_bajo(ruido("marron"), 90) * 2.0
    d = 0.7 * base + 0.3 * rum
    # más presente al inicio (túnel) y al final (vestíbulo)
    return d * env([(0, 0.0), (2.5, 0.8), (40, 0.6), (T_PASILLO, 0.75), (T_VESTIBULO, 0.95), (DUR, 1.0)])


# =============================================================================================
# 2) Viento / aire del túnel: ruido filtrado con barrido lento; fuerte al inicio, se apaga adentro
# =============================================================================================
def viento():
    r = ruido()
    lento = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + 1.0) * np.sin(2 * np.pi * 0.047 * t)
    sub = paso_banda(r, 180, 700) * (0.35 + 0.65 * lento)
    silbo = paso_banda(r, 900, 1400, 3) * (0.1 + 0.4 * lento ** 2)
    v = sub + 0.5 * silbo
    v /= np.max(np.abs(v))
    return v * env([(0, 1.0), (T_TREN_ARRANCA, 0.9), (T_TREN_FIN, 0.4), (T_ESCALERA, 0.2),
                    (T_PASILLO, 0.15), (T_VESTIBULO, 0.25), (DUR, 0.5)])


# =============================================================================================
# 3) Zumbido de las lámparas fluorescentes (red de 60 Hz: 120 Hz y armónicos)
#    Entra al llegar al andén y crece en los pasillos, donde las luminarias son más cercanas
# =============================================================================================
def zumbido():
    z = np.zeros(N)
    for k, a in ((120, 1.0), (240, 0.45), (360, 0.3), (480, 0.12), (600, 0.08)):
        z += a * np.sin(2 * np.pi * k * t + rng.uniform(0, 6.28))
    z *= 0.8 + 0.2 * np.sin(2 * np.pi * 7.3 * t) * np.sin(2 * np.pi * 0.31 * t)  # parpadeo leve
    z /= np.max(np.abs(z))
    return z * env([(0, 0.0), (8, 0.0), (T_TREN_ESTACION - 3, 0.12), (T_TREN_FIN, 0.3),
                    (52, 0.5), (T_PASILLO, 0.9), (T_VESTIBULO, 1.0), (DUR - 4, 0.9), (DUR, 0.4)])


# =============================================================================================
# 4) Tren: se oye venir por el túnel, pasa en el andén (clac-clac de las juntas) y se aleja
# =============================================================================================
def tren(est):
    # Intensidad según la distancia real cámara-tren (control a 50 Hz, suavizado)
    tc = np.arange(0, DUR, 0.02)
    gc = np.array([ganancia_tren(x) if x > TREN_F0 / FPS - 1 else 0.0 for x in tc])
    gc *= np.clip((tc - (TREN_F0 / FPS - 1)) / 3.0, 0, 1)      # entra desde el silencio, de lejos
    inten = np.interp(t, tc, gc)
    r = ruido()
    rodar = paso_banda(r, 60, 260, 3) * 2.2 + paso_banda(r, 700, 2500, 2) * 0.45
    # modulación por las ruedas: ~1.4 ciclos por metro recorrido, así que sigue la rapidez real
    v_t = np.interp(t, tc, [velocidad_tren(x) for x in tc])
    rodar *= 0.75 + 0.25 * np.sin(2 * np.pi * np.cumsum(1.4 * v_t) / SR)
    sonido = rodar * inten
    # clacs de juntas (dos golpes por bogie), con el volumen y el panorama de ese instante
    tt = T_TREN_ARRANCA + 2
    clac_n = int(0.06 * SR)
    clac = rng.standard_normal(clac_n) * np.exp(-np.arange(clac_n) / (0.012 * SR))
    clac = paso_banda(clac, 150, 2200)
    clac /= np.max(np.abs(clac))
    while tt < T_TREN_FIN - 0.5:
        g = ganancia_tren(tt)
        pan = tren_vs_camara(tt)[1]
        for d in (0.0, 0.17):
            evento(est, tt + d, clac, g * 0.6 * (0.8 + 0.4 * rng.random()), pan)
        tt += (0.72 * 10.0 / max(velocidad_tren(tt), 2.0)) * (1 + 0.1 * rng.standard_normal())
    # chirrido corto de frenos metálicos cuando la punta pasa frente a la cámara
    t_ch = T_PUNTA - 1.0
    chirrido_t = np.linspace(0, 2.0, int(2.0 * SR))
    f_ch = 1800 + 500 * np.sin(2 * np.pi * 0.5 * chirrido_t) + 300 * chirrido_t
    ch = np.sin(2 * np.pi * np.cumsum(f_ch) / SR) * np.hanning(len(chirrido_t))
    ch += 0.5 * paso_banda(rng.standard_normal(len(chirrido_t)), 2200, 3200) * np.hanning(len(chirrido_t))
    evento(est, t_ch, ch, 0.05, tren_vs_camara(t_ch + 1.0)[1])
    return sonido


# =============================================================================================
# 5) Gotas con eco (andén y zona del vagón) y golpes lejanos metálicos (pasillos)
# =============================================================================================
def gota():
    n = int(0.25 * SR)
    f = rng.uniform(900, 1900)
    s = np.sin(2 * np.pi * f * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.025 * SR))
    return s / np.max(np.abs(s))


def golpe_lejano():
    n = int(0.9 * SR)
    r = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.09 * SR))
    s = paso_bajo(r, 420) + 0.6 * np.sin(2 * np.pi * rng.uniform(70, 110) * np.arange(n) / SR) \
        * np.exp(-np.arange(n) / (0.2 * SR))
    return s / np.max(np.abs(s))


def eventos_sueltos(est):
    # gotas desde el inicio del andén hasta la escalera; menos en el pasillo
    tt = 3.0
    while tt < DUR - 5:
        zona = np.interp(tt, [0, T_TREN_ARRANCA, T_TREN_FIN, T_ESCALERA, T_PASILLO, DUR],
                         [0.6, 0.4, 1.0, 0.8, 0.4, 0.2])
        if not (T_TREN_ESTACION - 1 < tt < T_TREN_FIN + 1):          # no durante el tren
            evento(est, tt, gota(), VOL_GOTAS * zona * rng.uniform(0.4, 1.0), rng.uniform(-0.8, 0.8))
        tt += rng.uniform(1.6, 5.5)
    # golpes lejanos, irregulares, a partir de la escalera y sobre todo en los pasillos
    for tg in (44.5, 58.0, 71.0, 80.5, 86.0, 93.5, 99.0):
        evento(est, tg, golpe_lejano(), VOL_GOLPES * rng.uniform(0.7, 1.0), rng.uniform(-0.9, 0.9))


# =============================================================================================
# 6) Chisporroteo eléctrico: ráfagas muy cortas cuando se acerca a las luminarias que parpadean
# =============================================================================================
def chispas(est):
    zonas = [(T_PASILLO + 3, T_PASILLO + 5), (T_PASILLO + 12, T_PASILLO + 13.5),
             (T_VESTIBULO + 1, T_VESTIBULO + 3), (DUR - 3.5, DUR - 0.8)]   # la última: cortina
    for a, b in zonas:
        tt = a
        while tt < b:
            n = int(rng.uniform(0.02, 0.09) * SR)
            r = paso_banda(rng.standard_normal(n), 1500, 9000) * np.exp(-np.arange(n) / (0.02 * SR))
            evento(est, tt, r / np.max(np.abs(r)), VOL_CHISPAS * rng.uniform(0.4, 1.0), rng.uniform(-0.5, 0.5))
            tt += rng.uniform(0.04, 0.35)


# =============================================================================================
# 7) Tensión final: tono que sube lento hacia la cortina, y silencio brusco al negro
# =============================================================================================
def tension():
    t0 = T_VESTIBULO
    f = np.interp(t, [t0, DUR - 2], [110, 330])
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    s += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.0145) / SR)       # batido por desafinación
    s /= np.max(np.abs(s))
    return s * env([(0, 0), (t0, 0), (t0 + 6, 0.35), (DUR - 6, 0.8), (DUR - 2, 1.0), (DUR, 0.0)])



# =============================================================================================
# 8) Aire según la escena: el tren empuja una corriente por el túnel (llega antes que él),
#    rachas al pasar la punta y la cola, corriente en escalera y pasillo, silbo de las rejillas
#    de ventilación al pasar junto a ellas y soplo bajo la cortina al final.
# =============================================================================================
def racha(centro, ancho, f0, f1, ganancia, pan=0.0, orden=2):
    """Racha de aire: ruido en banda con envolvente gaussiana, mono con panorama."""
    n = int(ancho * 6 * SR)
    g = np.exp(-0.5 * ((np.arange(n) / SR - ancho * 3) / ancho) ** 2)
    r = paso_banda(rng.standard_normal(n), f0, f1, orden) * g
    return r / np.max(np.abs(r)) * ganancia


def aire(est):
    # a) corriente que empuja el tren: sube mientras se acerca, máximo al pasar la punta,
    #    y al irse la cola jala el aire hacia el túnel (succión que decae despacio)
    t_punta, t_cola = T_PUNTA, T_COLA
    corriente = env([(0, 0), (T_TREN_ARRANCA + 1, 0), (T_TREN_ESTACION, 0.35), (t_punta, 1.0),
                     (t_cola, 0.8), (t_cola + 3.0, 0.3), (T_TREN_FIN + 3.0, 0.0)])
    r = ruido()
    lento = 0.7 + 0.3 * np.sin(2 * np.pi * 0.35 * t) * np.sin(2 * np.pi * 0.13 * t + 1)
    emp = (paso_banda(r, 90, 450, 2) + 0.5 * paso_banda(r, 450, 1400, 2)) * corriente * lento
    emp /= max(np.max(np.abs(emp)), 1e-9)
    est[0] += VOL_AIRE * emp * 0.9
    est[1] += VOL_AIRE * emp * 0.9
    # b) golpes de aire cuando pasan la punta y la cola frente a la cámara
    evento(est, t_punta - 0.9, racha(0, 0.45, 150, 1100, 1.0), VOL_AIRE * 1.1, tren_vs_camara(t_punta)[1])
    evento(est, t_cola - 0.7, racha(0, 0.40, 120, 800, 1.0), VOL_AIRE * 0.8, tren_vs_camara(t_cola)[1])
    # c) corriente de aire en la escalera y el pasillo (el hueco comunica con el andén)
    paso = env([(0, 0), (T_ESCALERA - 6, 0), (T_ESCALERA + 3, 0.5), (T_PASILLO, 0.7),
                (T_VESTIBULO, 0.55), (DUR - 3, 0.7), (DUR, 0.0)])
    rr = ruido()
    sopl = paso_banda(rr, 100, 380, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * t + 2.0)) * paso
    sopl /= max(np.max(np.abs(sopl)), 1e-9)
    est[0] += VOL_AIRE * 0.45 * sopl
    est[1] += VOL_AIRE * 0.45 * np.roll(sopl, 40)
    # d) silbo de las rejillas del techo/muro sur (x = 9, 16, 23, 30) al pasar la cámara
    for tv, f in ((83.0, 1900), (86.3, 2150), (89.7, 1750), (93.3, 2050)):
        evento(est, tv - 3.6, racha(0, 0.6, f * 0.85, f * 1.1, 1.0, orden=3), VOL_AIRE * 0.12, 0.5)
    # e) la luz bajo la cortina: soplo que crece al acercarse, con un silbo fino
    t0 = T_VESTIBULO + 4.0
    n = int((DUR - t0) * SR)
    cr = np.linspace(0, 1, n) ** 1.6
    soplo = paso_banda(rng.standard_normal(n), 500, 1500, 2) * cr
    f_sil = 900 + 120 * np.sin(2 * np.pi * 0.23 * np.arange(n) / SR)
    sil = np.sin(2 * np.pi * np.cumsum(f_sil) / SR) * cr * 0.15 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * np.arange(n) / SR))
    cola = (soplo / np.max(np.abs(soplo)) * 0.5 + sil) * VOL_AIRE * 0.5
    i = int(t0 * SR)
    est[0][i:i + n] += cola[: len(est[0]) - i]
    est[1][i:i + n] += cola[: len(est[1]) - i]


# =============================================================================================
def main():
    est = [np.zeros(N), np.zeros(N)]
    camas = (VOL_DRONE * drone() + VOL_VIENTO * viento() + VOL_ZUMBIDO * zumbido()
             + VOL_TENSION * tension())
    # separación estéreo leve de la cama: ligero retraso entre canales
    est[0] += camas
    est[1] += np.roll(camas, int(0.0006 * SR))
    pista_tren = VOL_TREN * tren(est)
    est[0] += pista_tren * 0.95
    est[1] += pista_tren * 1.05
    aire(est)
    eventos_sueltos(est)
    chispas(est)
    est = [reverb(c, mezcla=0.30) for c in est]

    # fundido de entrada/salida (coinciden con los del video) y normalización a -2 dBFS
    fade = env([(0, 0), (1.0, 1.0), (DUR - 2.0, 1.0), (DUR, 0.0)])
    est = np.stack(est, axis=1) * fade[:, None]
    est *= 10 ** (-2 / 20) / np.max(np.abs(est))
    # filtro pasa-altos suave (< 25 Hz inaudible, solo gasta amplitud)
    sos = signal.butter(2, 25, btype="high", fs=SR, output="sos")
    est = signal.sosfilt(sos, est, axis=0)

    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "renders", "audio_ambiente.wav")
    wavfile.write(ruta, SR, (est * 32767).astype(np.int16))
    rms = np.sqrt(np.mean(est ** 2, axis=0))
    print(f"{ruta}: {DUR:.1f} s, {SR} Hz, RMS {20 * np.log10(rms[0]):.1f} dBFS, "
          f"pico {20 * np.log10(np.max(np.abs(est))):.1f} dBFS")


if __name__ == "__main__":
    main()
