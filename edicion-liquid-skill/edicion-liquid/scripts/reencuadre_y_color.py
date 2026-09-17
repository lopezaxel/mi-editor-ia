#!/usr/bin/env python3
"""reencuadre_y_color.py — prueba un reencuadre (zoom + centro) y una corrección
de color/luz con filtros de ffmpeg sobre stills, y deja la cadena lista para
reutilizar.

Por cada tiempo pedido genera en --out-dir:
  <prefijo>-<t>-antes.jpg         frame original
  <prefijo>-<t>-despues.jpg       reencuadre --zoom + look
  <prefijo>-<t>-punch.jpg         (si --punch) reencuadre al zoom de punch-in + look
  <prefijo>-<t>-comparar.jpg      antes | después lado a lado (mitad de resolución)
y un <prefijo>-reencuadre.json con la geometría de crop y las cadenas.

Reencuadre: ventana = W/zoom × H/zoom (par), centrada en --centro x,y (px de la
fuente), limitada a los bordes, escalada de vuelta a W×H con lanczos.

Look por defecto (exterior soleado, natural): baja un poco el contraste para
sostener cielo y cara, curva con roll-off de altas y sombras apenas levantadas,
saturación +3 %, rojo de medios -1 % (la piel al sol sale colorada en iPhone) y un unsharp suave para
compensar el zoom. Se reemplaza con --look "<cadena ffmpeg>".

Uso
  reencuadre_y_color.py --video toma.mov --tiempos 30 200 400 --zoom 1.4 \\
      --centro 950,540 [--punch 1.7 --centro-punch 950,516] --out-dir look/ [--prefijo t1]
"""
import argparse, json, os, subprocess

LOOK = ("eq=contrast=0.96:saturation=1.03,"
        "curves=master='0/0.015 0.2/0.215 0.5/0.505 0.8/0.785 1/0.96',"
        "colorbalance=rs=0.0:bs=0.01:rm=-0.01:bm=-0.005:rh=0.0:bh=0.0")
SHARP = "unsharp=5:5:0.35:5:5:0.0"

def probe(path):
    d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                            "stream=width,height", "-of", "json", path]))["streams"][0]
    return d["width"], d["height"]

def crop_chain(W, H, zoom, cx, cy):
    cw = int(round(W / zoom / 2)) * 2; ch = int(round(H / zoom / 2)) * 2
    x = int(min(max(0, round(cx - cw / 2)), W - cw)); y = int(min(max(0, round(cy - ch / 2)), H - ch))
    return {"zoom": zoom, "centro": [cx, cy], "crop": {"w": cw, "h": ch, "x": x, "y": y},
            "filtro": f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos"}

def grab(video, t, vf, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                    "-vf", vf, "-q:v", "2", out], check=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--tiempos", type=float, nargs="+", required=True)
    ap.add_argument("--zoom", type=float, default=1.4)
    ap.add_argument("--centro", required=True, help="x,y en px de la fuente")
    ap.add_argument("--punch", type=float, help="zoom de punch-in (p. ej. 1.7)")
    ap.add_argument("--centro-punch", help="x,y para el punch-in (por defecto = --centro)")
    ap.add_argument("--look", default=LOOK, help="cadena de color ffmpeg")
    ap.add_argument("--sin-nitidez", action="store_true")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--prefijo", default="still")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    W, H = probe(a.video)
    cx, cy = (float(v) for v in a.centro.split(","))
    base = crop_chain(W, H, a.zoom, cx, cy)
    look = a.look if a.sin_nitidez else f"{a.look},{SHARP}"
    res = {"video": a.video, "tamano": [W, H], "base": base, "look": a.look, "nitidez": None if a.sin_nitidez else SHARP,
           "cadena_look": f"{a.look},format=yuv420p",
           "cadena_base_completa": f"{base['filtro']},{look},format=yuv420p", "stills": []}
    if a.punch:
        px, py = (float(v) for v in (a.centro_punch or a.centro).split(","))
        punch = crop_chain(W, H, a.punch, px, py)
        res["punch"] = punch
        res["cadena_punch_completa"] = f"{punch['filtro']},{look},format=yuv420p"
    for t in a.tiempos:
        tag = f"{a.prefijo}-{t:07.2f}".replace(".", "_")
        antes = os.path.join(a.out_dir, f"{tag}-antes.jpg")
        despues = os.path.join(a.out_dir, f"{tag}-despues.jpg")
        grab(a.video, t, "null", antes)
        grab(a.video, t, res["cadena_base_completa"], despues)
        item = {"t": t, "antes": antes, "despues": despues}
        if a.punch:
            p = os.path.join(a.out_dir, f"{tag}-punch.jpg"); grab(a.video, t, res["cadena_punch_completa"], p)
            item["punch"] = p
        comp = os.path.join(a.out_dir, f"{tag}-comparar.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", antes, "-i", despues, "-filter_complex",
                        f"[0]scale={W//2}:-2[a];[1]scale={W//2}:-2[b];[a][b]hstack", "-q:v", "2", comp], check=True)
        item["comparar"] = comp
        res["stills"].append(item)
    out = os.path.join(a.out_dir, f"{a.prefijo}-reencuadre.json")
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print("cadena base :", res["cadena_base_completa"])
    if a.punch: print("cadena punch:", res["cadena_punch_completa"])
    print("look solo   :", res["cadena_look"])
    print("->", out)

if __name__ == "__main__":
    main()
