# La Línea Cero — Recorrido Virtual Atmosférico en 3D

Proyecto final de **Graficación por Computadora (Computer Graphics)**
Escuela Superior de Cómputo (ESCOM), IPN · Grupo 6CV3 · Semestre agosto-diciembre 2026
Profesora: Rosaura Palma Orozco

## Descripción general

Recorrido virtual 3D, guiado por cámaras, de una estación del Metro de la Ciudad de México
con ambientación de suspenso y abandono. La estación se modela a partir de fotografías de
referencia reales (andenes laterales, foso de vías, túneles, muros con travertino y banda de
línea, luminarias fluorescentes y letreros colgantes) con técnicas low-poly. El objetivo es
mostrar cómo la iluminación, el sombreado y los materiales PBR cambian la percepción de un
espacio cotidiano.

Técnicas de graficación contempladas: modelado 3D, texturizado PBR (color base, normal,
rugosidad), iluminación (luces fluorescentes parpadeantes), sombras duras, niebla
volumétrica, cámaras y proyección en perspectiva, y animación de cámara sobre una spline.

## Tecnologías utilizadas

- Blender 4.x: modelado, materiales, luces, cámaras y render (EEVEE)
- Python (API `bpy` de Blender): generación procedural de la geometría
- Git / GitHub: control de versiones
- Godot 4: opcional, solo si se migra a recorrido en tiempo real (no implementado)

## Integrante

- Brandon Velázquez Beltrán

## Estructura del repositorio

```
├── LaLineaCero.blend   Escena de Blender
├── scripts/        Scripts bpy numerados en orden de ejecución
├── texturas/       Texturas y LICENCIAS.md (atribución de cada recurso)
├── renders/        Capturas, renders de prueba y video final
├── docs/           Documento técnico, bitácora de IA y fotos de referencia
│   └── referencias/
└── README.md
```

## Instrucciones de instalación

1. Instalar [Blender 4.x](https://www.blender.org/download/).
2. Clonar el repositorio:
   ```
   git clone <URL_DEL_REPOSITORIO>
   ```
3. Descargar las texturas listadas en `texturas/LICENCIAS.md` en la carpeta `texturas/`
   (si se incluyen en el repositorio, no hace falta este paso).

## Instrucciones de ejecución

1. Abrir `LaLineaCero.blend` en Blender.
2. Ir a la pestaña **Scripting**.
3. En el editor de texto, pulsar **Open** (Alt+O) y elegir un script de `scripts/`.
4. Con el cursor sobre el editor de texto, pulsar **Alt+P** (Run Script).
5. Ejecutar los scripts en orden numérico.

| Script | Función | Estado |
|---|---|---|
| `01_geometria_base.py` | Estación: andenes, foso, túneles, muros, techo, vigas, luminarias (geometría) | Listo |

Cada script borra y reconstruye su propia colección, por lo que puede ejecutarse varias veces.

## Evidencias visuales

Pendiente: capturas y renders en `renders/`.

## Créditos, licencias y uso de IA

- Atribución de texturas y recursos de terceros: [`texturas/LICENCIAS.md`](texturas/LICENCIAS.md)
- Uso de herramientas de IA: [`docs/uso_ia.md`](docs/uso_ia.md)
- Fotos de referencia: [`docs/referencias/FUENTES.md`](docs/referencias/FUENTES.md)
