"""Servicio de incentivos: del catálogo por capas a una lista de `Incentive`.

`applicable` resuelve las capas (nacional → CCAA → municipio) para un proyecto y devuelve la
lista de incentivos que el motor financiero ya consume (mismo schema `Incentive`:
`kind`, `amount`, `year`, `label`). Dominio puro, sin Flask ni BD.

Mapeo a `kind`:
- IRPF       → capex_reduction (deducción estatal, abarata la inversión efectiva).
- Next Gen   → capex_reduction (subvención directa).
- IBI        → cashflow repartido en N años (bonificación municipal plurianual del tributo).
- ICIO       → cashflow del año 1 (bonificación municipal del tributo único de obra).

Si no se conoce el municipio, solo aplican los incentivos nacionales (IRPF + Next Gen base).
Los importes que dependen de datos externos (cuota del IBI, base del ICIO) usan estimaciones
del catálogo; en producción los aportaría el usuario. Ver docs/subsidies-research.md.
"""

from . import catalog


class SubsidyService:

    @staticmethod
    def _irpf(rules, capex):
        cfg = rules.get('irpf')
        if not cfg or capex <= 0:
            return None
        base = min(float(capex), float(cfg.get('base_max', 0.0)))
        amount = round(base * float(cfg.get('pct', 0.0)), 2)
        if amount <= 0:
            return None
        return {'kind': 'capex_reduction', 'amount': amount, 'year': 1,
                'label': f"Deducción IRPF ({int(cfg['pct'] * 100)}%)"}

    @staticmethod
    def _next_gen(rules, system_kwp, capex):
        cfg = rules.get('next_gen')
        if not cfg or not system_kwp or system_kwp <= 0:
            return None
        gross = float(system_kwp) * float(cfg.get('eur_per_kwp', 0.0))
        cap = float(cfg.get('cap_eur', 0.0))
        amount = round(min(gross, cap) if cap > 0 else gross, 2)
        amount = round(min(amount, float(capex)), 2)
        if amount <= 0:
            return None
        return {'kind': 'capex_reduction', 'amount': amount, 'year': 1,
                'label': 'Ayuda Next Generation autoconsumo'}

    @staticmethod
    def _ibi(rules):
        cfg = rules.get('ibi')
        if not cfg:
            return []
        years = int(cfg.get('years', 0) or 0)
        annual = round(float(cfg.get('annual_quota_eur', 0.0)) * float(cfg.get('pct', 0.0)), 2)
        if years <= 0 or annual <= 0:
            return []
        return [
            {'kind': 'cashflow', 'amount': annual, 'year': y,
             'label': f"Bonificación IBI ({int(cfg['pct'] * 100)}%)"}
            for y in range(1, years + 1)
        ]

    @staticmethod
    def _icio(rules, capex):
        cfg = rules.get('icio')
        if not cfg or capex <= 0:
            return None
        base = float(capex) * float(cfg.get('base_ratio', 0.0))
        amount = round(base * float(cfg.get('pct', 0.0)), 2)
        if amount <= 0:
            return None
        return {'kind': 'cashflow', 'amount': amount, 'year': 1,
                'label': f"Bonificación ICIO ({int(cfg['pct'] * 100)}%)"}

    @classmethod
    def applicable(cls, project=None, capex=0.0, system_kwp=None, ccaa=None, municipio=None):
        if municipio is None and project is not None:
            municipio = getattr(project, 'localidad', None)
        rules = catalog.resolve(ccaa=ccaa, municipio=municipio)
        capex = float(capex or 0.0)

        incentives = []
        irpf = cls._irpf(rules, capex)
        if irpf:
            incentives.append(irpf)
        next_gen = cls._next_gen(rules, system_kwp, capex)
        if next_gen:
            incentives.append(next_gen)
        incentives.extend(cls._ibi(rules))
        icio = cls._icio(rules, capex)
        if icio:
            incentives.append(icio)
        return incentives
