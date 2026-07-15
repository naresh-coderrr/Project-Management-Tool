# app.py
import dash
from layout import create_layout
from callbacks import register_callbacks

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    update_title=None
)
app.title = "Portfolio Analytics Suite"

app.layout = create_layout()
register_callbacks(app)

if __name__ == '__main__':
    print("🚀 Booting up Portfolio Analytics Engine on http://127.0.0.1:8050/ ...")
    app.run(debug=True, port=8050)