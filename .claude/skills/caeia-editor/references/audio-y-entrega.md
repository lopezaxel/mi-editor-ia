# Audio y entrega

Probado en Windows con HyperFrames 0.8.43 el 2026-10-10. El render de HyperFrames sale **mudo** porque el crudo va con `muted`. El audio se arma después con ffmpeg.

## A. Solo la voz del crudo + formato de entrega
```bash
ffmpeg -y -i renders/video.mp4 -i assets/crudo.mp4 -map 0:v -map 1:a \
  -c:v libx264 -profile:v high -crf 18 -preset slow -pix_fmt yuv420p \
  -vf "scale=out_color_matrix=bt709:out_range=tv" -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart renders/final.mp4
```
Si el crudo empieza recortado (`data-media-start="S"`), agregá `-ss S` antes de `-i assets/crudo.mp4`.

## B. Voz + música que eligió Axel, con ducking bajo la voz
```bash
ffmpeg -y -i renders/video.mp4 -i assets/crudo.mp4 -stream_loop -1 -i assets/musica.mp3 -filter_complex \
 "[1:a]aresample=48000,asplit=2[voz][sc];[2:a]aresample=48000,volume=0.5[mus];\
  [mus][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];\
  [voz][duck]amix=inputs=2:normalize=0:duration=first,afade=t=out:st=DUR-1:d=1,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart renders/mezcla.mp4
```
- Reemplazá `DUR-1` por el número (duración menos 1 s).
- Música tenue: si Axel dice que está alta, bajá `volume=0.5` a 0,35 o 0,25. Nunca la subas por iniciativa propia.
- Sin voz (solo música): sacá la rama del sidechain y usá `[2:a]volume=0.8,afade…`.
- Después pasá `renders/mezcla.mp4` por la receta A (con `-map 0:v -map 0:a`) si hace falta el formato de entrega.
- Para alinear efectos al pico de la animación o con la música: `kit/scripts/audio_tools.py` (`peaks`, `music`, `check`). Necesitan `numpy`; pedile el OK a Axel antes de `pip install numpy`.
- Voz de ElevenLabs: `kit/scripts/eleven_vo.py`. La key va en la variable `ELEVENLABS_API_KEY` (`setx ELEVENLABS_API_KEY sk_...`), **nunca en el chat**.

## C. Chequeo antes de entregar
```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,pix_fmt,color_range,color_space,nb_frames -of compact renders/final.mp4
ffmpeg -nostats -i renders/final.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:"
```
Pasa si:
- video `h264`, `yuv420p`, `color_range=tv`, `bt709`;
- tamaño correcto (1080×1920 o 1920×1080);
- `nb_frames` = duración × fps;
- una pista `aac`;
- ≈ −14 LUFS.

Después extraé 3 cuadros del final y miralos a tamaño de teléfono:
```bash
ffmpeg -v error -ss T -i renders/final.mp4 -frames:v 1 qa/final-T.png
```
