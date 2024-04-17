from osrsbox import monsters_api
from dash import Dash, html, dcc, callback, Output, Input
import numpy as np
import plotly.express as px
import pandas as pd
import sys

print(sys.path)

monsters = monsters_api.load()

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1(children="CDF for Item Drops", style={"textAlign": "center"}),
        dcc.Input(value="Cerberus", id="text-entry", type="text"),
        dcc.Dropdown(value="None", id="item-dropdown"),
        dcc.Graph(id="graph-content"),
    ]
)


@app.callback(Output("item-dropdown", "options"), [Input("text-entry", "value")])
def update_dropdown_options(monster):
    if monster:
        monster_found = search_monster(monster)
        if monster_found:
            items = get_drops(monster_found)
            options = [{"label": item, "value": item} for item in items]
            return options
        else:
            return [{"label": "No items found", "value": "None"}]
    else:
        return [{"label": "Enter monster name first", "value": "None"}]


def search_monster(monster_in):
    all_db_monsters = monsters_api.load()
    search_monster = next(
        (
            monster
            for monster in all_db_monsters
            if monster.name.lower() == monster_in.lower()
        ),
        None,
    )

    if search_monster:
        return search_monster.name


def get_drops(monster):
    drops = [item.name for item in monster.drops]
    return drops


# @callback(Output("graph-content", "figure"), Input("dropdown-selection", "value"))
# def update_graph(value):
#     dff = monsters[monsters. == value]
#     return px.line(dff, x="year", y="pop")


if __name__ == "__main__":
    app.run(debug=True)
