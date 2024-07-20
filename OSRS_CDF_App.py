from osrsreboxed import monsters_api
import dash
from dash import Dash, html, dcc, callback, Output, Input, no_update, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

app = Dash(__name__, assets_folder="assets", external_stylesheets=["/assets/style.css"])

all_monsters = monsters_api.load()

MAX_KILLS = 5000
PLAYER_COUNT = 5000
RARITY_SPECS = {
    "Always": {"color": "#AFEEEE", "range": (1 / 1, 1 / 1)},
    "Common": {"color": "#56E156", "range": (1 / 2, 1 / 25)},
    "Uncommon": {"color": "#FFDF00", "range": (1 / 26, 1 / 99)},
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
        html.Img(
            src=dash.get_asset_url("LOGO.png"),
            style={
                "display": "block",
                "margin": "auto",
                "width": "15%",
                "height": "auto",
            },
        ),
        html.H1(
            children="Old School Runescape Drop Probabilities",
            style={
                "textAlign": "center",
                "color": "Burlywood",
                "fontFamily": "Helvetica",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H4(
                            children="Select or type in an ENEMY below:",
                            style={
                                "textAlign": "center",
                                "fontFamily": "Helvetica",
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
                    ],
                    style={"flex": "1", "margin-right": "10px"},
                ),
                html.Div(
                    [
                        html.P(
                            id="info-div",
                            children=[],
                            style={
                                "textAlign": "center",
                                "fontFamily": "Helvetica",
                                "margin": "auto",
                            },
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.H4(
                            children="Select or type in the DROP you'd like to test:",
                            style={
                                "textAlign": "center",
                                "fontFamily": "Helvetica",
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
                    ],
                    style={"flex": "1", "margin-left": "10px"},
                ),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H4(
                            children="Drag the slider to select the simulated kill count",
                            style={
                                "textAlign": "center",
                                "fontFamily": "Helvetica",
                            },
                        ),
                        dcc.Slider(
                            min=1,
                            max=MAX_KILLS,
                            marks={
                                i: str(i)
                                for i in range(1, MAX_KILLS + 1)
                                if i % 500 == 0 or i == 1
                            },
                            value=500,
                            id="kill-count",
                            tooltip={"placement": "top", "always_visible": True},
                        ),
                    ],
                    style={"display": "inline-block", "width": "50%"},
                ),
                html.Div(
                    [
                        html.H4(
                            children="What drop percentage would you like to test?",
                            style={
                                "textAlign": "center",
                                "fontFamily": "Helvetica",
                            },
                        ),
                        dcc.Slider(
                            1,
                            99,
                            marks={
                                i: f"{i}%"
                                for i in range(1, 100)
                                if i % 10 == 0 or i == 1 or i == 99
                            },
                            value=80,
                            id="drop-test",
                            tooltip={"placement": "top", "always_visible": True},
                        ),
                    ],
                    style={"display": "inline-block", "width": "50%"},
                ),
            ]
        ),
        html.Div(
            [
                dcc.Graph(
                    id="graph-cdf",
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "textAlign": "center",
                    },
                ),
                dcc.Store(id="stored-graph-hist"),
                dcc.Graph(
                    id="graph-hist",
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "textAlign": "center",
                    },
                ),
            ],
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
        return [{"label": "Enter monster name first!", "value": "None"}]


def calculate_cdf(rarity, kills):
    """Based on the binomial distribution, probability of observing success at least once in 'kills' amount of independent Bernoulli trials."""
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


def get_rarity_color(rarity):
    for category, specs in RARITY_SPECS.items():
        if rarity >= specs["range"][1]:
            return specs["color"], category
    return "gray", "Unknown"


def search_monster(monster_in):
    found_monster = next(
        (monster for monster in all_monsters if monster.name == monster_in),
        None,
    )

    if found_monster:
        return found_monster


def run_simulation(rarity, num_kills, simulation_amount):
    output = []
    for _ in range(simulation_amount):
        sim_gen = np.random.default_rng()
        kills_to_drop = sim_gen.geometric(rarity, size=num_kills)
        if 1 not in kills_to_drop:
            output.append(None)
        else:
            drop_index = list(kills_to_drop).index(1) + 1
            output.append(drop_index)
    output = pd.DataFrame(output, columns=["Kills to Drop"])
    return output


@app.callback(
    Output("graph-cdf", "figure"),
    [
        Input("enemy-entry", "value"),
        Input("item-dropdown", "value"),
        Input("kill-count", "value"),
        Input("drop-test", "value"),
    ],
)
def plot_cdf(selected_enemy, selected_drop, num_kills, chance_input):
    if selected_enemy and selected_drop:
        find_monster = search_monster(selected_enemy)
        if find_monster:
            drops = get_drops(find_monster)

        rarity = get_rarity(drops, selected_drop)

        data = {
            "Number of Kill Attempts": range(1, num_kills + 1),
            "Cumulative Probability": [
                calculate_cdf(rarity, i) for i in range(1, num_kills + 1)
            ],
        }
        df = pd.DataFrame(data)
        filt_df = df[df["Cumulative Probability"] > int(chance_input) / 100]
        if int(rarity) == 1:
            cdf_output = f"You always get {selected_drop} from {selected_enemy}!"
            hit_rate = 1
        elif not filt_df.empty:
            kill_threshold = filt_df.iloc[0, 0]
            cdf_output = f"{chance_input}% chance of receiving at least one <br><i>{selected_drop}</i> from <i>{selected_enemy}</i><br>at {kill_threshold} kills!"
            hit_rate = 1
        elif int(round(df.iloc[-1, -1] * 100, 0)) != int(chance_input):
            most_likely_probability = df.iloc[-1, -1]
            cdf_output = f"Uh-oh! You don't have {chance_input}%, you have {int(round(most_likely_probability*100, 0))}% chance<br> to receive at least one <i>{selected_drop}</i> from<br><i>{selected_enemy}</i> at {num_kills} kills."
            hit_rate = 0

        rarity_color, _ = get_rarity_color(rarity)
        rarity_color = [rarity_color]
        fig = px.line(
            df,
            x="Number of Kill Attempts",
            y="Cumulative Probability",
            title=cdf_output,
            color_discrete_sequence=rarity_color,
        )
        fig.update_layout(title_x=0.5, plot_bgcolor="white")
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
            text_position = "bottom right" if chance_input >= 10 else "top right"
            fig.add_hline(
                y=chance_input / 100,
                annotation_text=f"{round(chance_input,1)}% chance",
                annotation_position=text_position,
            )
        fig.update_yaxes(range=[0, 1])
        return fig
    else:
        return {
            "layout": {
                "title": "Select an enemy, item,<br>and kill count to plot the CDF"
            }
        }


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
            html.Span(
                "Rarity: ",
                style={
                    "color": rarity_color,
                    "fontSize": "20px",
                    "fontFamily": "Helvetica",
                    "fontWeight": "bold",
                },
            ),
            html.Span(
                f"{rarity}({rarity_category})",
                style={
                    "color": rarity_color,
                    "fontSize": "20px",
                    "fontFamily": "Helvetica",
                    "fontWeight": "bold",
                },
            ),
        ]
    else:
        return []


@app.callback(
    Output("graph-hist", "figure"),
    [
        Input("enemy-entry", "value"),
        Input("item-dropdown", "value"),
        Input("kill-count", "value"),
        Input("drop-test", "value"),
    ],
)
def plot_hist(selected_enemy, selected_drop, num_kills, chance_input):
    if selected_enemy and selected_drop and num_kills != 0:
        find_monster = search_monster(selected_enemy)
        if find_monster:
            drops = get_drops(find_monster)
            rarity = get_rarity(drops, selected_drop)
            rarity_color, _ = get_rarity_color(rarity)
            simulation_results = run_simulation(rarity, num_kills, PLAYER_COUNT)
            no_drop = simulation_results["Kills to Drop"].isna().sum()
            got_drop = (1 - (no_drop / len(simulation_results))) * 100
            hist_title = f"If {PLAYER_COUNT} players killed<br><i>{selected_enemy}</i> for a <i>{selected_drop}</i> {num_kills} times<br>~{int(round(got_drop,0))}% of players would receive at least one!"
            if int(rarity) == 1:
                hist_title = f"You always get {selected_drop} from {selected_enemy}!"
            fig = px.histogram(
                simulation_results,
                x="Kills to Drop",
                nbins=35,
                title=hist_title,
            )
            fig.update_yaxes(title_text="Drops Obtained")
            fig.update_layout(title_x=0.5, plot_bgcolor="white")
            fig.update_traces(marker_color=rarity_color)
            return fig
    else:
        return {
            "layout": {
                "title": "Select an enemy, item,<br>and kill count to plot the histogram"
            }
        }
    return


if __name__ == "__main__":
    app.run(debug=True)
