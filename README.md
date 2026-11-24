# Croquis PM · tablero del puesto de mando

**La pizarra queda libre para lo que solo cabe en la pizarra.** Croquis PM reemplaza el croquis dibujado a mano en el puesto de mando de bomberos por un mapa satelital. Los carros despachados se mueven como piezas de un juego de mesa, con su estado, función y lado. La pantalla grande del PM muestra la escena completa, y la pizarra física queda para el PAR y los detalles de un mayday.

- **Aplicación publicada:** https://lechugaluminio.github.io/Simulador-PM/
- **Video (60 s):** [docs/video.mp4](docs/video.mp4)
- Proyecto personal de Daniel Victoriano · Diseño Industrial UDP. Pensado para el puesto de mando de bomberos (K-3, puesto de mando móvil).

![Croquis PM en uso: estructura con lados A–D, área con fuego, líneas, carros con sus estados, RIT, PC, zona de espera, ACV y MAYDAY](docs/demo.jpg)

*Prueba de funcionamiento: incidente en Las Enredaderas con Av. Fermín Vivaceta, Independencia.*

[![Video de demostración (60 s): clic para verlo](docs/video-portada.jpg)](docs/video.mp4)

*Video de demostración (60 s). Clic en la imagen para verlo.*

---

## 1. Concepto

En un incendio, el oficial del puesto de mando dibuja en una pizarra un croquis con la cuadra afectada, los lados A, B, C y D, el fuego y cada carro que llega. Ese dibujo se borra y se rehace a cada cambio, ocupa la pizarra que se necesita para la contabilidad de personal y nadie más lo ve.

Croquis PM propone que **el croquis sea un tablero vivo**:

- **El mapa es real.** Se busca la dirección del despacho y aparecen la imagen satelital, los nombres de calles, la numeración y los **grifos** publicados por Aguas Andinas.
- **Los carros son piezas.** Se pegan los códigos del despacho y se arrastran al mapa cuando llegan. Cada pieza lleva su color por tipo, su estado, su función y la salida a la que pertenece.
- **Las convenciones son las de siempre.** ✕ = carro sin función o que no puede cumplirla; ◯ = carro retirándose; símbolos SCI para el Puesto de Comando, la zona de espera y el ACV. No hay que aprender un lenguaje nuevo.
- **La información no sale del equipo.** Todo vive en el navegador del computador del PM. No pasa por servidores ajenos ni por grupos de mensajería durante la emergencia.

**Qué queremos lograr:** que todos en el puesto de mando lean de un vistazo dónde está cada recurso y qué está haciendo, y que el oficial deje de redibujar para dedicarse a decidir.

---

## 2. Cómo se usa

1. **Buscar el lugar.** Escribir la dirección o el cruce del despacho (por ejemplo `Las Enredaderas & Avenida Fermín Vivaceta, Independencia`) y pulsar *Buscar*.
2. **Dibujar la estructura.** Herramienta *Estructura*: clic en las esquinas. Los lados **A–D** se ponen solos; el botón **A abajo** orienta el mapa como en la pizarra.
3. **Marcar el fuego.** *Área fuego* (achurada), *Colapso*, *Foco*.
4. **Cargar el despacho.** Elegir la salida (despacho inicial, 1ª, 2ª o 3ª alarma), pegar los códigos (`B-21 BX-22 Q-7 RX-6…`) y pulsar *Agregar*. Quedan en **Por ubicar**.
5. **Ubicar los carros al llegar.** Arrastrarlos al mapa: queda registrada la hora de llegada. Clic en la pieza para asignar estado, función, lado y nota.
6. **Instalaciones y avisos.** PC, zona de espera (E), ACV, RIT con la compañía a cargo y MAYDAY.
7. **Mostrar.** *Presentación* para la pantalla grande del PM, o *Imagen* para copiar o descargar el croquis.
8. **Llevar a terreno.** Un ayudante escanea el QR y se lleva una copia editable al celular. Al volver, *Cambios* muestra qué se modificó.

---

## 3. Funcionamiento

### 3.1 Carros (piezas)

| Código | Tipo | Color de la pieza |
|---|---|---|
| `B` | Bomba | rojo |
| `BX` | Bomba 4x4 | naranja |
| `BM` | Bomba con escala telescópica | rojo oscuro |
| `BT` | Bomba tanker | frambuesa |
| `Q` | Porta escala | amarillo |
| `M` | Escala mecánica | café |
| `R` / `RX` | Rescate / rescate especializado | azul / celeste |
| `H` | Hazmat | verde |
| `Z` | Camión cisterna | turquesa |
| `K` / `K-3` | Comandancia / puesto de mando móvil | morado / amarillo |
| `X` | Telecomunicaciones, logística e investigación de incendios | gris |
| `S` | Ambulancia | blanco |

- **Carros de apoyo de otros cuerpos:** se aceptan con sufijo (`Z-3Ñ` = 3ª Cía. de Ñuñoa, `B-4QN` = Quinta Normal).
- **Salida:** cada pieza indica si llegó en el **despacho inicial, 1ª, 2ª o 3ª alarma**.
- **Colores y funciones:** se editan en *Ajustes*.

### 3.2 Estados

| Estado | Cómo se ve | Equivale en la pizarra a |
|---|---|---|
| Sin función | Pieza con **✕** | Carro con X |
| Trabajando | Pieza limpia, con su función (ataque, corte de propagación, abastecimiento, búsqueda y rescate, ventilación…) | Carro con su tarea anotada |
| No puede cumplir | Pieza con **✕** | Carro con X |
| Retirándose | Pieza con **◯** | Carro en círculo |
| Retirado | Pieza gris y tachada (se puede ocultar del mapa en *Ajustes*) | Carro borrado |

La barra superior resume la escena: cuántos están en escena, trabajando, sin función, retirándose y por llegar.

### 3.3 Herramientas del croquis

| Herramienta | Tecla | Qué dibuja |
|---|---|---|
| Mover | `V` | Seleccionar y mover piezas y marcadores |
| Estructura | `E` | Polígono del edificio con lados A–D automáticos |
| Área fuego | `F` | Zona con fuego, achurada en rojo |
| Colapso | `C` | Zona de colapso |
| Línea | `L` | Línea de ataque con flecha (color a elegir) |
| Trazo | `K` | Trazo punteado libre |
| Foco | `1` | Llama en el punto de origen |
| Puesto de Comando | `2` | Rectángulo naranja con **PC** (estándar SCI) |
| Grifo | `3` | Grifo manual (además de los automáticos) |
| Piscina | `4` | Piscina de abastecimiento |
| MAYDAY | `5` | Pastilla roja de MAYDAY en el lugar del bombero |
| RIT | `6` | Pastilla verde con la compañía a cargo |
| Zona de espera | `7` | Círculo amarillo con **E** |
| ACV | `8` | Círculo amarillo: área de concentración de víctimas |
| Texto | `T` | Rótulo libre |

### 3.4 Mapa y datos externos

| Fuente | Qué aporta | Cuándo se consulta |
|---|---|---|
| Esri World Imagery | Imagen satelital | Al mover el mapa |
| Esri World Street Map | Mapa de calles (alternativa al satélite) | Al elegir *Calles* |
| Esri World Transportation | Nombres de calles y numeración sobre el satélite | Con *Nombres* activado |
| Nominatim (OpenStreetMap) | Búsqueda de direcciones | Al pulsar *Buscar* |
| Overpass (OpenStreetMap) | Ubicación exacta de un **cruce** de calles | Al buscar un cruce `Calle A & Calle B` |
| Aguas Andinas · *Ubicación de grifos* | Grifos de Aguas Andinas, Aguas Cordillera y Aguas Manquehue | Una vez por semana o desde *Menú → Actualizar grifos*; quedan guardados en el navegador |

El control *Atenuar* oscurece el mapa para que las piezas resalten.

### 3.5 Compartir y respaldar

| Función | Qué hace |
|---|---|
| **Presentación** (`P`) | Vista limpia para la pantalla grande del PM |
| **Imagen** | Croquis en alta resolución (doble de la pantalla) con encabezado del incidente, hora y resumen; se copia para pegar o se descarga en `.jpg` |
| **Copia de terreno** | QR con una copia editable para el celular. Los datos viajan dentro del QR, en la parte `#` del enlace, que el navegador no envía a ningún servidor. La copia nunca modifica el croquis principal |
| **Cambios** | Al volver de terreno, lista lo modificado y muestra con líneas punteadas las posiciones originales |
| **Exportar croquis (.json)** | Respaldo completo del incidente |
| **Modo sol** (`S`) | Alto contraste para uso al exterior: piezas más grandes, líneas más gruesas y mapa con más contraste |

En celulares y tablets verticales, la lista de carros se abre como panel deslizable y las herramientas quedan en una barra inferior.

---

## 4. Créditos y autoría

| Elemento | Autor | Licencia / nota |
|---|---|---|
| Concepto, convenciones de la pizarra y decisiones de diseño | Daniel Victoriano | Proyecto propio, basado en su práctica en el puesto de mando |
| Código de la aplicación | Daniel Victoriano con asistencia de [Claude](https://anthropic.com) (Anthropic) | HTML, CSS y JavaScript en un solo archivo |
| Motor de mapa | [MapLibre GL JS](https://maplibre.org/) 4.7.1 | Licencia BSD-3-Clause |
| Códigos QR | [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4, Kazuhiko Arase | Licencia MIT |
| Imagen satelital, mapa de calles y nombres | © Esri y sus proveedores | Servicios de teselas de ArcGIS Online, con atribución en el mapa |
| Búsqueda de direcciones y cruces | © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright) (Nominatim, Overpass) | Datos ODbL |
| Grifos | Aguas Andinas · [Ubicación de grifos](https://www.aguasandinas.cl/web/aguasandinas/ubicacion-de-grifos) | Mapa público de la empresa |
| Íconos y símbolos (piezas, llama, PC, E, ACV, RIT, MAYDAY) | Dibujados con código (SVG y canvas) | Símbolos según el estándar SCI |

---

## 5. Reflexión

Este proyecto busca mejorar la visión de la escena desde el puesto de mando, la claridad de la información y su transmisión mediante funciones cooperativas.

No pretende ser un sistema panóptico. Se limita a las funciones que hoy se llevan a mano en la pizarra y las traslada al soporte digital, integrando la información de mapas y grifos.

Al ser de código abierto y funcionar en el navegador, busca evitar barreras de entrada y ser lo más accesible posible.

---

## 6. Ejecutar

### Usar la aplicación

- **En línea:** https://lechugaluminio.github.io/Simulador-PM/ (Chrome o Edge, en el computador del PM).
- **Pantalla grande:** botón *Presentación* (`P`) y pantalla completa.
- Se usa con **mouse**; el teclado es opcional.

### Atajos de teclado

| Tecla | Acción |
|---|---|
| `V` | Mover / seleccionar |
| `E` `F` `C` | Estructura / Área fuego / Colapso |
| `L` `K` | Línea de ataque / Trazo |
| `1` … `8` | Foco, PC, Grifo, Piscina, MAYDAY, RIT, Zona de espera, ACV |
| `T` | Texto |
| `A` | Orientar con el lado A abajo |
| `N` | Norte arriba |
| `Z` | Encuadrar todo |
| `S` | Modo sol |
| `P` | Modo presentación |
| `Enter` / `Backspace` | Terminar el dibujo / quitar el último punto |
| `Supr` | Borrar lo seleccionado |
| `Ctrl+Z` | Deshacer |
| `Esc` | Cancelar la herramienta |
| `H` o `?` | Ayuda |

### Estructura del repositorio

```
index.html   ← la aplicación completa (lo que publica GitHub Pages)
docs/        ← capturas y video de este README
.nojekyll    ← GitHub Pages sirve los archivos tal cual
```

**GitHub Pages:** *Settings → Pages → Deploy from a branch*, rama `main`, carpeta `/ (root)`.

---

## Datos y privacidad

- Todo se guarda **solo en el navegador del equipo** (localStorage). Nada del incidente se sube a GitHub ni a otro servidor propio.
- Para respaldar: *Menú → Exportar croquis (.json)*.
- La aplicación sí consulta servicios públicos para el mapa, la búsqueda y los grifos (sección 3.4). Esas consultas llevan la zona del mapa o el texto buscado, no el croquis.
