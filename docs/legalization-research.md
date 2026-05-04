# Legalización de autoconsumo fotovoltaico (España) — investigación

Conocimiento de dominio para la máquina de estados de legalización de Sunalyze.

## Marco normativo

- **RD 244/2019, de 5 de abril**: regula condiciones administrativas, técnicas y
  económicas del autoconsumo de energía eléctrica. Define tres modalidades:
  - Sin excedentes.
  - Con excedentes acogido a compensación.
  - Con excedentes no acogido a compensación.
- **REBT (RD 842/2002) e ITC-BT-40**: instalaciones generadoras de baja tensión.
  La **memoria técnica de diseño (MTD)** es el documento técnico exigible para
  instalaciones de baja tensión que no requieren proyecto (potencia reducida);
  por encima de los umbrales se exige **proyecto** firmado por técnico competente.
- **CIE / Boletín (Certificado de Instalación Eléctrica)**: lo emite y firma el
  instalador autorizado tras ejecutar la obra; certifica conformidad con el REBT.

## Umbrales de potencia relevantes

- **≤ 15 kW** (o sin excedentes): exentos de permisos de acceso y conexión.
- **≤ 100 kW en baja tensión**: el contrato de acceso lo realiza de oficio la
  distribuidora; basta presentar el CIE a la comunidad autónoma para inscripción
  en el registro de autoconsumo.
- **> 100 kW**: pueden requerir trámites adicionales (impacto ambiental, etc.).
- En torno a **10 kW**: por debajo, tramitación simplificada.

## Flujo real de tramitación (orden típico, baja tensión, autoconsumo)

Fase de diseño/documentación:
1. Memoria técnica de diseño (MTD) o proyecto según potencia. Firmada por técnico.
2. (Si aplica) permiso de acceso y conexión + Código de Autoconsumo (CAU) de la
   distribuidora.

Fase de ejecución y legalización:
3. Ejecución de la instalación por instalador autorizado.
4. CIE / boletín firmado por el instalador autorizado.
5. Presentación a la distribuidora / inscripción en el registro de autoconsumo
   de la comunidad autónoma.
6. Resolución: inscripción aprobada (o requerimiento de subsanación / rechazo).
7. Contrato de compensación de excedentes y alta/modificación con comercializadora.

## Mapeo al dominio de Sunalyze

Sunalyze cubre la fase de **diseño y memoria técnica**. La feature modela el
ciclo de vida administrativo del expediente del proyecto como máquina de estados:

| Estado          | Significado                                                        |
|-----------------|--------------------------------------------------------------------|
| `borrador`      | Expediente en elaboración; datos y diseño editables.               |
| `en_revision`   | Memoria técnica completada y firmada; pendiente de revisión interna.|
| `presentado`    | Expediente presentado a la distribuidora / registro autonómico.    |
| `aprobado`      | Inscripción/legalización resuelta favorablemente.                  |
| `rechazado`     | Rechazado por revisión interna o por la administración/distribuidora.|

### Transiciones permitidas y guardas

- `borrador  -> en_revision`  — guarda: la **memoria técnica debe estar firmada**.
- `en_revision -> presentado` — guarda: memoria firmada (sigue vigente).
- `en_revision -> borrador`   — devolver a edición (sin guarda).
- `en_revision -> rechazado`  — rechazo en revisión interna.
- `presentado -> aprobado`    — resolución favorable de la administración.
- `presentado -> rechazado`   — requerimiento/denegación.
- `presentado -> en_revision` — subsanación: vuelve a revisión.
- `rechazado  -> borrador`    — reabrir para corregir.

Estados terminales de trabajo: `aprobado` (no admite salida). `rechazado` admite
reapertura a `borrador`.

### Firma de la memoria (MEMORIA_SIGN)

La firma es el hito que habilita el avance del expediente. Al firmar se registra:
- firmante (usuario),
- timestamp,
- snapshot/hash del PDF generado (integridad: SHA-256 de los bytes del PDF).

La firma se invalida si el expediente vuelve a `borrador` (el diseño puede cambiar),
exigiendo re-firma antes de volver a avanzar.

## Fuentes

- RD 244/2019 — https://selectra.es/autoconsumo/normativa ,
  https://tarifasgasluz.com/autoconsumo/normativa
- CIE / boletín — https://autosolar.es/legislacion-autoconsumo-fotovoltaico/boletin-electrico-o-certificado-de-instalacion-electrica-cie ,
  https://imaginaenergia.com/blog/certificado-instalacion-electrica-cie/
- Guía de tramitación — https://www.endesa.com/es/luz-y-gas/autoconsumo-endesa/documentacion-autoconsumo-electrico ,
  https://www.edistribucion.com/content/dam/edistribucion/conexion-a-la-red/descargables/guia-autocosumo-es11.pdf
