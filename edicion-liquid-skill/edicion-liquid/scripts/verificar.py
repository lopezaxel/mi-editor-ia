#!/usr/bin/env python3
"""verificar.py — control de calidad técnico de un video renderizado.

Chequea (ffprobe/ffmpeg):
  - códec, tamaño, fps declarado (r_frame_rate) y que sea CFR (avg == r),
  - frames reales (conteo de paquetes) contra --frames-esperados (opcional),
  - duración de video vs audio (diferencia máxima --tol-av, 1 frame por defecto),
  - B-frames y timebase (esperado 1/15360 si --timebase),
  - metadatos sensibles (GPS/ubicación, modelo del teléfono),
  - decodificación completa sin errores (ffmpeg -v error -f null),
  - hoja de contacto con N frames repartidos y su timestamp.

Uso
  verificar.py --video final.mp4 [--frames-esperados 44260] [--n 16] \\
      [--hoja hoja.jpg] [--json qa.json] [--timebase 1/15360] [--sin-decodificar]
Sale con código 1 si algo falla.
"""
import argparse, json, subprocess, sys

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--frames-esperados", type=int)
    ap.add_argument("--fps", default="60/1")
    ap.add_argument("--timebase")
    ap.add_argument("--tol-av", type=float, default=None, help="tolerancia video-audio en s (def. 1 frame)")
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--hoja")
    ap.add_argument("--json")
    ap.add_argument("--sin-decodificar", action="store_true")
    a = ap.parse_args()
    fails = []
    d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_packets", "-show_streams",
                                            "-show_format", "-of", "json", a.video]))
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    au = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den
    frames = int(v["nb_read_packets"])
    vdur = float(v.get("duration", d["format"]["duration"]))
    r = {"video": a.video, "codec": v["codec_name"], "tamano": f"{v['width']}x{v['height']}", "pix_fmt": v.get("pix_fmt"),
         "r_frame_rate": v["r_frame_rate"], "avg_frame_rate": v["avg_frame_rate"], "time_base": v["time_base"],
         "has_b_frames": int(v.get("has_b_frames", 0)), "frames": frames, "dur_video_s": vdur,
         "dur_frames_s": round(frames / fps, 4)}
    if v["r_frame_rate"] != a.fps: fails.append(f"fps {v['r_frame_rate']} != {a.fps}")
    if v["avg_frame_rate"] != v["r_frame_rate"]:
        an, ad = (int(x) for x in v["avg_frame_rate"].split("/"))
        if ad == 0 or abs(an / ad - fps) > 0.01: fails.append(f"no CFR: avg {v['avg_frame_rate']}")
    if a.frames_esperados is not None and frames != a.frames_esperados:
        fails.append(f"frames {frames} != {a.frames_esperados}")
    if a.timebase and v["time_base"] != a.timebase: fails.append(f"timebase {v['time_base']}")
    if r["has_b_frames"]: fails.append("tiene B-frames")
    if au:
        adur = float(au.get("duration", 0))
        r.update({"audio_codec": au["codec_name"], "audio_sr": au.get("sample_rate"), "dur_audio_s": adur,
                  "dif_av_s": round(adur - frames / fps, 4)})
        tol = a.tol_av if a.tol_av is not None else 1.0 / fps + 0.03  # AAC agrega priming/padding
        if abs(adur - frames / fps) > tol: fails.append(f"audio {adur:.3f}s vs video {frames / fps:.3f}s")
    else:
        r["audio_codec"] = None
    tags = {**d["format"].get("tags", {}), **v.get("tags", {})}
    sens = {k: val for k, val in tags.items() if any(x in k.lower() for x in ("location", "iso6709", "gps", "model", "make"))}
    r["metadatos_sensibles"] = sens
    if sens: fails.append(f"metadatos sensibles: {list(sens)}")
    if not a.sin_decodificar:
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-f", "null", "-"], capture_output=True, text=True)
        errs = [l for l in p.stderr.splitlines() if l.strip()]
        r["decodificacion"] = {"ok": p.returncode == 0 and not errs, "errores": errs[:20], "n_errores": len(errs)}
        if not r["decodificacion"]["ok"]: fails.append(f"decodificación con {len(errs)} errores")
    if a.hoja:
        n = max(1, a.n); cols = 4 if n > 4 else n; rows = -(-n // cols)
        times = [vdur * (i + 0.5) / n for i in range(n)]
        sel = "+".join(f"eq(n\\,{int(t * fps)})" for t in times)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf",
                        f"select='{sel}',scale=480:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}",
                        "-frames:v", "1", "-fps_mode", "passthrough", a.hoja], check=True)
        r["hoja"] = a.hoja
    r["fallas"] = fails; r["ok"] = not fails
    if a.json: json.dump(r, open(a.json, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(r, indent=1, ensure_ascii=False))
    sys.exit(0 if r["ok"] else 1)

if __name__ == "__main__":
    main()
