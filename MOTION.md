# MOTION.md: cómo se ve y se mueve CAEIA

Leelo entero antes de diseñar o animar cualquier cosa. El **qué se dice** está en `brand.md`.
Marcas:
- **[brief]:** sale del brief de marca, es regla.
- **[propuesta]:** valor inicial de Claude, Axel lo puede cambiar.
- **PREGUNTAR A AXEL:** falta el dato. No se inventa.

## 1. Colores (solo estos hex)

### Identidad de marketing (overlays, titulares, cierres) [brief]

| Token CSS | Hex | Para qué |
|---|---|---|
| `--caeia-bg` | `#0a0e1a` | fondo oscuro, el de casi todas las piezas |
| `--caeia-cae` | `#0ea5e9` | "CAE" del wordmark; acento principal, una palabra clave por línea |
| `--caeia-ia` | `#8b5cf6` | "IA" del wordmark; segundo acento, nunca en la misma palabra que el azul |
| `--caeia-cae-claro` | `#1d7fc4` | el azul sobre fondos claros |
| `--caeia-ia-claro` | `#7c4fd6` | el violeta sobre fondos claros |
| `--caeia-texto` | `#ffffff` | texto sobre `--caeia-bg` [propuesta: PREGUNTAR A AXEL si prefiere otro blanco] |

- Fondo claro de marketing: **PREGUNTAR A AXEL**. Hasta que lo defina, las piezas son oscuras.
- Wordmark: "CAE" en `#0ea5e9` + "IA" en `#8b5cf6`, **split literal**. Nunca degradé, nunca un solo color.

### UI real de la app (solo dentro de capturas o mockups de CAEIA) [brief]

| Token CSS | Hex | Para qué |
|---|---|---|
| `--app-bg` | `#0f0b1e` | fondo de la app (tema oscuro por defecto) |
| `--app-texto` | `#ddd6fe` | texto de la app |
| `--app-acento` | `#8b5cf6` | acento violeta |
| `--app-acento-hondo` | `#6d28d9` | acento violeta profundo |

La app es **glassmorphism violeta**: vidrio esmerilado, blur, bordes sutiles. Si se recrea una pantalla, se mide y se muestrea desde la captura real, no se inventa.

## 2. Tipografía

- **Marketing** [brief + propuesta]: **Inter** 600/700 (sans geométrica bold). Si Axel prefiere Montserrat o Helvetica Bold: PREGUNTAR A AXEL.
- **App** [brief]: Space Grotesk (títulos), Geist (texto), JetBrains Mono (CUIT, montos, código).
- Archivo único: `assets/fonts/fonts.css`. Nunca depender de fuentes del sistema.
- Tracking de titulares `-0.03em`. Peso 700 en el gancho, 600 en el resto [propuesta].

| Elemento | Reel 1080×1920 | Horizontal 1920×1080 |
|---|---|---|
| Gancho (primeros 2 s) | 84–104 px, máx. 2 líneas | 72–88 px |
| Titular de escena | 64–76 px, máx. 2 líneas | 60–76 px |
| Subtítulos (voz) | 54–64 px, 1–2 líneas, máx. 5 palabras visibles | 44–52 px |
| Etiqueta o pastilla | 34–40 px | 28–34 px |

Una sola palabra de acento por línea (azul o violeta). Poco texto por pieza [brief].

## 3. Formatos

| Pieza | Tamaño | fps | Notas |
|---|---|---|---|
| Reel IG / TikTok | 1080×1920 | 30 | **compuesto nativo en vertical**, no un horizontal con barras |
| Venta, demo, evento | 1920×1080 y 1080×1920 | 30 (60 si hay scroll de UI rápido) | dos composiciones, no un recorte |
| Hero del 18/11 | el que pida Axel | 60 | máxima calidad, pocas piezas |

### Zona segura del reel (la app tapa los bordes)
- Arriba: nada importante en los primeros **220 px**.
- Abajo: nada importante en los últimos **480 px** (caption, botones, perfil).
- Derecha: nada importante en los últimos **140 px** (likes, comentarios).
- El gancho y los subtítulos viven entre **y 220 y y 1440**, con 80 px de margen lateral (140 a la derecha).

## 4. Tiempo y ritmo [propuesta]

- **Gancho en los primeros 2 s.** Si el primer cuadro está vacío, se corta.
- Cada titular: entra en 0,5–0,9 s, se sostiene lo que tarde en leerse (≈ 0,3 s por palabra + 0,6 s) y sale en 0,3–0,5 s.
- **Nada quieto más de 1 s**: deriva lenta, cámara que respira.
- Reels de 15–35 s. Piezas de venta de 30–45 s.
- 0,35 s limpios al principio y al final de cada escena, para empalmar.

## 5. Movimiento [propuesta, basada en el kit]

- **Entrada de palabras:** barrido lateral con desenfoque direccional (`MKP.smearIn`) o al ritmo de la voz (`MKP.sayIn`).
- **Salida:** *whip* acelerado con desenfoque (`MKP.whip`).
- **Cambio de escena:** corte en movimiento de 0,18 s (`MKP.cut`), escondido bajo un whip o un movimiento de cámara. **Nunca flash blanco.**
- **Cámara sobre UI** (estilo Screen Studio): zoom ×1,5–2,2 a cada acción (tocar, escribir, resultado) y zoom out a la vista completa.
- **Un objeto que se transforma en otro** antes que un fundido entre dos imágenes. Por ejemplo: el audio de WhatsApp → la hoja A4 de la factura.
- Easing: `expo.out` para entradas, `power3.in` para salidas, `expo.inOut` para la cámara. Sin rebotes (`back`, `elastic`, `bounce`).
- 3D solo cuando suma: el iPhone con WhatsApp facturando (`kit/three-stage.js`).

## 6. Textura y terminación [propuesta]
- Fondo `--caeia-bg` liso, con una viñeta suave. Grano 3–4 %.
- Sombras suaves y profundas en ventanas y teléfono. Vidrio esmerilado solo en elementos de la app.
- **Sin glow, sin halos de color, sin brillos que barren.**

## 7. Subtítulos (cuando hay voz)
- Palabra por palabra, sincronizados con la transcripción (`hyperframes transcribe`).
- Inter 700, blanco. La palabra que se está diciendo va en `--caeia-cae`, y solo esa.
- Sobre una placa `--caeia-bg` al 70 % con radio de 18 px, dentro de la zona segura.
- Nunca tapan la cara ni la UI que se está mostrando: se mueven arriba o abajo según la escena.

## 8. Cinco cosas que el motion de CAEIA no hace nunca
1. Destellos, sparkles de 4 puntas, glow o neón.
2. Degradé azul↔violeta (ni en texto, ni en fondos, ni en el logo).
3. Robots, circuitos PCB, mascotas, estética cyberpunk o gamer, símbolo $.
4. Texto que llena la pantalla o tipeo letra por letra en titulares (el tipeo vive solo dentro de un input de la app o de WhatsApp).
5. UI inventada: toda pantalla de CAEIA, de ARCA o de WhatsApp sale de una captura real.

## 9. Un ejemplo bien hecho, plano por plano (reel de 20 s) [propuesta]
1. **0–2 s:** fondo `#0a0e1a`. Gancho en dos líneas: "Facturar en ARCA" / "*te roba la tarde*" (la segunda en `#0ea5e9`). Entra con barrido.
2. **2–6 s:** captura real de ARCA cargando, la cámara se acerca al spinner y todo se congela en gris (`MKP.freeze`).
3. **6–7 s:** corte en movimiento. El iPhone 3D entra girando desde la derecha.
4. **7–13 s:** en el WhatsApp del iPhone llega un audio, "Factura C a Juan por 15 mil", y la burbuja de confirmación de CAEIA (datos de homologación).
5. **13–17 s:** la burbuja se transforma en la hoja A4 del PDF con QR. Zoom al CAE.
6. **17–20 s:** "Sin clave fiscal. *Sin vueltas.*". Wordmark CAE|IA y @caeia.app.
