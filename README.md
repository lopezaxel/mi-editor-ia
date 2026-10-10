# mi-editor-ia

El editor de motion graphics de **CAEIA** dentro de Claude Code. Axel trae el material crudo (su grabación, un clip de avatar con su voz, grabaciones de pantalla, capturas de la app, flyers) o una idea. La IA arma el reel o la pieza de venta con código (**HyperFrames 0.8.43 + GSAP + ffmpeg**), renderiza, revisa sus propios cuadros y corrige antes de entregar. Sin CapCut ni Premiere.

## Qué hay en este repo

| Ruta | Qué es |
|---|---|
| `brand.md` | **Qué es CAEIA y qué se puede decir** (estado real en homologación, prohibiciones, fechas). Fuente única. |
| `MOTION.md` | **Cómo se ve y se mueve**: colores, tipografías, formatos, zona segura del reel, ritmo, movimiento, prohibidos. |
| `CLAUDE.md` | Reglas del proyecto para Claude Code (leer los dos archivos de arriba primero). |
| `.claude/skills/caeia-editor/` | **La skill orquestadora.** Decide el modo según el material, arma el proyecto, construye, revisa y entrega. |
| `.claude/skills/launch-video`, `motion-effects`, `animated-chart`, `motion-brief-writer` | Skills de Charlie Hills (MIT), adaptadas a CAEIA y a HyperFrames. Las usa `caeia-editor`. |
| `kit/` | Librería de animación: `caeia.css` y `caeia.js` (marca, subtítulos palabra por palabra, cámara), `premium.js` (barridos, whips, cortes), `three-stage.js` (iPhone 3D), plantilla y `nuevo_proyecto.py`. Base: video-saas-premium de Rayyan Montoya (MIT). |
| `kit/scripts/` | Audio: `audio_tools.py`, `eleven_vo.py` (ElevenLabs), `sfx_curate.py`. Necesitan `numpy`. |
| `assets/fonts/` | Inter, Space Grotesk, Geist y JetBrains Mono (OFL), para que el render salga igual en cualquier máquina. |
| `proyectos-video/` | Una carpeta por pieza. Los videos y renders no se versionan. |
| `edicion-liquid-skill/` | Copia de referencia de la skill de Claudio Conde (talking-head horizontal Liquid Glass). No se modifica. |
| `estilo.md` | El `estilo.md` que usa `edicion-liquid` (todavía con `<<COMPLETAR>>`). |
| `contexto-caeia.md` | Histórico (17/9). Reemplazado por `brand.md`. |

## Cómo se usa

Abrí Claude Code en esta carpeta y pedí lo que necesitás, como a un editor:

> Armame un reel con este clip del avatar: `D:\...\avatar-01.mp4`. Gancho sobre lo lento que es ARCA, cierre con @caeia.app.

La skill `caeia-editor`:
1. pregunta lo que falte, en una sola tanda;
2. propone los beats y espera tu OK;
3. crea `proyectos-video/<fecha-nombre>/`;
4. transcribe, construye, chequea y revisa cuadros;
5. renderiza, mezcla el audio y entrega `renders/final.mp4` con un resumen.

## Requisitos de la máquina

| Herramienta | Versión | Chequeo |
|---|---|---|
| Node.js | 22+ | `node -v` |
| ffmpeg + ffprobe | reciente | `ffmpeg -version` |
| Python | 3.10+ (`python` en Windows) | `python --version` |
| HyperFrames | **0.8.43** (global; cada proyecto la fija en su `package.json`) | `hyperframes --version` |
| numpy | para los scripts de audio y los de `edicion-liquid` | `python -c "import numpy"` |

Cada proyecto instala sus dependencias adentro (`npm i hyperframes@0.8.43 gsap@3.15.0`). Nada global.
