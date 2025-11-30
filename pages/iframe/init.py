from dash import register_page

from .layout import layout

register_page(__name__, path='/3d-viewer', layout=layout)

from .callbacks import *