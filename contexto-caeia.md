> **Histórico (17/9/2026).** Reemplazado por `brand.md` (qué se dice) y `MOTION.md` (cómo se ve) el 2026-10-10. Lo de acá puede estar desactualizado: Excel ya existe en homologación, el cobro con Mercado Pago está bloqueado y falta el evento del 18/11. Usá `brand.md`.

# contexto-caeia.md — qué es el producto que estos videos venden

Este archivo le da a la IA (y a cualquiera que edite) el contexto del **producto real** detrás de los
reels que se editan en este repo. `estilo.md` define *cómo* se edita (colores, ritmo, tono personal
de Axel); este archivo define *qué* se está vendiendo, para que ningún gráfico, cifra o frase del
video contradiga lo que CAEIA realmente es o hace hoy.

Fuente: segundo cerebro de Axel (`WIKI/caeia.md`, `WIKI/caeia-brief-marca.md`, `WIKI/marketing-caeia.md`),
sincronizado a mano el 2026-09-17. Si algo suena desactualizado, la fuente de verdad sigue siendo el
segundo cerebro — preguntarle a Axel antes de asumir.

## 1. Qué es CAEIA (una línea)

Plataforma de facturación electrónica con Inteligencia Artificial para Argentina: reemplaza la
experiencia lenta y frustrante de facturar directo en ARCA (ex AFIP) por una experiencia rápida,
tanto desde una app web como desde WhatsApp.

## 2. El problema que resuelve (el ángulo de cada video)

ARCA es rígido, lento y se cae con frecuencia. Cualquier contribuyente que factura seguido pierde
tiempo real navegando una interfaz torpe para cada comprobante. CAEIA no reemplaza a ARCA (sigue
siendo quien valida y autoriza cada factura) — reemplaza la experiencia de usarlo.

**Mensaje central, siempre:** no se vende "tecnología" ni "IA" como concepto — se vende **tiempo
recuperado** y **simpleza**. Un gráfico o titular que hable de "innovación" o "inteligencia
artificial" en abstracto está fuera de mensaje; uno que muestre segundos/minutos ahorrados, o el
antes/después de cargar una factura, está en mensaje.

## 3. Para quién es (a quién le habla el video)

- **Monotributistas** — Factura C, sin complicarse con sistemas contables.
- **Responsables Inscriptos (RI)** — Factura A/B con discriminación de IVA correcta.
- **Contadores y estudios contables** — canal de crecimiento a futuro, todavía no construido en producto.

**Geografía:** foco inicial en **Salta y el NOA argentino** — identidad regional concreta, no un
producto genérico para toda Latinoamérica. El tono de los videos puede (y debe) sonar local, no
corporativo neutro.

## 4. Qué hace hoy de verdad (no inventar funciones que no existen)

Dos canales, mismo motor de emisión contra ARCA (WSFE) por detrás:

**Canal web** — wizard de emisión en 3 pasos; el tipo de comprobante (A/B/C) se calcula solo según
la condición de IVA del cliente; agenda de clientes con autocompletado desde el padrón de ARCA por
CUIT; cada factura sale con CAE real y PDF oficial con QR (RG 4291), logo propio y color de marca
personalizable por negocio; historial con filtros.

**Canal WhatsApp (agente de IA)** — el negocio pide por WhatsApp, texto o audio, que se emita una
factura en lenguaje natural; el agente también responde consultas de facturación ya emitida;
**siempre pide confirmación humana antes de emitir** (esto es un punto de tranquilidad a mostrar,
no un detalle técnico menor).

**Acceso:** registro self-serve con tarjeta, 10 días de prueba gratis, cobro recurrente vía Mercado Pago.

## 5. Qué NO mostrar ni prometer todavía

- **Módulo Compras** (digitalización de comprobantes de compra por foto) — pausado, sin desarrollo
  activo. No mostrarlo como feature disponible ni prometerlo en un CTA.
- Integraciones que no existen: Excel, e-commerce, multi-CUIT para contadores como feature ya construida.
- Casos de clientes reales identificables sin permiso explícito — mantener genérico (comercio tipo,
  no un negocio puntual) salvo que Axel confirme el permiso puntual para ese video.
- No inventar cifras de facturas emitidas, tiempo ahorrado, usuarios, etc. — si un video muestra un
  número, tiene que salir de lo que Axel dice en cámara o de un dato confirmado, igual que la regla
  general de `edicion-liquid` de "no inventar cifras".

## 6. El diferenciador de confianza más fuerte (útil como gancho/CTA)

**CAEIA nunca pide ni ve la clave fiscal del usuario.** Usa el mecanismo oficial de delegación de
ARCA para operar en nombre del cliente sin necesitar su clave fiscal real — contraste directo con
competidores (Facturitas, Vili) que sí la piden en algún punto del onboarding. Es el mensaje de
confianza más verificable y diferenciador que tiene la marca; sirve como cierre o como "gancho de
seguridad" en varios formatos de reel.

## 7. Identidad visual — qué colores/formas usar en los gráficos del video

Hay **dos estéticas distintas y no deben mezclarse**:

### 7.1 Identidad de marketing (usar esta en los overlays de los reels)

Colores exactos:

| Uso | Hex |
|---|---|
| Azul eléctrico ("CAE") | `#0ea5e9` |
| Violeta ("IA") | `#8b5cf6` |
| Fondo oscuro | `#0a0e1a` |
| Azul variante clara (fondos claros) | `#1d7fc4` |
| Violeta variante clara (fondos claros) | `#7c4fd6` |

Split de color literal entre "CAE" (azul) e "IA" (violeta) — **nunca degradé** entre ambos.

**Isotipo**: una hoja tipo documento A4 (proporción vertical completa, no ticket angosto), esquinas
redondeadas, esquina superior derecha doblada hacia adentro ("dog-ear") en violeta tenue. Un pulso
de datos (línea tipo electrocardiograma) atraviesa el documento horizontalmente y corta su borde
lateral. Representa "el papel que se convierte en dato validado por IA".

**Qué NO usar nunca**: destellos/"sparkles" de 4 puntas (ícono genérico tipo Gemini), circuitos tipo
PCB, neón/glow genérico, símbolo $, robots o mascotas de IA, ticket térmico en vez de hoja A4,
estética cyberpunk/gamer. (Esto es un descarte histórico ya validado — si un gráfico se empieza a
parecer a esto, es la señal de que se está desviando de marca.)

**Tono de marca**: profesional pero cercano · minimalista, poco texto por pieza · estética "SaaS
moderno" · con identidad local (Salta/NOA real, no corporativo abstracto).

### 7.2 Diseño real de la interfaz de la app (usar solo si el video muestra un mockup/captura de la app)

Distinto a propósito de la identidad de marketing: la UI real es **glassmorphism** (vidrio
esmerilado, blur, bordes sutiles), tema oscuro por defecto (`#0f0b1e` fondo, `#ddd6fe` texto,
acento violeta `#8b5cf6`/`#6d28d9`), tipografía real Space Grotesk (títulos)/Geist (texto)/JetBrains
Mono (mono). Si un video incluye una captura de pantalla real de la app, tiene que verse así — no
con los colores planos de marketing.

**Nota para `edicion-liquid`**: el material "Liquid Glass" que usa la skill (tarjetas de vidrio
translúcido para overlays) es un lenguaje visual propio de la edición, no una copia literal de la
UI de CAEIA — pero como la UI real de CAEIA *también* es glassmorphism violeta, el estilo de edición
y el producto quedan coherentes entre sí de forma natural. Aprovechar eso: los acentos de color
dentro de las tarjetas de vidrio de cada video pueden usar el azul/violeta de CAEIA en vez de un
azul genérico, para reforzar marca sin citar literalmente la UI.

## 8. Por qué estos videos usan avatar de IA (contexto, no un detalle técnico)

La estrategia de contenido decidió usar un avatar de IA clonado de Axel para poder sostener
publicación diaria/frecuente sin depender de su tiempo real en cámara (trabaja en Tevez Repuestos
de 16 a 19:30hs, tiempo acotado). El objetivo del contenido sigue siendo el mismo que si fuera
grabación real: reforzar autoridad y mostrar casos reales del producto — cambia el método de
producción, no el mensaje ni el estándar de calidad. Por eso el video final tiene que verse
profesional y coherente con la marca, no como un experimento de IA.

## 9. Objetivo de negocio detrás del contenido

Objetivo financiero de Axel con CAEIA: USD 4.000/mes como negocio principal. El contenido de
Instagram (@caeia.app) es contenido de **autoridad y credibilidad**, no el canal principal de
conversión (eso sigue siendo la venta en persona en Salta/NOA) — pero sí refuerza la confianza
cuando un prospecto ya conoció a Axel o CAEIA por otro canal. No forzar CTAs de venta directa y
agresiva en cada pieza; priorizar mostrar el producto funcionando y el dolor real que resuelve.
