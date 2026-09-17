#!/usr/bin/env node
// build_scene.mjs — construye una escena HyperFrames "Liquid Glass" desde JSON.
// Sin dependencias fuera de Node ≥22. Contrato completo en templates/API.md.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { makeLens, lensFilter } from './lib/lens.mjs'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const W = 1920
const H = 1080
const EDGE = 0.35 // segundos limpios al principio y al final de cada escena
const TYPES = ['stat-card', 'headline', 'phrase', 'steps', 'diagram', 'logo-card', 'photo-card', 'lower-third', 'cta-window', 'split-screen']
const DEFAULT_SAFE = [680, 270, 560, 810] // zona de la cara (x, y, ancho, alto) con la persona centrada

const HELP = `build_scene.mjs — escena Liquid Glass para HyperFrames 0.8.43

Uso:
  node <skill>/templates/build_scene.mjs --scene escena.json [--id <id>] [--project <dir>]
       [--theme tema.json] [--out <archivo.html>] [--no-check-assets]

  --scene    JSON con UNA escena, o {"scenes":[...]} (entonces --id elige cuál)
  --id       id de la escena dentro del manifest
  --project  carpeta del proyecto HyperFrames (default: carpeta actual). Las rutas
             de footage/src del JSON son relativas a esta carpeta.
  --theme    tema.json (fuente, colores, material) derivado de estilo.md
  --out      default: <project>/index.html. Siempre se guarda además una copia
             en <project>/scenes/<id>.html.txt para reeditar.
  --no-check-assets  no exige que existan los archivos referenciados
  --types    lista los tipos de elemento y sale

Tipos: ${TYPES.join(', ')}
Después: npx hyperframes check --at <t...>  y  npx hyperframes snapshot --at <t...> --no-end`

// ── CLI ─────────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const o = { project: process.cwd(), checkAssets: true }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    const next = () => {
      const v = argv[++i]
      if (v == null) die(`Falta valor para ${a}`)
      return v
    }
    if (a === '--help' || a === '-h') o.help = true
    else if (a === '--types') o.types = true
    else if (a === '--scene') o.scene = next()
    else if (a === '--id') o.id = next()
    else if (a === '--project') o.project = next()
    else if (a === '--theme') o.theme = next()
    else if (a === '--out') o.out = next()
    else if (a === '--no-check-assets') o.checkAssets = false
    else die(`Argumento desconocido: ${a}`)
  }
  return o
}
function die(msg) {
  console.error(`ERROR: ${msg}\n\n${HELP}`)
  process.exit(1)
}

const errors = []
const warnings = []
const fail = (m) => errors.push(m)
const warn = (m) => warnings.push(m)

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d)
const r3 = (v) => Math.round(v * 1000) / 1000
const isVideo = (p) => /\.(mp4|mov|m4v|webm)$/i.test(p || '')

// ── Movimiento: intro (denso) vs cuerpo (sobrio) ────────────────────────────
const MOTION = {
  intro: { dx: 880, rotY: 62, rotZ: 9, z: -350, dy: 40, inDur: 0.72, inEase: 'power4.out', outDur: 0.42, outEase: 'power3.in', outRotY: 55, outRotZ: 7, float: 12, topY: -160, topRotX: 60 },
  body: { dx: 110, rotY: 12, rotZ: 0, z: 0, dy: 12, inDur: 0.52, inEase: 'power3.out', outDur: 0.48, outEase: 'power2.in', outRotY: 8, outRotZ: 0, float: 6, topY: -40, topRotX: 0 },
}

// ── Geometría ───────────────────────────────────────────────────────────────
function place(slot, w, h, id) {
  if (slot && typeof slot === 'object') {
    if (!Number.isFinite(slot.x) || !Number.isFinite(slot.y)) fail(`${id}: slot {x,y} necesita números`)
    const dir = slot.x + w / 2 < W / 2 ? -1 : 1
    return { x: slot.x, y: slot.y, axis: 'x', dir }
  }
  switch (slot) {
    case 'left': return { x: 70, y: Math.max(40, Math.round(525 - h / 2)), axis: 'x', dir: -1 }
    case 'right': return { x: W - 70 - w, y: Math.max(40, Math.round(515 - h / 2)), axis: 'x', dir: 1 }
    case 'top': return { x: Math.round((W - w) / 2), y: 24, axis: 'y', dir: -1 }
    case 'top-left': return { x: 70, y: 40, axis: 'x', dir: -1 }
    case 'top-right': return { x: W - 70 - w, y: 40, axis: 'x', dir: 1 }
    case 'bottom-left': return { x: 70, y: H - 90 - h, axis: 'x', dir: -1 }
    case 'bottom-right': return { x: W - 70 - w, y: H - 90 - h, axis: 'x', dir: 1 }
    default:
      fail(`${id}: slot "${slot}" inválido (left|right|top|top-left|top-right|bottom-left|bottom-right|{x,y})`)
      return { x: 70, y: 400, axis: 'x', dir: -1 }
  }
}
const intersects = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h

// ── Lentes (una por tamaño) ─────────────────────────────────────────────────
const lenses = new Map()
let CUR_MODE = 'body' // modo del elemento que se está construyendo (tinte intro vs cuerpo)
function lensFor(w, h, radius) {
  const lens = makeLens({ width: w, height: h, radius })
  if (!lenses.has(lens.id)) lenses.set(lens.id, lens)
  return lens.id
}
function opticsStyle(lensId, blur, sat) {
  const f = `url(#${lensId}) blur(${blur}px) saturate(${sat})`
  return `backdrop-filter:${f};-webkit-backdrop-filter:${f}`
}
function glassShell({ id, cls, box, radius, material, blur = 1.4, sat = 1.28, inner }) {
  const lensId = lensFor(box.w, box.h, radius)
  if (material === 'dark') {
    blur = Math.max(blur, 1.5)
    sat = Math.min(sat, 1.15)
  }
  return (
    `<div id="${id}" class="glass ${cls} ${material} m-${CUR_MODE}" style="left:${box.x}px;top:${box.y}px;width:${box.w}px;height:${box.h}px;border-radius:${radius}px">` +
    `<div class="lg-optics" data-layout-ignore style="${opticsStyle(lensId, blur, sat)}"></div>` +
    `<div class="lg-content">${inner}</div>` +
    `<div class="lg-rim" data-layout-ignore></div></div>`
  )
}

// ── Constructores por tipo: devuelven { html, box, pos, js[], media[] } ─────
function buildElement(e, idx, ctx) {
  const id = `e${idx + 1}`
  const material = e.material || ctx.material
  const need = (k) => {
    if (e[k] == null || e[k] === '') fail(`${ctx.sid}/${id} (${e.type}): falta "${k}"`)
    return e[k]
  }
  const js = []
  const media = []
  let html = ''
  let box
  let pos

  switch (e.type) {
    case 'stat-card': {
      need('label'); need('value')
      if (!e.source) fail(`${ctx.sid}/${id}: stat-card exige "source" (de dónde sale la cifra: "cámara 00:42" o "estilo.md"). No se inventan números.`)
      const w = num(e.width, 546), h = num(e.height, 260)
      pos = place(e.slot || 'left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const unit = e.unit ? `<span>${esc(e.unit)}</span>` : ''
      const inner =
        `<div class="tag lf-caps">${esc(e.label)}</div>` + (e.dot === false ? '' : '<div class="lf-dot"></div>') +
        `<div class="amount lf-ink" data-fit="w">${esc(e.value)}${unit}</div>` + (e.sub ? `<div class="per">${esc(e.sub)}</div>` : '')
      html = `<!-- fuente de la cifra: ${esc(e.source)} -->` + glassShell({ id, cls: 'stat', box, radius: 44, material, inner })
      break
    }
    case 'headline': {
      need('title')
      pos = { x: 290, y: 75, axis: 'y', dir: -1 }
      box = { x: 290, y: 75, w: 1340, h: e.pill ? 167 : 100 }
      const tone = e.pill_tone === 'light' ? 'light' : 'dark'
      html =
        `<div id="${id}" class="lf-headline"><div id="${id}-t" class="h-title${e.scrim === false ? '' : ' scrim'}" data-fit="w" data-layout-allow-overlap>${esc(e.title)}</div>` +
        (e.pill ? `<div id="${id}-p" class="h-pill ${tone}">${esc(e.pill)}</div>` : '') + `</div>`
      break
    }
    case 'phrase': {
      need('title')
      const w = num(e.width, 546), h = num(e.height, 260)
      pos = place(e.slot || 'left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const inner = `<h2 class="p-title lf-ink">${esc(e.title)}</h2>` + (e.sub ? `<p class="p-sub">${esc(e.sub)}</p>` : '')
      html = glassShell({ id, cls: 'phrase', box, radius: 44, material, blur: 1.5, inner })
      break
    }
    case 'steps': {
      need('title')
      const items = Array.isArray(e.items) ? e.items : []
      if (items.length < 1 || items.length > 5) fail(`${ctx.sid}/${id}: steps necesita 1–5 items`)
      const w = num(e.width, 546)
      const h = num(e.height, 34 + 49 + 24 + items.length * 38 + Math.max(0, items.length - 1) * 18 + 38)
      pos = place(e.slot || 'left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const inner =
        `<h2 class="s-title lf-ink" data-fit="w">${esc(e.title)}</h2><ul>` +
        items.map((t) => `<li class="lf-ink" data-reveal data-fit="w"><i class="lf-marker"></i><span>${esc(t)}</span></li>`).join('') + '</ul>'
      html = glassShell({ id, cls: 'steps', box, radius: 44, material, blur: 1.5, inner })
      break
    }
    case 'diagram': {
      const nodes = Array.isArray(e.nodes) ? e.nodes : []
      if (nodes.length < 2 || nodes.length > 6) fail(`${ctx.sid}/${id}: diagram necesita 2–6 nodes`)
      const loop = e.loop || null
      if (loop && !(loop.from >= 1 && loop.to >= 1 && loop.from <= nodes.length && loop.to <= nodes.length && loop.to < loop.from))
        fail(`${ctx.sid}/${id}: loop {from,to} usa números de nodo 1..${nodes.length} con to < from`)
      if ((e.layout || 'row') === 'row') {
        const w = num(e.width, 1240), h = 240
        pos = place(e.slot || 'top', w, h, id)
        box = { x: pos.x, y: pos.y, w, h }
        const pad = 30, colW = (w - pad * 2) / nodes.length, cx = (i) => pad + colW * (i + 0.5)
        let wires = ''
        for (let i = 0; i < nodes.length - 1; i++) {
          const a = cx(i) + 32, b = cx(i + 1) - 32
          wires += `<path data-reveal-wire="${i + 1}" d="M${r3(a)} 80H${r3(b)}M${r3(b - 9)} 72L${r3(b)} 80L${r3(b - 9)} 88"/>`
        }
        let loopLabel = ''
        if (loop) {
          const f = cx(loop.from - 1), t = cx(loop.to - 1)
          wires += `<path data-reveal-loop d="M${r3(f)} 156C${r3(f)} 202 ${r3(t)} 202 ${r3(t)} 156M${r3(t - 8)} 166L${r3(t)} 156L${r3(t + 8)} 166"/>`
          const mid = (f + t) / 2, lw = Math.abs(f - t) + colW
          loopLabel = `<div class="loop-label" data-reveal-loop style="left:${r3(mid - lw / 2)}px;width:${r3(lw)}px">${esc(loop.label || 'loop')}</div>`
        }
        const cells = nodes
          .map((n, i) => `<div class="cell" data-reveal style="left:${r3(pad + colW * i)}px;width:${r3(colW)}px"><div class="num">${i + 1}</div><div class="n-label lf-ink" data-fit="w" style="width:${r3(colW - 8)}px">${esc(n)}</div></div>`)
          .join('')
        const inner = (e.title ? `<div class="r-label lf-caps">${esc(e.title)}</div>` : '') + `<svg class="wire" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${wires}</svg>` + cells + loopLabel
        html = glassShell({ id, cls: 'diagram-row', box, radius: 44, material, blur: 1.6, inner })
      } else {
        const w = num(e.width, 546)
        const h = (e.title ? 34 + 49 + 24 : 34) + nodes.length * 38 + (nodes.length - 1) * 34 + (loop ? 44 : 0) + 38
        pos = place(e.slot || 'left', w, h, id)
        box = { x: pos.x, y: pos.y, w, h }
        const arrow = '<svg class="conn" viewBox="0 0 27 26"><path d="M13 2V23M6 16L13 23L20 16"/></svg>'
        const inner =
          (e.title ? `<h2 class="s-title lf-ink" data-fit="w">${esc(e.title)}</h2>` : '') + '<div class="flow">' +
          nodes.map((n, i) => `<div data-reveal>${i ? arrow : ''}<div class="node lf-ink" data-fit="w">${esc(n)}</div></div>`).join('') + '</div>' +
          (loop ? `<div class="loop-note" data-reveal-loop>↺ ${esc(loop.label || `vuelve a ${nodes[loop.to - 1]}`)}</div>` : '')
        html = glassShell({ id, cls: 'diagram-col', box, radius: 44, material, blur: 1.5, inner })
      }
      break
    }
    case 'logo-card': {
      need('src')
      ctx.assets.push(e.src)
      const w = num(e.width, 460), h = num(e.height, e.label ? 300 : 260)
      pos = place(e.slot || 'left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const lh = num(e.logo_height, e.label ? 150 : 170)
      const inner = `<img src="${esc(e.src)}" alt="${esc(e.alt || e.label || 'logo')}" style="height:${lh}px">` + (e.label ? `<div class="l-label lf-caps">${esc(e.label)}</div>` : '')
      html = glassShell({ id, cls: 'logo', box, radius: 44, material, blur: 1.2, inner })
      break
    }
    case 'photo-card': {
      need('src')
      ctx.assets.push(e.src)
      const w = num(e.width, 590), h = num(e.height, 520)
      pos = place(e.slot || 'left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const mh = e.caption ? h - 13 - 74 : h - 26
      let mediaTag
      if (isVideo(e.src)) {
        const vid = `${id}-v`
        media.push(vid)
        mediaTag = `<video id="${vid}" class="media clip" src="${esc(e.src)}" data-start="${r3(e.in)}" data-duration="${r3(e.out + 0.6 - e.in)}" data-media-start="${num(e.media_start, 0)}" data-track-index="${ctx.track++}" muted playsinline style="height:${mh}px"></video>`
      } else {
        mediaTag = `<img class="media" src="${esc(e.src)}" alt="${esc(e.alt || e.caption || 'foto')}" style="height:${mh}px">`
      }
      const inner = mediaTag + (e.caption ? `<div class="caption lf-ink" data-fit="w">${esc(e.caption)}</div>` : '')
      html = glassShell({ id, cls: 'photo', box, radius: 44, material, blur: 1.1, sat: 1.25, inner })
      break
    }
    case 'lower-third': {
      need('name')
      const w = num(e.width, 560), h = num(e.height, e.role ? 128 : 96)
      pos = place(e.slot || 'bottom-left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const inner = `<div class="lt-name lf-ink" data-fit="w">${esc(e.name)}</div>` + (e.role ? `<div class="lt-role lf-caps" data-fit="w">${esc(e.role)}</div>` : '')
      html = glassShell({ id, cls: 'lower', box, radius: 32, material, blur: 1.5, inner })
      break
    }
    case 'cta-window': {
      need('src')
      ctx.assets.push(e.src)
      const w = num(e.width, 590), h = num(e.height, 800)
      pos = place(e.slot || 'left', w, h, id)
      box = { x: pos.x, y: pos.y, w, h }
      const inner =
        `<div class="chrome"><i></i><i></i><i></i><div class="address lf-ink">${esc(e.address || '')}</div></div>` +
        `<div class="viewport"><img id="${id}-page" class="page" data-layout-allow-overflow src="${esc(e.src)}" alt="${esc(e.alt || 'captura de la página')}"></div>`
      html = glassShell({ id, cls: 'window', box, radius: 35, material, blur: 1.5, inner })
      for (const s of e.scroll || []) {
        if (!(s.at >= e.in && s.at + s.duration <= e.out)) fail(`${ctx.sid}/${id}: cada scroll debe caer entre in y out`)
        js.push(`tl.to('#${id}-page',{y:${-num(s.to, 0)},duration:${num(s.duration, 3)},ease:'sine.inOut'},${num(s.at, e.in + 1)});`)
      }
      break
    }
    case 'split-screen': {
      need('src')
      ctx.assets.push(e.src)
      ctx.split = true
      const pw = Math.round(W * num(e.person_width_ratio, 0.38))
      const pcx = num(e.person_center_x, 960)
      const personLeft = (e.person_side || 'left') === 'left'
      const L = Math.round(pcx - pw / 2), R = W - (L + pw)
      if (L < 0 || R < 0) fail(`${ctx.sid}/${id}: person_center_x deja el recorte fuera del cuadro`)
      const targetX = personLeft ? 50 : W - 50 - pw
      const dx = targetX - L
      // screen_aspect: proporción ancho:alto de la grabación ("4:3" horizontal por defecto, "3:4" para tablet/celu en vertical)
      const [aw, ah] = String(e.screen_aspect || '4:3').split(':').map(Number)
      if (!(aw > 0 && ah > 0)) fail(`${ctx.sid}/${id}: screen_aspect inválido (usá "4:3", "3:4", "16:9"...)`)
      const areaW = W - 150 - pw
      let vw = areaW - 26, vh = Math.round(vw * ah / aw)
      if (70 + vh + 13 > 1000) { vh = 1000 - 83; vw = Math.round(vh * aw / ah) }
      const winW = vw + 26, winH = 70 + vh + 13
      const winX = Math.round((personLeft ? 50 + pw + 50 : 50) + (areaW - winW) / 2)
      const winY = Math.round((H - winH) / 2)
      box = { x: winX, y: winY, w: winW, h: winH }
      pos = { x: winX, y: winY, axis: 'x', dir: personLeft ? 1 : -1 }
      const vid = `${id}-screen`
      media.push(vid)
      // Fondo desenfocado: la misma toma, solo durante el split (se ve cuando la persona se achica).
      const bgStart = e.in, bgDur = e.out + 1.0 - e.in
      ctx.bg.push(`<video id="${id}-bg" class="lf-video clip" src="${esc(ctx.footage)}" data-start="${r3(bgStart)}" data-duration="${r3(bgDur)}" data-media-start="${r3(ctx.mediaStart + bgStart)}" data-track-index="0" muted playsinline></video>`)
      const inner =
        `<div class="chrome"><i></i><i></i><i></i><div class="address lf-ink">${esc(e.address || '')}</div></div>` +
        `<div class="viewport" style="background:${esc(e.background || '#0b0f14')}"><video id="${vid}" class="screen clip" src="${esc(e.src)}" data-start="${r3(e.in)}" data-duration="${r3(e.out + 1.0 - e.in)}" data-media-start="${num(e.media_start, 0)}" data-track-index="${ctx.track++}" muted playsinline style="object-fit:${e.fit === 'cover' ? 'cover' : 'contain'}"></video></div>`
      html =
        `<div id="${id}-frame" class="lf-person-rim" data-layout-ignore style="position:absolute;left:${targetX}px;top:40px;width:${pw}px;height:1000px;border-radius:44px;pointer-events:none;box-shadow:inset 0 2px 2px #ffffffd9,inset 0 -2px 3px #ffffff80;z-index:1"></div>` +
        glassShell({ id, cls: 'window', box, radius: 35, material, blur: 1.5, inner })
      const t0 = e.in, t1 = e.out
      const full = `inset(0px 0px 0px 0px round 0px)`
      const cut = `inset(40px ${R}px 40px ${L}px round 44px)`
      js.push(
        `gsap.set('#${id}-frame',{autoAlpha:0});`,
        `tl.fromTo('#lf-stage',{clipPath:'${full}',x:0},{clipPath:'${cut}',x:${dx},duration:.7,ease:'power3.inOut',immediateRender:false},${r3(t0)});`,
        `tl.fromTo('#${id}-frame',{autoAlpha:0},{autoAlpha:1,duration:.3,ease:'power1.out',immediateRender:false},${r3(t0 + 0.55)});`,
        `tl.to('#${id}-frame',{autoAlpha:0,duration:.25,ease:'power1.in'},${r3(t1 + 0.2)});`,
        `tl.fromTo('#lf-stage',{clipPath:'${cut}',x:${dx}},{clipPath:'${full}',x:0,duration:.7,ease:'power3.inOut',immediateRender:false},${r3(t1 + 0.3)});`,
      )
      break
    }
    default:
      fail(`${ctx.sid}/${id}: tipo "${e.type}" desconocido (${TYPES.join(', ')})`)
      return null
  }
  return { id, html, box, pos, js, media }
}

// ── Timeline por elemento ───────────────────────────────────────────────────
function motionJS(e, el, mode) {
  const m = MOTION[mode]
  const { id, pos } = el
  const t0 = e.in, t1 = e.out
  const out = []
  const targets = e.type === 'headline' ? [`#${id}-t`, ...(e.pill ? [`#${id}-p`] : [])] : [`#${id}`]
  const hideSel = `#${id}`
  out.push(`gsap.set('${hideSel}',{autoAlpha:0});`)
  out.push(`tl.set('${hideSel}',{autoAlpha:1},${r3(t0)});`)
  targets.forEach((sel, k) => {
    const delay = r3(t0 + k * 0.22)
    let from
    if (pos.axis === 'y') from = `{y:${m.topY},rotationX:${m.topRotX},opacity:0}`
    else from = `{x:${pos.dir * m.dx},y:${m.dy * (pos.dir < 0 ? 1 : -1)},z:${m.z},rotationY:${-pos.dir * m.rotY},rotationZ:${pos.dir * m.rotZ},opacity:0}`
    const to = pos.axis === 'y' ? `{y:0,rotationX:0,opacity:1,duration:${m.inDur},ease:'${m.inEase}',immediateRender:false}` : `{x:0,y:0,z:0,rotationY:0,rotationZ:0,opacity:1,duration:${m.inDur},ease:'${m.inEase}',immediateRender:false}`
    out.push(`tl.fromTo('${sel}',${from},${to},${delay});`)
  })
  if (e.type !== 'headline') {
    out.push(`tl.fromTo('#${id}',{'--glint-x':'-20%','--glint-strength':'.95'},{'--glint-x':'120%','--glint-strength':'.5',duration:1.65,ease:'power2.out',immediateRender:false},${r3(t0)});`)
  }
  const settle = t0 + m.inDur + 0.05
  const room = t1 - settle - 0.05
  if (room >= 0.6) {
    const rot = mode === 'intro' && pos.axis === 'x' ? `,rotationY:${-pos.dir * 3}` : ''
    out.push(`tl.to('${targets.join(',')}',{y:${-m.float}${rot},duration:${r3(Math.min(2.2, room))},ease:'sine.inOut'},${r3(settle)});`)
  }
  const exitTo = pos.axis === 'y'
    ? `{y:${mode === 'intro' ? -150 : -30},opacity:0,duration:${m.outDur},ease:'${m.outEase}'}`
    : `{x:${pos.dir * (m.dx * 0.95)},y:0,rotationY:${-pos.dir * m.outRotY},rotationZ:${pos.dir * m.outRotZ},opacity:0,duration:${m.outDur},ease:'${m.outEase}'}`
  out.push(`tl.to('${targets.join(',')}',${exitTo},${r3(t1)});`)
  out.push(`tl.set('${hideSel}',{autoAlpha:0},${r3(t1 + m.outDur)});`)
  // Aparición gradual de ítems (steps / diagram)
  if (e.type === 'steps' || e.type === 'diagram') {
    const rv = Array.isArray(e.reveal) ? e.reveal : []
    out.push(`(function(){const items=document.querySelectorAll('#${id} [data-reveal]');const rv=${JSON.stringify(rv)};items.forEach((it,i)=>{gsap.set(it,{opacity:0});tl.to(it,{opacity:1,duration:.35,ease:'power2.out'},rv[i]!=null?rv[i]:${r3(t0 + m.inDur)}+i*.35);});` +
      `document.querySelectorAll('#${id} [data-reveal-wire]').forEach((wv)=>{const i=+wv.dataset.revealWire;gsap.set(wv,{opacity:0});tl.to(wv,{opacity:1,duration:.3,ease:'power2.out'},(rv[i]!=null?rv[i]:${r3(t0 + m.inDur)}+i*.35)-.12);});` +
      `const lp=document.querySelectorAll('#${id} [data-reveal-loop]');if(lp.length){lp.forEach((x)=>gsap.set(x,{opacity:0}));tl.to(lp,{opacity:1,duration:.45,ease:'power2.out'},${e.loop && e.loop.at != null ? num(e.loop.at, 0) : `(rv.length?Math.max(...rv):${r3(t0 + m.inDur)}+items.length*.35)+.3`});}})();`)
  }
  return out
}

// ── Principal ───────────────────────────────────────────────────────────────
const opts = parseArgs(process.argv.slice(2))
if (opts.help) { console.log(HELP); process.exit(0) }
if (opts.types) { console.log(TYPES.join('\n')); process.exit(0) }
if (!opts.scene) die('Falta --scene')

const project = path.resolve(opts.project)
const doc = JSON.parse(fs.readFileSync(opts.scene, 'utf8'))
let scene
if (Array.isArray(doc.scenes)) {
  if (!opts.id) die('El JSON tiene varias escenas: pasá --id')
  scene = doc.scenes.find((s) => s.id === opts.id)
  if (!scene) die(`No existe la escena ${opts.id}`)
} else scene = doc
const theme = opts.theme ? JSON.parse(fs.readFileSync(opts.theme, 'utf8')) : {}

const sid = scene.id
if (!/^[a-z0-9][a-z0-9-]*$/.test(sid || '')) fail('id de escena: minúsculas, números y guiones')
const D = scene.duration
if (!(D > 1)) fail('duration (segundos) es obligatorio y > 1')
const fps = num(scene.fps, 60)
if (!scene.footage) fail('footage es obligatorio (ruta relativa al proyecto)')
const mode = scene.mode === 'intro' ? 'intro' : 'body'
const ctx = { sid, material: scene.material || theme.material || 'light', assets: [scene.footage], track: 2, split: false, bg: [], footage: scene.footage, mediaStart: num(scene.media_start, 0) }
const safe = scene.safe_zone === null ? null : scene.safe_zone || DEFAULT_SAFE
const elements = Array.isArray(scene.elements) ? scene.elements : []
if (!elements.length) warn('La escena no tiene elements: solo se renderiza el footage')

const built = []
elements.forEach((e, i) => {
  if (!(typeof e.in === 'number' && typeof e.out === 'number')) { fail(`${sid}/e${i + 1}: "in" y "out" (segundos) son obligatorios`); return }
  const emode = e.mode === 'intro' || e.mode === 'body' ? e.mode : mode
  const m = MOTION[emode]
  const tail = e.type === 'split-screen' ? 1.0 : m.outDur
  const head = e.type === 'split-screen' ? 1.0 : m.inDur + 0.4
  if (e.in < EDGE - 1e-6) fail(`${sid}/e${i + 1}: in=${e.in} < ${EDGE}s — los bordes de escena quedan limpios`)
  if (e.out + tail > D - EDGE + 1e-6) fail(`${sid}/e${i + 1}: la salida termina en ${r3(e.out + tail)}s; tiene que terminar antes de ${r3(D - EDGE)}s`)
  if (e.out - e.in < head) fail(`${sid}/e${i + 1}: out-in=${r3(e.out - e.in)}s es muy corto (mínimo ${r3(head)}s)`)
  CUR_MODE = emode
  const el = buildElement(e, i, ctx)
  if (!el) return
  el.e = e
  el.mode = emode
  el.span = [e.in, e.out + tail]
  if (e.type !== 'split-screen' && safe && !e.allow_face_overlap) {
    const s = { x: safe[0], y: safe[1], w: safe[2], h: safe[3] }
    if (intersects(el.box, s)) fail(`${sid}/${el.id} (${e.type}) pisa la zona de la cara [${safe}] con caja [${el.box.x},${el.box.y},${el.box.w},${el.box.h}]. Movelo, achicalo o ajustá safe_zone si la persona no está centrada.`)
  }
  if (el.box.x < 0 || el.box.y < 0 || el.box.x + el.box.w > W || el.box.y + el.box.h > H) fail(`${sid}/${el.id}: la caja se sale del cuadro`)
  built.push(el)
})
for (let a = 0; a < built.length; a++)
  for (let b = a + 1; b < built.length; b++) {
    const A = built[a], B = built[b]
    const timeOverlap = A.span[0] < B.span[1] && B.span[0] < A.span[1]
    if (!timeOverlap) continue
    if (A.e.type === 'split-screen' || B.e.type === 'split-screen') warn(`${A.id} y ${B.id} conviven con un split-screen: revisá la snapshot`)
    else if (intersects(A.box, B.box)) fail(`${A.id} y ${B.id} se superponen en espacio y tiempo`)
  }
if (opts.checkAssets) {
  for (const a of ctx.assets) if (a && !fs.existsSync(path.resolve(project, a))) fail(`No existe el archivo ${a} (relativo a ${project})`)
  if (!fs.existsSync(path.join(project, 'node_modules/gsap/dist/gsap.min.js'))) fail('Falta node_modules/gsap en el proyecto: npm i hyperframes@0.8.43 gsap@3.15.0')
}

if (errors.length) {
  console.error(errors.map((x) => `ERROR: ${x}`).join('\n'))
  warnings.forEach((x) => console.error(`AVISO: ${x}`))
  process.exit(2)
}

// Tema → variables CSS
const vars = []
if (theme.font) vars.push(`--lf-font:${theme.font}`)
if (theme.ink) vars.push(`--lf-ink:${theme.ink}`)
if (theme.label) vars.push(`--lf-label:${theme.label}`)
if (theme.accent) vars.push(`--lf-accent:${theme.accent}`)
if (theme.title) vars.push(`--lf-title:${theme.title}`)
const fontFaces = (theme.font_faces || [])
  .map((f) => `@font-face{font-family:"${f.family}";src:url("${f.src}");font-weight:${f.weight || 'normal'};font-style:${f.style || 'normal'};font-display:block}`)
  .join('')
for (const f of theme.font_faces || []) if (opts.checkAssets && !fs.existsSync(path.resolve(project, f.src))) { console.error(`ERROR: no existe la fuente ${f.src}`); process.exit(2) }

const css = fs.readFileSync(path.join(HERE, 'liquid.css'), 'utf8')
const footageAttrs = `src="${esc(scene.footage)}" data-start="0" data-duration="${r3(D)}" data-media-start="${num(scene.media_start, 0)}" muted playsinline`
const bg = ctx.bg.length ? `<div id="lf-bg" data-layout-ignore>${ctx.bg.join('')}</div>` : ''
const stage = `<div id="lf-stage"><video id="lf-footage" class="lf-video clip" ${footageAttrs} data-track-index="1"></video></div>`
const js = [
  `const tl=gsap.timeline({paused:true});`,
  // Ajuste de texto determinista: achica hasta que entre (sin relojes ni red).
  `document.querySelectorAll('[data-fit]').forEach((n)=>{const base=parseFloat(getComputedStyle(n).fontSize);let s=base;while(n.scrollWidth>n.clientWidth+1&&s>base*.6){s-=1;n.style.fontSize=s+'px';}});`,
  `document.querySelectorAll('.phrase .lg-content').forEach((c)=>{const t=c.querySelector('.p-title');if(!t)return;let s=parseFloat(getComputedStyle(t).fontSize);const min=s*.6;while(c.scrollHeight>c.clientHeight+1&&s>min){s-=1;t.style.fontSize=s+'px';}});`,
]
for (const el of built) {
  if (el.e.type !== 'split-screen') js.push(...motionJS(el.e, el, el.mode))
  else js.push(...motionJS({ ...el.e, in: el.e.in + 0.35 }, el, 'body'))
  js.push(...el.js)
}
js.push(`window.__timelines["liquid"]=tl;`)

const html = `<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=1920, height=1080"><title>${esc(sid)}</title>
<!-- Generado por edicion-liquid/templates/build_scene.mjs (modo ${mode}). Editá el JSON y reconstruí; no edites a mano. -->
<script src="node_modules/gsap/dist/gsap.min.js"></script>
<style>${fontFaces}
${css}
${vars.length ? `:root{${vars.join(';')}}` : ''}</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>${[...lenses.values()].map(lensFilter).join('')}</defs></svg>
<div id="root" data-composition-id="liquid" data-start="0" data-width="${W}" data-height="${H}" data-duration="${r3(D)}" data-fps="${fps}">
${bg}${stage}
${built.map((b) => b.html).join('\n')}
</div>
<script>
${js.join('\n')}
</script></body></html>
`
const outPath = path.resolve(opts.out || path.join(project, 'index.html'))
fs.mkdirSync(path.dirname(outPath), { recursive: true })
fs.writeFileSync(outPath, html)
fs.mkdirSync(path.join(project, 'scenes'), { recursive: true })
fs.writeFileSync(path.join(project, 'scenes', `${sid}.html.txt`), html)
fs.writeFileSync(path.join(project, 'scenes', `${sid}.json`), JSON.stringify(scene, null, 2) + '\n')
warnings.forEach((x) => console.error(`AVISO: ${x}`))
const samples = [...new Set(built.flatMap((b) => [r3((b.e.in + b.e.out) / 2 + 0.2)]))].sort((a, b) => a - b)
console.log(JSON.stringify({ id: sid, output: outPath, duration: D, fps, mode, elements: built.map((b) => ({ id: b.id, type: b.e.type, box: b.box, in: b.e.in, out: b.e.out })), lenses: lenses.size, sugerido_check: `npx hyperframes check --at ${samples.join(',') || r3(D / 2)}` }, null, 2))
