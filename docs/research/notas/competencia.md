# Panorama competitivo: software de inventario y gestión para talleres mecánicos pequeños en Honduras

*Investigación de mercado — octubre 2026. Fuentes primarias en las secciones siguientes; notas de research detalladas (con inferencias y brechas completas) en los archivos `_research-honduras-local.md`, `_research-latam-global-saas.md` y `_research-generic-alternatives.md` de esta misma carpeta.*

## Resumen ejecutivo

El mercado hondureño de software para talleres mecánicos y repuesteras está prácticamente **desatendido**:

- No existe ningún proveedor hondureño identificado que se posicione explícitamente como "software para talleres mecánicos" o "para repuesteras". El único candidato con presencia web y claim de certificación SAR (Zafra Cloud) es un producto genérico de gestión para pymes, lanzado en julio de 2026, sin reseñas independientes y sin mención alguna del rubro automotriz.
- Ningún SaaS especializado en talleres —ni los latinoamericanos (Appli-Car, TallerOS, Tuulapp, ClearMechanic, etc.) ni los globales (Tekmetric, Shopmonkey, AutoLeap, Mitchell1, GaragePlug)— declara soporte para Honduras, Lempiras (HNL) o el régimen fiscal del SAR (CAI/autoimpresor).
- Las alternativas genéricas de bajo costo que sí usan pequeños negocios en la región (Alegra, Loyverse, Zoho Inventory, Odoo, Excel, catálogo de WhatsApp Business) tampoco cubren el cumplimiento fiscal hondureño: Alegra, pese a tener presencia activa en Costa Rica, **excluye explícitamente a Honduras** de su lista oficial de países soportados.
- Honduras todavía no tiene un mandato de factura electrónica estructurada equivalente al de sus vecinos (Costa Rica, El Salvador, Guatemala); opera bajo el régimen de pre-autorización CAI (imprenta o autoimpresor), lo que reduce el incentivo regulatorio para que proveedores LatAm de facturación electrónica certifiquen ahí.
- Las quejas de usuarios sobre las herramientas existentes (locales, LatAm, globales y genéricas) se concentran en precio/valor, soporte post-venta lento y funciones faltantes — pero casi ninguna reseña aborda específicamente idioma español, modo offline o facturación hondureña, simplemente porque la base de usuarios que deja reseñas (EE.UU., Europa, Sudamérica) no enfrenta esos problemas. Esta ausencia de evidencia es en sí misma una señal: nadie está documentando el dolor de un taller hondureño porque casi nadie hondureño usa (o reseña) estas herramientas.

**Conclusión:** existe un vacío claro para un producto simple, barato, en español, que resuelva el combo "inventario de repuestos + órdenes de trabajo + facturación conforme al CAI/SAR" para talleres y repuesteras pequeñas de Honduras — ver sección 5.

---

## 1. Proveedores locales hondureños y centroamericanos

### 1.1 Empresas identificadas

La búsqueda general (no-Facebook) arrojó **solo dos candidatos** con presencia web verificable en Honduras, y ninguno se especializa en talleres mecánicos o repuesteras:

- **Zafra Cloud**: sistema de gestión "100% en la nube" para pymes, dirigido explícitamente a "Honduras y Centroamérica". Ofrece facturación, punto de venta, inventario multi-almacén, contabilidad automatizada y CRM. Los sectores que menciona son tiendas retail, restaurantes, distribuidores, clínicas y servicios profesionales — **no menciona talleres ni repuesteras**. Fecha de lanzamiento en el listado: 12 de julio de 2026. El publisher aparece como "Isabella Madrid" (nombre de persona, no de empresa registrada visible) — [Source](https://mwm.ai/apps/zafra-cloud/6771561083)
- **Softland**: ERP regional (con operación fuera de Honduras) que mantiene sitio específico para Honduras (softland.com/hn) y un módulo POS ("Colnet – Elisium") para retail y food & beverage, integrado en tiempo real a su ERP. Tiene al menos un cliente hondureño grande y nombrado: Banasupro (cadena estatal de distribución de productos básicos) — [Source](https://softland.com/hn/?p=1337); [Source](https://preview.softland.cl/cl/wp-content/uploads/2025/08/Banasupro-HN-1.pdf). Cuenta con un distribuidor local llamado "SOFTCA" — [Source](https://softland.com/hn/partners/). Es un ERP general, no vertical automotriz.
- **Odoo** (ERP internacional open-source, no hondureño) tiene socios implementadores registrados en Honduras según su propio directorio de partners, confirmando que hay integradores locales de Odoo en el país, aunque ninguno identificado como especializado en el rubro automotriz — [Source](https://www.odoo.com/es/partners/country/94)
- Un producto llamado "GNcys" apareció en las búsquedas pero fue descartado como probable falso positivo mexicano: su manual hace referencia a cumplimiento con el "SAT" (autoridad tributaria mexicana), no el SAR hondureño — [Source](https://gncys.com/manuales/gncys-tpv-manual-2021.pdf)

**Evidencia del vacío de mercado (fuentes académicas):** una tesis de la UNITEC (Universidad Tecnológica Centroamericana) documenta que Honduras tiene más de 130,000 Mypymes (usando pulperías/supermercados como categoría de referencia) y que la mayoría **no cuenta con un sistema especializado** de ventas, compras e inventario — [Source](https://repositorio.unitec.edu/items/cca5a2a6-bac9-43a8-abf5-5f749295ecd0/full). Otra tesis UNITEC sobre el "desafío de la implementación de la factura electrónica en el sector Mipyme" confirma que las mipymes hondureñas hoy dependen de impresión (imprentas autorizadas) o autoimpresión, no de una plataforma de software unificada — [Source](https://repositorio.unitec.edu/items/b87fb723-6cb6-46a0-9c2d-56f100e05ac2/full).

### 1.2 Precios y modelo de soporte

**No se encontró ningún precio público en HNL o USD** para ningún producto hondureño, automotriz o general. Único dato relacionado: Zafra Cloud ofrece prueba gratuita de 14 días sin tarjeta de crédito, sin precio de suscripción divulgado — [Source](https://mwm.ai/apps/zafra-cloud/6771561083). Softland requiere contacto directo (vía su distribuidor SOFTCA) para cotización — no publica lista de precios para Honduras.

El único canal de soporte confirmado es **WhatsApp en español**, explícitamente anunciado por Zafra Cloud como característica — [Source](https://mwm.ai/apps/zafra-cloud/6771561083). Es razonable inferir (sin confirmación independiente) que la venta vía cotización directa por WhatsApp/teléfono/visita es la norma en este segmento, dada la ausencia total de listas de precios públicas — patrón típico de software B2B en mercados pequeños centroamericanos.

### 1.3 Cumplimiento fiscal (SAR, CAI, autoimpresor)

El régimen hondureño está bien documentado por rastreadores de cumplimiento tributario:

- Toda factura en Honduras debe llevar un **CAI** (Código de Autorización de Impresión), código único que el SAR asigna por lote antes de imprimir/generar facturas, bajo un modelo de **pre-autorización de numeración** (no validación en tiempo real por documento) — [Source](https://invoicedataextraction.com/blog/honduras-invoice-requirements)
- Existen dos vías válidas de emisión: **"autoimpresor"** (el negocio autoimprime desde un sistema registrado ante el SAR) o **"imprenta"** (imprentas certificadas por el SAR producen los documentos) — [Source](https://invoicedataextraction.com/blog/honduras-invoice-requirements)
- Requisitos de una factura válida: RTN de 14 dígitos, numeración secuencial de 16 dígitos, desglose de ISV al 15%, y fecha de vencimiento del CAI (válido máximo 1 año) — [Source](https://invoicedataextraction.com/blog/honduras-invoice-requirements)
- El Acuerdo 481-2017 permite una modalidad opcional de "Facturación Electrónica" (CAEE) de autoimpresión, pero **no es un sistema de facturación electrónica obligatorio ni con clearance del SAR** como en Costa Rica o México — [Source](https://www.vatupdate.com/2026/08/11/honduras-e-invoicing-e-reporting-country-booklet/)
- Según el country booklet con fecha 11-ago-2026, el SAR está introduciendo **por fases** un sistema obligatorio de Continuous Transaction Controls (CTC) que exigirá XML firmado y validado antes de emitir al cliente — pero Honduras **todavía no tiene esto en vivo** y el SAR sigue en fase de diseño desde una encuesta a contribuyentes de diciembre de 2022 — [Source](https://www.vatupdate.com/2026/08/11/honduras-e-invoicing-e-reporting-country-booklet/)
- La Prensa (Honduras) reporta que el SAR creó un "acceso en línea para impresión de facturas" (portal relacionado con la autorización de impresión), aunque no se pudo verificar el contenido completo del artículo — [Source](https://www.laprensa.hn/honduras/el-sar-crea-acceso-en-linea-para-impresion-de-facturas-PSLP972508)

**No se encontró ninguna lista oficial del SAR** con autoimpresores o imprentas certificadas publicada en línea (no se hizo un crawl directo de sar.gob.hn por límite de tiempo de la investigación — queda como tarea pendiente).

De los productos identificados, **solo Zafra Cloud** afirma estar "oficialmente certificado por el SAR de Honduras" — marcado explícitamente como *claim* de marketing, no verificado independientemente — [Source](https://mwm.ai/apps/zafra-cloud/6771561083). Ningún otro producto (Softland, Odoo, ni los del resto de este informe) hace una afirmación citable de cumplimiento CAI/SAR.

### 1.4 Reseñas de usuarios

**No se encontró ninguna reseña** de Facebook, Google Maps o cualquier agregador para Zafra Cloud, Softland Honduras, o cualquier otro candidato local. Búsquedas específicas de "Zafra Cloud" devolvieron resultados completamente ajenos (tormentas tropicales, pueblos españoles llamados Zafra). Esta ausencia es consistente con el hallazgo general: este segmento de mercado existe mayormente fuera de la indexación web general (probablemente en páginas de Facebook y relaciones boca a boca/WhatsApp no accesibles a este método de investigación).

---

## 2. SaaS especializado en talleres: LatAm y jugadores globales

### 2.1 Productos latinoamericanos y españoles

Existe un mercado real pero fragmentado de software para talleres construido en Chile, Colombia, México, Argentina y España — ninguno declara cobertura de Honduras:

| Producto | Origen/cobertura declarada | Precio (USD, fecha) | Características clave |
|---|---|---|---|
| **Appli-Car** | Chile, Argentina, Uruguay, Brasil, Colombia, Ecuador, Perú, Paraguay "y varios países más" (Honduras no listado) — [Source](https://www.appli-car.com) | Básico $25/mes ($21 anual), Avanzado $32/mes ($27 anual), Pro a cotizar; add-on de facturación electrónica SII (Chile) 24,000 CLP/mes — [Source](https://www.appli-car.com) | Órdenes de trabajo móviles, cotizaciones por WhatsApp con aprobación instantánea, inventario (desde plan Avanzado), portal de cliente con "Timeline de Transparencia", dashboard financiero. No menciona pagos en línea ni historial de vehículo detallado |
| **TallerOS** | Canadá, Colombia, México, Perú (Honduras no listado); IDs fiscales soportados: CUIT, NIF, RFC, RUT — **no RTN** — [Source](https://www.softwareadvice.co.uk/software/554716/TallerOS) | Modelo Flat Rate, versión gratuita, planes desde ~19 EUR — [Source](https://www.capterra.es/directory/20006/auto-repair/pricing/free/software) | Historial de vehículo, órdenes de reparación, facturación, inventario, agenda; aprobaciones vía WhatsApp, portal de cliente, recordatorios, multiusuario |
| **Tuulapp** | Colombia; reportado en "42 países" (claim sin verificar) — [Source](https://www.portafolio.co/emprendimiento/la-apuesta-es-digitalizar-a-los-talleres-mecanicos-tuulapp-601986) | No encontrado | Gestión operativa y digitalización de talleres; startup levantando ronda de ~$250,000 USD (2024) |
| **Ingo Talleres** | Colombia (llegada reportada sept-2026) — [Source](https://noticias.autocosmos.com.co/2026/09/29/ingo-talleres-llega-a-colombia-para-digitalizar-la-gestion-de-los-talleres-mecanicos) | No encontrado | Gestión operativa y administrativa integrada |
| **ClearMechanic** | LatAm (25 países, claim), usado por redes de BMW, GM, Hyundai, Stellantis, JLR — [Source](https://portalautomotriz.com/print/noticias/servicios/ofrece-clearmechanic-reforzar-la-confianza-entre-talleres-y-sus-clientes) | No encontrado | Enfoque en inspección visual digital para generar confianza cliente-taller (no es gestión de inventario/POS) |
| **Balance Garage, Onmotor, OK CAR** | México/LatAm — [Source](https://www.comparasoftware.com/balance-garage); [Source](https://www.comparasoftware.com/onmotor); [Source](https://www.comparasoftware.com/ok-car) | No encontrado | Órdenes de trabajo, presupuestos, inventario de repuestos, facturación electrónica (Onmotor), base de clientes/vehículos |
| **SoftGestión, Taller GP, Atelio PRO, MiTallerOnline, ARI, RemOnline** | España | No encontrado | Recepción, presupuestos, órdenes de trabajo, albaranes, facturas, agenda, marketing, control de stock |

**Dato de adopción regional:** solo el **9%** de los talleres mecánicos en Colombia usa algún tipo de software de gestión, y 28-29% de quienes no lo usan citan el alto costo como barrera — [Source](https://dplnews.com/colombia-solo-9-de-talleres-mecanicos-utilizan-algun-tipo-de-software-dentro-de-operaciones/). Esto sugiere que incluso en mercados LatAm más grandes y con proveedores locales, la adopción de software de taller es baja — sería razonable esperar una adopción aún menor en Honduras, donde ni siquiera hay proveedores locales dedicados.

**Patrón notable:** las listas de identificadores fiscales soportados (CUIT, NIF, RFC, RUT) de productos como TallerOS nunca incluyen el RTN hondureño — señal de que soportar Honduras requeriría configuración manual, no un flujo nativo.

### 2.2 Jugadores globales

| Producto | Precio (USD/mes, fecha) | Mercado confirmado | Características |
|---|---|---|---|
| **Tekmetric** | Start $199 ($179 anual), Grow $349 ($309 anual), Scale $439, Enterprise a cotizar (ago-2026) — [Source](https://www.capterra.com/p/190952/Tekmetric/pricing/) | EE.UU./Canadá (sin evidencia de LatAm) | Calendarios, trabajos enlatados, autorizaciones digitales, inspección vehicular digital (DVI), inventario y gestión de proveedores |
| **Shopmonkey** | Basic $215, Clever $359, Genius $449; add-ons CRM Essentials $314.99 — [Source](https://pricingsaas.com/companies/shopmonkey) | Confirmado **solo EE.UU. y Canadá**, "más de 5,000 talleres" — [Source](https://sacra.com/c/shopmonkey) | Mensajería integrada, estimados/facturas rápidas, pagos en línea con BNPL |
| **AutoLeap** | Essentials $179-199/usuario/mes — [Source](https://ustechautomations.com/resources/blog/best-estimating-software-for-auto-repair-shops-2026) | No se encontró presencia LatAm | Usuarios y órdenes ilimitadas, DVI ilimitadas, 70+ integraciones |
| **Mitchell1 Manager SE** | Sin precio público ("todo pasa por un representante de ventas"); una reseña aislada menciona "menos de $500/mes" — [Source](https://www.g2.com/products/manager-se/pricing) | No se encontró presencia LatAm | On-premises, sin app móvil nativa |
| **GaragePlug** | Capterra: desde $200/mes "por función"; fuente secundaria (no verificada en el sitio oficial) sugiere Básico $99, Essential $199, Enterprise $999 — [Source](https://www.capterra.com/p/166660/GaragePlug/); [Source](https://test.spendbase.co/de/?p=35821) | Claim de 25+ países, 200+ marcas — [Source](https://www.capterra.com/p/166660/GaragePlug/) | Tarjetas de trabajo con firma digital, control de inventario, escaneo de código de barras/VIN, recordatorios automáticos, notificaciones SMS/email con marca propia |

**Conclusión de esta subsección:** los cuatro incumbentes de EE.UU./Canadá cobran en USD, sin opción visible de otra moneda, y ninguno muestra mensajería de mercado para LatAm o Centroamérica. GaragePlug, por su precio más bajo y huella multinacional ya declarada, es en teoría el más adaptable a un mercado emergente — pero no hay evidencia directa (positiva o negativa) de soporte a Honduras.

### 2.3 ¿Funciona alguno de estos productos realmente en Honduras?

**Ninguno de los productos investigados —LatAm o global— menciona explícitamente a Honduras, Lempiras o cumplimiento SAR/CAI.** Hallazgos concretos:

- Shopmonkey: confirmado solo EE.UU./Canadá — [Source](https://sacra.com/c/shopmonkey)
- Appli-Car: su propio sitio enumera países y Honduras no aparece; su único módulo de facturación electrónica es para Chile (SII) — [Source](https://www.appli-car.com)
- TallerOS: lista Canadá, Colombia, México, Perú — Honduras no aparece, ni el RTN entre sus IDs fiscales — [Source](https://www.softwareadvice.co.uk/software/554716/TallerOS)
- Una búsqueda combinando Tekmetric/Shopmonkey con "Honduras Lempiras facturación" no devolvió ninguna conexión vendor-Honduras — solo un artículo de La Prensa (fecha de publicación original no clara) sobre el mandato de que los documentos fiscales se expresen solo en Lempiras, sin relación con ningún software — [Source](https://www.laprensa.hn/economia/facturacion-sera-solo-en-lempiras-HXLP834298)

**Importante matiz metodológico:** esta ausencia de mención es evidencia de ausencia de mercadeo/documentación, **no prueba definitiva de que el producto rechace una cuenta de Honduras** (p. ej., un negocio hondureño podría registrarse igual pagando con tarjeta en USD, sin que eso se documente en ningún lugar). La forma más confiable de confirmar esto —probar el flujo de registro/facturación directamente— no se hizo en esta investigación y queda como siguiente paso recomendado.

---

## 3. Alternativas genéricas de bajo costo

Ante la falta de software de taller accesible, los pequeños negocios (incluyendo talleres) recurren a herramientas genéricas no diseñadas para el rubro:

### 3.1 Qué se usa

- **Plantillas de Excel/Sheets**: existen plantillas gratuitas específicamente para talleres mecánicos (inventario de repuestos/herramientas con frecuencia de mantenimiento, órdenes de trabajo con seguimiento de horas y tarifas, facturación simple) — [Source](https://getquipu.com/blog/plantillas-de-factura-taller-mecanico/); [Source](https://academiaxray.cl/blog/orden-de-trabajo-automotriz-excel/)
- **Loyverse**: suite POS freemium (Cavius International Ltd., Chipre), 25+ idiomas, 170+ países, con funcionamiento offline durante cortes de internet — [Source](https://loyverse.com/en-us/about); [Source](https://www.mobiletransaction.org/au/loyverse-pos-review/)
- **Alegra**: software de contabilidad/facturación electrónica en la nube, posicionado como "aliado tecnológico para pymes" en LatAm, soporte 24/7 — [Source](https://www.larepublica.co/especiales/facturacion-electronica-2024/alegra-el-aliado-tecnologico-para-las-pymes-3940991)
- **Zoho Inventory**: gestión de inventario/pedidos para pymes, integrado al ecosistema Zoho — [Source](https://costbench.com/software/inventory-management/zoho-inventory/free-plan/)
- **Odoo Community**: ERP open-source autoalojado, módulos ilimitados (CRM, Ventas, Inventario, Contabilidad básica) — [Source](https://octurasolutions.com/resources/how-much-does-odoo-cost-per-month-2026)
- **Catálogo de WhatsApp Business**: vitrina de productos sin sitio web — no gestiona stock real ni emite comprobantes, por lo que no compite en la misma categoría que las anteriores — [Source](https://learn.rasayel.io/en/blog/whatsapp-product-catalog)
- Apps móviles de inventario menos relevantes para la región (Vyapar — India, con marca de agua en facturas gratuitas; Sortly; inFlow) — [Source](https://www.accountune.com/free-accounting-software-for-small-business-india); [Source](https://www.inflowinventory.com/inflow-vs/sortly)

### 3.2 Límites de los planes gratuitos (verificado oct-2026)

| Herramienta | Límite del free tier |
|---|---|
| Zoho Inventory | 50 pedidos/mes, 1 usuario, 1 ubicación — "forever free" — [Source](https://costbench.com/software/inventory-management/zoho-inventory/free-plan/) |
| Loyverse | POS/Dashboard/KDS/CDS gratis con funciones básicas; Employee Management, Advanced Inventory y Unlimited Sales History son add-ons pagos ($25, $25 y $5/mes por tienda respectivamente) — [Source](https://loman.ai/blog/Loyverse-pricing) |
| Odoo Community | Gratis sin límite de módulos, pero sin Odoo Studio, sin app móvil oficial, sin soporte oficial, y requiere autoalojamiento (servidor, backups, parches propios) — [Source](https://octurasolutions.com/resources/how-much-does-odoo-cost-per-month-2026) |
| WhatsApp Business (catálogo) | Límite técnico de 500 productos; se recomienda no superar ~100 para buena UX — [Source](https://docs.360dialog.com/docs/waba-messaging/products-and-catalogs) |
| Sortly | 100 ítems de inventario; planes pagos desde $24/mes — [Source](https://www.inflowinventory.com/inflow-vs/sortly) |
| inFlow Inventory | Sin free tier permanente, solo prueba de 14 días; planes desde $129/mes — [Source](https://capterra.com/p/78431/inFlow-Inventory/pricing/) |
| Vyapar | App gratis con marca "Vyapar" visible en las facturas — [Source](https://www.accountune.com/free-accounting-software-for-small-business-india) |
| Alegra | No se encontró una cifra verificada de límite del plan gratuito/entrada — brecha abierta |

**Patrón general:** salvo Odoo Community (gratis pero técnicamente exigente), todos los free tiers están diseñados para "probar" la herramienta, no para operar un negocio real de forma sostenida — los límites se agotan rápido incluso en un taller pequeño con rotación diaria de órdenes y repuestos.

### 3.3 ¿Soportan HNL y el régimen SAR hondureño?

**Hallazgo clave verificado por fetch directo (6-oct-2026):** el selector de país del sitio oficial de Alegra (alegra.com) lista exactamente 9 países — Argentina, Colombia, Costa Rica, España, México, Panamá, Perú, República Dominicana, Venezuela — **Honduras no está incluido**, y no hay mención de Lempiras/HNL en la página — [Source](https://www.alegra.com/)

Esto es significativo porque Alegra sí tiene presencia activa y confirmada en **Costa Rica**, incluyendo cumplimiento con la versión 4.4 de facturación electrónica exigida por TRIBU-CR desde el 1 de septiembre de 2025 — [Source](https://blog.alegra.com/costa-rica/factura-electronica-costa-rica/). La inferencia razonable es que Alegra entra a países con un mandato de factura electrónica estructurada ya vigente, y Honduras todavía no lo tiene (ver régimen CAI en sección 1.3) — por lo que falta el incentivo regulatorio para que un proveedor LatAm de e-invoicing certifique ahí.

Otros hallazgos:
- No se verificó si Loyverse soporta HNL como moneda (su página de ayuda no enumera monedas específicas) — [Source](https://help.loyverse.com/help/how-set-currency)
- Un resultado de búsqueda no verificado por fetch directo sugiere que Zoho Subscriptions podría incluir HNL entre sus monedas — tratado como **no confirmado**
- No se encontró ningún módulo de localización fiscal de Odoo (`l10n_hn` o similar) para Honduras, ni resellers/distribuidores locales para ninguna de estas herramientas

**Conclusión:** ningún proveedor genérico analizado soporta de forma nativa el régimen CAI/SAR hondureño. Cualquier taller que use estas herramientas probablemente sigue emitiendo sus comprobantes fiscales por fuera (facturas pre-impresas con CAI físico, o un sistema separado), usando la herramienta genérica solo para inventario/ventas internas.

---

## 4. Qué critican los usuarios (síntesis de reseñas)

Reseñas independientes recopiladas de Capterra, G2 y Trustpilot (no se logró acceso directo a Google Play ni a Facebook/foros centroamericanos en ninguna de las tres líneas de investigación — brecha reconocida):

### 4.1 Jugadores globales de taller
- **Tekmetric**: "Ok product, too expensive" (3.0/5) — "Worked well but did the same thing as products half the price with few benefits"; otro reviewer señala complejidad y seguimiento post-onboarding débil — [Source](https://capterra.com/p/190952/Tekmetric/reviews/?page=2)
- **Shopmonkey**: falta de impresión de códigos de barra, falta de múltiples campos de precio, app móvil percibida como limitada ("lack of a robust mobile app… limits functionality for shop owners on-the-go") — [Source](https://g2.com/products/shopmonkey/reviews_and_filters?page=3)
- **AutoLeap**: a pesar de calificación alta (4.8/5, 744 reseñas), 38% de las reseñas negativas (de 52) mencionan precio: "money grab contract software", "pricing is a bit high and not fully disclosed" — [Source](https://www.capterra.com/p/216500/Autoleap/reviews/?page=8)
- **Mitchell1 Manager SE** (4.1/5, 78 reseñas): "Good But Outdated" — interfaz anticuada (comparada con una hoja de Excel), sin app móvil nativa, arquitectura on-premises, curva de aprendizaje empinada — [Source](https://capterra.com/p/145351/Manager-SE/reviews/)
- **GaragePlug** (4.8/5, 56 reseñas): mayormente positivo; quejas menores de funcionalidad ("Whatsapp from Desktop feature doesn't work properly") — [Source](https://www.capterra.com/p/166660/GaragePlug/)

### 4.2 Alternativas genéricas
- **Loyverse**: fallas de sincronización entre dispositivos/plataformas de terceros, **ausencia explícita de generación de facturas** ("lack of invoice generation"), soporte post-venta deficiente ("emails going unanswered"), y sin adaptación a regímenes fiscales locales fuera de su funcionalidad genérica (ejemplo documentado: no adaptación a VeriFactu en España) — [Source](https://www.capterra.com/p/150632/Loyverse-POS/reviews/?page=5); [Source](https://softwarefinder.com/retail/loyverse/reviews?page=2)
- **Zoho Inventory** (4.4/5, 90 reseñas en G2): fallas de sincronización con Amazon sin solución de soporte, app móvil con "could offer more offline support" — [Source](https://g2.com/products/zoho-inventory/reviews)
- **Alegra** (4.3-4.5/5): "Lacking features and support" — "the support team does not help with simple issues. Communications take ages" — [Source](https://www.capterra.co.uk/software/196363/alegra-erp)
- **Odoo** (app móvil, 2.6/5 reportado): soporte que "redirects them to their website without real assistance", POS que "repeatedly stopped working while shops were open", caso de preocupación de propiedad de datos — [Source](https://capterra.com/p/135618/Odoo/reviews/?page=5)

### 4.3 Patrón transversal y su limitación

El patrón dominante en todas las herramientas (globales y genéricas) es **precio/valor y soporte post-venta lento** — no idioma, modo offline o facturación local. Esto **no significa que esos problemas no existan para un usuario hondureño**: significa que la base de reseñadores (abrumadoramente EE.UU./Canadá/Europa/Sudamérica) simplemente no enfrenta esos problemas, así que el corpus de reseñas está estructuralmente callado justo en las dimensiones más relevantes para Honduras (UX en español, modo offline, facturación HNL/SAR). Ninguna de las tres investigaciones encontró una sola reseña que mencione Honduras, Centroamérica, "solo en inglés" o "sin modo offline" como queja explícita — esto se reporta como ausencia de evidencia, no como evidencia de que el problema no existe.

---

## 5. El vacío de mercado para un producto nuevo

Cruzando los hallazgos de las tres líneas de investigación, el espacio libre para un producto nuevo tiene este perfil:

1. **No hay competidor directo hoy.** Ningún producto —local, LatAm, global o genérico— combina las cuatro cosas que un taller/repuestera hondureña necesita: (a) gestión de inventario de repuestos, (b) órdenes de trabajo/cotizaciones, (c) facturación conforme al régimen CAI/autoimpresor del SAR, y (d) precio accesible en Lempiras con soporte en español. Esto no es una opinión — es la conclusión directa de que ningún vendor en las tres categorías investigadas declara soporte de Honduras, RTN, HNL o CAI/SAR.
2. **La barrera de entrada regulatoria en Honduras es, paradójicamente, baja ahora.** El régimen CAI/autoimpresor (pre-autorización de numeración, sin validación en tiempo real por documento) es técnicamente más simple de implementar que un sistema de clearance como el de Costa Rica o México — lo que significa que un producto nuevo no necesita construir una integración compleja con el SAR para cumplir, solo respetar el rango numérico asignado y los campos obligatorios (RTN, ISV 15%, vigencia del CAI). Esto reduce el costo de desarrollo de "cumplimiento fiscal" como feature diferenciador.
3. **El canal de venta/soporte que importa es WhatsApp, no una página de precios.** El único dato de soporte confirmado en todo el estudio (Zafra Cloud) es soporte en español vía WhatsApp — consistente con que todos los productos LatAm de taller (Appli-Car, TallerOS) usan WhatsApp como canal central de cotización/notificación, mientras que los jugadores de EE.UU. (Tekmetric, Shopmonkey) no lo mencionan en absoluto. Un producto hondureño debería construir el flujo de ventas y soporte alrededor de WhatsApp desde el diseño, no como add-on.
4. **El precio debe anclarse muy por debajo de los US$179-450/mes de los jugadores globales**, y probablemente también por debajo de los US$21-32/mes de Appli-Car (el LatAm más barato encontrado) — dado que el dato de adopción de Colombia (solo 9% de talleres usa algún software, 28-29% citando el costo como barrera) sugiere que incluso precios "LatAm-friendly" siguen siendo una barrera real para un taller pequeño. Un modelo freemium (como Loyverse, con capa gratuita funcional pero limitada) podría ser más efectivo para la adopción inicial que un trial de 14 días.
5. **El modo offline es una apuesta razonable pero no confirmada por evidencia directa de Honduras.** Loyverse ya lo ofrece como diferenciador en su capa gratuita, y es razonable asumir valor en un país con conectividad intermitente — pero ninguna investigación encontró una queja explícita de un usuario hondureño sobre falta de modo offline; esto es una hipótesis de producto, no un hallazgo confirmado.
6. **El riesgo de "falsos atajos":** Alegra, Zoho Inventory, Loyverse y Odoo seguirán siendo tentadores para un taller hondureño por ser gratuitos/baratos y fáciles de encontrar — pero las reseñas documentan que todos fallan en exactamente el punto que más le dolería a un taller: facturación local (Loyverse no genera facturas en absoluto) o soporte post-venta lento cuando algo se rompe (Alegra, Zoho, Odoo). Un producto nuevo compite no solo contra "no tener software" sino contra estas herramientas mal ajustadas que un taller probablemente ya probó o está usando a medias.

### Brechas de esta investigación que condicionan la confianza de las conclusiones anteriores

- Ninguna de las tres líneas de investigación tuvo acceso a búsqueda nativa de Facebook ni a Google Play Store — el canal que, según la propia inferencia del estudio, es donde probablemente operan los microvendedores hondureños y donde los usuarios reales de Loyverse/Zoho/Alegra en Centroamérica dejarían reseñas. Esto es la limitación metodológica más importante a resolver antes de validar el tamaño real de la oportunidad.
- No se probó directamente el flujo de registro/facturación de ningún SaaS de taller (Appli-Car, TallerOS, GaragePlug, etc.) con una dirección hondureña — la ausencia de mención de Honduras en el marketing no es prueba de rechazo técnico.
- No se encontró una lista oficial del SAR de autoimpresores/imprentas certificadas — un crawl directo de sar.gob.hn queda pendiente.
- No hay datos cuantitativos de adopción de ninguna herramienta específicamente en Honduras (solo el dato proxy de Colombia, 9% de adopción).
- Las entrevistas directas con dueños de talleres/repuesteras hondureñas (fuera del alcance de esta investigación de escritorio) serían la forma más confiable de confirmar o refutar varias de las inferencias de la sección 5.

---

## Metodología y fuentes

Esta síntesis combina tres líneas de investigación paralelas (~64 llamadas de búsqueda/fetch en total):
1. Proveedores locales hondureños/centroamericanos — ver `_research-honduras-local.md`
2. SaaS LatAm especializado en talleres + jugadores globales — ver `_research-latam-global-saas.md`
3. Alternativas genéricas de bajo costo + reseñas — ver `_research-generic-alternatives.md`

Todas las afirmaciones de marketing de proveedores se marcan explícitamente como *claim* cuando no fueron verificadas de forma independiente. Cuando no se encontró evidencia sobre un punto, se reporta como brecha (*gap*) en lugar de inferir o inventar un dato. Las fechas de precios citadas corresponden a octubre de 2026 salvo que se indique lo contrario junto a la cita.
