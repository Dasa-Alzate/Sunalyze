import re

from flask import Blueprint, Response, render_template, request

from app.security import login_required
from app.services.help_service import HelpService

help_bp = Blueprint('help', __name__, url_prefix='/api/help')

_KEY = re.compile(r'^[a-z0-9_-]{1,40}$')


def _clean(value):
    value = (value or '').strip().lower()
    return value if _KEY.fullmatch(value) else ''


@help_bp.route('/tutorial')
@login_required
def tutorial():
    view = _clean(request.args.get('view'))
    subview = _clean(request.args.get('subview'))
    data = HelpService.tutorial(view, subview or None)
    html = render_template('help/tutorial.html', tutorial=data)
    return Response(html, mimetype='text/html')
