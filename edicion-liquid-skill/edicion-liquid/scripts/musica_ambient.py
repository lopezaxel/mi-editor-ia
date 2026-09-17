#!/usr/bin/env python3
"""musica_ambient.py — genera un pad ambient suave, original y sin derechos
(síntesis con numpy, semilla fija), y opcionalmente SFX suaves.

Pad: progresión lenta de acordes (I–vi–IV–V en la tonalidad --tono), cada acorde
--compas s con crossfade largo; voces senoidales levemente desafinadas + un
armónico, pasa-bajos suave, sin percusión, estéreo por paneo de voces. Se
normaliza a --lufs (≈ -28 LUFS integrado por defecto, medido con ffmpeg
loudnorm si está disponible; si no, por RMS).

SFX (--sfx-dir): whoosh.wav (receta aprobada: 0,42 s de ruido suavizado
(media móvil de 12 muestras) + barrido senoidal 260→800 Hz, envolvente sin²,
ganancia baja) y tick.wav (golpe grave 72 Hz con caída exponencial, 0,2 s).

Uso
  musica_ambient.py --dur 745 --out musica.wav [--tono A] [--compas 8] \\
      [--lufs -28] [--seed 20260914] [--sfx-dir sfx/]
"""
import argparse, json, os, re, subprocess, wave
import numpy as np

SR = 48000
NOTES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

def write(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def measure_lufs(path):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    return float(json.loads(m.group(0))["input_i"]) if m else None

def pad(dur, tono, compas, rng):
    n = int(dur * SR); t = np.arange(n) / SR
    root = 440 * 2 ** ((NOTES[tono] - 9) / 12) / 2  # octava baja
    prog = [[0, 4, 7], [9, 12, 16], [5, 9, 12], [7, 11, 14]]  # I vi IV V (semitonos)
    out = np.zeros((n, 2))
    step = int(compas * SR); fade = int(min(compas * 0.45, 4) * SR)
    k = 0; pos = 0
    while pos < n:
        chord = prog[k % len(prog)]
        seg = min(n - pos, step + fade)
        tt = np.arange(seg) / SR
        env = np.ones(seg)
        fi = min(fade, seg); env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
        if seg > step: env[step:] = np.cos(np.linspace(0, np.pi / 2, seg - step)) ** 2
        for vi, semi in enumerate(chord + [chord[0] + 12]):
            f = root * 2 ** (semi / 12)
            det = 1 + rng.uniform(-0.0015, 0.0015)
            ph = rng.uniform(0, 2 * np.pi)
            lfo = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.03, 0.08) * (tt + pos / SR) + ph)
            v = (np.sin(2 * np.pi * f * det * tt + ph) + 0.18 * np.sin(2 * np.pi * 2 * f * tt + ph)) * lfo
            pan = 0.25 + 0.5 * (vi / 3)
            out[pos:pos + seg, 0] += v * env * (1 - pan)
            out[pos:pos + seg, 1] += v * env * pan
        pos += step; k += 1
    # pasa-bajos de un polo (~1,2 kHz)
    a = np.exp(-2 * np.pi * 1200 / SR)
    try:
        from scipy.signal import lfilter
        out = lfilter([1 - a], [1, -a], out, axis=0)
    except ImportError:  # sin scipy: suavizado por media móvil equivalente
        k = int(SR / 1200 / 2) or 1
        out = np.stack([np.convolve(out[:, c], np.ones(k) / k, mode="same") for c in range(2)], 1)
    g = np.ones(n); fi = min(n, 3 * SR); fo = min(n, 4 * SR)
    g[:fi] = np.linspace(0, 1, fi); g[-fo:] = np.minimum(g[-fo:], np.linspace(1, 0, fo))
    return out * g[:, None]

def sfx(rng):
    dur = 0.42; t = np.arange(int(SR * dur)) / SR
    noise = np.convolve(rng.normal(0, 1, len(t)), np.ones(12) / 12, mode="same")
    env = np.sin(np.pi * t / dur) ** 2
    sweep = np.sin(2 * np.pi * (260 * t + 800 * t * t))
    whoosh = (noise * 0.6 + sweep * 0.12) * env * 0.032
    w2 = np.stack([whoosh * 0.6, whoosh * 0.4], 1)
    tt = np.arange(int(SR * 0.20)) / SR
    tick = np.sin(2 * np.pi * (72 * tt + 6 * (1 - np.exp(-tt * 30)))) * np.exp(-tt * 22) * 0.026
    return w2, tick

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tono", default="A", choices=list(NOTES))
    ap.add_argument("--compas", type=float, default=8.0, help="segundos por acorde")
    ap.add_argument("--lufs", type=float, default=-28.0)
    ap.add_argument("--seed", type=int, default=20260914)
    ap.add_argument("--sfx-dir")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    x = pad(a.dur, a.tono, a.compas, rng)
    x /= np.max(np.abs(x)) + 1e-9
    x *= 0.3
    write(a.out, x)
    lufs = measure_lufs(a.out)
    if lufs is not None:
        x *= 10 ** ((a.lufs - lufs) / 20)
    else:
        x *= 10 ** ((a.lufs + 3 - 20 * np.log10(np.sqrt(np.mean(x ** 2)))) / 20)
    write(a.out, x)
    res = {"out": a.out, "dur_s": a.dur, "lufs_objetivo": a.lufs, "lufs_medido": measure_lufs(a.out), "seed": a.seed,
           "tono": a.tono, "compas_s": a.compas, "pico": round(float(np.max(np.abs(x))), 4)}
    if a.sfx_dir:
        os.makedirs(a.sfx_dir, exist_ok=True)
        w, t = sfx(rng)
        write(os.path.join(a.sfx_dir, "whoosh.wav"), w); write(os.path.join(a.sfx_dir, "tick.wav"), t)
        res["sfx"] = [os.path.join(a.sfx_dir, f) for f in ("whoosh.wav", "tick.wav")]
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
