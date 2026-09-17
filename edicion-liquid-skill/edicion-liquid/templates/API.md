# API de escenas Liquid Glass

Una **escena** es un tramo corto del video base (normalmente 4 a 12 s) con uno o varios elementos de vidrio encima. Cada escena se construye a un `index.html` de HyperFrames, se valida, se renderiza sola y después `scripts/ensamblar.py` la pega en su lugar del máster.

```bash
# dentro del proyecto HyperFrames (con node_modules/gsap y hyperframes instalados)
node <skill>/templates/build_scene.mjs --scene escenas/intro-01.json --theme tema.json
npx hyperframes check --at 1.2,3,5.8
npx hyperframes snapshot --at 3 --no-end --describe false --output qa/intro-01
npx hyperframes render --fps 60 --quality delivery --workers 1 --output renders/intro-01.mp4
```

Flags: `--scene <json>` (una escena, o `{"scenes":[...]}` + `--id <id>`), `--project <dir>` (default: carpeta actual; las rutas del JSON son relativas a esta carpeta), `--theme <json>`, `--out <html>` (default `<project>/index.html`), `--no-check-assets`, `--types`, `--help`.
Además escribe `scenes/<id>.html.txt` y `scenes/<id>.json` para reeditar. Imprime un JSON con las cajas de cada elemento y un `sugerido_check`.
Código de salida `2` = la escena viola una regla. Se corrige el JSON, nunca el HTML generado.

## Escena

```json
{
  "id": "intro-01",            // minúsculas, números y guiones
  "duration": 6,               // segundos (obligatorio)
  "fps": 60,                   // default 60
  "footage": "assets/intro-01.mp4",  // tramo del video base, H.264 1080p
  "media_start": 0,            // desde qué segundo de ese archivo arranca
  "mode": "intro",             // "intro" (denso, entradas 3D grandes) | "body" (sobrio). Default "body"
  "material": "light",         // "light" | "dark". Default: el del tema
  "safe_zone": [680, 270, 560, 810],  // caja de la cara [x,y,ancho,alto]; null la desactiva
  "elements": [ ... ]
}
```

Reglas que el builder hace cumplir (error, no aviso):
- Cada elemento entra en `in ≥ 0,35 s` y su salida termina antes de `duration − 0,35 s` (bordes limpios para empalmar).
- Ningún elemento pisa `safe_zone` (salvo `"allow_face_overlap": true`, que no se usa sin pedido explícito). Si la persona no está centrada, se ajusta `safe_zone` mirando un frame.
- Dos elementos no se superponen en espacio y tiempo a la vez.
- `stat-card` exige `source`: de dónde sale la cifra (minuto de la cámara o `estilo.md`). Sin fuente no hay número.
- Todos los archivos referenciados existen y `node_modules/gsap` está instalado.

## Campos comunes de cada elemento

| campo | qué es |
|---|---|
| `type` | uno de los 10 tipos de abajo |
| `in` / `out` | segundo de entrada y segundo en que **empieza** la salida (relativos a la escena) |
| `slot` | `left` · `right` · `top` · `top-left` · `top-right` · `bottom-left` · `bottom-right` · `{"x":..,"y":..}` |
| `mode` | pisa el `mode` de la escena para este elemento |
| `material` | `light` / `dark`, pisa el de la escena |
| `width` / `height` | pisan el tamaño por defecto (la lente se genera para el tamaño exacto) |

Duración mínima visible (`out − in`): 1,12 s en intro, 0,92 s en cuerpo, 1 s en split.
La salida dura 0,42 s (intro) o 0,48 s (cuerpo); el split necesita 1 s después de `out`.

## Tipos

**`stat-card`** — 546×260. Como la referencia: etiqueta en mayúsculas, punto de acento, cifra grande, unidad y sublínea.
`label`*, `value`*, `source`*, `unit`, `sub`, `dot` (false lo oculta). Slot por defecto `left`.
```json
{ "type": "stat-card", "in": 0.9, "out": 4.9, "slot": "left", "label": "Mis mentores", "value": "500 mil", "unit": "USD", "sub": "al mes", "source": "cámara 00:08" }
```

**`headline`** — titular blanco 90 px centrado arriba (y 75) + pastilla opcional (y 190). Posición fija.
`title`*, `pill`, `pill_tone` (`dark` default | `light`), `scrim` (default true: velo radial suave detrás del titular para que se lea sobre cielos claros; `false` lo saca).

**`phrase`** — 546×260. `title`* (50 px, hasta 2 líneas, se achica sola si no entra), `sub`.

**`steps`** — 546 × alto según ítems. `title`*, `items`* (1–5), `reveal` (segundos absolutos de aparición de cada ítem; default escalonado cada 0,35 s).

**`diagram`** — flujo de nodos con conectores en color de acento.
`nodes`* (2–6), `layout` (`row` default | `column`), `title`, `reveal` (segundo de cada nodo; la flecha aparece 0,12 s antes de su nodo), `loop` `{"from": 4, "to": 3, "label": "...", "at": 2.6}` (números de nodo desde 1, `to < from`; `at` opcional).
`row` = tarjeta 1240×240 arriba al centro (ideal para el framework Video base → Prompt → Proceso → Render → Loop). `column` = 546 de ancho, al costado.
```json
{ "type": "diagram", "layout": "row", "slot": "top", "in": 0.4, "out": 5.0, "title": "Cómo edita la IA",
  "nodes": ["Video base", "Prompt", "La IA procesa", "Renderiza", "Resultado"],
  "reveal": [0.9, 1.3, 1.7, 2.1, 3.2], "loop": { "from": 4, "to": 3, "label": "Loop: se revisa sola", "at": 2.6 } }
```

**`logo-card`** — 460×300 (260 sin etiqueta). `src`* (PNG/SVG en `assets/`), `label`, `logo_height` (px), `alt`. Con `"material": "dark"` usá el logo en versión clara.

**`photo-card`** — 590×520. `src`* (imagen, o video `.mp4/.mov/.webm`), `media_start` (si es video), `caption`, `alt`.

**`lower-third`** — 560×128 (96 sin rol), abajo a la izquierda. `name`*, `role`.

**`cta-window`** — ventana 590×800 con barra y dirección; adentro una captura larga que scrollea.
`src`* (captura vertical real, ancho ≈ 700 px), `address`, `scroll`: `[{"at": 1.4, "duration": 1.5, "to": 900}]` (`to` = desplazamiento en px a escala de la ventana; cada tramo entre `in` y `out`).

**`split-screen`** — la persona se recorta en una tarjeta a un lado (38 % del ancho) y la grabación de pantalla entra en una ventana de vidrio 4:3 del otro; al final vuelve a plano completo. Fondo: la misma toma desenfocada.
`src`* (grabación de pantalla, ya sincronizada con `scripts/sincronizar_pantalla.py`), `media_start`, `person_center_x` (px del centro de la persona en el cuadro, default 960), `person_width_ratio` (default 0.38), `person_side` (`left` default | `right`), `address`, `fit` (`contain` default | `cover`), `background` (color detrás de la pantalla), `screen_aspect` (`"4:3"` default; `"3:4"` si la tablet o el celular grabaron en vertical: la ventana pasa a ser vertical y se centra en su lado — conviene subir `person_width_ratio` a ~0.46 para no dejar hueco).
Transición de entrada 0,7 s desde `in`; ventana a `in + 0,35`; vuelta a plano completo entre `out + 0,3` y `out + 1,0`. No mezclar otros elementos durante el split.

## Tema (`tema.json`)

Se escribe una vez a partir de `estilo.md`:
```json
{ "font": "\"Helvetica Neue\", Arial, sans-serif", "ink": "#0a2030", "label": "#152f43", "accent": "#0066ff",
  "title": "#ffffff", "material": "light",
  "font_faces": [{ "family": "MiFuente", "src": "assets/fonts/MiFuente-Bold.woff2", "weight": 700 }] }
```
El render de HyperFrames es determinista: las fuentes de sistema de Apple (`SF Pro`, `Helvetica Neue`, `-apple-system`) se reemplazan por **Inter**. Para una tipografía exacta, poné el archivo en `assets/fonts/` y declaralo en `font_faces` (y respetá su licencia).

## Material (la receta aprobada, por si se escribe una escena a mano)

Cuatro capas por tarjeta, en `liquid.css`:
1. **Lente**: mapa de desplazamiento PNG (squircle + Snell, vidrio BK7, `lib/glass-optics.mjs`) → filtro SVG `feImage` + `feDisplacementMap` de una sola pasada, `filterUnits="userSpaceOnUse"`, PNG embebido como data URI; se aplica con `backdrop-filter: url(#lente) blur(1.1–1.8px) saturate(1.15–1.4)`.
2. **Tinte**: `linear-gradient(120deg,#ffffff75,#ffffff3b 42%,#eaf8ff30 72%,#ffffff6b)` + `inset 0 0 20px #eafaff35` (intro); el cuerpo usa el tinte más denso aprobado `#ffffff89 / 63 / #eaf8ff58 / #ffffff7e`.
3. **Borde**: `inset 0 2px 2px #ffffffd9, inset 0 -2px 3px #ffffff80`.
4. **Reflejo**: radial animado con `--glint-x` de −20 % a 120 %.
Radio 44, sombra `0 25px 46px #04101c38`.

`generate-lens-maps.mjs` exporta mapas sueltos: `node generate-lens-maps.mjs --spec card:546x260:44:24 --out assets`.

Alternativas del registry de HyperFrames (`npx hyperframes add ...`): `ios26-liquid-glass` y `liquid-glass-widgets` (WebGL). Se pueden usar, pero la receta por defecto es esta, SVG, porque es la aprobada y renderiza igual en cualquier máquina.
