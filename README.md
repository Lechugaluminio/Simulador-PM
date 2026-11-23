# Croquis PM

Tablero de mapa para el **puesto de mando** de bomberos: reemplaza el croquis de la pizarra por un mapa satelital donde los carros se mueven como piezas de un juego de mesa.

**Abrir:** https://lechugaluminio.github.io/Simulador-PM/

## Qué hace

- Busca la dirección o el cruce del despacho (ej: `Las Enredaderas & Avenida Fermín Vivaceta, Independencia`) y centra el mapa.
- Satélite (Esri) con nombres de calles y numeración, o mapa de calles (OpenStreetMap / CARTO). Se puede atenuar para que las piezas resalten.
- Croquis: estructura con lados A–D automáticos (y botón **A abajo** para orientar como la pizarra), área con fuego achurada, zona de colapso, líneas con flecha, trazos, foco, PM (círculo amarillo, estándar SCI), grifos, piscinas, pastilla de MAYDAY y textos.
- Carros: se pegan los códigos despachados, se arrastran al mapa al llegar (queda la hora) y se les asigna estado, función, lado y nota. Color por tipo (B, BX, BM, BT, Q, M, R, RX, H, Z, K, K-3, X, S), editable en *Ajustes*.
- Mismas convenciones que la pizarra: **✕** = carro sin función o que no puede cumplirla, **◯** = carro retirándose.
- **Grifos automáticos:** se cargan desde el mapa público *Ubicación de grifos* de Aguas Andinas (Aguas Andinas, Aguas Cordillera y Aguas Manquehue) y se guardan en el navegador; se actualizan solos cada semana o desde *Menú → Actualizar grifos*.
- Modo presentación para la pantalla grande, contador de tiempo del incidente, resumen copiable para la bitácora, Street View.
- Se usa con mouse; el teclado es opcional (atajos en *Menú → Ayuda*).

## Datos

Todo se guarda **solo en el navegador del equipo** (localStorage). Nada del incidente se sube a GitHub. Para respaldar, *Menú → Exportar croquis (.json)*.

Necesita internet para el mapa y la búsqueda (Nominatim / Overpass de OpenStreetMap).

## Créditos

Imágenes y nombres de calles © Esri · Calles © OpenStreetMap / CARTO · Grifos: Aguas Andinas · Mapa: MapLibre GL JS.
