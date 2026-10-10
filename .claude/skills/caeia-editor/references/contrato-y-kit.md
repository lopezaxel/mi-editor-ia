# Contrato HyperFrames 0.8.43 y API del kit

Probado en Windows el 2026-10-10 (`proyectos-video/_prueba-kit`: check en verde, render 1080×1920 de 240/240 cuadros).

## Contrato (lo que exige el motor)
- Una sola composición raíz por carpeta: `<div id="root" data-composition-id="root" data-start="0" data-duration="D" data-width="W" data-height="H">`.
- Los elementos con tiempo llevan `class="clip"` + `data-start` + `data-duration`. Video: `data-media-start` (recorte de entrada) y `muted` (el audio se mezcla después).
- Un `gsap.timeline({ paused: true })` y, **escrito literal en el `<script>` de la página** (el linter lo busca así):
  `window.__timelines = window.__timelines || {}; window.__timelines["root"] = root; root.seek(0);`
- Timelines hijos o del 3D: `new gsap.core.Timeline(...)`, no `gsap.timeline()`.
- Todo seekable: el cuadro sale solo del tiempo. Solo `set`, `to`, `from` y `fromTo`. Nada de `setTimeout`, ni animaciones CSS, ni `Math.random()` sin semilla.
- GSAP desde `node_modules/gsap/dist/gsap.min.js` (3.15.0, instalado en el proyecto). Fuentes desde `assets/fonts/fonts.css`. **Nada desde internet en el render.**
- El compilador **inyecta inline** los `.js` locales. Un `</script>` literal adentro de un `.js`, aunque sea en un comentario, rompe la página ("Invalid or unexpected token" + "gsap is not defined"). Escribilo `<\/script>`.
- Para no pisarse, cada composición vive en su carpeta: en el modo "ambos" son `reel/` y `horizontal/`.

## Comandos
```bash
npx hyperframes check                                    # gate: 0 errores en Lint, Runtime y Contrast
npx hyperframes snapshot --at 0.6,3.3,6.2 --no-end --describe false --output qa/v1   # --describe false: no mandar cuadros a Gemini
npx hyperframes render --fps 30 --quality high --workers 1 -o renders/video.mp4
npx hyperframes transcribe assets/crudo.mp4 -m large-v3 -l es                         # transcript.json [{text,start,end}]
```
Tiempos de referencia en esta PC (AMD R5, GPU integrada): `check` 1–5 min; render ≈ 9 s de captura por cada segundo de reel 1080×1920 a 30 fps.

## Capas de la plantilla (de atrás hacia adelante)
`#bg` (fondo de marca) → `video.base-video` (crudo, opcional) → `#cam` (mundo de la UI, cámara) → `.vignette` → `.scrim-top` (velo para el gancho) → `.panel#cierre-bg` (fondo del cierre) → `#front` (titulares, wordmark) → `#subs` (subtítulos) → `.grain`.
Para el 3D, un `<canvas id="gl">` entre `#cam` y `#front` (ver más abajo).

## kit/premium.js → `MKP` (movimiento principal)
Llamá `MKP.use(root)` primero. Para un acto aparte: `const a = MKP.act(); MKP.use(a); …; root.add(a, offset)`.

| Helper | Uso |
|---|---|
| `MKP.words()` | parte `data-w="Facturar en ARCA *te roba la tarde*"` en `.w` (`*…*` = azul `.acc`, `_…_` = violeta `.al`) |
| `MKP.smearIn(sel, t, {dx, stagger, dur})` | entrada con barrido lateral, giro 3D y desenfoque direccional |
| `MKP.sayIn(sel, tiempos)` | cada palabra entra cuando la voz la dice (tiempos de `transcript.json`) |
| `MKP.whip(sel, t, {dx})` | salida acelerada con desenfoque |
| `MKP.swap(sel, tiempos)` | palabra rotativa ("Facturá desde *la web / WhatsApp / un audio*") |
| `MKP.cut(sel, t)` | corte en movimiento de 0,18 s (oscuro↔claro, al cierre). **Nunca flash.** |
| `MKP.freeze(sels, t, hasta)` | gris + oscurecido: el "golpe" del problema (ARCA colgado) |
| `MKP.storm(t0, t1)` | tiempos que se aceleran (mensajes que llegan, facturas que se apilan) |
| `MKP.drift`, `MKP.press` | deriva lenta · rebote de un botón |

## kit/caeia.js → `CAEIA` (marca)
| Helper | Uso |
|---|---|
| `CAEIA.json("transcript")` | lee el `<script type="application/json" id="transcript">` |
| `CAEIA.captions(root, palabras, {offset, maxWords: 4, maxGap: 0.6})` | subtítulos palabra por palabra; la palabra dicha va en azul. `offset` = `data-start` del crudo − `data-media-start` |
| `CAEIA.wordmark("#wm")` | CAE (azul) + IA (violeta), split literal |
| `CAEIA.cam(root, "#cam", W, H)` → `cam(t, [x, y], escala, dur)` | cámara tipo Screen Studio sobre el mundo `#cam` |

## kit/caeia.css (clases)
`.t` (titular; `.hook`, `.center`), `.wordmark`, `.handle`, `.cap-line` (subtítulo), `.scrim-top` / `.scrim-bottom` (velo sobre footage), `.panel` (fondo de marca), `.shot` (captura con sombra dentro de `#cam`), `.base-video`, `.vignette`, `.grain`. Debug: `<body class="reel show-safe">` dibuja la zona segura.

## kit/three-stage.js (iPhone 3D, opcional; `npm i three@0.181.2` en el proyecto)
```html
<script type="importmap">{ "imports": { "three": "./node_modules/three/build/three.module.js", "three/addons/": "./node_modules/three/examples/jsm/" } }</script>
<canvas id="gl" width="2160" height="3840" style="position:absolute;inset:0;width:1080px;height:1920px"></canvas>
<script type="module">
  import { createStage, makePhone, chatUI, bindTimeline, put } from "./kit/three-stage.js";
  const st = createStage({ canvas: document.getElementById("gl"), width: 1080, height: 1920, rimColor: 0x8b5cf6 });
  const ph = makePhone(st); const ui = chatUI(ph.ctx, ph.SW, ph.SH, { accent: "#0ea5e9" });
  const S = { ph: { x: 6, y: 0, z: 0, rx: 0.1, ry: -1.2, rz: 0, s: 1, v: 0 } };
  const t3 = new gsap.core.Timeline({ paused: true });
  // t3.set(S.ph, { v: 1 }, 2); t3.fromTo(S.ph, { x: 6, ry: -1.2 }, { x: 0, ry: -0.25, duration: 1, ease: "expo.out" }, 2);
  bindTimeline(t3, (t) => { put(S.ph, ph.group); if (ph.group.visible) { ui.begin(); ui.header({ name: "CAEIA", sub: "en línea" }); ui.compose(); /* ui.bubble(...) */ ph.texture.needsUpdate = true; } st.render(); });
</script>
```
- `chatUI` imita WhatsApp claro. Antes de usarlo en una pieza, comparalo con una captura real del WhatsApp de CAEIA y ajustá los colores y textos.
- Reel: 1 unidad ≈ 162,8 px.
- **Probá el 3D con `check` + `snapshot` antes de prometerlo**: todavía no se probó en esta máquina.

## kit/motion-kit.js + .css → `MK` (piezas sueltas)
Cursor tipo Figma, ventana macOS, `typeOn` (solo dentro de un input de la app), `countUp` (solo con dato real), `chat`, `check`, `tap`, `push`, `zoomThrough`, `handoff`, `flip`. Se quitaron a propósito `MK.flash`, `MK.sweep`, `MK.aurora`, `.pm-glow` y `.mk-grad-text` porque chocan con la marca.
