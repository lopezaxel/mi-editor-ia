#!/usr/bin/env python3
"""sincronizar_pantalla.py — encuentra el offset de una grabación secundaria
(p. ej. grabación de pantalla de iPad con su propio audio) contra una o varias
tomas de cámara, por correlación cruzada normalizada del audio.

Convención del resultado:  t_camara = t_secundaria + offset
(offset > 0 => la secundaria arrancó `offset` segundos después que la toma).

Método
  1. Decodifica ambos audios a mono 8 kHz (ffmpeg), filtro pasa-altos 150 Hz
     (saca viento/rumble) y pasa-bajos 3,4 kHz (voz).
  2. Parte la secundaria en ventanas de --win s cada --hop s. Cada ventana se
     correlaciona (NCC deslizante, FFT) contra cada toma completa.
  3. Una ventana "acierta" si su pico NCC >= --min-ncc y el pico supera al
     segundo mejor pico (fuera de ±0,5 s) por --min-ratio.
  4. El offset de la toma es la mediana de las ventanas que acertaron; se
     refina a 48 kHz (±20 ms) sobre la mejor ventana. Se reporta la dispersión,
     la deriva (ppm) y la verificación en 3 ventanas distintas (inicio, medio,
     fin del solapamiento).

Modo visual (automático si el audio de la secundaria está mudo, < -80 dBFS;
forzable con --modo visual). Las grabaciones de pantalla de iPad a menudo
guardan una pista de audio digitalmente muda. Entonces:
  1. Offset inicial = diferencia de creation_time (resolución 1 s, iOS trunca) o
     --offset-inicial por toma.
  2. Señal A: píxeles que cambian por frame en la pantalla (escritura/dibujo),
     a 60 fps. Señal B: movimiento dentro de --roi en la cámara (la mano con el
     lápiz sobre la tablet), a 60 fps. Ambas en log y pasa-altos.
  3. NCC de A contra B en ±--busqueda s alrededor del offset inicial. Se
     reporta pico, pico/segundo pico y el mejor lag en 3 tercios del
     solapamiento (verificación).

Uso
  sincronizar_pantalla.py --secundaria pantalla.mp4 --tomas toma1.mov toma2.mov \
      --out pantalla-sync.json [--win 20] [--hop 15] [--min-ncc 0.25] \
      [--modo auto|audio|visual] [--roi 870,540,260,130 760,430,300,220] [--busqueda 1.2]
      [--actividad actividad.json] [--hojas DIR]
      [--offset-inicial 145.5 -482.0]
"""
import argparse, json, subprocess, sys
import numpy as np
from scipy import signal

def load(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "1",
                          "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def bandpass(x, sr):
    sos = signal.butter(4, [150, min(3400, sr / 2 - 100)], btype="band", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, x)

def ncc(big, small):
    """NCC deslizante de `small` sobre `big` (modo valid)."""
    small = small - small.mean()
    ns = np.linalg.norm(small)
    if ns == 0 or len(big) < len(small):
        return None
    num = signal.fftconvolve(big, small[::-1], mode="valid")
    c1 = np.concatenate([[0], np.cumsum(big)]); c2 = np.concatenate([[0], np.cumsum(big * big)])
    n = len(small)
    s1 = c1[n:] - c1[:-n]; s2 = c2[n:] - c2[:-n]
    var = np.maximum(s2 - s1 * s1 / n, 1e-12)
    return num / (ns * np.sqrt(var))

def best_peak(c, sr, excl=0.5):
    i = int(np.argmax(c)); p = float(c[i])
    m = c.copy(); lo = max(0, i - int(excl * sr)); m[lo:i + int(excl * sr)] = -1
    second = float(m.max()) if len(m) else 0.0
    return i, p, second

def creation_time(path):
    import datetime as dt
    out = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                               "format_tags=creation_time:format=duration", "-of", "json", str(path)]))
    ct = out["format"].get("tags", {}).get("creation_time")
    t = dt.datetime.fromisoformat(ct.replace("Z", "+00:00")).timestamp() if ct else None
    return t, float(out["format"]["duration"])

def motion_series(path, fps, roi=None, start=0.0, dur=None, width=160, thr=None):
    """Energía de movimiento por frame (media |diff|) o px cambiados si thr."""
    vf = f"fps={fps}"
    if roi:
        x, y, w, h = roi; vf += f",crop={w}:{h}:{x}:{y}"
    vf += f",scale={width}:-2:flags=area,format=gray"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(path)]
    if dur: cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-an", "-vf", vf, "-f", "rawvideo", "-"]
    probe = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(path), "-frames:v", "1",
                            "-vf", vf, "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    # alto real tras el escalado: lo deducimos de un frame
    fsz = len(probe)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    prev = None; out = []
    while True:
        b = p.stdout.read(fsz)
        if len(b) < fsz: break
        c = np.frombuffer(b, np.uint8).astype(np.int16)
        if prev is None: out.append(0.0)
        else:
            d = np.abs(c - prev)
            out.append(float(np.count_nonzero(d > thr)) if thr else float(d.mean()))
        prev = c
    if p.wait() != 0:
        raise SystemExit(f"ffmpeg falló leyendo {path}")
    return np.array(out)

def prep(x, fps):
    x = np.log1p(np.asarray(x, float))
    sos = signal.butter(2, 0.3, btype="high", fs=fps, output="sos")
    x = signal.sosfiltfilt(sos, x)
    return (x - x.mean()) / (x.std() + 1e-9)

def lag_search(a, b, fps, lo, hi):
    """Índice b = índice a + lag. Devuelve lags (s) y NCC en el solapamiento para lag en [lo,hi] s."""
    lags = np.arange(int(round(lo * fps)), int(round(hi * fps)) + 1)
    vals = []
    for L in lags:
        i0 = max(0, -L); i1 = min(len(a), len(b) - L)
        if i1 - i0 < fps * 5:
            vals.append(-1.0); continue
        aa = a[i0:i1]; bb = b[i0 + L:i1 + L]
        vals.append(float(np.dot(aa - aa.mean(), bb - bb.mean()) / (len(aa) * aa.std() * bb.std() + 1e-9)))
    return lags / fps, np.array(vals)

def gray_frames(path, ss, t, vf, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-i", str(path), "-t", f"{t:.3f}", "-vf",
                          vf + f",scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)

def x_track(F, thr, maxfrac=1.0):
    out = []
    for i in range(1, len(F)):
        d = np.abs(F[i] - F[i - 1]) > thr
        xx = np.nonzero(d)[1]
        out.append(xx.mean() if 3 < len(xx) < maxfrac * d.size else np.nan)
    return np.array(out)

def trajectory_refine(a, toma, roi, burst, guess, span=1.2, fps=60):
    """Correlaciona la posición x del trazo en pantalla con la x del movimiento de la
    mano en cámara. Devuelve (lag, r) para signo directo y espejado."""
    s0, s1 = burst
    sw, sh = 342, 456
    S = gray_frames(a.secundaria, s0, s1 - s0, f"fps={fps}", sw, sh)
    sx = x_track(S, 20, 0.01)
    x, y, w, h = roi
    c0 = max(0.0, s0 + guess - span - 0.5)
    C = gray_frames(toma, c0, s1 - s0 + 2 * span + 1, f"fps={fps},crop={w}:{h}:{x}:{y}", w // 2 * 2 // 2, h // 2 * 2 // 2)
    cx = x_track(C, 25)
    idx = np.where(~np.isnan(sx))[0]
    rows = []
    for L in range(int(round((guess - span) * fps)), int(round((guess + span) * fps)) + 1):
        j = np.round((s0 + (idx + 1) / fps + L / fps - c0) * fps - 1).astype(int)
        ok = (j >= 0) & (j < len(cx))
        c = cx[j[ok]]; sv = sx[idx[ok]]; m = ~np.isnan(c)
        if m.sum() < 30 or np.std(sv[m]) == 0 or np.std(c[m]) == 0:
            continue
        rows.append((L / fps, float(np.corrcoef(sv[m], c[m])[0, 1])))
    if not rows:
        return None
    r = np.array(rows)
    kd = int(np.argmax(r[:, 1])); ke = int(np.argmin(r[:, 1]))
    return {"burst_secundaria_s": [round(s0, 2), round(s1, 2)],
            "directo": {"offset_s": round(r[kd, 0], 3), "r": round(r[kd, 1], 3)},
            "espejado": {"offset_s": round(r[ke, 0], 3), "r": round(-r[ke, 1], 3)}}

def verification_sheet(a, toma, roi, t_sec, offset, out_png, dur=3.0):
    """Hoja de control: fila de cámara (ROI) y fila de pantalla, 10 fps, mismo reloj."""
    x, y, w, h = roi
    tc = t_sec + offset
    cam = out_png + ".cam.jpg"; scr = out_png + ".scr.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tc:.3f}", "-i", str(toma), "-t", str(dur), "-vf",
                    f"fps=5,crop={w}:{h}:{x}:{y},scale=240:-2,drawtext=text='cam %{{e\\:t+{tc:.2f}}}':x=4:y=4:fontcolor=red:fontsize=14,tile={int(dur*5)}x1",
                    "-frames:v", "1", cam], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t_sec:.3f}", "-i", str(a.secundaria), "-t", str(dur), "-vf",
                    f"fps=5,scale=240:-2,drawtext=text='pant %{{e\\:t+{t_sec:.2f}}}':x=4:y=4:fontcolor=red:fontsize=14,tile={int(dur*5)}x1",
                    "-frames:v", "1", scr], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cam, "-i", scr, "-filter_complex",
                    "[0][1]scale2ref=w=iw:h=ow/mdar[b][a];[a][b]vstack", out_png], check=False)
    return out_png

def visual_sync(a, toma, t0_guess, sec_dur, cam_dur, sec_series=None, roi=None):
    fps = 60.0
    if sec_series is None:
        sec_series = prep(motion_series(a.secundaria, fps, width=342, thr=10), fps)
    # tramo de cámara que solapa según el offset inicial, con margen de búsqueda
    c0 = max(0.0, t0_guess - a.busqueda); c1 = min(cam_dur, t0_guess + sec_dur + a.busqueda)
    if c1 - c0 < 10:
        return None, sec_series
    cam = prep(motion_series(toma, fps, roi=roi, start=c0, dur=c1 - c0, width=80), fps)
    # a = pantalla (t_sec), b = cámara desde c0; t_cam = t_sec + off => índice b = t_sec + off - c0
    base = t0_guess - c0
    lags, vals = lag_search(sec_series, cam, fps, base - a.busqueda, base + a.busqueda)
    k = int(np.argmax(vals)); best = lags[k] + c0
    m = vals.copy(); m[max(0, k - 30):k + 30] = -1
    ratio = float(vals[k] / max(m.max(), 1e-6))
    # verificación por tercios del solapamiento
    ov0 = max(0.0, -best); ov1 = min(sec_dur, cam_dur - best)
    checks = []
    for j in range(3):
        u0 = ov0 + j * (ov1 - ov0) / 3; u1 = ov0 + (j + 1) * (ov1 - ov0) / 3
        sa = sec_series[int(u0 * fps):int(u1 * fps)]
        l2, v2 = lag_search(sa, cam, fps, u0 + best - c0 - 1.0, u0 + best - c0 + 1.0)
        q = int(np.argmax(v2))
        checks.append({"tramo_secundaria_s": [round(u0, 1), round(u1, 1)], "ncc": round(float(v2[q]), 3),
                       "error_ms": round((l2[q] + c0 - u0 - best) * 1000, 1)})
    # Refinamiento por trayectoria sobre los bursts cortos e intensos del solapamiento
    refs = []
    if a.actividad and roi:
        tr = json.load(open(a.actividad))["tramos"]
        cand = [t for t in tr if 0.8 <= t["dur_s"] <= 6 and t["inicio_s"] >= ov0 + 1 and t["fin_s"] <= ov1 - 1]
        cand.sort(key=lambda t: -t["px_por_s"])
        for t in cand[:a.n_trazos]:
            r = trajectory_refine(a, toma, roi, (t["inicio_s"], t["fin_s"]), t0_guess, span=a.busqueda)
            if r: refs.append(r)
    traj = None
    if refs:
        for sign in ("espejado", "directo"):
            good = [r[sign] for r in refs if r[sign]["r"] >= 0.6]
            if good:
                offs = np.array([g["offset_s"] for g in good])
                traj = {"signo": sign, "offset_s": round(float(np.median(offs)), 3), "n": len(good),
                        "dispersion_ms": round(float(np.ptp(offs) * 1000), 1),
                        "r_medio": round(float(np.mean([g["r"] for g in good])), 3)}
                break
    if traj:
        best = traj["offset_s"]
    return {"metodo": "visual", "offset_s": round(float(best), 4), "offset_frames_60": round(float(best) * 60, 2),
            "offset_inicial_s": round(t0_guess, 3), "ncc": round(float(vals[k]), 3), "ratio": round(ratio, 2),
            "confianza": round(float(np.clip(vals[k] * 2, 0, 1) * min(1, ratio / 1.5)), 3),
            "solapamiento_en_secundaria_s": [round(ov0, 3), round(ov1, 3)],
            "solapamiento_en_toma_s": [round(ov0 + best, 3), round(ov1 + best, 3)],
            "verificacion_3_ventanas": checks, "trayectoria": traj, "trayectorias_por_trazo": refs,
            "nota": "El modo visual es menos preciso que el audio: revisá la hoja de verificación."}, sec_series

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--secundaria", required=True, help="grabación de pantalla (con audio)")
    ap.add_argument("--tomas", nargs="+", required=True, help="tomas de cámara, en orden")
    ap.add_argument("--out", required=True, help="JSON de salida")
    ap.add_argument("--win", type=float, default=20.0, help="largo de ventana (s)")
    ap.add_argument("--hop", type=float, default=15.0, help="paso entre ventanas (s)")
    ap.add_argument("--min-ncc", type=float, default=0.25, help="NCC mínimo para aceptar una ventana")
    ap.add_argument("--min-ratio", type=float, default=1.6, help="pico / segundo pico mínimo")
    ap.add_argument("--sr", type=int, default=8000, help="frecuencia de análisis gruesa")
    ap.add_argument("--modo", choices=["auto", "audio", "visual"], default="auto")
    ap.add_argument("--roi", nargs="+", help="x,y,w,h en la cámara donde se ve la mano/tablet, uno por toma (o uno para todas)")
    ap.add_argument("--busqueda", type=float, default=1.2, help="± segundos alrededor del offset inicial (visual; creation_time redondea a 1 s)")
    ap.add_argument("--actividad", help="JSON de detectar_actividad_pantalla.py (refinamiento por trayectoria)")
    ap.add_argument("--n-trazos", type=int, default=6, help="trazos a usar en el refinamiento")
    ap.add_argument("--hojas", help="carpeta para hojas de verificación visual")
    ap.add_argument("--offset-inicial", type=float, nargs="*", help="offset inicial por toma (s); si no, creation_time")
    a = ap.parse_args()

    sr = a.sr
    raw_sec = load(a.secundaria, sr)
    rms_db = 20 * np.log10(np.sqrt(np.mean(raw_sec ** 2)) + 1e-12)
    modo = a.modo
    if modo == "auto":
        modo = "visual" if rms_db < -80 else "audio"
    if modo == "visual":
        if not a.roi:
            raise SystemExit(f"Audio de la secundaria mudo ({rms_db:.0f} dBFS): hace falta --roi para el modo visual")
        ts, dsec = creation_time(a.secundaria)
        result = {"convencion": "t_camara = t_secundaria + offset_s", "secundaria": a.secundaria,
                  "secundaria_dur_s": round(dsec, 3), "audio_secundaria_dbfs": round(float(rms_db), 1),
                  "modo": "visual", "parametros": vars(a), "tomas": []}
        series = None
        for i, toma in enumerate(a.tomas):
            tc, dcam = creation_time(toma)
            guess = a.offset_inicial[i] if a.offset_inicial else (ts - tc)
            roi_t = tuple(int(v) for v in (a.roi[i] if i < len(a.roi) else a.roi[0]).split(","))
            r, series = visual_sync(a, toma, guess, dsec, dcam, series, roi_t)
            entry = {"toma": toma, "toma_dur_s": round(dcam, 3), "offset_por_metadatos_s": round(ts - tc, 3)}
            entry.update(r or {"solapa": False})
            if r:
                entry["solapa"] = True
                if a.hojas and r.get("trayectorias_por_trazo"):
                    import os
                    os.makedirs(a.hojas, exist_ok=True)
                    b0 = r["trayectorias_por_trazo"][0]["burst_secundaria_s"][0]
                    entry["hoja_verificacion"] = verification_sheet(
                        a, toma, roi_t, max(0, b0 - 0.5), r["offset_s"], os.path.join(a.hojas, f"sync-toma{i+1}.jpg"))
            result["tomas"].append(entry)
            print(toma, "->", {k: entry.get(k) for k in ("offset_s", "ncc", "ratio", "confianza")})
            for c in entry.get("verificacion_3_ventanas", []): print("   check", c)
        with open(a.out, "w") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
        return
    sec = bandpass(raw_sec, sr)
    dur_sec = len(sec) / sr
    result = {"convencion": "t_camara = t_secundaria + offset_s", "secundaria": a.secundaria,
              "secundaria_dur_s": round(dur_sec, 3), "parametros": vars(a), "tomas": []}
    sec48 = None
    for toma in a.tomas:
        cam = bandpass(load(toma, sr), sr)
        dur_cam = len(cam) / sr
        hits, allw = [], []
        t = 0.0
        while t + a.win <= dur_sec:
            w = sec[int(t * sr):int((t + a.win) * sr)]
            if np.sqrt(np.mean(w * w)) < 1e-4:
                t += a.hop; continue
            c = ncc(cam, w)
            i, p, s2 = best_peak(c, sr)
            off = i / sr - t
            rec = {"t_secundaria": round(t, 2), "offset_s": round(off, 4), "ncc": round(p, 3),
                   "ratio": round(p / max(s2, 1e-6), 2)}
            allw.append(rec)
            if p >= a.min_ncc and rec["ratio"] >= a.min_ratio:
                hits.append(rec)
            t += a.hop
        entry = {"toma": toma, "toma_dur_s": round(dur_cam, 3), "ventanas_probadas": len(allw),
                 "ventanas_aceptadas": len(hits)}
        if not hits:
            entry.update({"solapa": False, "confianza": 0.0,
                          "mejor_ventana_rechazada": max(allw, key=lambda r: r["ncc"]) if allw else None})
            result["tomas"].append(entry); continue
        offs = np.array([h["offset_s"] for h in hits])
        med = float(np.median(offs))
        inl = [h for h in hits if abs(h["offset_s"] - med) < 0.05]
        # Refinamiento a 48 kHz sobre la mejor ventana (±20 ms).
        best = max(inl, key=lambda r: r["ncc"])
        R = 48000
        if sec48 is None:
            sec48 = bandpass(load(a.secundaria, R), R)
        cam48 = bandpass(load(toma, R), R)
        t0 = best["t_secundaria"]
        w = sec48[int(t0 * R):int((t0 + a.win) * R)]
        base = int(round((t0 + med) * R)); pad = int(0.02 * R)
        seg = cam48[max(0, base - pad):base + len(w) + pad]
        c = ncc(seg, w); j = int(np.argmax(c))
        fine = (max(0, base - pad) + j) / R - t0
        # Deriva: pendiente offset vs tiempo en ventanas inlier.
        drift_ppm = 0.0
        if len(inl) >= 3:
            ts = np.array([h["t_secundaria"] for h in inl]); os_ = np.array([h["offset_s"] for h in inl])
            drift_ppm = float(np.polyfit(ts, os_, 1)[0] * 1e6)
        ov_start_sec = max(0.0, -fine); ov_end_sec = min(dur_sec, dur_cam - fine)
        # Verificación en 3 ventanas repartidas por el solapamiento (5 s cada una, a 48 kHz).
        checks = []
        for frac in (0.1, 0.5, 0.9):
            ts = ov_start_sec + frac * (ov_end_sec - ov_start_sec - 5)
            ww = sec48[int(ts * R):int((ts + 5) * R)]
            b = int(round((ts + fine) * R)); pd = int(0.1 * R)
            sg = cam48[max(0, b - pd):b + len(ww) + pd]
            cc = ncc(sg, ww)
            if cc is None:
                continue
            k = int(np.argmax(cc))
            checks.append({"t_secundaria": round(ts, 2), "ncc": round(float(cc[k]), 3),
                           "error_ms": round(((max(0, b - pd) + k) / R - ts - fine) * 1000, 2)})
        spread_ms = float(np.ptp([h["offset_s"] for h in inl]) * 1000)
        conf = float(np.clip(np.mean([h["ncc"] for h in inl]) * 1.5, 0, 1) *
                     min(1.0, len(inl) / 4) * (1.0 if spread_ms < 30 else 0.5))
        entry.update({
            "solapa": True, "offset_s": round(fine, 4), "offset_frames_60": round(fine * 60, 2),
            "offset_grueso_mediana_s": round(med, 4), "dispersion_ms": round(spread_ms, 1),
            "deriva_ppm": round(drift_ppm, 1), "confianza": round(conf, 3),
            "ncc_medio": round(float(np.mean([h["ncc"] for h in inl])), 3),
            "solapamiento_en_secundaria_s": [round(ov_start_sec, 3), round(ov_end_sec, 3)],
            "solapamiento_en_toma_s": [round(ov_start_sec + fine, 3), round(ov_end_sec + fine, 3)],
            "verificacion_3_ventanas": checks, "ventanas_inlier": inl})
        result["tomas"].append(entry)
        del cam48
    with open(a.out, "w") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    for e in result["tomas"]:
        print(e["toma"], "->", {k: e.get(k) for k in ("solapa", "offset_s", "confianza", "dispersion_ms", "deriva_ppm")})
        for c in e.get("verificacion_3_ventanas", []):
            print("   check", c)

if __name__ == "__main__":
    main()
