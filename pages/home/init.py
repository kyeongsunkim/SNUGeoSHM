from dash import register_page

from .layout import layout
# Import callbacks to register them
from . import callbacks
from . import wtg_callbacks

register_page(__name__, path='/', layout=layout)