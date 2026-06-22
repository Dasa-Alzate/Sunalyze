"""Jerarquia de excepciones de dominio + handlers HTTP centralizados."""

import logging
from flask import jsonify
from pydantic import ValidationError as PydanticValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class DomainError(Exception):
    status_code = 400
    code = 'error.bad_request'

    def __init__(self, message, code=None, status_code=None, details=None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details

    def to_dict(self):
        body = {'error': self.message, 'code': self.code}
        if self.details:
            body['details'] = self.details
        return body


class ValidationError(DomainError):
    status_code = 422
    code = 'error.validation'


class NotFound(DomainError):
    status_code = 404
    code = 'error.not_found'


class Unauthorized(DomainError):
    status_code = 401
    code = 'error.unauthorized'


class Forbidden(DomainError):
    status_code = 403
    code = 'error.forbidden'


class Conflict(DomainError):
    status_code = 409
    code = 'error.conflict'


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic(err):
        details = [{'field': '.'.join(str(p) for p in e['loc']), 'msg': e['msg']} for e in err.errors()]
        return jsonify({'error': 'Datos invalidos', 'code': 'error.validation', 'details': details}), 422

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception('Error no controlado')
        return jsonify({'error': 'Error interno del servidor', 'code': 'error.internal'}), 500
