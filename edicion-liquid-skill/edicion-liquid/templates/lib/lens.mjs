// lens.mjs — genera el mapa de desplazamiento (squircle + Snell BK7) y el
// filtro SVG de una sola pasada que usa cada tarjeta de vidrio.
import { buildDisplacementLUT, renderDisplacementMap } from './glass-optics.mjs'
import { encodePNG } from './png.mjs'

let cached = null
function lut() {
  if (!cached) cached = buildDisplacementLUT(1024)
  return cached
}

// Devuelve { id, width, height, radius, bezel, scale, png }
export function makeLens({ width, height, radius = 44, bezel } = {}) {
  width = Math.round(width)
  height = Math.round(height)
  if (!(width > 0 && height > 0)) throw new Error(`lente inválida ${width}x${height}`)
  if (bezel == null) bezel = Math.max(18, Math.min(26, Math.round(Math.min(width, height) / 11)))
  radius = Math.min(radius, Math.floor(Math.min(width, height) / 2))
  const { lut: table, peak } = lut()
  const rgba = Buffer.alloc(width * height * 4)
  renderDisplacementMap(rgba, { width, height, radius, bezel, lut: table })
  return {
    id: `lens-${width}x${height}r${radius}b${bezel}`,
    width,
    height,
    radius,
    bezel,
    scale: 2 * bezel * peak,
    png: encodePNG(rgba, width, height),
  }
}

// Filtro SVG: feImage (PNG embebido como data URI) + feDisplacementMap.
// filterUnits=userSpaceOnUse: coordenadas relativas a la caja del elemento
// que lo usa en backdrop-filter.
export function lensFilter(lens) {
  const uri = 'data:image/png;base64,' + lens.png.toString('base64')
  return (
    `<filter id="${lens.id}" x="0" y="0" width="${lens.width}" height="${lens.height}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">` +
    `<feImage href="${uri}" x="0" y="0" width="${lens.width}" height="${lens.height}" preserveAspectRatio="none" result="lensMap"/>` +
    `<feDisplacementMap in="SourceGraphic" in2="lensMap" scale="${lens.scale.toFixed(4)}" xChannelSelector="R" yChannelSelector="G"/>` +
    `</filter>`
  )
}
