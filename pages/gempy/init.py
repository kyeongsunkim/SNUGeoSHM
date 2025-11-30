from dash import register_page

from .layout import layout

register_page(__name__, path='/gempy', layout=layout)

from .callbacks import *