# estilo.md — Claudio Conde (ejemplo completo)

<!-- Ejemplo real de cómo se llena estilo.md. Las rutas son relativas a la carpeta del proyecto:
     cada uno pone ahí sus propios archivos. -->

## 1. Marca

- **Nombre (como aparece en pantalla):** Claudio Conde
- **Qué hacés, en una línea:** Opero dos negocios con IA y muestro cómo funcionan por dentro.
- **Negocios / productos que se pueden mostrar:**
  - 100ads · software · assets/logos/100ads.png · assets/logos/100ads-blanco.png
  - ND1 · consultoría · assets/logos/nd1.png · assets/logos/nd1-blanco.png
- **Fotos propias permitidas:** assets/fotos/ (solo las que están en esa carpeta)
- **Datos que se pueden mostrar siempre** (con su fuente):
  - "3 años publicando en YouTube todas las semanas" — fuente: el canal
  - "~300 mentorías" — fuente: registro propio
  - Cualquier otra cifra: solo si la digo en cámara, con su minuto.
- **Datos que NUNCA se muestran:** montos por cliente, nombres de alumnos o clientes, tablas de pagos, leads.

## 2. Tipografía y color

- **Fuente:** "Helvetica Neue" (tipografía de sistema estilo Apple; el render usa Inter como equivalente)
- **Color de acento:** #0066ff
- **Color de tinta:** #0a2030
- **Color de etiquetas:** #152f43
- **Color del titular grande:** #ffffff

```json
{ "font": "\"Helvetica Neue\", -apple-system, Arial, sans-serif", "ink": "#0a2030", "label": "#152f43",
  "accent": "#0066ff", "title": "#ffffff", "material": "light", "font_faces": [] }
```

## 3. Material

- **Vidrio:** claro
- **Dónde grabás normalmente:** exterior de día (patio con pasto y cielo), persona al centro.
- **Dónde suele estar tu cara en el cuadro:** centro.

## 4. Tono

- **Idioma y variante:** español rioplatense.
- **Tono:** directo, concreto, sin exagerar. Nada de promesas de facturación.
- **Palabras que usás:** "por dentro", "sistema", "dinero", "trabajo", "negocio".
- **Palabras que no usás nunca:** "plata", "laburo", superlativos no verificables ("el mejor", "sin precedentes").

## 5. Ritmo de edición

- **Intro:** primeros 45 s, edición densa: un recurso cada 3-5 s.
- **Cuerpo:** una intervención cada 30-60 s, de 6-8 s.
- **Intensidad de movimiento:** intro alta (entradas 3D laterales) · cuerpo sobria.
- **Tipos de recurso:** titular + pastilla, cifras en tarjeta, logos de 100ads y ND1, diagramas de flujo, pasos, split-screen con el iPad o la pantalla, ventana con scroll para la landing.
- **Cortes:** silencios de más de 0,5 s y muletillas fuera; nunca cortar a mitad de palabra; los bloopers que marque en el prompt se quedan.

## 6. Música

- **Música:** ambient tenue generada local.
- **Volumen bajo la voz:** −22 dB, sube apenas en pausas largas y en el cierre.
- **Efectos de sonido:** ninguno.

## 7. Qué NO hacer

- Tapar la cara con cualquier gráfico.
- Pantallas completas que oculten a la persona.
- Inventar cifras o redondearlas para arriba.
- Controlar CapCut/Premiere con computer-use.
- Estética "muy IA": gradientes violetas, glow genérico, tres tarjetas iguales.
- Mostrar caras de terceros sin pedido.

## 8. Referencias de estilo

- Liquid Glass de Apple (iOS 26): vidrio translúcido con el fondo visible, borde con refracción, reflejo especular.
- Referencia aprobada: titular blanco "MIS MENTORES." con pastilla "OTRO NIVEL." arriba y dos tarjetas de vidrio a los costados con etiqueta en mayúsculas, punto azul, cifra grande y "al mes" (ver `ejemplos/previews/intro-titular-y-cifras.jpg`).
