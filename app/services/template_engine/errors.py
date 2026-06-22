"""Errores del motor de plantillas. Independientes de Flask/HTTP."""


class TemplateError(Exception):
    """Error de plantilla: sintaxis inválida, variable desconocida o acceso prohibido.

    Es un fallo de datos del usuario (no del servidor): la capa HTTP lo traduce a 422.
    """
