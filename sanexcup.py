#!/usr/bin/env python
# encoding: utf-8
"""
sanexcup.py

Created by Breyten Ernsting on 2013-10-31.
Copyright (c) 2013 __MyCompanyName__. All rights reserved.
"""

import sys
import re
import getopt

from pprint import pprint

import feedparser

help_message = '''
Sanex cup calculator
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def cmp_teams(a, b):
    IDX_GAMES = 1
    IDX_SANEX = 2
    IDX_ANTI_SANEX = 3
    games_a = a[IDX_GAMES]
    games_b = b[IDX_GAMES]

    if games_a > 0:
        rate_a = a[IDX_SANEX] * 1.0 / games_a
        anti_rate_a = a[IDX_ANTI_SANEX] * 1.0 / games_a
    else:
        rate_a = 0.0
        anti_rate_a = 0.0
    if games_b > 0:
        rate_b = b[IDX_SANEX] * 1.0 / games_b
        anti_rate_b = b[IDX_ANTI_SANEX] * 1.0 / games_b
    else:
        rate_b = 0.0
        anti_rate_b = 0.0

    if a[IDX_SANEX] == b[IDX_SANEX]:
        if rate_a == rate_b:
            if anti_rate_a == anti_rate_b:
                a_is_ds = (re.search(r'DS', a[0]) is not None)
                b_is_ds = (re.search(r'DS', b[0]) is not None)
                if a_is_ds == b_is_ds:
                    return 0
                elif a_is_ds:
                    return 1
                else:
                    return -1
            elif anti_rate_a < anti_rate_b:
                return 1
            else:
                return -1
        elif rate_a > rate_b:
            return 1
        else:
            return -1
    elif a[IDX_SANEX] > b[IDX_SANEX]:
        return 1
    else:
        return -1


def get_result_for(game, club_name):
    participants, result = re.split(r', Uitslag: ', game.title, 1)
    home, away = re.split(' - ', participants, 1)
    sanex_incr = 0
    anti_sanex_incr = 0
    regex = '.*%s\s+([D|H])S([\d|\s])+$' % (club_name,)
    results = []
    if re.match(regex, home):
        team_id = home
        if result == u'4-0':
            sanex_incr = 1
        if result == u'0-4':
            anti_sanex_incr = 1
        results.append((team_id, sanex_incr, anti_sanex_incr,))
    if re.match(regex, away):
        team_id = away
        if result == u'0-4':
            sanex_incr = 1
        if result == u'4-0':
            anti_sanex_incr = 1
        results.append((team_id, sanex_incr, anti_sanex_incr,))
    return results


def get_all_results(club_id, club_name):
    data = {}

    url = 'https://api.nevobo.nl/export/vereniging/%s/resultaten.rss' % (
        club_id,)
    try:
        feed = feedparser.parse(url)
    except Exception:
        feed = None

    if feed is None:
        return data

    for game in feed.entries:
        if  not ', Uitslag: ' in game.title:
            continue
        results = get_result_for(game, club_name)
        for team_id, sanex_incr, anti_sanex_incr in results:
            if team_id not in data:
                data[team_id] = [team_id, 0, 0, 0]
            data[team_id][1] += 1
            data[team_id][2] += sanex_incr
            data[team_id][3] += anti_sanex_incr
    return data


def main(argv=None):
    if argv is None:
        argv = sys.argv

    team_id = 'CKL7K12'  # US
    team_name = 'US'
    as_html = False

    try:
        try:
            opts, args = getopt.getopt(
                argv[1:], "Hhvtn:", ["help", "team", "html", "name"]
            )
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-o", "--output"):
                output = value
            if option in ("-H", "--html"):
                as_html = True
            if option in ("-t", "--team"):
                team_id = int(value)
            if option in ("-n", "--name"):
                team_name = value
        data = get_all_results(team_id, team_name)
        sorted_data = sorted(data.values(), cmp=cmp_teams)
        sorted_data.reverse()

        num = 1
        longest_name = max([len(x[0]) for x in sorted_data])
        if as_html:
            print "<table class=\"table-striped\"><tr>"
            print "<th>Plek</th><th>Team</th><th>Gespeeld</th>"
            print "<th>4-0</th><th>0-4</th><th>Percentage</th></tr>"
        else:
            print ("%s\t%-" + str(longest_name) + "s\t%s\t%s\t%s\t%s") % (
                "plek", "team naam", "gesp", "4-0", "0-4", "pct",)
            print "-"*(54 + longest_name)
        for row in sorted_data:
            regex = '.*%s\s+([D|H])S([\d|\s]+)$' % (team_name,)
            matches = re.search(regex, row[0])
            if matches:
                x = {'D': 'Dames', 'H': 'Heren'}
                team_naam = "%s %s" % (x[matches.group(1)], matches.group(2),)
            else:
                team_naam = row[0]
            team_naam = row[0]
            if row[1] > 0:
                ratio = row[2] * 100.0 / row[1]
            else:
                ratio = 0.0
            if as_html:
                print (
                    "<tr><td>%d</td><td>%s</td><td>%s</td><td>%d</td><td>"
                    "%d</td><td>%.2f</td></tr>") % (
                        num, team_naam, row[1], row[2], row[3], ratio,)
            else:
                print ("%d\t%-" + str(longest_name) + "s\t%s\t%d\t%d\t%.2f") % (
                    num, team_naam, row[1], row[2], row[3], ratio,
                )
            num += 1
        if as_html:
            print "</table>"

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
