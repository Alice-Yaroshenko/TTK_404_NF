from flask import Blueprint

bp = Blueprint('info', __name__)

from app.info import routes
