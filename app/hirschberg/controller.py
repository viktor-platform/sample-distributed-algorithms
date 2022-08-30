from typing import List
from typing import Union

import numpy as np
import pandas as pd
import plotly.express as px

from viktor.core import ViktorController
from viktor.views import PlotlyResult
from viktor.views import PlotlyView

from .helper import add_initial_frames
from .helper import add_missing_frames
from .hirschberg_algorithm import run_hirschberg_sinclair_algorithm
from .parametrization import AppParametrization


def points_in_circum(n=100) -> List[Union[float, float]]:
    """Creates points in a circle to visualize the ring network.

    Args:
        n (int, optional): The number of points on the circle. Defaults to 100.

    Returns:
        List[Union[float, float]]: A list of x and y coordinates.
    """
    return [(np.cos(2 * np.pi / n * x), np.sin(2 * np.pi / n * x)) for x in range(0, n + 1)]


def get_network_figure(df: pd.DataFrame, mode: str) -> px.scatter:
    """Creates a figure of results of the algorithm.

    Args:
        df (pd.DataFrame): The states of the network.
        mode (Literal["rounds","messages"]): Rounds will plot the nodes currenlty still
        active in the round. Messages will plot the states during each message transfer.

    Raises:
        NotImplementedError: When not implemented mode is called.

    Returns:
        px.scatter: Figure to be used in PlotlyResult
    """
    nodes = df["name"].unique()

    # Assign coordinates to the nodes to visualise them
    points = points_in_circum(len(nodes))
    df["x"] = 0
    df["y"] = 0
    for idx, name in enumerate(nodes):
        df.loc[df["name"] == name, "x"] = points[idx][0]
        df.loc[df["name"] == name, "y"] = points[idx][1]
    if mode == "rounds":
        df["size"] = 1  # Dummy value to increase the scatter dots
        fig = px.scatter(
            df,
            x="x",
            y="y",
            animation_frame="round",
            animation_group="name",
            hover_name="id",
            size="size",
            size_max=25,
            text="id",
        )
    elif mode == "messages":
        df = add_missing_frames(df)
        df = add_initial_frames(df)
        df["size"] = 1
        fig = px.scatter(
            df,
            x="x",
            y="y",
            animation_frame="clock",
            color="state",
            animation_group="name",
            hover_name="id",
            size="size",
            size_max=25,
            range_x=(-1.1, 1.1),
            range_y=(-1.1, 1.1),
        )
        fig.update_layout(transition={"duration": 10})
    else:
        raise NotImplementedError("Currently implemented: messages, rounds.")

    return fig


class Controller(ViktorController):
    label = "Hirschberg and Sinclair"
    parametrization = AppParametrization

    @PlotlyView("Rounds", duration_guess=10)
    def visualize_network(self, params, **kwargs):
        """Run the Hirschberg and Sinclair algorithm and plot the remaining nodes after each round."""
        df = run_hirschberg_sinclair_algorithm(params.number_of_nodes)
        fig = get_network_figure(df, "rounds")
        return PlotlyResult(fig.to_json())

    @PlotlyView("Messages", duration_guess=10)
    def visualize_messages(self, params, **kwargs):
        """Run the Hirschberg and Sinclair algorithm and plot the states of each node during runtime."""
        df = run_hirschberg_sinclair_algorithm(params.number_of_nodes)
        fig = get_network_figure(df, "messages")
        return PlotlyResult(fig.to_json())
