# Estilo: Saturado Bold

Tarjetas planas y opacas (sin vidrio, sin blur), borde grueso, sombra dura desplazada,
tipografía enorme en mayúsculas y colores saturados a full. Piensa contenido tipo "viral
de feed" o Hormozi-style: el texto pega fuerte, no acompaña de fondo.

## Cuándo usarlo
- Ganchos/hooks agresivos, CTAs, contenido con tono de urgencia o "antes/después".
- Cuando el video ya tiene mucho ruido visual de fondo y necesita texto que se lea aunque
  se mire con el volumen apagado y a los 2 segundos.
- Alternativa cuando el cliente/marca pide algo "menos Apple, más MrBeast".

## Cuándo NO usarlo
- Contenido institucional, demos de producto serias, tono profesional-cercano (ahí va
  `liquid-glass`).
- Si la marca tiene una identidad ya asentada en vidrio/glassmorphism (como CAEIA — ver
  `contexto-caeia.md` § 7.2), usar este estilo para overlays puede leerse inconsistente
  con capturas reales de la app. Combinarlo solo en piezas de gancho puntuales, no en todo
  el catálogo de contenido.

## Cómo se usa
Igual que cualquier otro estilo: mismo `escenas/plan.json`, mismos 10 tipos de elemento.
Solo cambia el flag al construir cada escena:
```bash
node <skill>/templates/build_scene.mjs --scene escenas/plan.json --id intro-01 --theme tema.json --style saturado-bold
```

## Notas de diseño
- `--lf-accent` en `tema.json` define el color del chip de mayúsculas, el punto, los
  números de diagrama y el marcador de `steps`. Con colores de marca poco saturados
  (pasteles) este estilo pierde el punch — si `estilo.md` no trae un acento saturado,
  preguntar antes de asumir uno.
- El titular (`headline`) no lleva velo suave como en liquid-glass: lleva un bloque de
  color sólido detrás (`scrim`), como una franja. Si el fondo del video ya es muy
  saturado, `scrim: false` puede leerse mejor.
- No hay versión "dark" muy distinta a "light" más que invertir tarjeta blanca/negra:
  este estilo no busca sutileza, busca contraste.
