from dash import register_page

from .layout import layout

register_page(__name__, path='/groundhog', layout=layout)

from .callbacks import *