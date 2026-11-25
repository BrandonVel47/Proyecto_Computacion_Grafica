"""03_materiales.py
Asigna materiales PBR procedurales a cada objeto según el prefijo de su nombre.
Requiere 01 y 02. Las luces (Luminaria_*, Lampara_*) las resuelve 04_iluminacion.py.
"""
import sys
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
}

# (prefijos del nombre, clave del material). Gana la primera regla que coincida.
REGLAS = [
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
OMITIR = ("Luminaria", "Lampara")   # los materiales de luz los asigna 04_iluminacion.py

usados = Counter()
for obj in bpy.data.objects:
    if obj.type != 'MESH' or obj.name.startswith(OMITIR):
        continue
    clave = next((k for pref, k in REGLAS if obj.name.startswith(pref)), "concreto")
    obj.data.materials.clear()
    obj.data.materials.append(M[clave])
    usados[clave] += 1

print("Materiales asignados:", dict(usados))
