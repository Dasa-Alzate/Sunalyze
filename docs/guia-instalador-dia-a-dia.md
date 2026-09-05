# El día a día del instalador con Sunalyze

> **Documento vivo.** Lo actualizamos con cada iteración del producto. Última revisión:
> julio 2026 (alta de Comunitat Valenciana y Región de Murcia en legalización).
>
> El protagonista de este documento no es la aplicación: es **Marcos**, instalador
> habilitado en baja tensión con una empresa de tres personas que hace autoconsumo
> residencial y pequeño comercial. Lo que sigue es su semana, contada desde su silla.
> Donde Sunalyze aparece, se explica qué hace por él; donde no llega, se dice claramente
> qué tiene que hacer Marcos por su cuenta y ante quién.

---

## Lunes — una visita comercial que acaba en propuesta

Un particular de Torrent (Valencia) quiere placas. Marcos abre Sunalyze en la tablet
durante la visita:

1. **Nuevo proyecto** con el nombre del cliente. Busca la dirección en el mapa y fija el
   pin en el tejado. Apunta el consumo anual que sale en la factura (kWh) y marca
   coplanar con la inclinación y azimut del tejado.
2. **Equipos**: elige el panel y deja que el análisis le proponga inversores compatibles
   de su biblioteca.
3. **Análisis**: un clic y tiene strings, paneles por string y producción anual estimada
   con datos PVGIS. Con eso y el presupuesto integrado ya puede hablar de números y
   amortización con el cliente — incluidas la deducción de IRPF y las bonificaciones
   de IBI/ICIO si su municipio las tiene.

*Lo que la app no hace:* cerrar la venta. Marcos manda la propuesta y espera.

## Martes — el cliente acepta: empieza el papeleo previo

Aquí arranca el proceso **oficial**, el que existe con o sin software:

1. **CAU y acceso a la red.** Antes de ejecutar, Marcos pide a la distribuidora de la
   zona (i-DE, e-distribución, UFD…) el **código CAU** que identificará el autoconsumo
   y, según el caso, el permiso de **acceso y conexión**. Esto se hace en el portal
   privado de cada distribuidora, con sus formularios. *Sunalyze todavía no interviene
   aquí* — el CUPS y los datos del contrato que ya guardó en el proyecto son justo los
   que le van pidiendo.
2. **Memoria técnica de diseño (MTD).** Como la instalación es ≤10 kW, no necesita
   proyecto de ingeniería: basta la MTD firmada por él como instalador habilitado
   (REBT RD 842/2002; autoconsumo según RD 244/2019). Abre el proyecto en Sunalyze,
   completa el formulario de la memoria (protecciones, ubicaciones, contrato) y genera
   el PDF: cálculos justificativos, esquemas unifilares y fichas técnicas de los equipos
   anexadas, todo en un documento. Lo firma en la app, que deja constancia con hash del
   PDF, y el proyecto pasa a «En revisión».

## Miércoles y jueves — instalación

Dos días de obra. Al terminar, Marcos emite el **certificado de instalación eléctrica
(CIE / boletín)** — hoy lo rellena en el modelo de su comunidad; el enlace al modelo
oficial lo tiene en la pantalla de legalización de Sunalyze.

## Viernes por la mañana — la sede electrónica

El momento burocrático. En la pantalla de **Legalización** del proyecto, Marcos tiene
asignada la **Comunitat Valenciana**, así que ve:

- **La guía paso a paso** de su trámite: el procedimiento de autoconsumo ≤10 kW de la
  GVA (PROP 18168), qué documentos adjuntar, y que necesitará su certificado digital.
- **El impreso oficial de MTD de la GVA (modelo 23167) ya rellenado** con los datos del
  proyecto: titular, emplazamiento, referencia catastral, potencias, número de módulos.
  Le quedan por marcar a mano las casillas técnicas finas y su número de habilitación.
  Ya no retranscribe nada.
- **El asistente de presentación**: los datos del proyecto en el mismo orden en que se
  los pedirá el formulario web de la sede, con botón de copiar campo a campo.

Entra en la sede de la GVA **con su certificado** (esto no lo puede hacer nadie por él:
ni Sunalyze ni ninguna otra herramienta — no hay API y la responsabilidad de la
declaración es suya), rellena el formulario pegando los datos, adjunta MTD, CIE y
esquema unifilar, firma y presenta.

La sede le devuelve el **justificante de registro con número de expediente**. Lo apunta
en la pantalla de legalización, marca el proyecto como «Presentado», y ese número queda
en el historial del proyecto para siempre — cuando el cliente llame dentro de un año
preguntando por su expediente, está a un clic.

> Si el proyecto fuera en **Murcia**, el viernes cambiaría poco: el trámite sería la
> declaración responsable del procedimiento 0019 de la sede de la CARM (con la tasa
> pagada con tarjeta durante la presentación), y el modelo de MTD que genera Sunalyze
> seguiría la estructura del modelo IEBT murciano.

## La semana siguiente — cierre del ciclo

- La comunidad inscribe la instalación en el **registro de autoconsumo** y la
  información llega a la distribuidora; el cliente activa con su comercializadora la
  **compensación de excedentes**. Marcos solo vigila que no se atasque.
- Cuando llegue la resolución, marca el proyecto como «Aprobado» en Sunalyze.
- La instalación pasa al módulo de **posventa**: mantenimientos, incidencias y lecturas
  de producción, con el expediente y la memoria firmada colgando del mismo proyecto.

---

## Qué cubre Sunalyze y qué sigue siendo de Marcos

| Fase | Lo hace Sunalyze | Lo hace Marcos |
|---|---|---|
| Estudio y propuesta | Dimensionado, producción PVGIS, presupuesto, finanzas con ayudas | Vender |
| CAU y acceso/conexión | Le da los datos ordenados (CUPS, potencias) | Solicitarlo en el portal de la distribuidora |
| Memoria técnica | Documento completo con cálculos, unifilares y fichas; firma con trazabilidad | Revisarla y responder por ella como redactor |
| Modelo oficial MTD | CV: impreso GVA 23167 rellenado; Murcia: modelo estructura IEBT | Casillas técnicas finas y nº de habilitación |
| CIE / boletín | Enlace al modelo oficial | Rellenarlo y firmarlo |
| Presentación en la sede | Guía del trámite + asistente de presentación (copiar campo a campo) | Presentar y firmar con su certificado digital |
| Expediente | Registro del nº de expediente y trazabilidad en el historial | Anotar el número del justificante |
| Registro de autoconsumo y compensación | — | Seguimiento con CCAA y comercializadora |
| Posventa | Instalaciones, mantenimientos, incidencias, lecturas | Ejecutarla |

## Enlaces oficiales que Marcos tiene a mano

### Comunitat Valenciana (GVA)
- Autoconsumo ≤10 kW, alta telemática por instalador habilitado (PROP 18168): <https://www.gva.es/es/inicio/procedimientos?id_proc=18168>
- Instalaciones BT con MTD (PROP 440): <https://sede.gva.es/es/detall-tramit?id_proc=440>
- Puesta en servicio simplificada ≤100 kW (PROP 2889): <https://sede.gva.es/es/detall-tramit?id_proc=2889>
- Impreso oficial MTD, modelo 23167: <https://www.gva.es/downloads/publicados/IN/23167_BI.pdf>

### Región de Murcia (CARM)
- Registro de instalaciones eléctricas de BT, procedimiento 0019: <https://sede.carm.es/web/pagina?IDCONTENIDO=19&IDTIPO=240>
- Registro de instalaciones de producción: <https://sede.carm.es/web/pagina?IDCONTENIDO=4659&IDTIPO=240>
- Portal de autoconsumo (MUI): <https://mui.carm.es/web/mui/informacion-tramitacion-instalaciones-autoconsumo>
- Modelo MTD IEBT (Word, junio 2021): <https://sede.carm.es/documentos/19/Memoria%20t%C3%A9cnica%20de%20dise%C3%B1o%20IEBT%20(Junio-2021).doc>
- Modelo CIE BT (Word): <https://sede.carm.es/documentos/1064/Certificado%20de%20instalaci%C3%B3n%20el%C3%A9ctrica%20de%20baja%20tensi%C3%B3n.docx>

### Distribuidoras (CAU y acceso/conexión)
- i-DE (Iberdrola): <https://www.i-de.es/conexion-red-electrica/autoconsumo-electrico/autoconsumidores>
- UFD (Naturgy): <https://www.ufd.es/en/new-self-consumption-connection/finaliza-tu-proceso-de-autoconsumo-acceso-y-conexion/>
- Endesa / e-distribución (guía): <https://www.endesa.com/es/luz-y-gas/autoconsumo-endesa/documentacion-autoconsumo-electrico>

### Contexto normativo y del sector
- Guía de legalización para instaladores (Gaussol, 2026): <https://gaussol.es/blog/legalizar-una-instalacion-fotovoltaica-en-espana/>
- Qué es el CAU (RD 244/2019): <https://suelosolar.com/noticias/autoconsumo-cau/espana/16-2-2020/que-es-codigo-autoconsumo-solar-fotovoltaico-cau>

## Pendientes de este documento

- [ ] Añadir más comunidades autónomas al catálogo (siguiente candidata: Andalucía, PUES/TECI).
- [ ] Cubrir el flujo de CAU/acceso y conexión desde la app cuando exista.
- [ ] Detallar el caso >10 kW (proyecto técnico en lugar de MTD) cuando el producto lo cubra.
- [ ] Verificar periódicamente que los enlaces oficiales no han cambiado (las sedes los mueven).
