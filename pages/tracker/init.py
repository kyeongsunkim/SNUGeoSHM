from dash import register_page

from .layout import layout

register_page(__name__, path='/tracker', layout=layout)

# No callbacks for stub