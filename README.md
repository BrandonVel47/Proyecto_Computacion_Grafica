# La Línea Cero — Recorrido Virtual Atmosférico en 3D

Proyecto final de **Graficación por Computadora (Computer Graphics)**
Escuela Superior de Cómputo (ESCOM), IPN · Grupo 6CV3 · Semestre agosto-diciembre 2026
Profesora: Rosaura Palma Orozco

## Descripción general

Recorrido virtual 3D, guiado por cámaras, de una estación del Metro de la Ciudad de México
con ambientación de suspenso y abandono. La estación se modela a partir de fotografías de
referencia reales (andenes laterales, foso de vías, túneles, muros con travertino y banda de
línea, luminarias fluorescentes y letreros colgantes) con técnicas low-poly. El recorrido
sale del túnel, ve pasar un tren que cruza la estación sin detenerse, sube por la escalera a
un pasillo con una correspondencia tapiada y termina en un vestíbulo, frente a la cortina
de la salida por donde se cuela la luz del día. El objetivo es mostrar cómo la iluminación,
el sombreado y los materiales PBR cambian la percepción de un espacio cotidiano.

Técnicas de graficación contempladas: modelado 3D, texturizado PBR (color base, normal,
rugosidad), iluminación (luces fluorescentes parpadeantes), sombras duras, niebla
volumétrica, reflejos, cámaras y proyección en perspectiva, animación de cámara sobre una
spline (por longitud de arco) y animación jerárquica del tren (objetos emparentados a un
empty).

## Tecnologías utilizadas

- Blender 5.0: modelado, materiales, luces, cámaras y render (EEVEE)
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

1. Instalar [Blender 5.0](https://www.blender.org/download/) o posterior.
2. Clonar el repositorio:
   ```
   git clone <URL_DEL_REPOSITORIO>
   ```
3. Descargar las texturas listadas en `texturas/LICENCIAS.md` en la carpeta `texturas/`
   (si se incluyen en el repositorio, no hace falta este paso).

## Instrucciones de ejecución

1. Abrir `LaLineaCero.blend` en Blender (desde la raíz del repositorio).
2. Ir a la pestaña **Scripting**.
3. En el editor de texto, pulsar **Open** (Alt+O) y elegir `scripts/00_construir_todo.py`.
4. Con el cursor sobre el editor de texto, pulsar **Alt+P** (Run Script). Construye toda la
   escena en unos segundos ejecutando los scripts 01 a 08 en orden.
5. Para renderizar el recorrido: **Render → Render Animation** (los frames se guardan en
   `renders/frames/`; si se interrumpe, al relanzarlo continúa donde se quedó).

Cada script también se puede abrir y ejecutar por separado, en orden numérico.

| Script | Función |
|---|---|
| `00_construir_todo.py` | Ejecuta los scripts 01 a 08 en orden |
| `01_geometria_base.py` | Estación: andenes, foso, vías, túneles, muros, techo, vigas, nicho de acceso y luminarias (geometría) |
| `02_vagon_y_accesos.py` | Vagón naranja estacionado (con bogies y ruedas) y torniquetes |
| `03_pasillos.py` | Escalera de dos tramos, pasillo con correspondencia tapiada y vestíbulo con taquilla, reloj y cortina de salida |
| `04_detalles.py` | Bancas, botes, gabinetes, cámaras, señalización con texto, anuncios, semáforos, mapa de la red, charcos, basura, plafón caído y luminaria desprendida |
| `05_tren.py` | Tren de 3 vagones que cruza la estación por la vía sur (animación jerárquica con un empty) |
| `06_materiales.py` | Materiales PBR procedurales (concreto, mármol, travertino, azulejo, terrazo, lámina, madera, agua, metal oxidado, pintura) asignados por nombre |
| `07_iluminacion.py` | Luminarias fijas, parpadeantes y apagadas, semáforos, luz del día bajo la cortina, niebla volumétrica, mundo oscuro y ajustes de EEVEE |
| `08_camara.py` | Cámara sobre spline con punto de mira, avance por longitud de arco, distancia focal animada y marcadores de escena |

Cada script borra y reconstruye su propia colección, por lo que puede ejecutarse varias veces.
`layout.py` (medidas, textos de señalización y tiempos de la animación), `lib_bpy.py` (funciones de modelado) y `lib_materiales.py` (constructor de materiales) son módulos compartidos: no se ejecutan solos, los importan los scripts. Hay que abrir el `.blend` desde la raíz del repositorio para que encuentren la carpeta `scripts/`.

## Evidencias visuales

Pendiente: capturas y renders en `renders/`.

## Créditos, licencias y uso de IA

- Atribución de texturas y recursos de terceros: [`texturas/LICENCIAS.md`](texturas/LICENCIAS.md)
- Uso de herramientas de IA: [`docs/uso_ia.md`](docs/uso_ia.md)
- Fotos de referencia: [`docs/referencias/FUENTES.md`](docs/referencias/FUENTES.md)
