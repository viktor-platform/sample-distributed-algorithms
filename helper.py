import pandas as pd

from hirschberg_algorithm import State


def add_initial_frames(df: pd.DataFrame) -> pd.DataFrame:
    """The initial overall state does not contain all possible states. Plotly will therefor ignore the
    states when a figure is made. This function will add dummy nodes with all the possible states in
    the initial frame.

    Args:
        df (pd.DataFrame): The results of the algorithm.

    Returns:
        pd.DataFrame: Results of the algorithm with dummy initial states.
    """
    columns = df.columns
    initial_frames = pd.DataFrame(columns=columns)
    for state in State:
        data = {"name": -state.value - 1, "id": 0, "round": 0, "clock": 0, "state": state.name, "x": 2, "y": 0}
        initial_frames = initial_frames.append(data, ignore_index=True)
    new_df = initial_frames.append(df, ignore_index=True)
    return new_df


def add_missing_frames(df: pd.DataFrame) -> pd.DataFrame:
    """Adds the states of each node to each frame.

    Args:
        df (pd.DataFrame): Results of the algorithm with single node per timestamp.

    Returns:
        pd.DataFrame: Results of the algorithm with all the nodes per timestamp.
    """
    frames = df["clock"].to_numpy()  # The timeline for the animation
    names = df["name"].unique()

    df = df.reset_index(drop=True)
    initial_states = df.loc[0 : len(names) - 1]
    new_df = pd.DataFrame(columns=df.columns)
    for (_, row), frame in zip(df.iterrows(), frames):
        if frame > 0:
            initial_states["clock"] = frame
            initial_states.loc[(df.name == row["name"]), "state"] = row.at["state"]
            new_df = pd.concat([new_df, initial_states])
        else:
            new_df = new_df.append(row, ignore_index=True)

    new_df.sort_values(by=["clock", "name"])
    new_df = new_df.reset_index(drop=True)

    return new_df
