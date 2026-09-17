#!/usr/bin/env bash
# transcribir.sh — transcribe un video/audio con whisper.cpp y deja .txt, .vtt y
# .json (JSON "full" de whisper.cpp) + <base>.words.json (segmentos y tokens con
# tiempos en segundos, formato simple para el resto del pipeline).
#
# Uso:
#   transcribir.sh -i <video|audio> -m <modelo.bin> [-o <dir_salida>] [-l es] [-t 8]
#
# Flags de whisper probados (no tocar sin medir):
#   -mc 0          sin contexto previo: evita los loops de repetición
#   -ml 60 -sow    segmentos cortos partidos por palabra: timestamps finos
#   -et 2.8 -tp 0 -tpi 0.2 -nth 0.5 -bs 5 -bo 5 -sns
#
# Requiere: whisper-cli (whisper.cpp), ffmpeg, python3. Windows: correr en Git Bash o WSL.
set -euo pipefail

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

[[ "${1:-}" == "--help" ]] && usage 0
IN=""; MODEL=""; OUT=""; LANG_="es"; THREADS=8
while getopts "i:m:o:l:t:h" opt; do
  case "$opt" in
    i) IN="$OPTARG" ;; m) MODEL="$OPTARG" ;; o) OUT="$OPTARG" ;;
    l) LANG_="$OPTARG" ;; t) THREADS="$OPTARG" ;; h) usage 0 ;; *) usage 1 ;;
  esac
done
[[ -z "$IN" || -z "$MODEL" ]] && usage 1
[[ -f "$IN" ]] || { echo "No existe la entrada: $IN" >&2; exit 1; }
[[ -f "$MODEL" ]] || { echo "No existe el modelo: $MODEL" >&2; exit 1; }
command -v whisper-cli >/dev/null || { echo "Falta whisper-cli (brew install whisper-cpp)" >&2; exit 1; }

base="$(basename "${IN%.*}")"
OUT="${OUT:-$(dirname "$IN")}"
mkdir -p "$OUT"
wav="$OUT/$base.16k.wav"

# whisper.cpp exige WAV 16 kHz mono PCM. Si la entrada ya lo es, se reusa.
fmt="$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of csv=p=0 "$IN" || true)"
if [[ "$fmt" == "pcm_s16le,16000,1" ]]; then
  wav="$IN"
else
  ffmpeg -v error -y -i "$IN" -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le "$wav"
fi

whisper-cli -m "$MODEL" -f "$wav" -l "$LANG_" -t "$THREADS" \
  -mc 0 -et 2.8 -tp 0 -tpi 0.2 -nth 0.5 -bs 5 -bo 5 -sns \
  -ml 60 -sow -pp -ovtt -otxt -ojf -of "$OUT/$base"

python3 - "$OUT/$base.json" "$OUT/$base.words.json" <<'PY'
import json, sys, re
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8", errors="replace"))
segs, words = [], []
for s in d.get("transcription", []):
    o = s["offsets"]; text = s["text"].strip()
    segs.append({"start": o["from"]/1000, "end": o["to"]/1000, "text": text})
    # Reconstruye palabras desde tokens (un token que empieza con espacio abre palabra).
    cur = None
    for t in s.get("tokens", []):
        tx = t["text"]
        if tx.startswith("[_") or not tx.strip():
            continue
        to = t.get("offsets", {"from": o["from"], "to": o["to"]})
        if tx.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur = {"word": tx.strip(), "start": to["from"]/1000, "end": to["to"]/1000, "p": t.get("p", 1)}
        else:
            cur["word"] += tx; cur["end"] = to["to"]/1000; cur["p"] = min(cur["p"], t.get("p", 1))
    if cur: words.append(cur)
words = [w for w in words if re.search(r"\w", w["word"])]
json.dump({"source": src, "segments": segs, "words": words}, open(dst, "w"), ensure_ascii=False, indent=1)
print(f"{len(segs)} segmentos, {len(words)} palabras -> {dst}")
PY
