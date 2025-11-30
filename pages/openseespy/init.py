from dash import register_page

from .layout import layout

register_page(__name__, path='/openseespy', layout=layout)

# No callbacks for stub