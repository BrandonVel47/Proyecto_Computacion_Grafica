"""00_construir_todo.py
Construye la escena completa ejecutando los scripts 01 a 08 en orden.
Uso: abrir LaLineaCero.blend desde la raíz del repositorio, abrir este archivo en el
editor de texto de Blender (pestaña Scripting) y pulsar Alt+P.
Cada script también se puede ejecutar solo, siempre que los anteriores ya hayan corrido.
"""
import os
import time
import runpy

import bpy

ORDEN = [
    "01_geometria_base.py",    # estación: andenes, vías, túneles, muros, techo, luminarias
    "02_vagon_y_accesos.py",   # vagón estacionado y torniquetes
    "03_pasillos.py",          # escalera, pasillo tapiado y vestíbulo con salida
    "04_detalles.py",          # bancas, señalización, charcos, basura, mapa, semáforos
    "05_tren.py",              # tren de 3 vagones que cruza la estación
    "06_materiales.py",        # materiales PBR procedurales por nombre de objeto
    "07_iluminacion.py",       # luces, parpadeo, niebla y ajustes de EEVEE
    "08_camara.py",            # recorrido de cámara, lentes y marcadores
]

carpeta = bpy.path.abspath("//scripts")
if not os.path.isdir(carpeta):
    raise RuntimeError("Abre el .blend desde la raíz del repositorio (no encuentro scripts/)")
inicio = time.time()
for nombre in ORDEN:
    t = time.time()
    runpy.run_path(os.path.join(carpeta, nombre), run_name="__main__")
    print(f"  {nombre}: {time.time() - t:.1f} s")
print(f"Escena completa en {time.time() - inicio:.1f} s")
