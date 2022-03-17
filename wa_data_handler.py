import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

pd.options.mode.chained_assignment = None
pd.options.plotting.backend = "plotly"


def load_dict_flatten_into_df(data, json_root):
    """Loads dict and flattens the elements
    json_root : the root that the archives are in, ex: "attacks" or "revives"

    Returns dataframe
    """
    df = pd.DataFrame.from_dict(data)

    # list1 = []
    # for x in df[json_root]:
    #     list1.append(pd.DataFrame(pd.json_normalize(x)))
    # flattened_df = pd.concat(list1, ignore_index=True)

    # Same thing as above, but using list comprehension for a one liner
    flattened_df = pd.concat(
        [pd.DataFrame(pd.json_normalize(x)) for x in df[json_root]], ignore_index=True
    )

    return flattened_df


def load_json_flatten_into_df(filename, json_root):
    """Loads JSON buffer or file and flattens the elements
    json_root : the root that the archives are in, ex: "attacks" or "revives"

    Returns dataframe
    """
    df = pd.read_json(filename)
    flattened_df = pd.concat(
        [pd.DataFrame(pd.json_normalize(x)) for x in df[json_root]], ignore_index=True
    )

    return flattened_df


def prepare_attack_dataframe(df, war_data):
    df.drop(columns=["raid", "code"], inplace=True)
    df = df.replace(r"^\s*$", np.NaN, regex=True)
    df["timestamp_ended"] = pd.to_datetime(df["timestamp_ended"], unit="s")
    df["timestamp_started"] = pd.to_datetime(df["timestamp_started"], unit="s")
    df["attacker_factionname"].replace("N/A", "STEALTHED", inplace=True)
    df["attacker_name"].replace("N/A", "STEALTHED", inplace=True)
    df["attacker_id"].fillna(0, inplace=True)
    df["attacker_faction"].fillna(0, inplace=True)
    df["defender_faction"].fillna(0, inplace=True)
    df["defender_factionname"].fillna("No Faction", inplace=True)
    df.loc[:, ["attacker_id"]] = df["attacker_id"].astype("int64")
    df.loc[:, ["defender_id"]] = df["defender_id"].astype("int64")
    df.loc[:, ["attacker_faction"]] = df["attacker_faction"].astype("int64")
    df.loc[:, ["defender_faction"]] = df["defender_faction"].astype("int64")
    df.loc[:, ["attacker_factionname"]] = df["attacker_factionname"].astype("string")
    df.loc[:, ["attacker_name"]] = df["attacker_name"].astype("string")
    df.loc[:, ["defender_factionname"]] = df["defender_factionname"].astype("string")
    df.loc[:, ["defender_name"]] = df["defender_name"].astype("string")
    df.loc[:, ["result"]] = df["result"].astype("string")
    df = df.sort_values(by="timestamp_ended")
    df = df.rename(
        columns={
            "attacker_name": "Attacker",
            "defender_name": "Defender",
            "attacker_factionname": "Attacker Faction",
            "defender_factionname": "Defender Faction",
            "attacker_faction": "Attacker Faction ID",
            "defender_faction": "Defender Faction ID",
            "timestamp_ended": "Time",
            "timestamp_started": "Time Started",
        }
    )

    # Determine if a stealth attack was from a warring faction
    factions = list(war_data["factions"].keys())
    faction1_id = factions[0]
    faction2_id = factions[1]
    faction1 = war_data["factions"][faction1_id]["name"]
    faction2 = war_data["factions"][faction2_id]["name"]
    df.loc[
        df["Attacker"].eq("STEALTHED")
        & (df["ranked_war"] > 0)
        & df["Defender Faction"].eq(faction1),
        "Attacker Faction ID",
    ] = faction2_id
    df.loc[
        df["Attacker"].eq("STEALTHED")
        & (df["ranked_war"] > 0)
        & df["Defender Faction"].eq(faction2),
        "Attacker Faction ID",
    ] = faction1_id
    df.loc[
        df["Attacker"].eq("STEALTHED")
        & (df["ranked_war"] > 0)
        & df["Defender Faction"].eq(faction1),
        "Attacker Faction",
    ] = faction2
    df.loc[
        df["Attacker"].eq("STEALTHED")
        & (df["ranked_war"] > 0)
        & df["Defender Faction"].eq(faction2),
        "Attacker Faction",
    ] = faction1

    df = df.reset_index(drop=True)

    return df


def prepare_revive_dataframe(df):
    df.drop(
        columns=["target_last_action.status", "target_last_action.timestamp"],
        inplace=True,
    )
    df = df.replace(r"^\s*$", np.NaN, regex=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df.rename(
        columns={
            "target_name": "Target",
            "reviver_name": "Reviver",
            "target_factionname": "Target Faction",
            "reviver_factionname": "Reviver Faction",
            "target_faction": "Target Faction ID",
            "reviver_faction": "Reviver Faction ID",
            "timestamp": "Time",
        }
    )
    df = df.sort_values(by="Time")

    return df


def create_respect_gainloss_graph(df, war_data, return_df=False):
    """Create bar graph with the respect gained and lost for each faction"""
    temp_df = df

    factions = list(war_data["factions"].keys())
    faction1_id = factions[0]
    faction2_id = factions[1]
    faction1 = war_data["factions"][faction1_id]["name"]
    faction2 = war_data["factions"][faction2_id]["name"]

    respect_gain = (
        temp_df.groupby(["Attacker Faction"])["respect_gain"].sum().reset_index()
    )
    respect_loss = (
        temp_df.groupby(["Defender Faction"])["respect_loss"].sum().reset_index()
    )

    respect_gain = respect_gain.rename(columns={"Attacker Faction": "Faction"})
    respect_loss = respect_loss.rename(columns={"Defender Faction": "Faction"})

    respect_gain = respect_gain.loc[
        respect_gain["Faction"].eq(faction1) | respect_gain["Faction"].eq(faction2)
    ]
    respect_loss = respect_loss.loc[
        respect_loss["Faction"].eq(faction1) | respect_loss["Faction"].eq(faction2)
    ]

    rg_count = respect_gain["Faction"].value_counts()
    rl_count = respect_loss["Faction"].value_counts()

    respect = None

    # Determine which list is longer to make so no players are dropped during the merge
    if rl_count.shape[0] >= rg_count.shape[0]:
        respect = respect_gain.merge(respect_loss, how="right")
    else:
        respect = respect_gain.merge(respect_loss, how="left")

    respect = respect.fillna(0)

    respect = respect.set_index("Faction")
    respect.at[faction1, "respect_gain"] = (
        respect.at[faction1, "respect_gain"]
        + war_data["factions"][faction1_id]["rewards"]["respect"]
    )
    respect.at[faction2, "respect_gain"] = (
        respect.at[faction2, "respect_gain"]
        + war_data["factions"][faction2_id]["rewards"]["respect"]
    )
    respect = respect.reset_index()

    if return_df:
        return respect

    fig = go.Figure(
        data=[
            go.Bar(
                x=respect["Faction"], y=respect["respect_gain"], name="Respect Gain"
            ),
            go.Bar(
                x=respect["Faction"], y=respect["respect_loss"], name="Respect Loss"
            ),
        ],
        layout=go.Layout(
            title="Respect Gain and Loss by Faction",
            height=800,
            width=800,
            barmode="group",
            xaxis={"title": "Faction"},
            yaxis={"title": "Respect"},
        ),
    )

    fig.add_annotation(
        text="Includes bonus respect awarded at the end of the war",
        xref="paper",
        yref="paper",
        x=0.5,
        y=1,
        showarrow=False,
    )

    return fig


def create_war_attacks_graph(df, war_data):
    """Create line graph with cumulative war attacks over time by faction"""
    temp_df = df

    factions = list(war_data["factions"].keys())
    faction1_id = factions[0]
    faction2_id = factions[1]
    faction1 = war_data["factions"][faction1_id]["name"]
    faction2 = war_data["factions"][faction2_id]["name"]

    temp_df = temp_df.loc[
        (
            temp_df["Attacker Faction"].eq(faction1)
            & temp_df["Defender Faction"].eq(faction2)
        )
        | (
            temp_df["Attacker Faction"].eq(faction2)
            & temp_df["Defender Faction"].eq(faction1)
        )
    ]
    temp_df["Cumulative Faction Attacks"] = temp_df.groupby(
        "Attacker Faction"
    ).cumcount()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            name=faction2,
            x=temp_df["Time"].loc[temp_df["Attacker Faction"].eq(faction2)],
            y=temp_df["Cumulative Faction Attacks"].loc[
                temp_df["Attacker Faction"].eq(faction2)
            ],
        )
    )

    fig.add_trace(
        go.Scatter(
            name=faction1,
            x=temp_df["Time"].loc[temp_df["Attacker Faction"].eq(faction1)],
            y=temp_df["Cumulative Faction Attacks"].loc[
                temp_df["Attacker Faction"].eq(faction1)
            ],
        )
    )

    fig.update_layout(
        title="War Attacks over Time by Faction",
        height=800,
        width=800,
        xaxis={"title": "Time"},
        yaxis={"title": "Attacks"},
    )

    fig.add_annotation(
        text="Only includes attacks made on the opposing faction",
        xref="paper",
        yref="paper",
        x=0.5,
        y=1,
        showarrow=False,
    )
    return fig


def create_assists_graph(df, war_data, return_df=False):
    """Create line graph with cumulative assists by the warring factions
    Returns plotly figure"""
    temp_df = df

    factions = list(war_data["factions"].keys())
    faction1_id = factions[0]
    faction2_id = factions[1]
    faction1 = war_data["factions"][faction1_id]["name"]
    faction2 = war_data["factions"][faction2_id]["name"]

    s = temp_df["Attacker Faction"]
    s = s.where(
        ((s == faction1) | (s == faction2)),
        "Other",
    )
    temp_df["Attacker Faction"] = s
    temp_df = temp_df.loc[
        temp_df["result"].eq("Assist") & temp_df["Attacker Faction"].ne("Other")
    ]
    temp_df["Cumulative Faction Assists"] = temp_df.groupby(
        "Attacker Faction"
    ).cumcount()
    fig = px.line(
        temp_df,
        x="Time",
        y="Cumulative Faction Assists",
        color="Attacker Faction",
        title="Assists over Time by Faction",
        height=800,
        width=800,
    )
    return fig


def create_net_score_graph(df, basic_faction_info):
    """Create bar graph showing net score of the players in the faction"""
    temp_df = df
    temp_df = temp_df.loc[
        (temp_df["ranked_war"] > 0)
        & (temp_df["respect_gain"] > 0)
        & (temp_df["chain"].ne(10))
        & (temp_df["chain"].ne(25))
        & (temp_df["chain"].ne(50))
        & (temp_df["chain"].ne(100))
        & (temp_df["chain"].ne(250))
        & (temp_df["chain"].ne(500))
        & (temp_df["chain"].ne(1000))
        & (temp_df["chain"].ne(2500))
        & (temp_df["chain"].ne(5000))
        & (temp_df["chain"].ne(10000))
        & (temp_df["chain"].ne(25000))
        & (temp_df["chain"].ne(50000))
    ]

    score_gained = (
        temp_df.groupby(["Attacker", "Attacker Faction"])["respect_gain"]
        .sum()
        .reset_index()
    )
    score_ceded = (
        temp_df.groupby(["Defender", "Defender Faction"])["respect_gain"]
        .sum()
        .reset_index()
    )
    score_gained = score_gained.rename(
        columns={
            "Attacker": "Player",
            "Attacker Faction": "Faction",
            "respect_gain": "Score Gained",
        }
    )
    score_ceded = score_ceded.rename(
        columns={
            "Defender": "Player",
            "Defender Faction": "Faction",
            "respect_gain": "Score Ceded",
        }
    )

    sg_count = (
        score_gained["Player"]
        .loc[score_gained["Faction"].eq(basic_faction_info["name"])]
        .value_counts()
    )
    sc_count = (
        score_ceded["Player"]
        .loc[score_ceded["Faction"].eq(basic_faction_info["name"])]
        .value_counts()
    )
    score_net = None

    # Determine which list is longer to make so no players are dropped during the merge
    if sc_count.shape[0] >= sg_count.shape[0]:
        score_net = score_gained.merge(score_ceded, how="right")
    else:
        score_net = score_gained.merge(score_ceded, how="left")

    score_net = score_net.fillna(0)
    score_net["Net Score"] = score_net["Score Gained"] - score_net["Score Ceded"]
    score_net.loc[:, ["Net Score"]] = score_net["Net Score"].astype("int64")
    score_net = score_net.loc[score_net["Faction"].eq(basic_faction_info["name"])]
    score_net = score_net.sort_values(by="Net Score")

    fig = go.Figure(
        data=[
            go.Bar(
                x=score_net["Net Score"],
                y=score_net["Player"],
                # text=score_net["Player"],
                # textposition="auto",
                orientation="h",
            )
        ],
        layout=go.Layout(
            title="Net Score per Player",
            height=1250,
            width=800,
            yaxis={
                "autorange": True,
                "automargin": True,
                "dtick": 1,
                "title": "Player",
            },
            xaxis={"title": "Net Score"},
        ),
    )

    return fig


def attacks_and_losses_player_graph(df, basic_faction_info):
    """Create bar graph with attacks and losses per player, grouped bars"""
    temp_df = df
    attacks_made = (
        temp_df.loc[:, ["Attacker", "Attacker Faction"]].value_counts().reset_index()
    )
    attacks_received = (
        temp_df.loc[:, ["Defender", "Defender Faction"]].value_counts().reset_index()
    )

    attacks_made = attacks_made.rename(
        columns={
            "Attacker": "Player",
            "Attacker Faction": "Faction",
            0: "Made",
        }
    )
    attacks_received = attacks_received.rename(
        columns={
            "Defender": "Player",
            "Defender Faction": "Faction",
            0: "Received",
        }
    )

    ar_count = (
        attacks_received["Player"]
        .loc[attacks_received["Faction"].eq(basic_faction_info["name"])]
        .value_counts()
    )
    am_count = (
        attacks_made["Player"]
        .loc[attacks_received["Faction"].eq(basic_faction_info["name"])]
        .value_counts()
    )
    attack_df = None
    # Determine which list is longer to make so no players are dropped during the merge
    if ar_count.shape[0] >= am_count.shape[0]:
        attack_df = attacks_made.merge(attacks_received, how="right")
    else:
        attack_df = attacks_made.merge(attacks_received, how="left")

    attack_df = attack_df.loc[attack_df["Faction"].eq(basic_faction_info["name"])]
    attack_df = attack_df.fillna(0)
    attack_df = attack_df.sort_values(by="Made")

    # Works, but no dtick control
    # fig = px.bar(attack_df,y='Player', x=['Made','Received'], title='Attacks Made and Received per Player', height=1500, width=800, barmode="overlay", opacity=.65)

    fig = go.Figure(
        data=[
            go.Bar(
                name="Attacks Made",
                x=attack_df["Made"],
                y=attack_df["Player"],
                # text=score_net["Player"],
                # textposition="auto",
                orientation="h",
                opacity=0.65,
            ),
            go.Bar(
                name="Attacks Received",
                x=attack_df["Received"],
                y=attack_df["Player"],
                # text=score_net["Player"],
                # textposition="auto",
                orientation="h",
                opacity=0.65,
            ),
        ],
        layout=go.Layout(
            title="Attacks Made and Received per Player",
            height=1500,
            width=800,
            yaxis={
                "autorange": True,
                "automargin": True,
                "dtick": 1,
                "title": "Players",
            },
            xaxis={"title": "Attacks"},
            barmode="overlay",
        ),
    )

    return fig


def create_faction_revives_graph(revive_df, basic_faction_info, return_df=False):
    """Revives over time, line graph"""
    temp_df = revive_df
    temp_df = temp_df.loc[temp_df["Target Faction"].eq(basic_faction_info["name"])]
    temp_df["Cumulative Revives"] = temp_df.groupby("Target Faction").cumcount()
    fig = px.line(
        temp_df,
        x="Time",
        y="Cumulative Revives",
        color="Target Faction",
        title="Revives Received over Time",
        height=800,
        width=800,
    )
    return fig


def create_player_revives_over_time_graph(revive_df, basic_faction_info):
    temp_df = revive_df
    temp_df = temp_df.loc[temp_df["Target Faction"].eq(basic_faction_info["name"])]
    temp_df["Cumulative Revives"] = temp_df.groupby("Target").cumcount()
    fig = px.scatter(
        temp_df,
        x="Time",
        y="Cumulative Revives",
        color="Target",
        title="Revives Received over Time by Player",
        height=800,
        width=800,
    )
    return fig


def create_player_revives_graph(revive_df, basic_faction_info):
    """Revives per player, stacked bar graph showing success and fails"""
    temp_df = revive_df
    temp_df = temp_df.loc[temp_df["Target Faction"].eq(basic_faction_info["name"])]
    results = temp_df.loc[:, ["Target", "result"]].value_counts().reset_index()
    success = results.loc[results["result"].eq("success")]
    failure = results.loc[results["result"].eq("failure")]

    success = success.rename(columns={0: "Success"})
    failure = failure.rename(columns={0: "Failure"})

    success = success.drop("result", axis=1)
    failure = failure.drop("result", axis=1)

    s_count = success["Target"].value_counts()
    f_count = failure["Target"].value_counts()
    final = None
    # Determine which list is longer to make so no players are dropped during the merge
    if f_count.shape[0] >= s_count.shape[0]:
        final = success.merge(failure, how="right")
    else:
        final = success.merge(failure, how="left")
    final = final.fillna(0)
    final = final.sort_values(by="Success")

    fig = px.bar(
        final,
        y="Target",
        x=["Success", "Failure"],
        title="Revives Received by Player",
        height=1250,
        width=800,
        orientation="h",
        barmode="relative",
        labels={"value": "Total Revives Received"},
    )
    return fig


def create_faction_summary_table(attack_df, revive_df, war_data, basic_faction_info):
    """Create a dataframe that contains summary information for each faction in the war"""
    factions = list(war_data["factions"].keys())
    faction1_id = factions[0]
    faction2_id = factions[1]
    faction1 = war_data["factions"][faction1_id]["name"]
    faction2 = war_data["factions"][faction2_id]["name"]

    temp_df = attack_df.loc[
        attack_df["Attacker Faction"].eq(faction1)
        | attack_df["Attacker Faction"].eq(faction2)
    ]

    summary_df = pd.DataFrame()
    summary_df["Faction"] = [faction1, faction2]
    summary_df = summary_df.set_index("Faction")

    respect_df = create_respect_gainloss_graph(attack_df, war_data, return_df=True)
    respect_df["Respect Net"] = respect_df["respect_gain"] - respect_df["respect_loss"]
    respect_df.rename(
        columns={"respect_gain": "Respect Gain", "respect_loss": "Respect Loss"},
        inplace=True,
    )
    respect_df = respect_df.set_index("Faction")
    respect_df.drop(columns={'Respect Gain', 'Respect Loss'}, inplace=True)

    summary_df = summary_df.merge(respect_df, on="Faction")

    war_attacks = attack_df.loc[
        (
            attack_df["Attacker Faction"].eq(faction1)
            | attack_df["Attacker Faction"].eq(faction2)
        )
        & attack_df["ranked_war"].eq(1)
    ]
    war_attacks = war_attacks["Attacker Faction"].value_counts().reset_index()
    war_attacks = war_attacks.rename(
        columns={"index": "Faction", "Attacker Faction": "War Hits"}
    )
    war_attacks = war_attacks.set_index("Faction")

    summary_df = summary_df.merge(war_attacks, on="Faction")

    non_war_hits = attack_df.loc[
        (attack_df["Attacker Faction"].eq(basic_faction_info["name"]))
        & attack_df["ranked_war"].eq(0)
        & (
            attack_df["result"].eq("Attacked")
            | attack_df["result"].eq("Hospitalized")
            | attack_df["result"].eq("Mugged")
            | attack_df["result"].eq("Arrested")
        )
    ]
    non_war_hits = non_war_hits["Attacker Faction"].value_counts().reset_index()
    non_war_hits = non_war_hits.rename(
        columns={"index": "Faction", "Attacker Faction": "Non-War Hits"}
    )
    non_war_hits = non_war_hits.set_index("Faction")

    summary_df.at[basic_faction_info["name"], "Non-War Hits"] = non_war_hits.at[
        basic_faction_info["name"], "Non-War Hits"
    ]

    assist_attacks = attack_df.loc[
        (
            attack_df["Attacker Faction"].eq(faction1)
            | attack_df["Attacker Faction"].eq(faction2)
        )
        & attack_df["result"].eq("Assist")
    ]
    assist_attacks = assist_attacks["Attacker Faction"].value_counts().reset_index()
    assist_attacks = assist_attacks.rename(
        columns={"index": "Faction", "Attacker Faction": "Assists"}
    )
    assist_attacks = assist_attacks.set_index("Faction")

    summary_df = summary_df.merge(assist_attacks, on="Faction")

    retal_attacks = attack_df.loc[
        (
            attack_df["Attacker Faction"].eq(faction1)
            | attack_df["Attacker Faction"].eq(faction2)
        )
        & attack_df["modifiers.retaliation"].eq(1.50)
    ]
    retal_attacks = retal_attacks["Attacker Faction"].value_counts().reset_index()
    retal_attacks = retal_attacks.rename(
        columns={"index": "Faction", "Attacker Faction": "Retaliations"}
    )
    retal_attacks = retal_attacks.set_index("Faction")

    summary_df = summary_df.merge(retal_attacks, on="Faction")

    failed_attacks = attack_df.loc[
        (
            attack_df["Attacker Faction"].eq(faction1)
            | attack_df["Attacker Faction"].eq(faction2)
        )
        & (
            attack_df["result"].eq("Interrupted")
            | attack_df["result"].eq("Lost")
            | attack_df["result"].eq("Escape")
            | attack_df["result"].eq("Stalemate")
            | attack_df["result"].eq("Timeout")
        )
    ]
    failed_attacks = failed_attacks["Attacker Faction"].value_counts().reset_index()
    failed_attacks = failed_attacks.rename(
        columns={"index": "Faction", "Attacker Faction": "Failed Attacks"}
    )
    failed_attacks = failed_attacks.set_index("Faction")

    summary_df = summary_df.merge(failed_attacks, on="Faction")

    total_attacks = (
        temp_df["Attacker Faction"].value_counts().reset_index().set_index("index")
    )

    summary_df.at[basic_faction_info["name"], "Total Attacks"] = total_attacks.at[
        basic_faction_info["name"], "Attacker Faction"
    ]

    successful_revives = revive_df.loc[
        (revive_df["Target Faction"].eq(basic_faction_info["name"]))
        & revive_df["result"].eq("success")
    ]
    successful_revives = (
        successful_revives["Target Faction"].value_counts().reset_index()
    )
    successful_revives = successful_revives.rename(columns={"index": "Faction"})
    successful_revives = successful_revives.set_index("Faction")

    summary_df.at[
        basic_faction_info["name"], "Successful Revives"
    ] = successful_revives.iat[0,0]

    failed_revives = revive_df.loc[
        (revive_df["Target Faction"].eq(basic_faction_info["name"]))
        & revive_df["result"].eq("failure")
    ]
    failed_revives = failed_revives["Target Faction"].value_counts().reset_index()
    failed_revives = failed_revives.rename(columns={"index": "Faction"})
    failed_revives = failed_revives.set_index("Faction")

    summary_df.at[basic_faction_info["name"], "Failed Revives"] = failed_revives.iat[0,0]

    return summary_df.to_html(index_names=False, na_rep="N/A")


def main():
    # df = pd.read_csv("attacks_336_test_clean.csv")
    # create_war_attacks_graph(df)
    pass


if __name__ == "__main__":
    main()
