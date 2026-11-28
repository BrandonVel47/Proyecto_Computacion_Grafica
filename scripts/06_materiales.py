"""06_materiales.py
Asigna materiales PBR procedurales a cada objeto según el prefijo de su nombre.
Requiere 01 a 05. Las luces (Luminaria_*, Lampara_*) las resuelve 07_iluminacion.py y los
objetos marcados con la propiedad "mat_propio" (líneas del mapa) conservan el suyo.
"""
import sys
import re
import importlib
from collections import Counter

import bpy

_scripts_dir = bpy.path.abspath("//scripts")
if _scripts_dir not in sys.path:
    sys.path.append(_scripts_dir)
import lib_materiales as lm
importlib.reload(lm)

# ---------- Catálogo de materiales ----------
M = {
    # estación
    "concreto":      lm.concreto("Concreto_Sucio"),
    "concreto_osc":  lm.concreto("Concreto_Oscuro", base=(0.12, 0.12, 0.12)),
    "concreto_hum":  lm.concreto("Concreto_Humedo", base=(0.14, 0.14, 0.15), wet=True),
    "marmol":        lm.marmol("Marmol_Pulido"),
    "travertino":    lm.travertino("Travertino"),
    "balasto":       lm.balasto("Balasto"),
    "metal":         lm.metal_oxidado("Metal_Oxidado"),
    "acero":         lm.acero("Acero_Cepillado"),
    "negro":         lm.mate("Negro_Mate", (0.015, 0.015, 0.015)),
    "banda":         lm.pintura("Banda_Azul", (0.03, 0.14, 0.5), rough=0.45),
    "amarillo":      lm.pintura("Pintura_Amarilla", (0.85, 0.6, 0.02), rough=0.5, wear_at=0.48),
    "naranja_panel": lm.pintura("Panel_Naranja", (0.8, 0.27, 0.04), rough=0.5, wear_at=0.64),
    "vagon":         lm.pintura("Vagon_Naranja", (0.75, 0.2, 0.03), rough=0.25, wear_at=0.64),
    "vagon_techo":   lm.mate("Vagon_Techo_Gris", (0.45, 0.45, 0.43), 0.5),
    "letrero":       lm.mate("Letrero_Verde", (0.03, 0.07, 0.04), 0.4),
    "cristal":       lm.cristal_interior("Cristal_Interior"),
    "faro":          lm.emision("Faro_Luz", (1.0, 0.9, 0.7), 8.0),
    # pasillos, vestíbulo y detalles
    "azulejo":       lm.azulejo("Azulejo"),
    "terrazo":       lm.terrazo("Terrazo"),
    "muro_pas":      lm.pintura("Aplanado_Crema", (0.42, 0.4, 0.34), rough=0.75, wear_at=0.6),
    "banda_naranja": lm.pintura("Banda_Naranja", (0.8, 0.28, 0.04), rough=0.4, wear_at=0.62),
    "lamina":        lm.lamina("Lamina_Cortina"),
    "madera":        lm.madera("Madera_Vieja"),
    "agua":          lm.agua("Agua_Charco"),
    "cartel":        lm.cartel("Cartel_Roto"),
    "papel":         lm.mate("Papel", (0.5, 0.48, 0.42), 0.9),
    "carton":        lm.mate("Carton", (0.3, 0.2, 0.1), 0.9),
    "rojo":          lm.pintura("Pintura_Roja", (0.55, 0.03, 0.02), rough=0.4, wear_at=0.66),
    "blanco":        lm.mate("Blanco_Sucio", (0.62, 0.6, 0.55), 0.5),
    "verde_salida":  lm.emision("Salida_Verde", (0.1, 1.0, 0.35), 4.0),
    "texto":         lm.emision("Texto_Blanco", (0.9, 0.92, 0.95), 0.8),
    "texto_rojo":    lm.pintura("Pintura_Aerosol_Roja", (0.6, 0.02, 0.015), rough=0.7, wear_at=0.75),
    "semaforo":      lm.emision("Semaforo_Rojo", (1.0, 0.04, 0.02), 12.0),
    "verde_osc":     lm.mate("Verde_Apagado", (0.01, 0.05, 0.02), 0.3),
    "taquilla":      lm.cristal_luz("Cristal_Taquilla", (1.0, 0.65, 0.3), 0.05),
    "exterior":      lm.emision("Luz_Dia", (0.8, 0.88, 1.0), 3.0),
    # tren en movimiento
    "cristal_tren":  lm.cristal_tren("Cristal_Tren_Encendido"),
    "faro_rojo":     lm.emision("Calavera_Roja", (1.0, 0.04, 0.02), 6.0),
}

# (prefijos del nombre, clave del material). Gana la primera regla que coincida, así que
# los prefijos más específicos van antes que los generales.
REGLAS = [
    # --- tren en movimiento (nombre completo) ---
    (("Tren_FaroDel",), "faro"),
    (("Tren_FaroTras",), "faro_rojo"),
    (("Tren_Fuelle",), "negro"),
    # --- pasillos, vestíbulo y detalles ---
    (("Azulejo", "Columna"), "azulejo"),
    (("Piso_Pas", "Escalon", "Descanso"), "terrazo"),
    (("Muro_Pas",), "muro_pas"),
    (("Salida_Recinto_Fondo",), "exterior"),
    (("Techo_Pas", "Panel_Caido", "Salida_Recinto"), "concreto"),
    (("Banda_Pas",), "banda_naranja"),
    (("Zoclo_Pas", "Nariz_Escalon", "Hueco_Techo", "Pasaje", "Rejilla_Vent", "Cable_Colgante",
      "Camara_CCTV", "Semaforo_Caja", "Reloj_Caja", "Reloj_Marca", "Reloj_Manecilla",
      "Marco_Anuncio", "Marco_Mapa", "Cortina_Guia", "Cortina_Caja", "Bote_Tapa",
      "TextoNegro"), "negro"),
    (("Pasamanos", "Poste_Pasamanos", "Taquilla_Mostrador"), "acero"),
    (("Banca", "Bote_Basura", "Puerta_Servicio", "Clavo"), "metal"),
    (("Cortina",), "lamina"),
    (("Tablon",), "madera"),
    (("Charco",), "agua"),
    (("Cartel",), "cartel"),
    (("Papel",), "papel"),
    (("Caja_Carton",), "carton"),
    (("Gabinete_Vidrio",), "cristal"),
    (("Gabinete", "Letrero_Rojo"), "rojo"),
    (("Reloj_Cara", "Mapa_Panel", "Mapa_Estacion"), "blanco"),
    (("Salida_Caja",), "verde_salida"),
    (("TextoRojo",), "texto_rojo"),
    (("Texto",), "texto"),
    (("Semaforo_Rojo",), "semaforo"),
    (("Semaforo_Verde",), "verde_osc"),
    (("Taquilla_Cristal",), "taquilla"),
    (("Taquilla_Cuerpo",), "naranja_panel"),
    (("Letrero_Pasillo", "Letrero_Taquilla", "Letrero_Caido"), "letrero"),
    # --- estación ---
    (("Piso_Marmol", "Acceso_Piso"), "marmol"),
    (("Travertino",), "travertino"),
    (("Banda_Linea", "Rotulo_Estacion"), "banda"),
    (("Franja_Amarilla",), "amarillo"),
    (("Borde_Gris",), "concreto_osc"),
    (("Foso_Concreto",), "concreto_hum"),
    (("Balasto",), "balasto"),
    (("Riel", "Tuberia", "Cable", "Varilla"), "metal"),
    (("Torniquete_Cuerpo", "Torniquete_Brazo"), "acero"),
    (("Zoclo", "Rejillas_Foso", "Ventila", "Vagon_Faldon", "Ventana_Marco",
      "Puerta_Marco", "Torniquete_Lector", "Vagon_Rueda"), "negro"),
    (("Vagon_Carroceria",), "vagon"),
    (("Vagon_Techo",), "vagon_techo"),
    (("Puerta_Cristal", "Ventana_Cristal", "Parabrisas"), "cristal"),
    (("Faro",), "faro"),
    (("Letrero_Colgante",), "letrero"),
    (("Nicho_Fondo", "Acceso_Muro", "Acceso_Fondo", "Acceso_Techo", "Acceso_Dintel"),
     "naranja_panel"),
]
OMITIR = ("Luminaria", "Lampara")   # los materiales de luz los asigna 07_iluminacion.py
VENTANAS = ("Puerta_Cristal", "Ventana_Cristal")
PREFIJO_TREN = re.compile(r"^Tren\d+_")   # "Tren1_Vagon_Carroceria" -> "Vagon_Carroceria"


def material_para(nombre):
    """Clave del material para un objeto. Las copias del tren usan las reglas del vagón,
    salvo las ventanas, que en el tren en marcha van encendidas."""
    base = PREFIJO_TREN.sub("", nombre)
    if base != nombre and base.startswith(VENTANAS):
        return "cristal_tren"
    return next((k for pref, k in REGLAS if base.startswith(pref)), "concreto")


usados = Counter()
for obj in bpy.data.objects:
    if obj.type != 'MESH' or obj.name.startswith(OMITIR) or obj.get("mat_propio"):
        continue
    clave = material_para(obj.name)
    obj.data.materials.clear()
    obj.data.materials.append(M[clave])
    usados[clave] += 1

print("Materiales asignados:", dict(usados))
