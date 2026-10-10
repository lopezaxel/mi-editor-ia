# Prompt para tu editor

> Tomalo como si le hablaras a tu editor. Copiá la plantilla, completala y pegala en Claude Code o Codex junto con tus archivos.
> Lo que no sepas, dejalo en blanco: la IA te lo pregunta en bloque antes de empezar.

## Plantilla

```markdown
Editá este video con la skill edicion-liquid, usando mi estilo.md.

## 1. Video base y fuentes
- Video a cámara: <ruta>
- Grabación de pantalla / iPad: <ruta o "no hay">
- Assets extra (logos, fotos, capturas): <rutas>
- Música: <ruta o "la de estilo.md">
- Estilo visual: <liquid-glass (default) | saturado-bold | otro de estilos/ | "elegí vos según el tono">
- Formato: <horizontal 16:9 (default) | vertical 9:16 (reel/TikTok)>

## 2. Objetivo del video
- De qué trata, en una línea: <...>
- Qué tiene que hacer el que lo mira al terminar: <...>

## 3. Intro (primeros __ segundos)
- Qué mostrar: <titular, cifras, logos, foto, diagrama...>
- Datos (solo los que digo en cámara o están en estilo.md): <...>
- Logos: <cuáles y cuándo>
- Fotos: <cuáles y cuándo>

## 4. Cuerpo
- Ideas que quiero reforzar en pantalla (con el minuto aproximado): <...>
- Frecuencia: <la de estilo.md u otra>

## 5. Escenas de pantalla
- <minuto> → <qué muestro en la pantalla/iPad y si va split-screen o ventana>

## 6. Música
- <como estilo.md / más baja / sin música en tal tramo>

## 7. Cortes y pausas
- Cortar: <silencios, muletillas, tomas repetidas, tramos>
- Respetar: <pausas que quiero dejar>

## 8. Bloopers a conservar
- <minuto y por qué>

## 9. Entrega
- Archivo: <ruta y nombre>
- Formato: 1920×1080, 60 fps
- Antes de entregar: revisá tu render solo y corregí lo que haga falta.
```

## Ejemplo lleno

```markdown
Editá este video con la skill edicion-liquid, usando mi estilo.md.

## 1. Video base y fuentes
- Video a cámara: videos/2026-09-16-camara.mov
- Grabación de pantalla / iPad: videos/2026-09-16-ipad.mov (dibujo el framework)
- Assets extra: assets/logos/software.png, assets/logos/consultoria.png, assets/landing-captura.png
- Música: la de estilo.md
- Estilo visual: liquid-glass (default)
- Formato: horizontal (default)

## 2. Objetivo del video
- De qué trata: cómo edito mis videos con IA sin tocar un programa de edición.
- Qué tiene que hacer el que lo mira: descargar la skill desde el link de la descripción.

## 3. Intro (primeros 45 segundos)
- Qué mostrar: titular "EDITO CON IA." con pastilla "SIN CAPCUT."; después mis dos negocios con sus logos; después el framework en una fila.
- Datos: solo los que digo en cámara (la IA toma el minuto del transcript).
- Logos: software cuando lo nombro, consultoría cuando la nombro.
- Fotos: ninguna.

## 4. Cuerpo
- ~02:10 "hablale como a tu editor" → frase al costado.
- ~04:30 los tres archivos que hay que tener → pasos.
- ~06:00 el loop que se revisa solo → diagrama en columna.
- Frecuencia: la de estilo.md.

## 5. Escenas de pantalla
- 03:05 → muestro en el iPad el dibujo del framework: split-screen hasta 03:50.
- 08:20 → la landing de descarga: ventana con scroll, 10 segundos.

## 6. Música
- Como estilo.md, sin música en los primeros 3 segundos.

## 7. Cortes y pausas
- Cortar: silencios largos, "eh", la toma repetida de 05:10 a 05:40.
- Respetar: la pausa después de "sin tocar un programa".

## 8. Bloopers a conservar
- 07:12, cuando se me cae el lápiz: queda, le da vida.

## 9. Entrega
- Archivo: renders/2026-09-16-final.mp4
- Resolución: 1920×1080, 60 fps (según el Formato de la sección 1)
- Antes de entregar: revisá tu render solo y corregí lo que haga falta.
```

## Ejemplo lleno (reel vertical con avatar de IA)

Caso típico: varios clips cortos de un avatar de IA clonado, unidos en un solo reel corto para Instagram/TikTok — sin grabación de pantalla, foco 100% en retener del segundo 1.

```markdown
Editá este video con la skill edicion-liquid, usando mi estilo.md.

## 1. Video base y fuentes
- Video a cámara: videos/avatar-clip-1.mp4, videos/avatar-clip-2.mp4, videos/avatar-clip-3.mp4, videos/avatar-clip-4.mp4 (unir en ese orden)
- Grabación de pantalla / iPad: no hay
- Assets extra: assets/logos/caeia.png
- Música: la de estilo.md
- Estilo visual: saturado-bold (gancho agresivo, primeros 3 segundos)
- Formato: vertical (reel de Instagram/TikTok)

## 2. Objetivo del video
- De qué trata: por qué facturar por WhatsApp con CAEIA es más rápido que ARCA.
- Qué tiene que hacer el que lo mira: quedarse viendo hasta el final y probar la app.

## 3. Intro (primeros 3 segundos)
- Qué mostrar: titular gancho apenas arranca el primer clip (ej. "ARCA TE HACE PERDER TIEMPO."), sin esperar a que la persona termine la frase.
- Datos: solo los que digo en cámara.
- Logos: logo de CAEIA en el cierre, no en la intro.

## 4. Cuerpo (todo el reel, no solo la intro)
- Denso de punta a punta: cada escena en `"mode": "intro"` (ver SKILL.md § Ritmo para reels cortos) — no bajar el ritmo a mitad de video.
- Un recurso gráfico por clip como mínimo (cifra, frase o pasos), tomado de lo que digo en cada uno.
- Frecuencia: cada 3-6 segundos, no cada 30-60 como en un video largo.

## 5. Escenas de pantalla
- No aplica (sin grabación de pantalla en este reel).

## 6. Música
- Como estilo.md, presente desde el segundo 0 (no hay "intro sin música" en un reel de 3s).

## 7. Cortes y pausas
- Cortar: silencios entre los 4 clips, cualquier arranque falso al inicio de cada uno.
- Respetar: nada especial, priorizar ritmo sobre pausas naturales.

## 8. Bloopers a conservar
- Ninguno (es avatar de IA, no aplica).

## 9. Entrega
- Archivo: renders/2026-09-18-reel-final.mp4
- Resolución: 1080×1920, 60 fps
- Antes de entregar: revisá tu render solo y corregí lo que haga falta.
```
