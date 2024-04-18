from osrsbox import monsters_api
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

app = Dash(__name__)
all_monsters = monsters_api.load()

MAX_KILLS = 5000
RARITY_SPECS = {
    "Always": {"color": "#AFEEEE", "range": (1 / 1, 1 / 1)},
    "Common": {"color": "#56E156", "range": (1 / 2, 1 / 25)},
    "Uncommon": {"color": "#FFED4C", "range": (1 / 26, 1 / 99)},
    "Rare": {"color": "#FF863C", "range": (1 / 100, 1 / 999)},
    "Very rare": {"color": "#FF6262", "range": (1 / 1000, 0)},
}


def get_all_monsters(database):
    """Returns a list of all unique monsters and their levels for the monster choice dropdown."""
    monster_options = [
        (monster.name, monster.combat_level)
        for monster in all_monsters
        if monster.name is not None and monster.drops
    ]
    monster_options = sorted(set(monster_options))
    monster_options = [
        {"label": f"{monster[0]} (Level {monster[1]})", "value": monster[0]}
        for monster in monster_options
    ]
    return monster_options


app.layout = html.Div(
    [
        html.H1(
            children="Old School Runescape Drop Probabilities",
            style={
                "textAlign": "center",
                "color": "Burlywood",
                "fontFamily": "Helvetica",
            },
        ),
        html.H4(
            children="Select or type in an enemy below",
            style={
                "textAlign": "center",
                "backgroundColor": "#f2f2f2",
            },
        ),
        dcc.Dropdown(
            options=get_all_monsters(all_monsters),
            value=None,
            id="enemy-entry",
            multi=False,
            style={
                "textAlign": "center",
                "width": "350px",
                "margin": "auto",
            },
        ),
        html.H4(
            children="Select or type in the drop you'd like to test",
            style={
                "textAlign": "center",
                "backgroundColor": "#f2f2f2",
            },
        ),
        dcc.Dropdown(
            value=None,
            id="item-dropdown",
            multi=False,
            style={
                "textAlign": "center",
                "width": "350px",
                "margin": "auto",
            },
        ),
        html.H4(
            children="Drag the slider to select the simulated kill count",
            style={
                "textAlign": "center",
                "backgroundColor": "#f2f2f2",
            },
        ),
        dcc.Slider(
            0,
            MAX_KILLS,
            marks={i: str(i) for i in range(1, MAX_KILLS + 1) if i % 1000 == 0},
            value=500,
            id="kill-count",
            tooltip={"placement": "top", "always_visible": True},
        ),
        html.H4(
            children="What drop percentage would you like to test?",
            style={
                "textAlign": "center",
                "backgroundColor": "#f2f2f2",
            },
        ),
        dcc.Slider(
            1,
            100,
            marks={i: f"{i}%" for i in range(1, 101) if i % 10 == 0},
            value=80,
            id="drop-test",
            tooltip={"placement": "top", "always_visible": True},
        ),
        html.Div(
            id="info-div",
            children=[],
            style={
                "textAlign": "center",
                "whiteSpace": "pre-line",
                "justifyContent": "left",
            },
        ),
        dcc.Graph(
            id="graph-cdf",
        ),
    ],
    className="justify-content-center",
)


@app.callback(Output("item-dropdown", "options"), [Input("enemy-entry", "value")])
def update_monster_options(monster):
    if monster:
        monster_found = search_monster(monster)
        if monster_found:
            items = get_drops(monster_found)
            options = [{"label": item.name, "value": item.name} for item in items]
            options = sorted(options, key=lambda x: x["label"])
            return options
        else:
            return [{"label": "No items found", "value": "None"}]
    else:
        return [{"label": "Enter monster name first", "value": "None"}]


def calculate_cdf(rarity, kills):
    """Based on the binomial distribution, probability of observing success at least once in kills amount of independent Bernoulli trials"""
    cdf = 1 - (1 - rarity) ** kills
    return cdf


def get_drops(monster):
    drops = [item for item in monster.drops]
    return drops


def get_rarity(drops_in, selected_drop):
    get_drop = next(
        (drop for drop in drops_in if drop.name == selected_drop),
        None,
    )

    if get_drop:
        return get_drop.rarity


def search_monster(monster_in):
    found_monster = next(
        (monster for monster in all_monsters if monster.name == monster_in),
        None,
    )

    if found_monster:
        return found_monster


@app.callback(
    Output("graph-cdf", "figure"),
    [
        Input("enemy-entry", "value"),
        Input("item-dropdown", "value"),
        Input("kill-count", "value"),
        Input("drop-test", "value"),
    ],
)
def plot_cdf(selected_enemy, selected_drop, num_kills, drop_chance):
    if selected_enemy and selected_drop and num_kills != 0:
        find_monster = search_monster(selected_enemy)
        if find_monster:
            drops = get_drops(find_monster)

        rarity = get_rarity(drops, selected_drop)

        data = {
            "Number of Kill Attempts (n)": range(1, num_kills + 1),
            "Cumulative Probability": [
                calculate_cdf(rarity, i) for i in range(1, num_kills + 1)
            ],
        }
        df = pd.DataFrame(data)
        filt_df = df[df["Cumulative Probability"] > int(drop_chance) / 100]
        if not filt_df.empty:
            kill_threshold = filt_df.iloc[0, 0]
            cdf_output = f"{drop_chance}% chance of receiving at least one {selected_drop} from {selected_enemy} at {kill_threshold} kills!"
            hit_rate = 1
        elif int(round(df.iloc[-1, -1] * 100, 0)) != int(drop_chance):
            most_likely_probability = df.iloc[-1, -1]
            cdf_output = f"Uh-oh! You only have a {int(round(most_likely_probability*100, 0))}% chance to receive at least one {selected_drop} from {selected_enemy} at {num_kills} kills."
            hit_rate = 0

        rarity_color, _ = get_rarity_color(rarity)
        rarity_color = [rarity_color]
        fig = px.line(
            df,
            x="Number of Kill Attempts (n)",
            y="Cumulative Probability",
            title=cdf_output,
            color_discrete_sequence=rarity_color,
        )
        fig.update_layout(title_x=0.5)
        fig.update_traces(line=dict(width=4))
        x = fig.data[0]["x"]
        y = fig.data[0]["y"]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                fill="tozeroy",
                fillcolor=rarity_color[0],
                mode="none",
                showlegend=False,
            )
        )
        if hit_rate:
            fig.add_shape(
                type="line",
                x0=min(x),
                x1=max(x),
                y0=drop_chance / 100,
                y1=drop_chance / 100,
                line=dict(color="black", width=2, dash="solid"),
            )
        return fig
    else:
        return {
            "layout": {"title": "Select an enemy, item, and kill count to plot the CDF"}
        }


def get_rarity_color(rarity):
    for category, specs in RARITY_SPECS.items():
        if specs["range"][0] >= rarity >= (specs["range"][1]):
            return specs["color"], category
    return "black", "Unknown"


@app.callback(
    Output("info-div", "children"),
    [
        Input("enemy-entry", "value"),
        Input("item-dropdown", "value"),
        Input("kill-count", "value"),
    ],
)
def instance_info(selected_enemy, selected_drop, num_kills):
    if selected_enemy and selected_drop and num_kills != 0:
        find_monster = search_monster(selected_enemy)
        if find_monster:
            drops = get_drops(find_monster)

        rarity = get_rarity(drops, selected_drop)
        rarity_color, rarity_category = get_rarity_color(rarity)
        rarity = f"1/{int(1/rarity)}"
        return [
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Span("RARITY: ", style={"background-color": rarity_color}),
            html.Span(
                f"{rarity} ({rarity_category})",
                style={"background-color": rarity_color},
            ),
            html.Br(),
            "KILL COUNT: ",
            str(num_kills),
        ]
    else:
        return []


if __name__ == "__main__":
    app.run(debug=True)
