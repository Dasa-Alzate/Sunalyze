"""Generacion de la memoria tecnica de diseno en el modelo oficial de cada CCAA.

Comunitat Valenciana: rellena el impreso oficial MTD 23167 de la GVA (PDF XFA
estatico) escribiendo los valores en el AcroForm y en el paquete XFA datasets.
Region de Murcia: genera un PDF propio que replica la estructura del modelo
IEBT de la CARM (el original es un Word no rellenable por software).
"""

import io
import os
import xml.etree.ElementTree as ET
from datetime import date

from app.errors import NotFound
from app.services import legalization_catalog

GVA_FORM_FILENAME = 'gva_mtd_23167.pdf'

_MESES = (
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
)


def _fmt(value):
    if value is None:
        return ''
    if isinstance(value, float):
        return f'{value:.2f}'.rstrip('0').rstrip('.')
    return str(value)


class OfficialFormService:

    @staticmethod
    def generate(project):
        entry = legalization_catalog.resolve(project.ccaa)
        if entry is None:
            raise NotFound(
                'El proyecto no tiene asignada una comunidad autonoma con modelo oficial disponible.',
                code='legalization.ccaa_unknown',
            )
        if entry['mtd_oficial'] == 'gva_pdf':
            return OfficialFormService._fill_gva(project), f'mtd-oficial-gva-{project.id}.pdf'
        return OfficialFormService._render_carm(project), f'mtd-modelo-carm-{project.id}.pdf'

    @staticmethod
    def _gva_values(project):
        today = date.today()
        provincia = legalization_catalog.provincia_hint(project.ccaa)
        inverter_kw = project.inverter.power if project.inverter else None
        values = {
            'A_TIT_NOM': project.cliente,
            'A_TIT_DOM': project.direccion,
            'A_TIT_LOC': project.localidad,
            'A_TIT_PRO': provincia,
            'B_EMPL': project.direccion,
            'B_LOC': project.localidad,
            'B_PROV': provincia,
            'B_REFCAD': project.referencia_catastral,
            'B_P_Inversor': inverter_kw,
            'B_P_Instalada': project.kwp,
            'B_N_Modulos': project.n_paneles,
            'FI_LLOC': project.localidad,
            'FI_DIA': today.day,
            'FI_MES': _MESES[today.month - 1],
            'FI_ANY': today.year,
            'FI_LLOC_1': project.localidad,
            'FI_DIA_1': today.day,
            'FI_MES_1': _MESES[today.month - 1],
            'FI_ANY_1': today.year,
        }
        return {key: _fmt(value) for key, value in values.items() if value not in (None, '')}

    @staticmethod
    def _fill_gva(project):
        import pikepdf

        values = OfficialFormService._gva_values(project)
        form_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'official_forms', GVA_FORM_FILENAME,
        )
        with pikepdf.open(form_path) as pdf:
            acroform = pdf.Root.AcroForm
            acroform.NeedAppearances = True
            OfficialFormService._fill_acroform_fields(acroform.get('/Fields', []), values, pikepdf)
            OfficialFormService._sync_xfa_datasets(acroform, values)
            output = io.BytesIO()
            pdf.save(output)
            return output.getvalue()

    @staticmethod
    def _fill_acroform_fields(fields, values, pikepdf):
        for field in fields:
            base_name = str(field.get('/T', '')).split('[')[0]
            if base_name in values and str(field.get('/FT', '')) == '/Tx':
                field.V = pikepdf.String(values[base_name])
                if '/AP' in field:
                    del field.AP
            kids = field.get('/Kids')
            if kids:
                OfficialFormService._fill_acroform_fields(kids, values, pikepdf)

    @staticmethod
    def _sync_xfa_datasets(acroform, values):
        if '/XFA' not in acroform:
            return
        xfa = acroform.XFA
        for index in range(0, len(xfa) - 1, 2):
            if str(xfa[index]) != 'datasets':
                continue
            stream = xfa[index + 1]
            try:
                root = ET.fromstring(stream.read_bytes())
            except ET.ParseError:
                return
            changed = False
            for element in root.iter():
                tag = element.tag.split('}')[-1]
                if tag in values and len(element) == 0:
                    element.text = values[tag]
                    changed = True
            if changed:
                stream.write(ET.tostring(root))
            return

    @staticmethod
    def _render_carm(project):
        from flask import current_app, render_template
        from weasyprint import HTML
        from app.services.pdf_url_fetcher import restricted_url_fetcher

        today = date.today()
        html_string = render_template(
            'mtd_carm_pdf.html',
            project=project,
            provincia=legalization_catalog.provincia_hint(project.ccaa),
            inverter=project.inverter,
            panel=project.panel,
            battery=project.battery,
            fecha=f'{today.day} de {_MESES[today.month - 1]} de {today.year}',
        )
        return HTML(
            string=html_string,
            base_url=current_app.instance_path,
            url_fetcher=restricted_url_fetcher,
        ).write_pdf()
