#!/usr/bin/env python3
"""Pick the best sound effects for motion graphics from ANY folder of SFX packs.

It measures every file (clipping, noise floor, clean attack/tail, envelope shape, stereo width,
sample rate…), classifies it by role (whoosh, riser, impact, UI click…), scores it, keeps the top N
per role, and exports them trimmed, faded and peak-normalised as `assets/sfx/premium/<role>-N.mp3`
plus a `manifest.json` with each file's source (so you can check its licence).

  python3 sfx_curate.py --src ~/Downloads/MiPackDeSFX --out assets/sfx/premium
  python3 sfx_curate.py --src ... --out ... --per-role 3 --sheet curated.png   # + spectrogram sheet to eyeball

Needs ffmpeg + numpy (+ matplotlib for --sheet). Only redistribute sounds whose licence allows it.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np

os.environ["LC_ALL"] = "C"
SR = 48000
SKIP = re.compile(r"gun|rifle|pistol|shotgun|sniper|meme|scream|horror|fart|burp|laugh|crowd|siren|explosion-gore", re.I)
EXT = (".wav", ".mp3", ".aif", ".aiff", ".flac", ".ogg", ".m4a")
RULES = [  # (role, regex on path) — first match wins; whooshes are split by duration below
    ("subdrop", r"sub ?drop|bass ?drop|low ?boom"), ("reverse", r"reverse|suck"), ("riser", r"riser|build ?up|uplifter"),
    ("impact", r"impact|\bhit\b|hits/|boom|braam|slam|thud"), ("glitch", r"glitch|glich|gltch"), ("typing", r"typing|keyboard|\btype\b"),
    ("camera", r"camera|shutter"), ("cash", r"cash|register|ka-?ching|cha-?ching|coin"), ("shimmer", r"shimmer|sparkle|glitter|magic|chime|twinkle"),
    ("ui-pop", r"\bpop\b|pop-|bubble"), ("ui-notify", r"notif|ping|ding|alert"), ("ui-confirm", r"confirm|success|accept|right|select|correct"),
    ("ui-click", r"click|button|\btap\b|mouse|toggle"), ("whoosh", r"whoosh|swoosh|swish|woosh|whip|transition|swipe|fly ?by|pass"),
]


def decode(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def metrics(p):
    x = decode(p)
    if len(x) < 2000: return None
    m = x.mean(1); hop = 480
    fr = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2) + 1e-12) for i in range(0, len(m) - hop, hop)])
    db = 20 * np.log10(fr + 1e-9); pk = int(np.argmax(fr)); pkdb = db[pk]
    act = db > pkdb - 30
    seg = m[:SR * 4]; sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fq = np.fft.rfftfreq(len(seg), 1 / SR)
    L, Rr = x[:, 0], x[:, 1]
    sr_in = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
    return dict(dur=len(m) / SR, act=act.sum() * hop / SR, clip=float(np.mean(np.abs(x) > 0.995)), floor=float(np.percentile(db, 5) - pkdb),
                start=float(db[:3].mean() - pkdb), end=float(db[-3:].mean() - pkdb), tpk=pk * hop / SR,
                cen=float(np.sum(sp * fq) / np.sum(sp)), low=float(np.sum(sp[fq < 150]) / np.sum(sp)),
                width=float(np.sqrt(np.mean(((L - Rr) / 2) ** 2)) / (np.sqrt(np.mean(((L + Rr) / 2) ** 2)) + 1e-9)),
                rough=float(np.mean(np.abs(np.diff(db[act]))) if act.sum() > 3 else 99), sr=int(sr_in or 0))


def role(path, r):
    for name, rx in RULES:
        if re.search(rx, path, re.I):
            if name != "whoosh": return name
            if re.search(r"whip", path, re.I) or r["act"] < 0.35: return "whip"
            return "whoosh-soft" if r["act"] <= 0.6 else "whoosh-pass" if r["act"] <= 1.2 else "whoosh-long"
    return None


def score(r, c):
    s = -r["clip"] * 2000 - max(0, r["floor"] + 60) * 0.15 + (3 if r["sr"] >= 44100 else -6)
    if c.startswith("whoosh") or c in ("whip", "reverse", "riser"):
        s += (4 if r["start"] < -20 else -4) + (3 if r["end"] < -25 else -2) - r["rough"] * 1.2 + min(r["width"], 0.6) * 6
    if c.startswith("whoosh"): s -= abs(r["cen"] - 3000) / 1500
    if c in ("riser", "reverse"): s += 6 if r["tpk"] / max(r["dur"], .01) > 0.65 else -6
    if c == "subdrop": s += r["low"] * 12 + (3 if r["end"] < -30 else 0) - abs(r["dur"] - 3) * 0.5
    if c == "impact": s += (4 if r["tpk"] < 0.06 else -3) + r["low"] * 6 + (3 if r["end"] < -30 else -2) - abs(r["dur"] - 2.5) * 0.4
    if c.startswith("ui") or c in ("glitch", "camera", "cash", "shimmer", "typing"):
        s += (3 if r["end"] < -30 else -2) - max(0, r["dur"] - (3.5 if c == "typing" else 1.6)) * 2 + (2 if r["floor"] < -60 else 0)
    return s


def export(src, dst, first_take, max_s):
    x = decode(src); m = np.abs(x).max(1); pk = m.max()
    idx = np.where(m > pk * 10 ** (-50 / 20))[0]; a = max(0, idx[0] - int(0.004 * SR)); b = idx[-1] + 1
    if first_take:   # keep only the first event if the file holds several takes
        hop = 240; env = np.array([m[i:i + hop].max() for i in range(0, len(m), hop)])
        quiet = env < pk * 0.05; gap = int(0.08 * SR / hop); i = a // hop + int(0.02 * SR / hop)
        while i < len(env) - gap and not quiet[i:i + gap].all(): i += 1
        if i < len(env) - gap and (env[i + gap:] > pk * 0.3).any(): b = min(b, (i + gap) * hop)   # a second take follows the gap
    b = min(b, a + int(max_s * SR)); y = x[a:b]
    fo = min(int(0.25 * SR), len(y) // 4)
    if fo > 0: y[-fo:] *= np.linspace(1, 0, fo)[:, None]
    y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))[:, None]
    g = 10 ** (-1 / 20) / max(np.abs(y).max(), 1e-6)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", f"volume={g:.4f}", "-c:a", "libmp3lame", "-b:a", "320k", dst],
                   input=y.astype(np.float32).tobytes(), check=True)
    return len(y) / SR


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--per-role", type=int, default=3); ap.add_argument("--sheet"); a = ap.parse_args()
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(a.src) for f in fs if f.lower().endswith(EXT) and not SKIP.search(os.path.join(dp, f))]
    print(f"analysing {len(files)} files…", file=sys.stderr)
    rows = []
    for p in files:
        try:
            r = metrics(p)
        except Exception as e:  # unreadable file
            print("skip", p, e, file=sys.stderr); continue
        if not r: continue
        c = role(os.path.relpath(p, a.src), r)
        if c: r.update(path=p, role=c, score=score(r, c)); rows.append(r)
    os.makedirs(a.out, exist_ok=True); man = []
    caps = {"whoosh-long": 6.0, "riser": 8.0, "subdrop": 5.0, "impact": 4.5, "typing": 3.0}
    for c in sorted({r["role"] for r in rows}):
        seen, n = set(), 0
        for r in sorted((r for r in rows if r["role"] == c), key=lambda r: -r["score"]):
            k = (round(r["dur"], 2), round(r["cen"], -1))
            if k in seen: continue
            seen.add(k); n += 1
            dst = os.path.join(a.out, f"{c}-{n}.mp3")
            d = export(r["path"], dst, c in ("ui-pop", "ui-click"), caps.get(c, 3.5))
            man.append({"file": os.path.basename(dst), "role": c, "dur": round(d, 2), "score": round(r["score"], 1), "source": os.path.relpath(r["path"], a.src)})
            print(f"{os.path.basename(dst):20} {d:5.2f}s  <- {os.path.relpath(r['path'], a.src)[-70:]}")
            if n >= a.per_role: break
    json.dump(man, open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if a.sheet:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        cols = 6; rws = (len(man) + cols - 1) // cols
        fig, axs = plt.subplots(rws, cols, figsize=(cols * 2.6, rws * 1.5), facecolor="black"); axs = np.array(axs).reshape(-1)
        for i, ax in enumerate(axs):
            ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("black")
            if i >= len(man): ax.axis("off"); continue
            y = decode(os.path.join(a.out, man[i]["file"])).mean(1)
            ax.specgram(y + 1e-9, NFFT=512, Fs=SR, noverlap=384, cmap="magma", vmin=-130, vmax=-20); ax.set_title(man[i]["file"][:-4], color="yellow", fontsize=7)
        plt.tight_layout(); plt.savefig(a.sheet, dpi=70, facecolor="black")
    print(f"\n{len(man)} sounds → {a.out}  (sources in manifest.json — check each pack's licence before sharing)")


if __name__ == "__main__":
    main()
