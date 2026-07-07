"""Interfaz de envío de correo desacoplada del proveedor.

Un `MailGateway` entrega un mensaje ya renderizado (destinatario, asunto, HTML).
Los adaptadores concretos (log, SMTP) se seleccionan por configuración sin que el
dominio los conozca, siguiendo el mismo patrón que `StorageGateway` y `JobQueue`.
"""


class MailError(Exception):
    """Fallo de entrega de un backend de correo."""


class MailGateway:
    """Contrato mínimo que cumplen todos los adaptadores de correo."""

    def send(self, to, subject, html, locale=None):
        """Entrega el mensaje y devuelve `{'sent': bool, 'reason'?: str}`.

        Lanza `MailError` si el backend no puede entregar; quien orquesta decide
        si el fallo propaga o se degrada.
        """
        raise NotImplementedError
