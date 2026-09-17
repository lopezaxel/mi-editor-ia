#!/usr/bin/env python3
"""mezclar_audio.py — mezcla voz + música con ducking + SFX en tiempos dados y
normaliza a -14 LUFS integrado con true peak <= -1 dBTP.

Ducking: envolvente RMS de la voz (ventana 50 ms, ataque --ataque, relajación
--relajacion). Donde hay voz la música queda en --musica-bajo-voz dB; en las
pausas sube a --musica-pausa dB; antes de --intro-fin s la música va a
--musica-intro dB (más presente) y baja con una rampa de 1,5 s. Los dB son
ganancia aplicada a la pista de música tal como viene (musica_ambient.py la
entrega a ~-28 LUFS).

SFX: --sfx "12.4:whoosh.wav" "30.0:tick.wav:-3" (tiempo en s : archivo [: dB]).

Normalización: dos pasadas de loudnorm lineal (sin compresión dinámica) a
--lufs / --tp. Si la ganancia lineal no alcanza por el true peak, se pasa
antes por un limitador suave (alimiter) y se repite. El resultado se mide y se
reporta; sale con código 1 si queda fuera de ±0,5 LU o TP > objetivo.

Uso
  mezclar_audio.py --voz voz.wav --musica musica.wav --out mezcla.wav \\
      [--intro-fin 25] [--sfx 0.5:whoosh.wav 12:tick.wav:-6] [--lufs -14] [--tp -1]
"""
import argparse, json, re, subprocess, sys, wave, os
import numpy as np

SR = 48000

def read(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR)
        i = (x * 8388607).astype(np.int32)
        b = np.zeros((i.size, 3), np.uint8); f = i.reshape(-1)
        b[:, 0] = f & 255; b[:, 1] = (f >> 8) & 255; b[:, 2] = (f >> 16) & 255
        w.writeframes(b.tobytes())

def loud(path, extra=""):
    af = (extra + "," if extra else "") + "loudnorm=print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", af, "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    return json.loads(m[-1])

def smooth_env(x, att, rel):
    win = int(0.05 * SR)
    e = np.sqrt(np.convolve(np.mean(x ** 2, axis=1), np.ones(win) / win, mode="same"))
    # ataque/relajación a 100 Hz de control
    hop = SR // 100
    c = e[::hop]
    out = np.empty_like(c); acc = 0.0
    aa = np.exp(-1 / (att * 100)); ar = np.exp(-1 / (rel * 100))
    for i, v in enumerate(c):
        k = aa if v > acc else ar
        acc = k * acc + (1 - k) * v; out[i] = acc
    return np.interp(np.arange(len(x)), np.arange(len(out)) * hop, out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--voz", required=True)
    ap.add_argument("--musica")
    ap.add_argument("--out", required=True)
    ap.add_argument("--intro-fin", type=float, default=0.0)
    ap.add_argument("--musica-intro", type=float, default=-8.0)
    ap.add_argument("--musica-bajo-voz", type=float, default=-11.0)
    ap.add_argument("--musica-pausa", type=float, default=-7.0)
    ap.add_argument("--umbral-voz-db", type=float, default=-38.0)
    ap.add_argument("--ataque", type=float, default=0.08)
    ap.add_argument("--relajacion", type=float, default=0.45)
    ap.add_argument("--sfx", nargs="*", default=[])
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    a = ap.parse_args()
    v = read(a.voz); n = len(v)
    mix = v.copy()
    rep = {"voz": a.voz, "dur_s": round(n / SR, 4)}
    if a.musica:
        m = read(a.musica)
        m = m[:n] if len(m) >= n else np.concatenate([m, np.zeros((n - len(m), 2))])
        env = smooth_env(v, a.ataque, a.relajacion)
        env_db = 20 * np.log10(env + 1e-9)
        # 0 = pausa, 1 = voz, transición de 10 dB
        w = np.clip((env_db - (a.umbral_voz_db - 5)) / 10, 0, 1)
        g_db = a.musica_pausa + (a.musica_bajo_voz - a.musica_pausa) * w
        if a.intro_fin > 0:
            t = np.arange(n) / SR
            ramp = np.clip((t - a.intro_fin) / 1.5, 0, 1)
            g_db = a.musica_intro * (1 - ramp) + g_db * ramp
        mix += m * (10 ** (g_db / 20))[:, None]
        rep.update({"musica": a.musica, "ducking_db": {"intro": a.musica_intro, "bajo_voz": a.musica_bajo_voz,
                    "pausa": a.musica_pausa}, "intro_fin_s": a.intro_fin,
                    "musica_bajo_voz_pct_tiempo": round(float((w > 0.5).mean() * 100), 1)})
    placed = []
    for spec in a.sfx:
        parts = spec.split(":")
        t0 = float(parts[0]); path = parts[1]; gdb = float(parts[2]) if len(parts) > 2 else 0.0
        s = read(path) * 10 ** (gdb / 20)
        i0 = int(round(t0 * SR)); i1 = min(n, i0 + len(s))
        if i0 < n: mix[i0:i1] += s[:i1 - i0]; placed.append({"t": t0, "sfx": os.path.basename(path), "db": gdb})
    rep["sfx"] = placed
    tmp = a.out + ".pre.wav"
    write(tmp, mix / max(1.0, np.max(np.abs(mix))))
    extra = ""
    for intento in range(3):
        meas = loud(tmp, extra)
        gain = a.lufs - float(meas["input_i"])
        if float(meas["input_tp"]) + gain <= a.tp - 0.1:
            break
        # hace falta limitar: techo tal que después de la ganancia quede en tp
        ceiling = 10 ** ((a.tp - 0.3 - gain) / 20)
        extra = f"alimiter=limit={min(1.0, ceiling):.4f}:attack=5:release=80:level=false"
    af = (extra + "," if extra else "") + f"volume={gain:.3f}dB"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", a.out], check=True)
    os.remove(tmp)
    fin = loud(a.out)
    rep.update({"limitador": extra or None, "ganancia_db": round(gain, 2), "lufs_final": float(fin["input_i"]),
                "tp_final": float(fin["input_tp"]), "lra": float(fin["input_lra"]), "out": a.out})
    ok = abs(rep["lufs_final"] - a.lufs) <= 0.5 and rep["tp_final"] <= a.tp + 0.05
    rep["ok"] = ok
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    json.dump(rep, open(a.out + ".json", "w"), indent=1, ensure_ascii=False)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
