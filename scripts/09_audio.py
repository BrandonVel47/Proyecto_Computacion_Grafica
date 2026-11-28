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
T_TREN_ESTACION, T_TREN_SALE = 568 / FPS, 673 / FPS   # entra / sale del andén
T_TREN_FIN = 859 / FPS
T_ESCALERA, T_PASILLO, T_VESTIBULO = 1440 / FPS, 1840 / FPS, 2300 / FPS

# --- mezcla (0..1) -------------------------------------------------------------------------
VOL_DRONE, VOL_VIENTO, VOL_ZUMBIDO = 0.55, 0.35, 0.16
VOL_TREN, VOL_GOTAS, VOL_GOLPES, VOL_CHISPAS, VOL_TENSION = 0.9, 0.30, 0.45, 0.22, 0.30

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
    # Intensidad: sube desde que arranca (lejos), máximo mientras cruza el andén, se aleja
    inten = env([(0, 0), (T_TREN_ARRANCA - 2, 0), (T_TREN_ARRANCA + 3, 0.12),
                 (T_TREN_ESTACION - 1.0, 0.55), (T_TREN_ESTACION + 1.5, 1.0),
                 (T_TREN_SALE - 0.5, 0.85), (T_TREN_SALE + 3, 0.35), (T_TREN_FIN, 0.0)])
    r = ruido()
    rodar = paso_banda(r, 60, 260, 3) * 2.2 + paso_banda(r, 700, 2500, 2) * 0.45
    # modulación por las ruedas: ~14 Hz (juntas de riel cada ~0.7 m a 10 m/s)
    rodar *= 0.75 + 0.25 * np.sin(2 * np.pi * 14.0 * t)
    sonido = rodar * inten
    # clacs de juntas: más seguidos cuanto más cerca (a 10 m/s, junta cada ~12 m ≈ 1.2 s,
    # dos golpes por bogie)
    tt = T_TREN_ARRANCA + 2
    clac_n = int(0.06 * SR)
    clac = rng.standard_normal(clac_n) * np.exp(-np.arange(clac_n) / (0.012 * SR))
    clac = paso_banda(clac, 150, 2200)
    clac /= np.max(np.abs(clac))
    while tt < T_TREN_FIN - 1:
        g = np.interp(tt, [T_TREN_ARRANCA + 2, T_TREN_ESTACION, T_TREN_SALE, T_TREN_FIN],
                      [0.1, 0.9, 0.7, 0.05])
        pan = np.interp(tt, [T_TREN_ARRANCA, T_TREN_ESTACION, T_TREN_SALE, T_TREN_FIN],
                        [-0.6, 0.0, 0.5, 0.9])
        for d in (0.0, 0.17):
            evento(est, tt + d, clac, g * 0.6 * (0.8 + 0.4 * rng.random()), pan)
        tt += 0.72 + 0.1 * rng.standard_normal()
    # chirrido corto de frenos metálicos al entrar al andén (sin llegar a parar)
    chirrido_t = np.linspace(0, 2.0, int(2.0 * SR))
    f_ch = 1800 + 500 * np.sin(2 * np.pi * 0.5 * chirrido_t) + 300 * chirrido_t
    ch = np.sin(2 * np.pi * np.cumsum(f_ch) / SR) * np.hanning(len(chirrido_t))
    ch += 0.5 * paso_banda(rng.standard_normal(len(chirrido_t)), 2200, 3200) * np.hanning(len(chirrido_t))
    evento(est, T_TREN_ESTACION + 0.2, ch, 0.05)
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
        if not (T_TREN_ESTACION - 1 < tt < T_TREN_SALE + 4):          # no durante el tren
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
