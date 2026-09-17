#!/usr/bin/env node
// generate-lens-maps.mjs — exporta mapas de lente sueltos (PNG + manifest).
// build_scene.mjs ya los genera y embebe solo; esto sirve para escenas
// escritas a mano o para inspeccionar un mapa.
import fs from 'node:fs'
import path from 'node:path'
import { makeLens } from './lib/lens.mjs'

const HELP = `Uso:
  node generate-lens-maps.mjs --spec <id>:<ancho>x<alto>[:radio[:bisel]] [--spec ...] [--out <dir>]
  node generate-lens-maps.mjs --json specs.json [--out <dir>]

specs.json = [{"id":"wide","width":546,"height":260,"radius":44,"bezel":24}, ...]
Salida: <dir>/lens-<id>.png y <dir>/lens-manifest.json con {id,width,height,radius,bezel,scale,filename}.
"scale" es el valor para feDisplacementMap (2 · bisel · pico del perfil Snell).
Default --out: ./assets`

const args = process.argv.slice(2)
if (!args.length || args.includes('--help') || args.includes('-h')) {
  console.log(HELP)
  process.exit(args.length ? 0 : 1)
}
const specs = []
let out = 'assets'
for (let i = 0; i < args.length; i++) {
  const a = args[i]
  if (a === '--out') out = args[++i]
  else if (a === '--json') specs.push(...JSON.parse(fs.readFileSync(args[++i], 'utf8')))
  else if (a === '--spec') {
    const m = /^([\w-]+):(\d+)x(\d+)(?::(\d+))?(?::(\d+))?$/.exec(args[++i] || '')
    if (!m) {
      console.error(`--spec inválido: ${args[i]}\n\n${HELP}`)
      process.exit(1)
    }
    specs.push({ id: m[1], width: +m[2], height: +m[3], radius: m[4] ? +m[4] : 44, bezel: m[5] ? +m[5] : undefined })
  } else {
    console.error(`Argumento desconocido: ${a}\n\n${HELP}`)
    process.exit(1)
  }
}
fs.mkdirSync(out, { recursive: true })
const manifest = []
for (const s of specs) {
  const lens = makeLens(s)
  const filename = path.join(out, `lens-${s.id}.png`)
  fs.writeFileSync(filename, lens.png)
  manifest.push({ id: s.id, width: lens.width, height: lens.height, radius: lens.radius, bezel: lens.bezel, scale: +lens.scale.toFixed(4), filename })
  console.log(`ok ${filename} scale=${lens.scale.toFixed(4)}`)
}
fs.writeFileSync(path.join(out, 'lens-manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
