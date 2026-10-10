# Estilo: Liquid Glass (default)

Tarjetas de vidrio translúcido con refracción real (lente SVG + Snell BK7), tipografía
sobria, movimiento 3D suave. El estilo "Apple" original de esta skill — sigue siendo el
default si un prompt no pide otro.

## Cuándo usarlo
- Talking-head profesional pero cercano, demos de producto, contenido de autoridad.
- Cuando la marca ya usa glassmorphism en su propia UI (coherencia visual — ver
  `contexto-caeia.md` § 7.2 para el caso CAEIA).

## Cuándo NO usarlo
- Ganchos muy agresivos / contenido tipo feed viral donde el texto tiene que pegar en
  2 segundos con el volumen apagado — ahí conviene `../saturado-bold/`.

## Cómo se usa
Es el estilo por default: no hace falta pasar `--style`. Para ser explícito:
```bash
node <skill>/templates/build_scene.mjs --scene escenas/plan.json --id intro-01 --theme tema.json --style liquid-glass
```

## Receta del material
La receta completa de las 4 capas (lente, tinte, borde, reflejo) está documentada en
`../../templates/API.md` § Material — no se duplica acá para no desincronizarse.
