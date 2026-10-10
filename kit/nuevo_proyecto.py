#!/usr/bin/env python
"""Scaffold a CAEIA video project for HyperFrames 0.8.43 (Windows/macOS/Linux).

  python kit/nuevo_proyecto.py 2026-10-12-reel-whatsapp --formato reel --duracion 20
  python kit/nuevo_proyecto.py 2026-10-12-demo --formato ambos --crudo "D:/grabaciones/demo.mp4"

Creates proyectos-video/<nombre>/ with index.html (or reel/ + horizontal/ for "ambos"),
its own copy of kit/ and assets/fonts/ (so the project re-renders identically later),
and a package.json pinning hyperframes 0.8.43 + gsap 3.15.0. With --crudo the footage is
copied to assets/crudo.<ext>, probed with ffprobe and placed as the base video layer (muted:
its audio is muxed back after the render, see the caeia-editor skill).
Nothing is installed: it prints the npm command to run.
"""
import argparse, json, os, shutil, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(REPO, "kit")
FORMATS = {"reel": (1080, 1920, "reel", 260), "horizontal": (1920, 1080, "wide", 160)}
KIT_FILES = ["premium.js", "caeia.js", "caeia.css", "three-stage.js", "motion-kit.js", "motion-kit.css"]


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    return float(d["format"]["duration"]), d["streams"][0]["width"], d["streams"][0]["height"]


def build(dest, fmt, dur, crudo_rel):
    w, h, cls, hook_top = FORMATS[fmt]
    os.makedirs(os.path.join(dest, "kit"), exist_ok=True)
    for f in KIT_FILES:
        shutil.copy2(os.path.join(KIT, f), os.path.join(dest, "kit", f))
    shutil.copytree(os.path.join(REPO, "assets", "fonts"), os.path.join(dest, "assets", "fonts"), dirs_exist_ok=True)
    crudo = ""
    if crudo_rel:
        crudo = (f'      <video id="base" class="base-video clip" src="{crudo_rel}" data-start="0" data-duration="{dur:.3f}" '
                 f'data-media-start="0" muted playsinline></video>')
    tpl = open(os.path.join(KIT, "plantillas", "reel.html"), encoding="utf-8").read()
    for k, v in {"{{W}}": str(w), "{{H}}": str(h), "{{CLASE}}": cls, "{{DUR}}": f"{dur:.3f}".rstrip("0").rstrip("."),
                 "{{HOOK_TOP}}": str(hook_top), "{{CRUDO}}": crudo}.items():
        tpl = tpl.replace(k, v)
    open(os.path.join(dest, "index.html"), "w", encoding="utf-8").write(tpl)
    pkg = {"name": os.path.basename(dest).lower(), "private": True,
           "scripts": {"check": "hyperframes check", "render": "hyperframes render --workers 1"},
           "dependencies": {"hyperframes": "0.8.43", "gsap": "3.15.0"}}
    json.dump(pkg, open(os.path.join(dest, "package.json"), "w", encoding="utf-8"), indent=2)
    for d in ("assets/capturas", "qa", "renders"):
        os.makedirs(os.path.join(dest, d), exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("nombre", help="carpeta dentro de proyectos-video/, ej. 2026-10-12-reel-whatsapp")
    ap.add_argument("--formato", choices=["reel", "horizontal", "ambos"], default="reel")
    ap.add_argument("--duracion", type=float, help="segundos (con --crudo se toma la del video si falta)")
    ap.add_argument("--crudo", help="video crudo: grabación, avatar o pantalla")
    ap.add_argument("--three", action="store_true", help="la pieza usa el iPhone 3D (agrega three@0.181.2)")
    a = ap.parse_args()

    base = os.path.join(REPO, "proyectos-video", a.nombre)
    if os.path.exists(os.path.join(base, "index.html")) or os.path.exists(os.path.join(base, "reel")):
        sys.exit(f"Ya existe {base}: elegí otro nombre (no piso proyectos).")
    os.makedirs(base, exist_ok=True)

    dur, crudo_rel = a.duracion, None
    if a.crudo:
        vdur, vw, vh = probe(a.crudo)
        dur = dur or round(vdur, 3)
        ext = os.path.splitext(a.crudo)[1].lower() or ".mp4"
        os.makedirs(os.path.join(base, "assets"), exist_ok=True)
        shutil.copy2(a.crudo, os.path.join(base, "assets", "crudo" + ext))
        crudo_rel = "assets/crudo" + ext
        print(f"crudo: {vw}x{vh}, {vdur:.2f} s -> {crudo_rel}")
    if not dur:
        sys.exit("Falta --duracion (o --crudo).")

    targets = ["reel", "horizontal"] if a.formato == "ambos" else [a.formato]
    for fmt in targets:
        dest = os.path.join(base, fmt) if a.formato == "ambos" else base
        build(dest, fmt, dur, crudo_rel)
        if crudo_rel and dest != base:   # each composition serves files from its own folder only
            shutil.copy2(os.path.join(base, crudo_rel), os.path.join(dest, crudo_rel))
        if a.three:
            p = os.path.join(dest, "package.json"); pkg = json.load(open(p, encoding="utf-8"))
            pkg["dependencies"]["three"] = "0.181.2"; json.dump(pkg, open(p, "w", encoding="utf-8"), indent=2)
        print("listo:", os.path.relpath(dest, REPO))
    deps = "hyperframes@0.8.43 gsap@3.15.0" + (" three@0.181.2" if a.three else "")
    print(f"\nSiguiente: en cada carpeta, npm i {deps}  (instala solo dentro del proyecto)")


if __name__ == "__main__":
    main()
