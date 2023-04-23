#!/usr/bin/env python

"""collect all games from all years from different formatted files"""


import pandas as pd
import sys
from dataclasses import dataclass
import os
import math


C = 200
KFACTOR = 24
MIN_RATING = 1000
START_RATING = 1100


datapath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


@dataclass
class Player:
    name: str
    aliases: list[str]


games = pd.DataFrame(
    columns=[
        "Date",
        "Player1",
        "Player2",
        "Legs1",
        "Legs2",
        "Max1",
        "Max2",
        "Finishes1",
        "Finishes2",
        "L21_1",
        "L21_2",
    ]
)


def parse_tm20160219():
    global games
    df = pd.read_csv(f"{datapath}/tm20160219.csv")
    df["Date"] = pd.to_datetime(df["datum"], format="%Y-%m-%d")
    df[["Player1", "Player2"]] = df[["speler1", "speler2"]]
    df[["Legs1", "Legs2"]] = df[["score1", "score2"]]

    games = pd.concat(
        [games, df[["Date", "Player1", "Player2", "Legs1", "Legs2"]]], ignore_index=True
    )


def parse_xml_format2016(filename):
    global games
    xls = pd.ExcelFile(f"{datapath}/{filename}")
    for sheet in xls.sheet_names:
        if sheet[0:2] != "20":
            continue

        # print(sheet)

        df = pd.read_excel(xls, sheet)
        df["Date"] = pd.to_datetime(sheet, format="%Y-%m-%d")
        df[["Player1", "Player2"]] = df[["Speler1", "Speler2"]]

        games = pd.concat(
            [
                games,
                df[
                    [
                        "Date",
                        "Player1",
                        "Player2",
                        "Legs1",
                        "Legs2",
                        "Max1",
                        "Max2",
                        "Finishes1",
                        "Finishes2",
                    ]
                ],
            ],
            ignore_index=True,
        )
        # print(df)

    # print(xls.sheet_names)


def parse_xml_format2021(filename):
    global games
    xls = pd.ExcelFile(f"{datapath}/{filename}")
    for sheet in xls.sheet_names:
        if sheet[0:5] == "Sheet":
            continue
        if sheet[10:22] != " competitie":
            continue

        df = pd.read_excel(xls, sheet)

        # print(sheet)
        # print(df)

        datestr = sheet[0:10]
        df["Date"] = pd.to_datetime(datestr, format="%Y-%m-%d")
        df[["Player1", "Player2"]] = df[["Speler 1", "Speler 2"]]
        df[["Legs1", "Legs2"]] = df[["S1 Legs", "S2 Legs"]]
        df[["Max1", "Max2"]] = df[["S1 180s", "S2 180s"]]
        df[["Finishes1", "Finishes2"]] = df[["S1 Finish", "S2 Finish"]]

        # pandas check if column exists
        if not "S1 21-" in df.columns:
            df["S1 21-"] = 0
        if not "S2 21-" in df.columns:
            df["S2 21-"] = 0

        df[["TwentyOne1", "TwentyOne2"]] = df[["S1 21-", "S2 21-"]]
        games = pd.concat(
            [
                games,
                df[
                    [
                        "Date",
                        "Player1",
                        "Player2",
                        "Legs1",
                        "Legs2",
                        "Max1",
                        "Max2",
                        "Finishes1",
                        "Finishes2",
                        "TwentyOne1",
                        "TwentyOne2",
                    ]
                ],
            ],
            ignore_index=True,
        )
    # print(df)


aliases = {
    "Jekel": {"*": "GertJ"},
    "Gert": {"*": "GertJ"},
    "Gert J": {"*": "GertJ"},
    "Ed": {
        "2015-2016": "EdG",
        "2016-2017": "EdG",
        "2017-2018": "EdG",
        "*": "Ed",
    },
}


def replace_alias(game, player: str):
    alias = aliases.get(player)
    if alias:
        season = game["Season"]
        new_name = alias.get(season)
        if new_name:
            return new_name
        if "*" in alias:
            return alias["*"]
    return player


def parse_all_games() -> pd.DataFrame:
    global games

    parse_tm20160219()
    parse_xml_format2016("Austerlitz_seizoen_2016-2017.xlsx")
    parse_xml_format2016("Austerlitz_seizoen_2017-2018.xlsx")
    parse_xml_format2016("Austerlitz_seizoen_2018-2019.xlsx")
    parse_xml_format2016("Austerlitz_seizoen_2019-2020.xlsx")
    parse_xml_format2016("Austerlitz_seizoen_2020-2021.xlsx")
    parse_xml_format2021("Austerlitz_seizoen_2021-2022.xlsx")
    games["Year"] = games["Date"].dt.year
    games["Season"] = games.apply(
        lambda game: f'{game["Year"]}-{game["Year"]+1}'
        if game["Date"].month >= 7
        else f'{game["Year"]-1}-{game["Year"]}',
        result_type="reduce",
        axis=1,
    )
    games["Player1"] = games.apply(
        lambda game: replace_alias(game, game["Player1"]),
        result_type="reduce",
        axis=1,
    )
    games["Player2"] = games.apply(
        lambda game: replace_alias(game, game["Player2"]),
        result_type="reduce",
        axis=1,
    )

    return games


current_state = {}


def init_scores(players):
    global current_state

    current_state = {
        player: {"rating": START_RATING, "games_count": 0, "games": []}
        for player in players
    }


def calc_game_rating(
    game,
):
    global current_state

    r1 = current_state[game["Player1"]]
    r2 = current_state[game["Player2"]]

    p1 = game["Legs1"]
    p2 = game["Legs2"]

    if {p1, p2} == {0, 0}:
        # no result, rating stays the same
        return pd.Series([r1["rating"], r2["rating"]])

    fraction_1 = p1 / (p1 + p2)
    fraction_2 = p2 / (p1 + p2)

    # expected
    expected_fraction_1 = 1 / (1 + math.pow(10, (r2["rating"] - r1["rating"]) / C))
    expected_fraction_2 = 1 - expected_fraction_1

    new_rating_1 = r1["rating"] + KFACTOR * (fraction_1 - expected_fraction_1)
    new_rating_2 = r2["rating"] + KFACTOR * (fraction_2 - expected_fraction_2)

    r1["rating"] = max(new_rating_1, MIN_RATING)
    r1["games_count"] += 1
    # r1["games"].append(game)

    r2["rating"] = max(new_rating_2, MIN_RATING)
    r2["games_count"] += 1
    # r2["games"].append(game)

    # game['Rating1'] = new_rating_1
    # game['Rating2'] = new_rating_2

    return pd.Series([new_rating_1, new_rating_2])


def main(argv):
    games = parse_all_games()
    players = pd.concat([games["Player1"], games["Player2"]]).unique()

    global current_state
    current_state = {
        player: {"rating": START_RATING, "games_count": 0, "games": []}
        for player in players
    }

    games[["Rating1", "Rating2"]] = pd.DataFrame(
        games.apply(
            calc_game_rating,
            result_type="reduce",
            axis=1,
        )
    )

    #save players to json
    for player in players:
        player_games = games[
            (games["Player1"] == player) | (games["Player2"] == player)
        ]
        player_games.to_json(f"../docs/data/players/{player}.json", orient="records")

    print(games)
    print(games.describe())


if __name__ == "__main__":
    main(sys.argv[1:])
