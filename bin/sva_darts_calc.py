#!/usr/bin/env python

import re
import os
import sys

import libsvadarts as sva

from pprint import pprint


c = 400
k = 24
minrating = 1000
startrating = 1100


def finishes_points(f):
    if(f == '0'):
        return 0

    retval = 0
    finishes = f.split(',')
    for finish in finishes:
        finish = int(finish)
        if finish >= 100 and finish <= 110:
            retval += 1
        elif finish <= 120:
            retval += 2
        elif finish <= 130:
            retval += 3
        elif finish <= 140:
            retval += 4
        elif finish <= 150:
            retval += 5
        elif finish <= 160:
            retval += 6
        elif finish == 161:
            retval += 7
        elif finish == 164:
            retval += 8
        elif finish == 167:
            retval += 9
        elif finish == 170:
            retval += 10
    return retval


def insert_game_data(
        game_id, speler_naam, speler_punten, speler_rating,
        speler_rating_adj, speler_game_number):

    sva.db.execute('''
    INSERT INTO game_data (
        game_id, speler_naam, speler_punten, speler_rating, 
        speler_rating_adj, speler_game_number
    ) VALUES (
        ?,?,?,?,?,?
    )
    ''', [
        game_id, speler_naam, speler_punten, speler_rating,
        speler_rating_adj, speler_game_number
    ])


def main(argv):
    sva.db.execute('DELETE FROM game_data')

    spelers_a = sva.exec_select_query('''
        SELECT speler_naam, ? as rating, 0 as games FROM speler
    ''', [startrating])
    spelers = {speler['speler_naam']: speler for speler in spelers_a}

    competitions = sva.exec_select_query('''
        SELECT DISTINCT comp
        FROM game
        ORDER BY comp
    ''')
    for competition in competitions:
        comp = competition['comp']
        comp_games = []
        comp_spelers = {}

        # haal de data op van alle games
        games = sva.exec_select_query('''
            SELECT game_id, datum, 
                speler1_naam, speler1_legs, speler1_finishes, speler1_180s, 
                speler2_naam, speler2_legs, speler2_finishes, speler2_180s
            FROM game
            WHERE comp=?
            ORDER BY game_order
        ''', [comp])

        # bereken de punten

        for game in games:
            # pprint(game)
            speler1_punten = 0
            speler2_punten = 0
            if game['speler1_legs'] == 2 and game['speler2_legs'] == 0:
                r1 = 1
                r2 = 0
                speler1_punten = 5
            elif game['speler1_legs'] == 2 and game['speler2_legs'] == 1:
                r1 = 0.67
                r2 = 0.33
                speler1_punten = 3
                speler2_punten = 1
            elif game['speler1_legs'] == 1 and game['speler2_legs'] == 2:
                r1 = 0.33
                r2 = 0.67
                speler1_punten = 1
                speler2_punten = 3
            elif game['speler1_legs'] == 0 and game['speler2_legs'] == 2:
                r1 = 0
                r2 = 1
                speler2_punten = 5

            speler1_punten = speler1_punten + game['speler1_180s']
            speler1_punten = speler1_punten + \
                finishes_points(game['speler1_finishes'])

            speler2_punten = speler2_punten + game['speler2_180s']
            speler2_punten = speler2_punten + \
                finishes_points(game['speler2_finishes'])

            rating_speler1 = spelers[game['speler1_naam']]
            rating_speler2 = spelers[game['speler2_naam']]

            # TODO als één van beide spelers in zijn eerste 16 wedstrijden zit: geen aftrek
            # als een ervaren speler tegen speler in zijn eerste 16 speelt: minder winst, geen verlies
            # minimum rating is 1000

            diff = rating_speler2['rating']-rating_speler1['rating']

            e1 = 1 / (1+10**(diff/c))
            e2 = 1 / (1+10**(-diff/c))

            mut1 = round(k * (r1-e1))
            mut2 = round(k * (r2-e2))
            new1 = rating_speler1['rating'] + mut1
            new2 = rating_speler2['rating'] + mut2

            rating_speler1['rating'] = max(new1, minrating)
            rating_speler1['games'] += 1
            rating_speler2['rating'] = max(new2, minrating)
            rating_speler2['games'] += 1

            # pprint(game)
            insert_game_data(
                game['game_id'], game['speler1_naam'], speler1_punten,
                rating_speler1['rating'], mut1, rating_speler1['games']
            )            
            insert_game_data(
                game['game_id'], game['speler2_naam'], speler2_punten,
                rating_speler2['rating'], mut2, rating_speler2['games']
            )
        # bereken de rating
        sva.db.commit()
    pprint(spelers)
    print('---')


if __name__ == "__main__":
    main(sys.argv[1:])
