#!/usr/bin/env python
# encoding: utf-8
"""
sanexcup.py

Created by Breyten Ernsting on 2013-10-31.
Copyright (c) 2013 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import re
import getopt

from pprint import pprint

import requests
import feedparser
from BeautifulSoup import BeautifulSoup

help_message = '''
Sanex cup calculator
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def get_sanex_counts(team_link):
    games = 0
    sanex = 0
    anti_sanex = 0

    try:
        html = requests.get('http://www.volleybal.nl%s/uitslagen/volledig' % (team_link,)).text
    except Exception, e:
        html = None

    if html is None:
        return (0, -1, -1)

    soup = BeautifulSoup(html)
    #uitslagen = [s.find('span').string for s in soup.findAll('td', 'score')]
    
    #for uitslag in uitslagen:
    #    if uitslag
    
    for week in soup.findAll('table', 'scheduleTabs'):
        for game in week.tbody.findAll('tr'):
            home_link = game.find('td', 'teamHome').a['href']
            is_home_game = (home_link == team_link)
            uitslag = game.find('td', 'score').span.string
            info = uitslag.split('-', 1)
            if info[0].strip() != u'':
                num_sets = int(info[0]) + int(info[1])
            else:
                num_sets = 0
            if num_sets >= 4:
                games += 1
                if is_home_game and uitslag == u'4-0':
                    sanex += 1
                if is_home_game and uitslag == u'0-4':
                    anti_sanex += 1
                if not is_home_game and uitslag == u'4-0':
                    anti_sanex += 1
                if not is_home_game and uitslag == u'0-4':
                    sanex += 1

    return (games, sanex, anti_sanex)

def get_all_teams(team_id):
    try:
        html = requests.get('http://www.volleybal.nl/competitie/vereniging/%s/teams' % (team_id,)).text
    except Exception, e:
        html = None
    
    if html is None:
        return []

    soup = BeautifulSoup(html)
    team_cells = soup.findAll('td', 'team')
    team_links = [t.find('a')['href'] for t in team_cells]
    return team_links

def cmp_teams(a, b):
    IDX_GAMES = 1
    IDX_SANEX = 2
    IDX_ANTI_SANEX = 3
    rate_a = a[IDX_SANEX] * 1.0 / a[IDX_GAMES]
    rate_b = b[IDX_SANEX] * 1.0 / b[IDX_GAMES]
    anti_rate_a = a[IDX_ANTI_SANEX] * 1.0 / a[IDX_GAMES]
    anti_rate_b = b[IDX_ANTI_SANEX] * 1.0 / b[IDX_GAMES]

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

def main(argv=None):
    if argv is None:
        argv = sys.argv

    team_id = 3208 # US

    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hvt:", ["help", "team"])
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
            if option in ("-t", "--team"):
                team_id = int(value)
    
        team_links = get_all_teams(team_id)
        data = {}
        for team_link in team_links:
            games, sanex, anti_sanex = get_sanex_counts(team_link)
            info = (team_link, games, sanex, anti_sanex)
            data[team_link] = info

        sorted_data = sorted(data.values(), cmp=cmp_teams)
        sorted_data.reverse()
        #pprint(sorted_data)

        num = 1
        print "plek\tteam naam \tgesp\t4-0\t0-4\tpct"
        print "-"*54
        for row in sorted_data:
            team_naam = row[0].replace(u'/competitie/team/', u'')
            matches = re.search(r'^\d+(H|D)S\+?(\d+)', team_naam)
            kind = "Heren"
            if matches.group(1) == 'D':
                kind = "Dames"
            team_naam = u"%s %s" % (kind, matches.group(2))
            ratio = row[2] * 100.0 / row[1]
            print "%d\t%s \t%s\t%d\t%d\t%.2f" % (num, team_naam, row[1], row[2], row[3], ratio,)
            num += 1

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
