---
name: edicion-liquid
description: Edita videos talking-head (una persona hablando a cámara) con HyperFrames en estilo Liquid Glass de Apple — tarjetas de vidrio translúcido con refracción, cifras, logos, diagramas, split-screen con grabación de pantalla y música tenue — a partir de un video base y un prompt tipo "brief para tu editor". Usar cuando pidan editar, recortar o agregar gráficos a un video grabado a cámara con este estilo, o mencionen edicion-liquid, liquid glass o estilo.md. No usar para videos generados desde cero sin grabación, reels verticales ni para operar CapCut/Premiere.
---

# Edición Liquid

Editás un video grabado a cámara como lo haría un editor, pero sin tocar un programa de edición: **generás HTML/CSS/GSAP con HyperFrames y ffmpeg**, renderizás, revisás tu propio render y corregís hasta que pase. La persona te habla como a su editor; vos entregás el video terminado.

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

- "Editá este video", "armame la intro", "agregale los gráficos", "hacelo estilo liquid glass/Apple".
- Hay un `estilo.md` o un prompt con la forma de `prompt-editor.md`.
- No: reels 9:16, animaciones sin footage, edición en apps de escritorio.

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
node <skill>/templates/build_scene.mjs --scene escenas/plan.json --id intro-01 --theme tema.json
```
El builder genera la lente exacta para cada tarjeta, embebe todo en `index.html` y **se niega a construir** si una tarjeta pisa la cara, se superpone con otra, entra antes de 0,35 s o sale después de `duración − 0,35 s`, o si una cifra no tiene `source`. Se corrige el JSON, nunca el HTML generado. Tipos: `stat-card`, `headline`, `phrase`, `steps`, `diagram`, `logo-card`, `photo-card`, `lower-third`, `cta-window`, `split-screen`. Ejemplos listos en `templates/ejemplos/`.

### 3. Música
Tenue y de fondo, nunca protagonista. Por defecto, ambient generada localmente (ver `estilo.md` › Música); si la persona trae una pista, se usa esa. Mezcla con **ducking bajo la voz**: `mezclar_audio.py --intro-fin 0 --musica-bajo-voz -11 --musica-pausa -7` (valores aprobados; subí solo si la persona lo pide). Detalles de mezcla: skill `hyperframes-audio`; para generar/buscar audio: `media-use`. Nada con copyright que la persona no haya provisto.

### 4. Render
```bash
npx hyperframes render --fps 60 --quality delivery --workers 1 --output renders/<id>.mp4
```
**Un render por vez, un worker.** No reconstruyas `index.html` mientras renderiza. Verificá cada salida: 1920×1080, 60 fps, cantidad de frames exacta = duración × 60.
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

Receta aprobada, 4 capas por tarjeta (detalle en `templates/API.md` › Material): lente SVG con mapa de desplazamiento (squircle + Snell BK7, `templates/lib/glass-optics.mjs`, MIT, licencia en `templates/lib/liquid-glass-LICENSE`) → tinte blanco translúcido → borde especular → reflejo animado. Es una aproximación CSS/SVG del material de Apple, no el material nativo.
Alternativas del registry: `ios26-liquid-glass` y `liquid-glass-widgets` (WebGL) vía `hyperframes-registry`. Usalas solo si la persona las pide; por defecto, la receta SVG.

## Archivos

| archivo | para qué |
|---|---|
| `estilo.md` | la identidad de la persona: marca, colores, tipografía, ritmo, música, qué no hacer |
| `prompt-editor.md` | plantilla del brief + ejemplo lleno |
| `ejemplos/estilo-claudio.md` | un `estilo.md` completo de referencia |
| `ejemplos/previews/` | cómo tiene que verse |
| `templates/build_scene.mjs` | constructor de escenas (API en `templates/API.md`) |
| `templates/liquid.css` | material y tipos de escena |
| `templates/generate-lens-maps.mjs` | exporta mapas de lente sueltos |
| `templates/ejemplos/*.json` | una escena de cada tipo + `tema-ejemplo.json` |
| `scripts/*` | transcripción, cortes, sync de pantalla, color, ensamblado, verificación |
