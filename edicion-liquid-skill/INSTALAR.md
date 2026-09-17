# Instalar la skill edicion-liquid

Funciona en **Claude Code** y en **Codex**. Tiempo estimado: 10-15 minutos la primera vez.

## 1. Requisitos

| herramienta | versión | para qué |
|---|---|---|
| Node.js | 22 o más nuevo | HyperFrames y el constructor de escenas |
| ffmpeg | cualquiera reciente (con ffprobe) | cortes, audio, ensamblado |
| HyperFrames | **0.8.43** (fijada) | render de las escenas |
| GSAP | **3.15.0** (fijada, se instala por proyecto) | animación |
| Python | 3.10 o más nuevo | scripts de preparación y ensamblado |
| whisper.cpp | opcional | transcripción local, sin subir tu audio a ningún lado |

### Mac

```bash
# Homebrew: https://brew.sh
brew install node@22 ffmpeg python
brew install whisper-cpp          # opcional
npm i -g hyperframes@0.8.43
```

### Windows (PowerShell)

```powershell
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
winget install Python.Python.3.12
npm i -g hyperframes@0.8.43
```
whisper.cpp (opcional): bajá el binario de https://github.com/ggml-org/whisper.cpp/releases y agregalo al PATH.
Cerrá y abrí la terminal después de instalar, y comprobá:

```bash
node -v            # v22 o más
ffmpeg -version
hyperframes --version   # 0.8.43
```

## 2. Skills oficiales de HyperFrames

```bash
npx hyperframes skills          # primera vez: instala en las herramientas de IA que detecta
npx hyperframes skills update   # hyperframes, hyperframes-core, -cli, -animation, -keyframes, -audio, -registry, -creative, media-use
npx skills add heygen-com/hyperframes --skill talking-head-recut
```

## 3. Copiar la skill

Copiá la carpeta **`edicion-liquid/`** entera (no su contenido suelto):

| herramienta | Mac / Linux | Windows |
|---|---|---|
| Claude Code | `~/.claude/skills/edicion-liquid/` | `%USERPROFILE%\.claude\skills\edicion-liquid\` |
| Codex | `~/.codex/skills/edicion-liquid/` (o `~/.agents/skills/edicion-liquid/`) | `%USERPROFILE%\.codex\skills\edicion-liquid\` |

```bash
# Mac / Linux
mkdir -p ~/.claude/skills && cp -R edicion-liquid ~/.claude/skills/
mkdir -p ~/.codex/skills  && cp -R edicion-liquid ~/.codex/skills/     # si usás Codex
```
```powershell
# Windows
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force edicion-liquid "$HOME\.claude\skills\"
```

Reiniciá Claude Code / Codex para que la detecte.

## 4. Completar tu estilo

Abrí `edicion-liquid/estilo.md` (la copia instalada) y reemplazá cada `<<COMPLETAR>>`. Guiate con `edicion-liquid/ejemplos/estilo-claudio.md`.
Dejá tus logos y fotos en una carpeta tuya y poné las rutas en `estilo.md`.

## 5. Primer uso

1. Creá una carpeta para el video y poné adentro la grabación a cámara (y la de pantalla si hay).
2. Abrí Claude Code o Codex **en esa carpeta**.
3. Copiá la plantilla de `edicion-liquid/prompt-editor.md`, completala y pegala. Empezá con:
   > Editá este video con la skill edicion-liquid, usando mi estilo.md.
4. La IA prepara el proyecto (`npm i hyperframes@0.8.43 gsap@3.15.0`), transcribe, corta, arma las escenas, renderiza y se revisa sola antes de entregarte el video.

Consejo: para el primer video, probá con una grabación corta (2-3 minutos). Un render es un proceso por vez y tarda: en una Mac con chip M, unos 5 s por cada segundo de escena con vidrio.

## Problemas comunes

- **`hyperframes: command not found`** → reinstalá con `npm i -g hyperframes@0.8.43` y abrí una terminal nueva.
- **La skill no aparece** → verificá que la ruta sea `.../skills/edicion-liquid/SKILL.md` (no una carpeta de más en el medio).
- **"Falta node_modules/gsap"** → en la carpeta del proyecto: `npm i hyperframes@0.8.43 gsap@3.15.0`.
- **La tipografía no es igual a la de mi Mac** → es a propósito: el render reemplaza las fuentes de sistema por Inter para salir igual en cualquier máquina. Para una fuente exacta, poné el archivo en `assets/fonts/` y declaralo en `estilo.md`.
