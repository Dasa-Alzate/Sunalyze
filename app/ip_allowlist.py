"""Allowlist de IP compartida para superficies administrativas.

Fuente unica de la logica de filtrado por IP que protege tanto el portal
superadmin (HTML) como la API `/api/admin/*` (JSON). Lee la configuracion
`SUPERADMIN_IP_ALLOWLIST` (IPs o redes CIDR separadas por coma o punto y coma;
vacia = sin filtro) y `SUPERADMIN_TRUST_PROXY` (confiar en el primer salto de
`X-Forwarded-For`).
"""

import ipaddress

from flask import current_app, request


def client_ip():
    if current_app.config.get('SUPERADMIN_TRUST_PROXY'):
        forwarded = request.headers.get('X-Forwarded-For', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def _allowlist():
    raw = current_app.config.get('SUPERADMIN_IP_ALLOWLIST') or ''
    networks = []
    for token in raw.replace(';', ',').split(','):
        token = token.strip()
        if not token:
            continue
        try:
            networks.append(ipaddress.ip_network(token, strict=False))
        except ValueError:
            current_app.logger.warning('SUPERADMIN_IP_ALLOWLIST: entrada inválida «%s»', token)
    return networks


def ip_allowed():
    networks = _allowlist()
    if not networks:
        return True
    try:
        addr = ipaddress.ip_address(client_ip())
    except ValueError:
        return False
    return any(addr in net for net in networks)
