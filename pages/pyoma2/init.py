from dash import register_page

from .layout import layout

register_page(__name__, path='/pyoma2', layout=layout)

from .callbacks import *