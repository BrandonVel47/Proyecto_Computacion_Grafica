# Uso de Herramientas de IA

Bitácora de uso de IA del proyecto *La Línea Cero*. Se actualiza en cada sesión de trabajo.
Todo componente apoyado con IA fue revisado, ejecutado y adaptado por el autor, quien debe
poder explicarlo técnicamente.

| Fecha | Herramienta | Para qué se usó | Contribución original del autor |
|---|---|---|---|
| 2026-11-23 | Claude (Anthropic) | Plan por fases para los días disponibles, propuesta inicial de layout y primer script de geometría en `bpy` | Tema, propuesta del proyecto y objetivos; ejecución y revisión del script en Blender |
| 2026-11-24 | Claude (Anthropic) | Reescritura del script de geometría (v2) para seguir el diseño de las fotos de referencia | Selección de las fotos de referencia y decisión de rediseñar la estación según ellas; ejecución y revisión del resultado |
| 2026-11-25 | Claude (Anthropic) | Reorganización de los scripts en módulos compartidos (`layout.py`, `lib_bpy.py`) y script 02 del vagón, torniquetes y escalera; prueba automática de los scripts sin interfaz | Referencias fotográficas, revisión de las capturas del modelo en Blender y decisiones de diseño |
| 2026-11-25 | Claude (Anthropic) | Scripts 03 (materiales procedurales) y 04 (iluminación, parpadeo y niebla), ruedas del vagón; pruebas con renders de verificación | Observación del defecto del vagón flotando, selección de referencias y revisión de resultados en Blender |
| 2026-11-25 | Claude (Anthropic) | Script 05 del recorrido de cámara (spline, punto de mira, lentes y marcadores) y ajuste de sombras de EEVEE tras el aviso de memoria de sombras | Reporte de los errores en Blender (sin cámara y buffer de sombras), revisión del resultado y decisiones del recorrido |
| 2026-11-26 | Claude (Anthropic) | Ampliación del escenario: scripts 03 (escalera, pasillo y vestíbulo), 04 (detalles y señalización) y 05 (tren en movimiento); reorganización de materiales, iluminación y cámara como 06 a 08 (cámara por longitud de arco) y script 00 que construye todo; pruebas con renders de verificación | Idea de extender la estación con pasillos y un tren en movimiento, decisión de mejorar el modelo antes del render final y revisión del resultado en Blender |

> Completar y ajustar cada fila con lo que realmente hizo el autor.
