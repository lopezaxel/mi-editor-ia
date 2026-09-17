# edicion-liquid — leeme primero

Una skill para **Claude Code y Codex** que edita tus videos a cámara en estilo **Liquid Glass de Apple**: tarjetas de vidrio translúcido con tus cifras, logos y diagramas, split-screen con tu pantalla y música tenue. Sin CapCut ni Premiere: la IA edita con código (HyperFrames + ffmpeg), renderiza, revisa su propio render y corrige sola hasta que queda.

**Qué hay en esta carpeta**
- `edicion-liquid/` → la skill (esto es lo que se instala).
- `INSTALAR.md` → instalación paso a paso en Mac y Windows.

**Los 3 pasos**
1. **Instalá** Node 22, ffmpeg y HyperFrames 0.8.43, y copiá `edicion-liquid/` a tu carpeta de skills (detalle en `INSTALAR.md`).
2. **Completá** `edicion-liquid/estilo.md` con tu marca, colores, logos y ritmo (hay un ejemplo lleno en `edicion-liquid/ejemplos/estilo-claudio.md`).
3. **Pedile el video** a la IA con la plantilla de `edicion-liquid/prompt-editor.md`, como si le hablaras a tu editor.

Cómo se ve: `edicion-liquid/ejemplos/previews/`.
