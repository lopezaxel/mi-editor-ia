---
name: edicion-liquid
description: Edita videos talking-head (una persona hablando a cámara, incluye avatares de IA) con HyperFrames — tarjetas gráficas (cifras, logos, diagramas, split-screen con grabación de pantalla) y música tenue — a partir de un video base y un prompt tipo "brief para tu editor". El estilo visual es elegible (default Liquid Glass, o Saturado Bold, ver `estilos/`) y el formato también (horizontal 16:9 o vertical 9:16 para reels/TikTok, ver `--format`). Usar cuando pidan editar, recortar o agregar gráficos a un video grabado a cámara o generado con avatar de IA, o mencionen edicion-liquid, liquid glass, saturado bold, reel, TikTok o estilo.md. No usar para animaciones sin footage de base ni para operar CapCut/Premiere.
---

# Edición Liquid

Editás un video grabado a cámara (o un avatar de IA hablando) como lo haría un editor, pero sin tocar un programa de edición: **generás HTML/CSS/GSAP con HyperFrames y ffmpeg**, renderizás, revisás tu propio render y corregís hasta que pase. La persona te habla como a su editor; vos entregás el video terminado.

Esta skill es un **motor** (transcripción, corte de silencios, plan de escenas, render, QA) con dos ejes intercambiables:
- **Estilo** (piel visual: colores, tipografía, si hay vidrio o no) — carpeta `estilos/`, flag `--style`.
- **Formato** (orientación del lienzo: horizontal 16:9 u vertical 9:16) — flag `--format`, ver "## Formato".

El JSON de escena y los 10 tipos de elemento son los mismos sin importar estilo o formato — lo único que cambia es la piel visual y la geometría del lienzo.

## Regla madre

**Nunca controles CapCut, Premiere, DaVinci ni ninguna app con computer-use.** Todo se edita con código: `scripts/` (ffmpeg, transcripción) + `templates/` (escenas HyperFrames). Si algo no se puede hacer así, lo decís y proponés la alternativa.

## El framework (así se enseña, así se ejecuta)

```
(1) Video base ─▶ (2) Prompt ─▶ (3) La IA procesa ─▶ (4) Renderiza ─▶ (6) Resultado final
                                        ▲                    │
                                        └──── (5) LOOP ──────┘
```

1. **Video base** — la grabación a cámara (+ grabación de pantalla/iPad si hay).
2. **Prompt** — el brief estandarizado de `prompt-editor.md`. *Hablale como a tu editor*: qué video es, qué mostrar en la intro, qué datos, qué logos, qué escenas de pantalla, qué cortar y qué conservar.
3. **La IA procesa** — transcribe, corta silencios, planifica escenas, construye el HTML.
4. **Renderiza** — HyperFrames + ffmpeg, un render por vez.
5. **Loop automático** — revisás tu propio render contra `estilo.md` y el prompt (`hyperframes check`, snapshots, frames del MP4 final), corregís y volvés a renderizar **sin que la persona tenga que pedirlo**. El loop se corta cuando pasa todos los gates de la sección QA, no antes.
6. **Resultado final** — el MP4 + un resumen corto de qué se hizo y qué quedó fuera.

## Cuándo activarte

- "Editá este video", "armame la intro", "agregale los gráficos", "hacelo estilo liquid glass/Apple/saturado", "armame un reel/TikTok con esto".
- Hay un `estilo.md` o un prompt con la forma de `prompt-editor.md`.
- No: animaciones 100% generadas sin footage/avatar de base, edición en apps de escritorio.

## Estilos disponibles

Cada estilo vive en `estilos/<nombre>/` (un `style.css` con la misma piel visual sobre las mismas clases + un `estilo-visual.md` con cuándo usarlo). Se elige con `--style <nombre>` al construir cada escena (paso 2 del pipeline); sin el flag se usa `liquid-glass`.

| estilo | qué es | cuándo |
|---|---|---|
| `liquid-glass` (default) | vidrio translúcido con refracción, sobrio, movimiento 3D | talking-head profesional/cercano, demos de producto, marcas con UI glassmorphism |
| `saturado-bold` | tarjetas planas y opacas, borde grueso, sombra dura, tipografía enorme y saturada | ganchos agresivos, contenido tipo feed viral, CTAs |

Si el prompt no dice qué estilo usar y no es obvio por el tono del video, preguntalo **una vez, en bloque**, junto con el resto de datos que falten — no asumas. Para sumar un estilo nuevo a la librería: crear `estilos/<nombre>/style.css` (mismas clases que `templates/liquid.css`, ver comentarios de cada bloque) + `estilos/<nombre>/estilo-visual.md`; el motor (`build_scene.mjs`, los scripts, la API de escenas) no cambia.

## Formato

Se elige con `--format <nombre>` al construir cada escena; sin el flag se usa `horizontal`. Cambia el tamaño del lienzo y los márgenes/zona de cara por default — el JSON de escena (tipos, campos) es el mismo.

| formato | lienzo | cuándo |
|---|---|---|
| `horizontal` (default) | 1920×1080 | video largo (charla, demo), YouTube, contenido no vertical |
| `vertical` | 1080×1920 | reels de Instagram, TikTok, YouTube Shorts |

Notas para `vertical`:
- **`safe_zone` default** asume una persona/avatar centrado en la columna central del cuadro; si el encuadre real es distinto, ajustalo por escena como en horizontal.
- **Slots `left`/`right` con tarjetas anchas (500-600px) suelen pisar la cara** en un lienzo de 1080 de ancho — no hay lugar a los costados de un sujeto centrado. Preferí `top`, `bottom-left`/`bottom-right`, o un `slot: {x,y}` explícito con un `width` más angosto.
- **`split-screen` no está afinado para vertical todavía** — funciona (no revienta), pero las proporciones se pensaron para un lienzo horizontal; el builder avisa con un AVISO cuando lo usás en vertical. Revisá la snapshot con más atención que de costumbre, o esperá a que se rediseñe (ver `templates/API.md`).
- Para avatares de IA (sin grabación de pantalla real), `split-screen`/`cta-window` normalmente no aplican: el video es la persona sola, así que `headline`, `stat-card`, `phrase`, `lower-third` son los tipos que más se usan.

## Ritmo para reels cortos (hook-driven)

El framework de "intro densa (recurso cada 3-6s) / cuerpo sobrio (cada 30-60s)" está pensado para un video largo donde después del gancho inicial conviene que respire. **Un reel de 40-90s para retener de punta a punta necesita estar denso todo el tiempo**, no solo al principio: marcá **todas** las escenas con `"mode": "intro"` en vez de mezclar con `"body"`. La elección de modo es una decisión de `escenas/plan.json`, no depende del minutaje real del video — nada obliga a que "intro" sean literalmente los primeros segundos.

## Antes de empezar (una sola vez por máquina)

- Node ≥ 22, ffmpeg, `npm i -g hyperframes@0.8.43`. Versión fijada: **hyperframes 0.8.43 + gsap 3.15.0**.
- Skills oficiales: `npx hyperframes skills update` (instala hyperframes, hyperframes-core, -cli, -animation, -keyframes, -audio, -registry, -creative y media-use) y `npx skills add heygen-com/hyperframes --skill talking-head-recut`. **Antes de escribir una composición a mano, leé `hyperframes-core`** (contrato: `data-composition-id`, `data-start`/`data-duration`/`data-track-index`, `class="clip"`, un timeline pausado en `window.__timelines`, todo seekable). Para comandos, `hyperframes-cli`; para mezcla de audio, `hyperframes-audio`.
- `estilo.md` completo (sin `<<COMPLETAR>>`). Si faltan datos, preguntalos **en bloque y como opciones**, no uno por uno.

## Pipeline

Trabajá en una carpeta de proyecto: `proyecto/` con `assets/`, `escenas/`, `qa/`, `renders/`, y adentro `npm i hyperframes@0.8.43 gsap@3.15.0`.
Cada script tiene `--help`; leelo antes de usarlo.

### 0. Preparación
1. `scripts/transcribir.sh` → transcript con tiempos por palabra. Es la fuente de verdad de lo que se dice.
2. `scripts/cortar_silencios.py` → corte de silencios y muletillas. **Cortes siempre en silencios medidos**, nunca por timecode a ojo; conservá los bloopers que el prompt pida.
3. Si hay grabación de pantalla: `scripts/sincronizar_pantalla.py` (alinea por audio) y `scripts/detectar_actividad_pantalla.py` (dónde pasa algo en la pantalla, para elegir qué tramo mostrar).
4. `scripts/reencuadre_y_color.py` → reencuadre y color parejo del máster. Resultado: máster 1920×1080 60 fps H.264.
5. Mirá 3-4 frames del máster con la herramienta de lectura de imágenes: dónde está la cara (`safe_zone`), si el fondo es claro u oscuro (material `light`/`dark`).
6. Escribí `tema.json` desde `estilo.md` (ver `templates/API.md` › Tema).

### 1. Plan de escenas
Escribí `escenas/plan.json` (`{"scenes":[...]}`) con, para cada escena: `id`, tramo del máster (inicio/fin en frames exactos), tipo de elementos y el texto **tomado de lo que la persona dice** en ese tramo. Cortá del máster un archivo por escena en `assets/<id>.mp4` (ffmpeg, frames exactos). API completa de escenas: **`templates/API.md`**.

- **Intro (primeros 30-60 s): edición densa.** `"mode": "intro"`. Un recurso cada 3-6 s: titular + pastilla, cifras, logos de los negocios, foto, diagrama. Entradas 3D grandes.
- **Cuerpo: espaciado.** `"mode": "body"`. **Una intervención cada 30-60 s** (lo que diga `estilo.md`), de 6-8 s, un solo recurso lateral: frase, pasos, diagrama, lower-third. Sobrio.
- **Escenas de pantalla/iPad:** `split-screen` cuando la persona muestra algo en pantalla; `cta-window` para una página con scroll.
- **Cierre/CTA:** `cta-window` o `phrase` con la acción concreta.

### 2. Construir cada escena
```bash
node <skill>/templates/build_scene.mjs --scene escenas/plan.json --id intro-01 --theme tema.json --style liquid-glass --format horizontal
```
El builder genera la lente exacta para cada tarjeta, embebe todo en `index.html` y **se niega a construir** si una tarjeta pisa la cara, se superpone con otra, entra antes de 0,35 s o sale después de `duración − 0,35 s`, o si una cifra no tiene `source`. Se corrige el JSON, nunca el HTML generado. Tipos: `stat-card`, `headline`, `phrase`, `steps`, `diagram`, `logo-card`, `photo-card`, `lower-third`, `cta-window`, `split-screen`. Ejemplos listos en `templates/ejemplos/`. `--style` y `--format` son los únicos flags que cambian; el JSON de escena es idéntico (ver "## Estilos disponibles" y "## Formato").

### 3. Música
Tenue y de fondo, nunca protagonista. Por defecto, ambient generada localmente (ver `estilo.md` › Música); si la persona trae una pista, se usa esa. Mezcla con **ducking bajo la voz**: `mezclar_audio.py --intro-fin 0 --musica-bajo-voz -11 --musica-pausa -7` (valores aprobados; subí solo si la persona lo pide). Detalles de mezcla: skill `hyperframes-audio`; para generar/buscar audio: `media-use`. Nada con copyright que la persona no haya provisto.

### 4. Render
```bash
npx hyperframes render --fps 60 --quality delivery --workers 1 --output renders/<id>.mp4
```
**Un render por vez, un worker.** No reconstruyas `index.html` mientras renderiza. Verificá cada salida: 1920×1080 (horizontal) o 1080×1920 (vertical) según el `--format` usado, 60 fps, cantidad de frames exacta = duración × 60.
Después `scripts/ensamblar.py` reemplaza cada tramo del máster por su render y mezcla audio y música.

### 5. QA loop (automático)
Por cada escena, antes de renderizar:
- `npx hyperframes check --at <tiempos>` → **0 errores** (lint, runtime, layout, contraste). Un error de lint apaga los demás chequeos: si ves "0 samples", no pasó nada.
- `npx hyperframes snapshot --at <tiempos> --no-end --describe false --output qa/<id>` y **mirá cada PNG** con la herramienta de lectura: vidrio translúcido con el fondo visible, texto legible, cara libre, nada cortado.

Sobre el video final:
- `scripts/verificar.py` → duración, frames, audio, uniones.
- Extraé frames del MP4 final en cada escena y miralos. Transcribí el final y comparalo con el transcript: **ningún corte pisa una palabra**.
- Checklist contra el prompt: cada pedido cumplido o anotado por qué no.

Si algo falla, corregís el JSON o el corte, reconstruís, re-renderizás esa escena y volvés a verificar. No entregás con un gate en rojo.

### 6. Entrega
`renders/final.mp4` + resumen de 5-10 líneas: escenas, qué datos se mostraron y de qué minuto salen, qué se cortó, qué quedó pendiente de decisión de la persona.

## Lecciones de la primera edición real (14/9/2026)

- **Muestra antes que máster.** Renderizá primero la intro sola y pedí OK; recién después el cuerpo.
- **Arranques falsos:** con las palabras de Vosk/Whisper encontrá la última arrancada limpia y cortá todo lo anterior. La persona casi siempre lo pide.
- **Tarjetas sobre fondo limpio.** Sobre un cerco, hojas o rayas el texto chico no se lee aunque pase el chequeo de contraste: subí la tarjeta al cielo o a una pared lisa (`slot: {x,y}`).
- **Música más baja de lo que parece.** Ducking también en la intro (música ≈ −11 dB bajo la voz y −7 dB en pausas con `mezclar_audio.py --intro-fin 0 --musica-bajo-voz -11 --musica-pausa -7`). La primera mezcla "presente" fue rechazada por alta.
- **Bloopers:** si la persona dice en cámara que se conserva, va entero (antes, durante y después), sin recortes de pausa, sin zoom, y con una placa `headline` tipo "BLOOPER." encima.
- **Pantalla dividida que varía:** split mientras escribe o explica lo que dibujó, pero nunca más de 25-30 s seguidos sin un plano solo de 3-6 s. Si la tablet grabó en vertical, `screen_aspect: "3:4"` y `person_width_ratio: 0.46`.
- **Grabaciones de pantalla sin audio** (el iPad suele grabar silencio): sincronizá por imagen (trazo en pantalla contra la mano en cámara) y verificá con dos momentos distintos.
- **Encuadre por toma.** Si la cámara se movió entre tomas, cada toma tiene su propio centro de recorte. Base 1,4× y acercamientos a 1,7× en frases fuertes, nunca durante un titular (le taparía la cabeza).
- **Frames exactos:** HyperFrames redondea la duración hacia arriba y a veces entrega 1 frame de más; al ensamblar recortá cada render al conteo esperado (`-frames:v N`) y verificá el total de punta a punta.
- **Empalme con una parte ya aprobada:** no la re-renderices; uní en un frame de silencio dentro de un tramo conservado y contá frames de punta a punta.

## Reglas de diseño (duras)

- **La cara siempre libre.** Overlays al costado o arriba de la persona. Nunca pantallas completas que la tapen (el split-screen la achica, no la tapa).
- **Intro con mucha más edición que el cuerpo.** El cuerpo respira.
- **0,35 s limpios** al principio y al final de cada escena, para empalmar sin saltos.
- **No inventar cifras.** Todo número sale de lo que la persona dice en cámara (con su minuto) o de `estilo.md`. Si no está, no va.
- **Un render por vez, 1 worker.**
- Textos cortos: titular ≤ 3 palabras, frase ≤ 8, ítems ≤ 4 palabras.
- Solo assets que la persona dio (logos, fotos, capturas). Nada de caras de terceros sin pedido.
- Las escenas se escriben en el idioma y el tono de `estilo.md`.

## El material Liquid Glass

Receta aprobada, 4 capas por tarjeta (detalle en `templates/API.md` › Material): lente SVG con mapa de desplazamiento (squircle + Snell BK7, `templates/lib/glass-optics.mjs`, MIT, licencia en `templates/lib/liquid-glass-LICENSE`) → tinte blanco translúcido → borde especular → reflejo animado. Es una aproximación CSS/SVG del material de Apple, no el material nativo. Este es el estilo default (`liquid-glass`); para otros estilos ver `estilos/<nombre>/estilo-visual.md`.
Alternativas del registry: `ios26-liquid-glass` y `liquid-glass-widgets` (WebGL) vía `hyperframes-registry`. Usalas solo si la persona las pide; por defecto, la receta SVG.

## Archivos

| archivo | para qué |
|---|---|
| `estilo.md` | la identidad de la persona: marca, colores, tipografía, ritmo, música, qué no hacer |
| `prompt-editor.md` | plantilla del brief + ejemplo lleno |
| `ejemplos/estilo-claudio.md` | un `estilo.md` completo de referencia |
| `ejemplos/previews/` | cómo tiene que verse |
| `templates/build_scene.mjs` | constructor de escenas, multi-estilo (`--style`) y multi-formato (`--format`) (API en `templates/API.md`) |
| `templates/liquid.css` | piel visual del estilo default `liquid-glass` (ruta histórica, no se movió) |
| `estilos/<nombre>/style.css` | piel visual de cada estilo adicional (mismas clases que `liquid.css`) |
| `estilos/<nombre>/estilo-visual.md` | cuándo usar ese estilo y cuándo no |
| `templates/generate-lens-maps.mjs` | exporta mapas de lente sueltos (solo relevante para `liquid-glass`) |
| `templates/ejemplos/*.json` | una escena de cada tipo + `tema-ejemplo.json` (sirven para cualquier estilo) |
| `scripts/*` | transcripción, cortes, sync de pantalla, color, ensamblado, verificación (no cambian por estilo) |
