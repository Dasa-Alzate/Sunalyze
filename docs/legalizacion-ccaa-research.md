# Investigación — Tramitación de legalización por CCAA (Comunitat Valenciana y Región de Murcia)

Investigación para la feature de legalización por CCAA: registro de expediente, guía de
tramitación, generación del modelo oficial de MTD y asistente de presentación.
Verificado contra fuentes oficiales en julio de 2026.

## 1. El marco común (España)

- La instalación de autoconsumo FV en baja tensión ≤10 kW se documenta con **Memoria
  Técnica de Diseño (MTD)** en lugar de proyecto (REBT, RD 842/2002, ITC-BT-04);
  el marco de autoconsumo es el **RD 244/2019** (deroga al RD 900/2015 en lo esencial,
  que ya estaba derogado por RDL 15/2018).
- El flujo completo: MTD → (CAU + acceso/conexión con la distribuidora) → ejecución →
  **CIE** (certificado de instalación) → comunicación de puesta en servicio ante la CCAA
  → inscripción en el registro de autoconsumo → compensación de excedentes con la
  comercializadora.
- La puesta en servicio se comunica **exclusivamente por vía telemática** en la sede de
  cada CCAA; la presenta el **instalador habilitado** (o el titular/representante) con
  **firma electrónica cualificada** (certificado FNMT, DNIe, Cl@ve Firma).
- La sede **genera un número de expediente/registro** y un justificante. **La MTD no se
  rellena online: se adjunta como documento**, en el modelo oficial cuando la CCAA lo
  define.
- **No existe API pública** en ninguna sede para presentar desde software de terceros.
  El punto máximo de automatización lícito: entregar al instalador el modelo oficial ya
  cumplimentado + los datos ordenados como los pide el formulario web + registrar el
  expediente resultante.

## 2. Comunitat Valenciana (GVA)

### Procedimientos
| Procedimiento | Qué cubre | Enlace |
|---|---|---|
| **PROP 440** | Instalaciones BT que requieren MTD: alta, modificación, baja, cambio de titularidad | <https://sede.gva.es/es/detall-tramit?id_proc=440> |
| **PROP 18168** | Generación BT para autoconsumo ≤10 kW: comunicación de alta (puesta en servicio) e inscripción de consumidores en el registro de autoconsumo. Exclusivamente telemático por instalador habilitado | <https://www.gva.es/es/inicio/procedimientos?id_proc=18168> |
| PROP 2889 | Puesta en servicio + registro de producción (procedimiento simplificado ≤100 kW en BT) | <https://sede.gva.es/es/detall-tramit?id_proc=2889> |

### Impresos oficiales
- **MTD (modelo 23167, rev. 29/09/22, bilingüe):** <https://www.gva.es/downloads/publicados/IN/23167_BI.pdf>
  — PDF **XFA estático** (`acrobat9.0static`) con AcroForm; **rellenable por software**
  (pikepdf: valores en AcroForm `/V` + paquete XFA `datasets`).
- MEMTECDI (modelo 23224, variante a titular): <https://www.gva.es/downloads/publicados/IN/23224_BI.pdf>
- Ficha del procedimiento en PDF: <https://www.gva.es/pdf/PR440_es.pdf>

### Estructura de campos del modelo 23167 (extraída del XFA template)
| Sección | Campos clave (nombre AcroForm) |
|---|---|
| A — Titular | `A_TIT_NOM`, `A_TIT_DNI`, `A_TIT_DOM`, `A_TIT_CP`, `A_TIT_LOC`, `A_TIT_PRO`, `A_TIT_CORREO`, `A_TIT_TEL`, `A_REP_NOM`, `A_REP_NIF` |
| B — Emplazamiento y generación | `B_EMPL`, `B_TEL`, `B_LOC`, `B_PROV`, `B_CP`, `B_REFCAD`, `B_P_Inversor`, `B_P_Instalada`, `B_Uso`, `B_Superficie`, `B_N_Modulos` |
| C — Características técnicas | acometida/CGP (`C1_CV*`, `C_ENT`, `C_INOM`…), circuitos (tablas `C4_F*`, `T2_F*`), puesta a tierra (`C_PRTE`, `C_RESPT` en Ω) |
| G — Clasificación | checkboxes `G_CV1..G_CV8` (1a/1b/1c/2/3a/3b/4a/4b), `G_prc` (kW) |
| H/I/J — Empresa instaladora e instalador | `H_CT1`, `I_CT1`, habilitaciones `I_CV_IBTB1`, `I_CV_IBTE1..9` |
| Fecha y firma | `FI_LLOC`, `FI_DIA`, `FI_MES`, `FI_ANY` (y `_1` para la segunda firma), `CampoFirma_Tecnico_1`, `CampoFirma_Instalador_2` |

La ruta completa de cada campo es `form1[0].PaginaN[0].seccion.x[0].<NOMBRE>[0]`.

### Autenticación y resultado
- Firma electrónica avanzada/cualificada (DNIe, FNMT, ACCV, Cl@ve Firma).
- Presenta el instalador habilitado o el titular/representante.
- Devuelve justificante de registro + **número de expediente** en la Carpeta Ciudadana.

## 3. Región de Murcia (CARM)

### Procedimientos
| Procedimiento | Qué cubre | Enlace |
|---|---|---|
| **0019 — Registro de instalaciones eléctricas de baja tensión** | Declaración responsable de inscripción; telemático; liquidación de tasa durante la presentación (pago con tarjeta) | <https://sede.carm.es/web/pagina?IDCONTENIDO=19&IDTIPO=240> |
| Registro administrativo de instalaciones de producción | Inscripción de instalaciones de producción | <https://sede.carm.es/web/pagina?IDCONTENIDO=4659&IDTIPO=240> |
| 1075 — Registro de establecimientos industriales | Declaración responsable complementaria según característica de la instalación | (guía de procedimientos de carm.es) |

- Portal informativo de autoconsumo (MUI): <https://mui.carm.es/web/mui/informacion-tramitacion-instalaciones-autoconsumo>
  y FAQ: <https://mui.carm.es/preguntas-frecuentes2> (protegidos con anti-bot; consultar en navegador).

### Impresos oficiales
- **MTD IEBT (modelo junio 2021, Word .doc):** <https://sede.carm.es/documentos/19/Memoria%20t%C3%A9cnica%20de%20dise%C3%B1o%20IEBT%20(Junio-2021).doc>
  — documento Word, **no rellenable por software** sin dependencia nueva (python-docx).
  Decisión: generar réplica HTML→PDF con WeasyPrint siguiendo su estructura y enlazar el
  original.
- **CIE (certificado de instalación, .docx):** <https://sede.carm.es/documentos/1064/Certificado%20de%20instalaci%C3%B3n%20el%C3%A9ctrica%20de%20baja%20tensi%C3%B3n.docx>
- En la declaración responsable se ratifica al **redactor de la MTD**.

### Autenticación y resultado
- Sede electrónica CARM con certificado digital; tasa liquidada en la propia presentación.
- La inscripción en el registro devuelve número de expediente/registro.

## 4. Decisiones de dominio derivadas

1. **Expediente**: campos `legalizacion_ccaa`, `expediente_numero`, `expediente_fecha`
   en el proyecto; se informan al transicionar a `presentado` (o después). El evento de
   proyecto guarda el rastro.
2. **Catálogo por CCAA** (patrón `subsidies/catalog.py`): por cada CCAA, plataforma,
   URL del trámite, impresos oficiales con URL, autenticación, tasas, umbrales y pasos.
   Solo `comunitat_valenciana` y `murcia` en esta iteración; ampliable.
3. **Modelo oficial CV**: rellenado real del PDF 23167 con pikepdf (AcroForm `/V` +
   `NeedAppearances` + sincronización del paquete XFA `datasets`). El PDF oficial se
   almacena en `data/official_forms/` (binario ~1 MB, licencia: impreso público).
   Se rellenan los campos inequívocos (A, B, tierra, fecha); lo técnico fino queda para
   el instalador.
4. **Modelo oficial Murcia**: plantilla HTML→PDF propia que replica la estructura del
   modelo IEBT de la CARM + enlace al .doc oficial en la guía.
5. **Asistente de presentación**: endpoint que devuelve los datos del proyecto en el
   orden de los apartados del formulario de la sede de cada CCAA (etiqueta → valor),
   para copiar durante la presentación manual.
6. **Trampa evitada**: nada de RPA/scraping de sedes ni firma delegada — la firma
   cualificada y la responsabilidad son del instalador.

## 5. Fuentes adicionales del ecosistema (para artículos de ayuda)

- Guía de legalización 2026 (Gaussol): <https://gaussol.es/blog/legalizar-una-instalacion-fotovoltaica-en-espana/>
- CAU (definición, RD 244/2019): <https://suelosolar.com/noticias/autoconsumo-cau/espana/16-2-2020/que-es-codigo-autoconsumo-solar-fotovoltaico-cau>
- Portales de distribuidora: i-DE/GEA <https://www.i-de.es/conexion-red-electrica/autoconsumo-electrico/autoconsumidores>,
  UFD <https://www.ufd.es/en/new-self-consumption-connection/finaliza-tu-proceso-de-autoconsumo-acceso-y-conexion/>,
  Endesa/e-distribución <https://www.endesa.com/es/luz-y-gas/autoconsumo-endesa/documentacion-autoconsumo-electrico>
- FAQ PUES/TECI Andalucía (referencia de otra CCAA, fuera de alcance de esta iteración):
  <https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/03/Preguntas_inst_electricas%20-PUES-TECI_v1.4_rev.Sev_.En_.pdf>
