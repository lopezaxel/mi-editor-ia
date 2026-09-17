#!/usr/bin/env python3
"""cortar_silencios.py — arma el timeline de una o varias tomas cortando pausas,
sin cortar palabras. Trabaja en frames a --fps (60 por defecto).

Para cada toma:
  1. Energía RMS en ventanas de 10 ms (audio mono 16 kHz, pasa-altos 120 Hz para
     que el viento no cuente como voz).
  2. Umbral de silencio = piso de ruido (percentil --pct-piso) + --margen-db,
     con tope en --umbral-max-db. Pausa = tramo bajo el umbral >= --min-pausa s
     (se rellenan huecos de voz < 60 ms dentro de una pausa).
  3. Corte = pausa recortada --pad s de cada lado (por defecto 0,13 s), ajustada
     al hueco entre la palabra anterior y la siguiente con margen
     --margen-palabra, redondeada hacia adentro a frames. Se descarta si:
       - dura menos de --min-frames frames (12 = 0,2 s a 60 fps),
       - toca cualquier palabra con margen ±--margen-palabra s (0,10),
       - cae dentro de una zona protegida (proteger=a-b).
  4. Tramos conservados = [inicio, fin] de la toma menos los cortes.

Palabras: JSON de Vosk (lista de {word,start,end}) o <base>.words.json de
transcribir.sh ({"words":[...]}). Se pueden pasar varios separados por '+'.

Uso
  cortar_silencios.py --out timeline.json [--voz-out voz.wav] \\
    --toma video=IMG_1.MOV,audio=IMG_1.wav,palabras=IMG_1.vosk.json,inicio=1.2,fin=586.05,proteger=575-586.05 \\
    --toma video=IMG_2.MOV,audio=IMG_2.wav,palabras=IMG_2.vosk.json,inicio=0.9,fin=194.3

  audio= es opcional (si falta se extrae del video). inicio/fin en segundos de la toma.

Salida timeline.json
  fps, umbrales usados, por toma: pausas detectadas / cortes aplicados / descartados
  (con motivo), segmentos conservados en frames de fuente y de edición, y
  "mapa": [[toma, src_ini_s, src_fin_s, edit_ini_s], ...] para convertir
  tiempo-fuente -> tiempo-editado (edit = edit_ini + (t - src_ini) dentro del tramo).
  --voz-out escribe la voz editada a 48 kHz cortando en muestras múltiplo exacto
  de un frame (800 muestras a 60 fps): alineada frame-exacto con el video.
"""
import argparse, json, subprocess, math, wave
import numpy as np
from scipy import signal

def load_audio(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768

def load_words(spec):
    words = []
    for p in spec.split("+"):
        d = json.load(open(p))
        lst = d["words"] if isinstance(d, dict) else d
        words += [{"word": w["word"], "start": float(w["start"]), "end": float(w["end"])} for w in lst]
    return sorted(words, key=lambda w: w["start"])

def parse_toma(s):
    kv = dict(x.split("=", 1) for x in s.split(","))
    kv["inicio"] = float(kv.get("inicio", 0)); kv["fin"] = float(kv["fin"]) if "fin" in kv else None
    prot = []
    for z in filter(None, kv.get("proteger", "").split(";")):
        a, b = z.split("-"); prot.append((float(a), float(b)))
    kv["proteger"] = prot
    return kv

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--toma", action="append", required=True, help="video=..,audio=..,palabras=..,inicio=..,fin=..,proteger=a-b;c-d")
    ap.add_argument("--out", required=True)
    ap.add_argument("--voz-out", help="wav 48 kHz de la voz editada")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--pad", type=float, default=0.13)
    ap.add_argument("--min-frames", type=int, default=12)
    ap.add_argument("--margen-palabra", type=float, default=0.10)
    ap.add_argument("--min-pausa", type=float, default=0.45)
    ap.add_argument("--pct-piso", type=float, default=10.0)
    ap.add_argument("--margen-db", type=float, default=9.0)
    ap.add_argument("--margen-hueco-db", type=float, default=16.0,
                    help="huecos entre palabras se cortan si su p90 < piso + esto (0 = desactivar)")
    ap.add_argument("--umbral-max-db", type=float, default=-30.0)
    a = ap.parse_args()
    fps = a.fps; SR = 16000; hop = 160
    sos = signal.butter(4, 120, btype="high", fs=SR, output="sos")
    out = {"fps": fps, "parametros": {k: v for k, v in vars(a).items() if k not in ("toma",)}, "tomas": [],
           "segmentos": [], "mapa": []}
    edit_frame = 0
    pcm_parts = []
    for ti, spec in enumerate(a.toma):
        t = parse_toma(spec)
        audio_src = t.get("audio", t["video"])
        x = signal.sosfiltfilt(sos, load_audio(audio_src, SR))
        dur_audio = len(x) / SR
        vdur = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                              "stream=duration", "-of", "default=nw=1:nk=1", t["video"]]).decode().split()[0])
        fin = min(t["fin"] if t["fin"] else vdur, vdur)
        n = len(x) // hop
        rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
        db = 20 * np.log10(rms)
        floor = float(np.percentile(db, a.pct_piso))
        thr = min(floor + a.margen_db, a.umbral_max_db)
        quiet = db < thr
        # rellena voz de < 60 ms dentro de pausas
        q = quiet.copy()
        i = 0
        while i < n:
            if not q[i]:
                j = i
                while j < n and not q[j]: j += 1
                if j - i < 6 and i > 0 and j < n: q[i:j] = True
                i = j
            else:
                i += 1
        pauses = []
        i = 0
        while i < n:
            if q[i]:
                j = i
                while j < n and q[j]: j += 1
                if (j - i) * hop / SR >= a.min_pausa: pauses.append((i * hop / SR, j * hop / SR))
                i = j
            else:
                i += 1
        words = load_words(t["palabras"]) if t.get("palabras") else []
        # Huecos entre palabras: el viento sube el piso y la energía sola no los ve.
        # Se aceptan si el p90 de energía del hueco queda bajo el umbral relajado.
        thr_relax = min(floor + a.margen_hueco_db, a.umbral_max_db)
        voice_db = float(np.percentile(db, 90))
        gap_pauses = 0
        if words and a.margen_hueco_db > 0:
            for w1, w2 in zip(words, words[1:]):
                g0, g1 = w1["end"], w2["start"]
                if g1 - g0 < a.min_pausa:
                    continue
                seg = db[int(g0 * SR / hop):int(g1 * SR / hop)]
                if len(seg) and np.percentile(seg, 90) < thr_relax and not any(ps < g1 and pe > g0 for ps, pe in pauses):
                    pauses.append((g0, g1)); gap_pauses += 1
            pauses.sort()
        f0 = math.ceil(t["inicio"] * fps - 1e-6); f1 = math.floor(fin * fps + 1e-6)
        cuts, rejected = [], []
        for ps, pe in pauses:
            c0, c1 = ps + a.pad, pe - a.pad
            # Si la pausa roza una palabra, se ajusta al hueco entre palabras (con margen)
            # en vez de tirarla; si después no llega al mínimo, se descarta.
            prev_end = max([w["end"] for w in words if w["end"] <= (ps + pe) / 2], default=None)
            next_start = min([w["start"] for w in words if w["start"] >= (ps + pe) / 2], default=None)
            if prev_end is not None: c0 = max(c0, prev_end + a.margen_palabra)
            if next_start is not None: c1 = min(c1, next_start - a.margen_palabra)
            x0 = max(f0, math.ceil(c0 * fps)); x1 = min(f1, math.floor(c1 * fps))
            if x1 - x0 < a.min_frames:
                if x1 > x0: rejected.append({"pausa_s": [round(ps, 3), round(pe, 3)], "motivo": "corta"})
                continue
            hit = [w["word"] for w in words if w["end"] + a.margen_palabra > x0 / fps and w["start"] - a.margen_palabra < x1 / fps]
            if hit:
                rejected.append({"pausa_s": [round(ps, 3), round(pe, 3)], "motivo": "toca palabra", "palabras": hit[:4]}); continue
            if any(x0 / fps < pb and x1 / fps > pa for pa, pb in t["proteger"]):
                rejected.append({"pausa_s": [round(ps, 3), round(pe, 3)], "motivo": "zona protegida"}); continue
            cuts.append([x0, x1])
        kept = []; cur = f0
        for x0, x1 in cuts:
            if x0 > cur: kept.append([cur, x0])
            cur = x1
        if cur < f1: kept.append([cur, f1])
        take_frames = sum(b - a_ for a_, b in kept)
        for s0, s1 in kept:
            out["segmentos"].append({"toma": ti, "video": t["video"], "src_ini_frame": s0, "src_fin_frame": s1,
                                     "edit_ini_frame": edit_frame, "frames": s1 - s0})
            out["mapa"].append([ti, round(s0 / fps, 4), round(s1 / fps, 4), round(edit_frame / fps, 4)])
            edit_frame += s1 - s0
        out["tomas"].append({
            "toma": ti, "video": t["video"], "audio": audio_src, "palabras": t.get("palabras"),
            "rango_s": [round(f0 / fps, 4), round(f1 / fps, 4)], "dur_video_s": vdur, "dur_audio_s": round(dur_audio, 3),
            "piso_ruido_db": round(floor, 1), "umbral_silencio_db": round(thr, 1),
            "umbral_hueco_p90_db": round(thr_relax, 1), "voz_p90_db": round(voice_db, 1), "pausas_por_hueco": gap_pauses,
            "zonas_protegidas_s": t["proteger"], "pausas_detectadas": len(pauses),
            "cortes": cuts, "cortes_n": len(cuts), "cortado_s": round(sum(b - a_ for a_, b in cuts) / fps, 3),
            "descartados": rejected, "frames_conservados": take_frames, "dur_conservada_s": round(take_frames / fps, 3),
            "palabras_dentro_de_cortes": sum(1 for c in cuts for w in words if w["end"] > c[0] / fps and w["start"] < c[1] / fps)})
        if a.voz_out:
            SR2 = 48000; spf = SR2 // fps
            y = load_audio(audio_src, SR2)
            yi = (np.clip(y, -1, 1) * 32767).astype(np.int16)
            need = f1 * spf
            if len(yi) < need: yi = np.concatenate([yi, np.zeros(need - len(yi), np.int16)])
            for s0, s1 in kept:
                pcm_parts.append(yi[s0 * spf:s1 * spf])
    out["frames_totales"] = edit_frame
    out["dur_editada_s"] = round(edit_frame / fps, 4)
    out["cortes_totales"] = sum(t["cortes_n"] for t in out["tomas"])
    out["pausas_cortadas_s"] = round(sum(t["cortado_s"] for t in out["tomas"]), 3)
    if a.voz_out:
        pcm = np.concatenate(pcm_parts)
        assert len(pcm) == edit_frame * (48000 // fps)
        with wave.open(a.voz_out, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(pcm.tobytes())
        out["voz_out"] = a.voz_out
    json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: out[k] for k in ("frames_totales", "dur_editada_s", "cortes_totales", "pausas_cortadas_s")}))
    for t in out["tomas"]:
        print(f"toma {t['toma']}: piso {t['piso_ruido_db']} dB, umbral {t['umbral_silencio_db']} dB, "
              f"pausas {t['pausas_detectadas']}, cortes {t['cortes_n']} ({t['cortado_s']} s), descartados {len(t['descartados'])}")

if __name__ == "__main__":
    main()
