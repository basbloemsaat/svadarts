#!/usr/bin/env python

import getopt
import os
import pathlib
import re
import sys

import libsvadarts as sva

from pprint import pprint

rootdir = os.path.dirname(os.path.abspath(__file__)) + '/../docs/data/'

def main(argv):

    # per seizoen
    data = {}

    competitions = sva.exec_select_query('''
        SELECT DISTINCT comp
        FROM game
        ORDER BY comp
    ''')
    competitions = [c['comp'] for c in competitions]
    for competition in competitions:
        data = {}
        # pprint(competition)

        data['games'] = sva.exec_select_query('''
            SELECT *
            FROM game
            WHERE comp=?
        ''', [competition])

        data['adjustments'] = sva.exec_select_query('''
            SELECT * 
            FROM adjustments a
            where comp=?
        ''', [competition])

        data['standings'] = sva.exec_select_query('''
           SELECT DISTINCT
                x.speler_naam,
                SUM(x.speler_punten) OVER (
                    PARTITION BY x.speler_naam
                    ORDER BY x.game_order ASC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND 
                    UNBOUNDED FOLLOWING
                ) AS speler_punten,
                SUM(x.speler_games) OVER (
                    PARTITION BY x.speler_naam
                    ORDER BY x.game_order ASC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND 
                    UNBOUNDED FOLLOWING
                ) AS speler_games,
                LAST_VALUE ( x.speler_rating) OVER (
                    PARTITION BY x.speler_naam
                    ORDER BY x.game_order ASC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND 
                    UNBOUNDED FOLLOWING
                ) AS rating,
                SUM(x.speler_180s) OVER (
                    PARTITION BY x.speler_naam
                    ORDER BY x.game_order ASC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND 
                    UNBOUNDED FOLLOWING
                ) AS speler_180s,
                GROUP_CONCAT(x.speler_finishes, ',' ) OVER (
                    PARTITION BY x.speler_naam
                    ORDER BY x.game_order ASC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND 
                    UNBOUNDED FOLLOWING
                ) AS speler_finishes,
                SUM(x.speler_lollies) OVER (
                    PARTITION BY x.speler_naam
                    ORDER BY x.game_order ASC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND 
                    UNBOUNDED FOLLOWING
                ) AS speler_lollies
                FROM (
                SELECT
                    a.comp,
                    0 as game_order,
                    a.speler_naam,
                    a.speler_points as speler_punten,
                    0 as speler_rating,
                    a.speler_games,
                    a.speler_180s,
                    NULLIF(a.speler_finishes,'0') AS speler_finishes,
                    a.speler_lollies
                FROM adjustments a
                WHERE comp=?
                UNION ALL
                SELECT 
                    g.comp,
                    g.game_order,
                    gd.speler_naam,
                    gd.speler_punten,
                    gd.speler_rating,
                    1 as speler_games,
                    CASE 
                        WHEN g.speler1_naam = gd.speler_naam
                        THEN g.speler1_180s
                        ELSE g.speler2_180s
                    END,
                    NULLIF(CASE 
                        WHEN g.speler1_naam = gd.speler_naam
                        THEN g.speler1_finishes
                        ELSE g.speler2_finishes
                    END,'0'),
                    CASE 
                        WHEN g.speler1_naam = gd.speler_naam
                        THEN g.speler1_lollies
                        ELSE g.speler2_lollies
                    END
                    
                FROM game g
                JOIN game_data gd on gd.game_id=g.game_id
                WHERE comp=?
            ) as x
            ORDER BY speler_punten DESC

        ''', [competition, competition])

        filename = rootdir + '/perseason/' + competition + '.json'
        # pprint(filename)

        # pprint(data)
        sva.save_data_to_json(data, filename)

    # per speler
    spelers = sva.exec_select_query('''
        SELECT speler_naam
        FROM speler
        ORDER BY speler_naam
    ''')
    spelers = [s['speler_naam'] for s in spelers]
    for speler in spelers:
        data = {}
        data['games'] = sva.exec_select_query('''
            SELECT 
                g.comp
                , g.datum
                , g.game_order
                , g.game_id
                , gd.speler_game_number
                , g.speler1_180s
                , g.speler1_finishes
                , g.speler1_legs
                , g.speler1_lollies
                , g.speler1_naam    
                , g.speler2_180s
                , g.speler2_finishes
                , g.speler2_legs
                , g.speler2_lollies
                , g.speler2_naam
                
                , gd.speler_punten
                , gd.speler_rating
                , gd.speler_rating_adj
            FROM
                game g
                JOIN game_data gd ON gd.game_id = g.game_id
                
            WHERE   gd.speler_naam = ?
            ORDER BY gd.speler_game_number
        ''', [speler])

        data['avonden'] = sva.exec_select_query('''
            SELECT 
                datum
                , comp
                , last_rating AS rating
                , SUM (speler_rating_adj) as rating_adj
                , SUM(speler_punten) as punten
                , SUM(CASE WHEN speler1_naam = speler_naam THEN speler1_180s ELSE speler2_180s END) AS m180s
                , SUM(CASE WHEN speler1_naam = speler_naam THEN speler1_lollies ELSE speler2_lollies END) AS lollies
                , GROUP_CONCAT(CASE WHEN speler1_naam = speler_naam THEN speler1_finishes ELSE speler2_finishes END) AS finishes
                , 1 as game_count
                , 'game' as type
            FROM (
                SELECT 
                    *
                    , LAST_VALUE(gd.speler_rating) OVER (
                        PARTITION BY datum
                        ORDER BY g.game_order ASC
                        RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) as last_rating
                FROM
                    game g
                    JOIN game_data gd ON gd.game_id = g.game_id
                WHERE gd.speler_naam = ?
            ) AS a
            GROUP BY datum

            UNION
            SELECT 
                datum
                , comp
                , 0 as rating
                , 0 as rating_adj
                , speler_points
                , speler_180s
                , speler_lollies
                , speler_finishes
                , speler_games
                , adj_type
            FROM adjustments
            WHERE speler_naam = ?

        ''', [speler, speler])

        filename = rootdir + 'perspeler/' + speler + '.json'
        pprint(filename)
        
        sva.save_data_to_json(data, filename)

    # overzicht
    data = {}

    data['spelers'] = spelers
    data['competitions'] = competitions

    # pprint(data)

    sva.save_data_to_json(data, rootdir + '/index.json')




def usage():
    print('''read_file.py 
        --file <filename>
        ''')
    sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
