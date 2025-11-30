from dash import register_page

from .layout import layout

register_page(__name__, path='/optumgx', layout=layout)

from .callbacks import *