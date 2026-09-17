#!/usr/bin/env python3
"""ensamblar.py — arma un video editado frame-exacto a partir de timeline.json
(cortar_silencios.py) y, opcional, la pista secundaria (pantalla) alineada.

Normalización (el concat -c copy solo es seguro si todas las partes son iguales):
  fps=60 explícito ANTES de select (las fuentes de iPhone son de frecuencia
  variable), select por número de frame, setpts=N/(60*TB),
  h264_videotoolbox 25M (fallback libx264 CRF 16), -bf 0, -g 60, yuv420p,
  -video_track_timescale 15360. Concat final -c copy con el audio mapeado
  aparte, -map_metadata -1 (borra GPS y datos del iPhone), +faststart, escribe
  <out>.partial.mp4 y renombra solo si el conteo de frames da exacto.

Modos
  camara (defecto): una pasada de decodificación por toma con select sobre los
    segmentos del timeline. --vf-toma aplica un filtro por toma (look,
    reencuadre); si se pasa uno solo, vale para todas.
  pantalla: --pantalla <video> --offsets o1 o2 ... (t_toma = t_pantalla + o).
    Cada frame editado toma el frame de pantalla correspondiente; donde no hay
    grabación va un fondo --fondo (blanco). Salida --tamano WxH (por defecto
    1080x1440, 3:4). Offsets redondeados al frame (error <= 8 ms a 60 fps).

Uso
  ensamblar.py --timeline timeline.json --out camara.mp4 [--audio voz.wav] \\
      [--vf-toma "<look>" "<look>"] [--tmp dir]
  ensamblar.py --timeline timeline.json --out pantalla.mp4 --modo pantalla \\
      --pantalla ScreenRecording.MP4 --offsets 145.48 -479.95 [--tamano 1080x1440]
"""
import argparse, json, os, shutil, subprocess, sys

FPS = 60
TAGS = "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709"

def encoder_args(bitrate):
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    except Exception:
        out = ""
    common = ["-bf", "0", "-g", str(FPS), "-pix_fmt", "yuv420p", "-video_track_timescale", "15360",
              "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    if "h264_videotoolbox" in out:
        return ["-c:v", "h264_videotoolbox", "-b:v", bitrate, "-profile:v", "high"] + common
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-profile:v", "high", "-x264opts", "bframes=0"] + common

def probe_frames(path):
    d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
        "-show_entries", "stream=nb_read_packets,r_frame_rate,time_base,width,height,has_b_frames", "-of", "json", path]))
    return d["streams"][0]

def run(cmd):
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"falló: {' '.join(cmd[:12])} ...")

def select_expr(ranges):
    return "+".join(f"between(n\\,{a}\\,{b - 1})" for a, b in ranges)

def encode_select(src, ranges, vf_extra, out, enc, size=None, pad_white=False):
    """ranges: [(ini, fin_excl)] en frames del grid 60 fps de src, crecientes."""
    total = sum(b - a for a, b in ranges)
    first = ranges[0][0]
    ss = first // FPS  # seek al segundo entero, el resto se resuelve por número de frame
    shifted = [(a - ss * FPS, b - ss * FPS) for a, b in ranges]
    # select con expresión larga: se escribe a un script de filtros
    chain = f"fps={FPS},select='{select_expr(shifted)}',setpts=N/({FPS}*TB)"
    if size:
        w, h = size
        chain += f",scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:white"
    if vf_extra:
        chain += "," + vf_extra
    chain += ",setsar=1,format=yuv420p," + TAGS
    script = out + ".filtro.txt"
    open(script, "w").write(chain)
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", src, "-an", "-filter_script:v", script,
         "-frames:v", str(total), *enc, "-map_metadata", "-1", out])
    got = int(probe_frames(out)["nb_read_packets"])
    if got != total:
        sys.exit(f"{out}: {got} frames, esperaba {total}")
    return total

def encode_color(frames, size, color, out, enc):
    """Fondo liso. Blanco/negro se escriben directo en YUV de rango TV (235/16) para que
    coincidan bit a bit con el blanco de la grabación y el decodificador no vea un
    cambio de parámetros entre partes."""
    w, h = size
    vf = "setsar=1,format=yuv420p"
    if color in ("white", "black"):
        vf += f",geq=lum={235 if color == 'white' else 16}:cb=128:cr=128"
    vf += "," + TAGS  # sin esto ffmpeg reescala el rango al codificar (blanco 235 -> 233)
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}:r={FPS}",
         "-frames:v", str(frames), "-vf", vf, *enc, "-map_metadata", "-1", out])
    assert int(probe_frames(out)["nb_read_packets"]) == frames

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio", help="wav alineado (se codifica AAC 320k)")
    ap.add_argument("--modo", choices=["camara", "pantalla"], default="camara")
    ap.add_argument("--vf-toma", nargs="*", default=[], help="filtro por toma (o uno para todas)")
    ap.add_argument("--pantalla")
    ap.add_argument("--offsets", type=float, nargs="*")
    ap.add_argument("--tamano", default=None, help="WxH (modo pantalla: 1080x1440 por defecto)")
    ap.add_argument("--fondo", default="white")
    ap.add_argument("--bitrate", default="25M")
    ap.add_argument("--tmp", help="carpeta de partes (por defecto <out>.partes/)")
    ap.add_argument("--conservar-partes", action="store_true")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    segs = tl["segmentos"]; total = tl["frames_totales"]
    tmp = a.tmp or (os.path.splitext(a.out)[0] + ".partes")
    os.makedirs(tmp, exist_ok=True)
    enc = encoder_args(a.bitrate)
    parts = []
    if a.modo == "camara":
        tomas = sorted({s["toma"] for s in segs})
        size = tuple(int(v) for v in a.tamano.split("x")) if a.tamano else None
        for ti in tomas:
            ss = [s for s in segs if s["toma"] == ti]
            vf = a.vf_toma[ti] if ti < len(a.vf_toma) else (a.vf_toma[0] if a.vf_toma else "")
            out = os.path.join(tmp, f"toma{ti}.mp4")
            n = encode_select(ss[0]["video"], [(s["src_ini_frame"], s["src_fin_frame"]) for s in ss], vf, out, enc, size)
            print(f"toma {ti}: {n} frames", flush=True)
            parts.append(out)
    else:
        if not (a.pantalla and a.offsets):
            sys.exit("modo pantalla requiere --pantalla y --offsets")
        size = tuple(int(v) for v in (a.tamano or "1080x1440").split("x"))
        pdur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                              "-of", "default=nw=1:nk=1", a.pantalla]).decode().split()[0])
        pn = int(pdur * FPS) - 1  # último frame seguro
        pieces = []  # (tipo, a, b) con a,b en frames de pantalla o cantidad
        for s in segs:
            off = round(a.offsets[s["toma"]] * FPS)
            m0, m1 = s["src_ini_frame"] - off, s["src_fin_frame"] - off
            cur = m0
            if cur < 0:
                k = min(m1, 0) - cur; pieces.append(["color", k]); cur += k
            if cur < m1 and cur < pn:
                e = min(m1, pn); pieces.append(["pant", cur, e]); cur = e
            if cur < m1:
                pieces.append(["color", m1 - cur])
        # fusiona piezas contiguas del mismo tipo
        runs = []
        for p in pieces:
            if runs and runs[-1][0] == p[0]:
                if p[0] == "color": runs[-1][1] += p[1]
                else: runs[-1][1].append((p[1], p[2]))
            else:
                runs.append(["color", p[1]] if p[0] == "color" else ["pant", [(p[1], p[2])]])
        for i, r in enumerate(runs):
            out = os.path.join(tmp, f"pieza{i:02d}.mp4")
            if r[0] == "color":
                encode_color(r[1], size, a.fondo, out, enc)
            else:
                encode_select(a.pantalla, r[1], "", out, enc, size)
            parts.append(out)
            print(f"pieza {i}: {r[0]} {r[1] if r[0]=='color' else sum(b-x for x,b in r[1])} frames", flush=True)
    for p in parts:
        v = probe_frames(p)
        assert v["r_frame_rate"] == "60/1" and v["time_base"] == "1/15360" and int(v.get("has_b_frames", 0)) == 0, (p, v)
    listing = os.path.join(tmp, "concat.txt")
    with open(listing, "w") as f:
        for p in parts:
            f.write("file '" + os.path.abspath(p).replace("'", "'\\''") + "'\n")
    partial = os.path.splitext(a.out)[0] + ".partial.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing]
    if a.audio:
        cmd += ["-i", a.audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
    else:
        cmd += ["-map", "0:v:0", "-c", "copy"]
    cmd += ["-map_metadata", "-1", "-map_chapters", "-1", "-movflags", "+faststart", partial]
    run(cmd)
    got = int(probe_frames(partial)["nb_read_packets"])
    if got != total:
        sys.exit(f"concat: {got} frames, esperaba {total}; queda {partial} para revisar")
    os.replace(partial, a.out)
    if not a.conservar_partes:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK {a.out}: {got} frames = {got / FPS:.3f} s")

if __name__ == "__main__":
    main()
