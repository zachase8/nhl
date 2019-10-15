# nhl_current_data.py
"""
Erik Hannesson
9 April 2019
"""

from selenium import webdriver
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import time
import pickle

# Team name --> abbr dict
with open('team_name_map', 'rb') as f:
    team_names = pickle.load(f)

# team_names = {"Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF", "Carolina Hurricanes": "CAR", "Calgary Flames": "CGY", "Chicago Blackhawks": "CHI", "Columbus Blue Jackets": "CBJ", "Colorado Avalanche": "COL", "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montréal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI", "Phoenix Coyotes": "PHX", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK", "Winnipeg Jets": "WPG", "Washington Capitals": "WSH"}

base_url = 'http://www.nhl.com/stats'
stat_type = (
                '/{}?'              # {player/team}
                'reportType={}&'    # {season/game}
                '{}From={}&'        # {season/date} {YYYYYYYY/YYYY-MM-DD}
                '{}To={}&'          # {season/date} {YYYYYYYY/YYYY-MM-DD}
                'gameType=2&filter=gamesPlayed,gte,1&sort=points,goals,assists'
            )

report = ['player', 'team']
r_type = ['season', 'game']
season = '20192020'
date_from = ''
date_to = ''

def get_page(url):
    # open the broser and get the html
    browser = webdriver.Chrome()
    browser.get(url)

    # get the next page button
    next_page = browser.find_element_by_class_name("-next")

    games = []
    results = []

    # get souce code to find number of pages
    soup = BeautifulSoup(browser.page_source, "html.parser")
    tot_pages = soup.find(class_='-totalPages')


    for page in range(51):
        # spit it into a soup object
        soup = BeautifulSoup(browser.page_source, "html.parser")


        # grab the rows from the page
        rows = soup.find_all(class_="rt-tr-group")
        time.sleep(0.25)


        # iterate through each row to get the game data
        for game in rows:
            res = []
            g = game.find_all(class_="rt-td")
            # | HOME | AWAY | WIN | LOSS | TIE | OT | GF | GA |
            res.append(g[1].text)
            res.append(g[2].text[-3:])
            res.append(g[4].text)
            res.append(g[5].text)
            res.append(g[6].text)
            res.append(g[7].text)
            res.append(g[9].text)
            res.append(g[10].text)

            # add to the big results list
            results.append(res)
        if page == 50:
            break
        next_page.click()

    return np.array(results)

def scrape():
    np.save("NHL_data.npy", get_page()[:-8])

def clean(filename="NHL_data.npy"):
    team_names = {"Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF", "Carolina Hurricanes": "CAR", "Calgary Flames": "CGY", "Chicago Blackhawks": "CHI", "Columbus Blue Jackets": "CBJ", "Colorado Avalanche": "COL", "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montréal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI", "Phoenix Coyotes": "PHX", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK", "Winnipeg Jets": "WPG", "Washington Capitals": "WSH"}

    data = np.load(filename)

    for i in range(data.shape[0]):
        data[i, 0] = team_names[data[i, 0]]

    return data
