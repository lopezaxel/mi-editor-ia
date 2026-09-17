# mi-editor-ia

Pipeline para producir contenido diario (reels/videos) para el Instagram de **CAEIA** (@caeia.app),
usando avatares de IA clonados y edición estilo **Liquid Glass** de Apple (tarjetas de vidrio
translúcido, split-screen, datos y logos) sin tocar CapCut/Premiere: la edición se genera con
HTML/CSS/GSAP vía **HyperFrames** + **ffmpeg**, renderizada y auto-revisada por la skill de
Claude Code `edicion-liquid`.

## Qué hay en este repo

- `estilo.md` — tu identidad de marca (colores, logo, tipografía, tono de música) que la skill
  lee antes de cada edición. Completar los `<<COMPLETAR>>` una sola vez.
- `contexto-caeia.md` — qué es CAEIA, a quién le habla, qué mostrar y qué no, colores exactos de
  marca. Contexto de producto para que los gráficos de cada video sean coherentes y no inventen
  funciones/cifras que no existen.
- `edicion-liquid-skill/` — copia de referencia del paquete original de la skill (documentación,
  ejemplos, INSTALAR.md). La copia *activa* que usa Claude Code vive en
  `~/.claude/skills/edicion-liquid/` (fuera del repo, es de la máquina).
- `proyectos-video/` — una subcarpeta por cada reel/video que se edita. Los videos pesados
  (.mp4/.mov) y los renders NO se versionan (ver `.gitignore`); sí se versionan los prompts,
  planes de escena (`escenas/*.json`) y assets livianos (logos, fuentes).

## Flujo de trabajo (por video)

1. Crear una carpeta dentro de `proyectos-video/` (ej. `proyectos-video/2026-09-17-reel-onboarding/`).
2. Poner adentro la grabación a cámara del avatar (y la de pantalla si hay).
3. Abrir Claude Code **en esa carpeta** y pedirle, con la plantilla de
   `~/.claude/skills/edicion-liquid/prompt-editor.md`:
   > Editá este video con la skill edicion-liquid, usando mi estilo.md.
   (`estilo.md` está en la raíz de este repo — copiar la ruta o el contenido al prompt).
4. La skill transcribe, corta silencios, arma las escenas, renderiza con HyperFrames+ffmpeg,
   revisa su propio render contra `estilo.md` y corrige sola hasta pasar el QA.
5. El resultado (`renders/final.mp4`) queda dentro de la carpeta del proyecto — no se sube al repo,
   se sube directo a Instagram.

## Setup de una máquina nueva (notebook / PC de escritorio)

Dependencias necesarias en el sistema (no viven en este repo):

| herramienta | versión | chequeo |
|---|---|---|
| Node.js | 22+ | `node -v` |
| ffmpeg (con ffprobe) | cualquiera reciente | `ffmpeg -version` |
| Python | 3.10+ | `python --version` |
| hyperframes | 0.8.43 exacto (npm global) | `hyperframes --version` |

Instalación (Windows, con winget):
```powershell
winget install Gyan.FFmpeg
winget install Python.Python.3.12
npm i -g hyperframes@0.8.43
```

Instalación (Mac, con Homebrew):
```bash
brew install node@22 ffmpeg python
npm i -g hyperframes@0.8.43
```

Después, copiar la skill a la carpeta de skills de Claude Code:
```bash
# Mac/Linux
cp -R edicion-liquid-skill/edicion-liquid ~/.claude/skills/edicion-liquid

# Windows (PowerShell)
Copy-Item -Recurse -Force edicion-liquid-skill\edicion-liquid "$HOME\.claude\skills\edicion-liquid"
```
Reiniciar Claude Code para que la detecte.

Detalle completo (incluye Skills oficiales de HyperFrames y whisper.cpp opcional):
`edicion-liquid-skill/INSTALAR.md`.

## Estado de `estilo.md`

Completar manualmente antes del primer video: nombre de marca, negocios a mostrar, colores,
tipografía, logos (rutas a `assets/`), tono de música. Guía: `edicion-liquid-skill/edicion-liquid/ejemplos/estilo-claudio.md`.
