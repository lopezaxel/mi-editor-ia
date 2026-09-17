#!/usr/bin/env python3
"""detectar_actividad_pantalla.py — detecta en una grabación de pantalla (iPad,
tablet, escritorio) los tramos donde la persona escribe, dibuja o cambia de
página/vista, por diferencia de frames a baja resolución.

Método
  - ffmpeg decodifica a --fps (CFR, las grabaciones de pantalla son de frecuencia
    variable), recorta la barra de estado de arriba y la barra de abajo
    (--excluir-arriba / --excluir-abajo, fracción del alto: el reloj y el % de
    zoom cambian solos) y escala a --ancho px en gris.
  - Por frame: fracción de píxeles con |diff| > --umbral (0-255).
  - Un frame está "activo" si cambian >= --min-px píxeles.
  - Tramos: frames activos contiguos, fusionando huecos < --fusionar s y
    descartando tramos < --min-dur s.
  - intensidad = píxeles cambiados por segundo dentro del tramo, normalizado
    al máximo del video (0-1). tipo = "cambio_de_vista" si algún frame cambia
    más de --frac-vista (scroll, zoom, hoja nueva); si no, "escritura".

Salidas
  --out tramos.json   (tramos + parámetros)
  --serie serie.npz   (opcional: fps y señal por frame, útil para sincronizar)
  --hojas DIR         (opcional: un JPG al final de cada tramo, para describirlo)

Uso
  detectar_actividad_pantalla.py --video pantalla.mp4 --out actividad.json \
     [--fps 30] [--ancho 342] [--umbral 18] [--fusionar 2.0] [--min-dur 0.6]
"""
import argparse, json, subprocess, os
import numpy as np

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--ancho", type=int, default=342, help="ancho de análisis (px, par)")
    ap.add_argument("--excluir-arriba", type=float, default=0.05)
    ap.add_argument("--excluir-abajo", type=float, default=0.05)
    ap.add_argument("--umbral", type=int, default=18, help="diferencia de gris mínima por píxel")
    ap.add_argument("--min-px", type=int, default=3, help="píxeles cambiados para marcar frame activo")
    ap.add_argument("--frac-vista", type=float, default=0.12, help="fracción que indica cambio de vista")
    ap.add_argument("--fusionar", type=float, default=2.0, help="fusiona huecos menores a esto (s)")
    ap.add_argument("--min-dur", type=float, default=0.6, help="descarta tramos más cortos (s)")
    ap.add_argument("--serie", help="guardar señal por frame (.npz)")
    ap.add_argument("--hojas", help="carpeta donde guardar un still al final de cada tramo")
    a = ap.parse_args()

    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:stream_side_data=rotation", "-of", "json", a.video]))["streams"][0]
    W, H = probe["width"], probe["height"]
    rot = int(next((sd.get("rotation", 0) for sd in probe.get("side_data_list", [])), 0))
    if abs(rot) % 180 == 90:  # ffmpeg autorrota: el frame decodificado viene girado
        W, H = H, W
    top = int(H * a.excluir_arriba); bot = int(H * a.excluir_abajo); ch = H - top - bot
    w = a.ancho - a.ancho % 2
    h = int(round(ch * w / W / 2)) * 2
    vf = f"fps={a.fps},crop={W}:{ch}:0:{top},scale={w}:{h}:flags=area,format=gray"
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-an", "-vf", vf,
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    fr = w * h
    prev = None; frac = []
    while True:
        buf = proc.stdout.read(fr)
        if len(buf) < fr:
            break
        cur = np.frombuffer(buf, np.uint8).astype(np.int16)
        if prev is None:
            frac.append(0.0)
        else:
            frac.append(float(np.count_nonzero(np.abs(cur - prev) > a.umbral)) / fr)
        prev = cur
    if proc.wait() != 0:
        raise SystemExit("ffmpeg falló decodificando la grabación")
    frac = np.array(frac)
    n = len(frac); fps = a.fps
    active = frac * fr >= a.min_px
    # tramos crudos
    raw = []
    i = 0
    while i < n:
        if active[i]:
            j = i
            while j + 1 < n and active[j + 1]:
                j += 1
            raw.append([i, j + 1]); i = j + 1
        else:
            i += 1
    merged = []
    for s, e in raw:
        if merged and (s - merged[-1][1]) / fps < a.fusionar:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    tramos = []
    rates = []
    for s, e in merged:
        dur = (e - s) / fps
        if dur < a.min_dur:
            continue
        seg = frac[s:e]
        rate = float(seg.sum() * fr / dur)
        rates.append(rate)
        tramos.append({"inicio_s": round(s / fps, 3), "fin_s": round(e / fps, 3), "dur_s": round(dur, 3),
                       "px_por_s": round(rate, 1), "max_frac": round(float(seg.max()), 4),
                       "tipo": "cambio_de_vista" if seg.max() > a.frac_vista else "escritura"})
    mx = max(rates) if rates else 1
    for t in tramos:
        t["intensidad"] = round(min(1.0, t["px_por_s"] / mx), 3)
    if a.hojas:
        os.makedirs(a.hojas, exist_ok=True)
        for k, t in enumerate(tramos):
            p = os.path.join(a.hojas, f"tramo-{k:03d}-{t['fin_s']:.1f}s.jpg")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, t["fin_s"] - 0.05)), "-i", a.video,
                            "-frames:v", "1", "-vf", "scale=683:-2", p], check=True)
            t["still"] = p
    out = {"video": a.video, "dur_analizada_s": round(n / fps, 3), "parametros": vars(a),
           "activo_total_s": round(sum(t["dur_s"] for t in tramos), 2), "tramos": tramos}
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    if a.serie:
        np.savez_compressed(a.serie, fps=fps, frac=frac)
    print(f"{len(tramos)} tramos, {out['activo_total_s']} s activos de {out['dur_analizada_s']} s -> {a.out}")

if __name__ == "__main__":
    main()
