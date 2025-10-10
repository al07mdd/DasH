from dash import Dash, html, dcc, Input, Output, State, callback, dash_table
from dash import dash_table
import plotly.express as px
import pandas as pd
import numpy as np

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ======= 1) Данные Spotify =======
df_spotify = pd.read_csv("data/spotify_churn_dataset.csv")

# --- Sunburst: подготовка ---
bins = [0, 30, 60, 180, 240, float("inf")]
labels = ["<30 min", "30–60 min", "1–3 h", "3–4 h", "4+ h"]
df_spotify["listening_time_bin"] = pd.cut(
    df_spotify["listening_time"], bins=bins, labels=labels, right=False
)

path_cols = ["country", "subscription_type", "gender", "listening_time_bin"]
agg = (
    df_spotify.groupby(path_cols, dropna=False, observed=True)
    .agg(
        users=("user_id", "nunique"),
        listening_time_avg=("listening_time", "mean"),
        songs_per_day_avg=("songs_played_per_day", "mean"),
        skip_rate_avg=("skip_rate", "mean"),
        ads_per_week_avg=("ads_listened_per_week", "mean"),
    )
    .reset_index()
)

# --- Фигуры (тёмная тема по умолчанию) ---
fig_sun = px.sunburst(
    agg,
    path=path_cols,
    values="users",
    color="listening_time_avg",
    color_continuous_scale="Viridis",
    hover_data={
        "users": True,
        "listening_time_avg": ":.1f",
        "songs_per_day_avg": ":.1f",
        "skip_rate_avg": ":.1%",
        "ads_per_week_avg": ":.1f",
    },
    maxdepth=-1,
    title="Spotify Sunburst: Country → Subscription → Gender → Listening Time",
)
fig_sun.update_layout(
    coloraxis_colorbar_title="listening_time_avg",
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

min_age = int(np.floor(df_spotify["age"].min() // 5 * 5))
max_age = int(np.ceil(df_spotify["age"].max() / 5) * 5)
bin_edges = list(range(min_age, max_age + 5, 5))

fig_age = px.histogram(
    data_frame=df_spotify,
    x="age",
    color="subscription_type",
    nbins=len(bin_edges) - 1,
    barmode="group",
    opacity=0.75,
    text_auto=True,
    labels={"age": "Возраст"},
    title="Распределение возраста пользователей по типу подписки",
)
fig_age.update_layout(
    xaxis_title="Возраст (годы)",
    yaxis_title="Количество пользователей",
    legend_title_text="Тип подписки",
    bargap=0.05,
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

# ======= 2) Страницы =======
def page_sunburst():
    return html.Section(
        [
            html.Article(
                [
                    html.H3("Иерархия пользователей (Sunburst)"),
                    dcc.Graph(figure=fig_sun, id="sunburst", className="plot-card", style={"height": "52vh"}),
                ]
            )
        ],
        className="container",
    )


def page_age_hist():
    return html.Section(
        [
            html.Article(
                [
                    html.H3("Возрастная структура по подпискам"),
                    dcc.Graph(figure=fig_age, id="age_hist", className="plot-card", style={"height": "48vh"}),
                ]
            )
        ],
        className="container",
    )


def page_donut():
    # поля, по которым строим пончик (можете расширить список при желании)
    donut_fields = ["gender", "country", "subscription_type", "offline_listening"]
    return html.Section(
        [
            html.Article(
                [
                    html.H3("Пончик: распределение пользователей"),
                    dcc.Dropdown(
                        id="donut_field",
                        options=[{"label": f, "value": f} for f in donut_fields],
                        value="gender",
                        clearable=False,
                        className="",  # стили берутся из assets/style.css при желании
                    ),
                    dcc.Graph(id="donut_chart", className="plot-card", style={"height": "52vh"}),
                ]
            )
        ],
        className="container",
    )


def page_age_by_device():
    # значения device_type из данных
    devices = df_spotify["device_type"].dropna().unique().tolist()
    default_device = devices[0] if devices else None
    return html.Section(
        [
            html.Article(
                [
                    html.H3("Гистограмма возраста по типу устройства"),
                    dcc.RadioItems(
                        id="device_radio",
                        options=[{"label": v, "value": v} for v in devices],
                        value=default_device,
                        inline=True,
                    ),
                    dcc.Graph(id="age_device_hist", className="plot-card", style={"height": "48vh"}),
                ]
            )
        ],
        className="container",
    )


def page_table():
    # простые фильтры
    return html.Section([
        html.Article([
            html.H3("Таблица (первые 500 строк)"),
            html.Div([
                dcc.Dropdown(
                    id="flt_gender",
                    options=[{"label": v, "value": v} for v in sorted(df_spotify["gender"].dropna().unique())],
                    placeholder="gender", clearable=True, style={"minWidth": 180, "marginRight": "8px"}
                ),
                dcc.Dropdown(
                    id="flt_sub",
                    options=[{"label": v, "value": v} for v in sorted(df_spotify["subscription_type"].dropna().unique())],
                    placeholder="subscription_type", clearable=True, style={"minWidth": 220, "marginRight": "8px"}
                ),
                dcc.Dropdown(
                    id="flt_device",
                    options=[{"label": v, "value": v} for v in sorted(df_spotify["device_type"].dropna().unique())],
                    placeholder="device_type", clearable=True, style={"minWidth": 200}
                ),
            ], style={"display": "flex", "flexWrap": "wrap", "gap": "8px", "margin": "6px 6px 14px"}),

            dash_table.DataTable(
                id="data_table",
                data=df_spotify.head(500).to_dict("records"),
                columns=[{"name": c, "id": c} for c in df_spotify.columns],
                page_size=20,
                sort_action="native",
                filter_action="none",
                style_table={"overflowX": "auto", "borderRadius": "12px"},
                style_header={
                    "fontWeight": "700",
                    "backgroundColor": "rgba(255,255,255,0.06)",
                    "border": "1px solid rgba(255,255,255,0.08)",
                    "color": "var(--text)"
                },
                style_cell={
                    "backgroundColor": "transparent",
                    "color": "var(--text)",
                    "borderBottom": "1px solid rgba(255,255,255,0.08)",
                    "padding": "8px 10px",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "fontSize": "14px",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "rgba(255,255,255,0.03)"},
                ],
            ),
        ])
    ], className="container")


def page_notes():
    return html.Section(
        [
            html.Article(
                [
                    html.H3("Выводы"),
                    dcc.Markdown(
                        """
**Черновик выводов**  
- Здесь можно кратко описать распределения по полу/странам/подпискам.  
- Укажите возрастные когорты, где выше/ниже активность.  
- Зафиксируйте инсайты по устройствам (device_type) после просмотра гистограммы.  
"""
                    ),
                ]
            )
        ],
        className="container",
    )


# ======= 3) Макет с сайдбаром и роутером =======
header = html.Header(html.Div([html.H1("Dashboard: SpotiFY")], className="header-inner"))

sidebar = html.Aside(
    [
        html.Div("My Panel", className="brand"),
        html.Nav(
            [
                dcc.Link([html.Span(className="icon"), html.Span("Sunburst", className="label")],
                         href="/sunburst", id="nav_sunburst", className="active"),
                dcc.Link([html.Span(className="icon"), html.Span("Age Histogram", className="label")],
                         href="/age", id="nav_age"),
                dcc.Link([html.Span(className="icon"), html.Span("Donut", className="label")],
                         href="/donut", id="nav_donut"),
                dcc.Link([html.Span(className="icon"), html.Span("Age by Device", className="label")],
                         href="/age-device", id="nav_age_device"),
                dcc.Link([html.Span(className="icon"), html.Span("Table", className="label")],
                         href="/table", id="nav_table"),
                dcc.Link([html.Span(className="icon"), html.Span("Notes", className="label")],
                         href="/notes", id="nav_notes"),
            ],
            className="nav",
        ),
    ],
    className="sidebar",
)

content = html.Div([dcc.Location(id="url"), html.Div(id="page_container")], className="content")

footer = html.Footer([html.P("Copyright (c) 2025 My SpotiFY Dashboard"), html.P("Ссылка на емейл???")])

app.layout = html.Div(
    [header, html.Div([html.Div(className="sidebar-overlay"), html.Div([sidebar, content], className="app-main")],
                      className="app-shell"), footer],
    id="theme_root",
    className="dark",
)

# ======= 4) Роутинг =======
@callback(
    Output("page_container", "children"),
    Output("nav_sunburst", "className"),
    Output("nav_age", "className"),
    Output("nav_donut", "className"),
    Output("nav_age_device", "className"),
    Output("nav_table", "className"),
    Output("nav_notes", "className"),
    Input("url", "pathname"),
)
def render_page(pathname):
    if pathname in ("/", "/sunburst", None):
        return page_sunburst(), "active", "", "", "", "", ""
    if pathname == "/age":
        return page_age_hist(), "", "active", "", "", "", ""
    if pathname == "/donut":
        return page_donut(), "", "", "active", "", "", ""
    if pathname == "/age-device":
        return page_age_by_device(), "", "", "", "active", "", ""
    if pathname == "/table":
        return page_table(), "", "", "", "", "active", ""
    if pathname == "/notes":
        return page_notes(), "", "", "", "", "", "active"
    return page_sunburst(), "active", "", "", "", "", ""  # fallback

# ======= 5) Колбэки для новых страниц =======

@callback(
    Output("donut_chart", "figure"),
    Input("donut_field", "value"),
)
def update_donut(field):
    vc = df_spotify[field].value_counts(dropna=False).reset_index()
    vc.columns = [field, "users"]
    fig = px.pie(vc, names=field, values="users", hole=0.5, title=f"Распределение пользователей по «{field}»")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


@callback(
    Output("age_device_hist", "figure"),
    Input("device_radio", "value"),
)
def update_age_by_device(device_value):
    df = df_spotify[df_spotify["device_type"] == device_value]
    fig = px.histogram(df, x="age", nbins=20, opacity=0.8, title=f"Возраст пользователей — {device_value}")
    fig.update_layout(
        xaxis_title="Возраст (годы)",
        yaxis_title="Количество пользователей",
        template="plotly_dark",
        bargap=0.05,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

@callback(
    Output("data_table", "data"),
    Input("flt_gender", "value"),
    Input("flt_sub", "value"),
    Input("flt_device", "value"),
)
def filter_table(g, s, d):
    df = df_spotify
    if g: df = df[df["gender"] == g]
    if s: df = df[df["subscription_type"] == s]
    if d: df = df[df["device_type"] == d]
    return df.head(500).to_dict("records")


if __name__ == "__main__":
    app.run(debug=True)
