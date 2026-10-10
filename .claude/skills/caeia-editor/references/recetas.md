# Recetas por modo

Puntos de partida, no fórmulas: cada pieza necesita su idea. Los textos de ejemplo hay que reemplazarlos por lo que dice Axel o por lo que está en `brand.md`.

## talking (Axel o el avatar hablando, vertical)
1. Crudo de fondo a pantalla completa (`object-fit: cover`). Si viene horizontal, recortá centrado en la cara con `object-position` y verificá en los snapshots que la cara quede entera.
2. **0–2 s:** gancho arriba (`.t.hook` sobre `.scrim-top`) con las palabras exactas que dice la persona, al ritmo de la voz (`MKP.sayIn`).
3. Subtítulos palabra por palabra en `#subs`, debajo de la cara y arriba de la zona tapada (y ≈ 1180–1440).
4. Una intervención cada 4–6 s en reels: una palabra clave, un ícono simple, una captura chica (`.shot`) que entra con `smearIn` y sale con `whip`. Nunca tapa la cara.
5. Zoom suave (escala 1,0 → 1,08 sobre el video, `expo.inOut`) en la frase más fuerte. Nunca durante el gancho.
6. Cierre: `MKP.cut` al `.panel`, wordmark + @caeia.app + CTA exacto.

## pantalla (app de CAEIA, ARCA o WhatsApp)
1. Captura o grabación dentro de `.shot` en `#cam`, con sus medidas reales. Se mide y se muestrea de la captura, no se inventa.
2. Antes de usar una factura de homologación: tapá o reemplazá CUIT, nombre y domicilio de terceros (rectángulo `--app-bg` + texto de prueba en JetBrains Mono).
3. Cámara: vista completa (escala 1) → zoom 1,6–2,2 a la acción (botón, campo, CAE) → vuelta a la vista completa. Un `cam()` por acción; el cursor o el `MK.tap` vive dentro de `#cam`.
4. Lo de ARCA lento: `MKP.freeze` sobre la captura + titular corto. Nada de cifras de tiempo inventadas.
5. La UI de CAEIA se ve como es (glassmorphism violeta, tokens `--app-*`). Los titulares de marketing usan los tokens `--caeia-*`.

## flyer
1. Recortá el flyer en bloques (titular, imagen, datos, logo) con PIL o ffmpeg, o recrealo en HTML si es simple. Mejor que mover la imagen entera.
2. Cada bloque entra en su beat (`smearIn` escalonado), con deriva lenta para que nada quede quieto más de 1 s.
3. Fechas y datos del flyer: se copian textuales y se verifican contra `brand.md` (por ejemplo, el evento del 18/11).

## motion puro (sin crudo)
- Idea vaga → `motion-brief-writer`. Pieza de venta → `launch-video`. Un efecto de UI → `motion-effects`. Un dato → `animated-chart`.
- Esas skills vienen de un pack externo (Charlie Hills, MIT). Construí siempre con el contrato de `contrato-y-kit.md`, no con un `window.seek()` suelto.

## cuenta regresiva al 18/11
- Un número grande por pieza ("faltan 12 días"), calculado desde la fecha de publicación que diga Axel. **No desde la fecha de hoy si no se publica hoy.**
- Lugar y fecha exactos de `brand.md`. Hora e inscripción: PREGUNTAR A AXEL.
