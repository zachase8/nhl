# nhl_data.py
import requests
    """
    base_url = 'https:/statsapi.web.nhl.com/api/v1'

    Stats Types:
        base_url/statTypes          -- returns all stat types used in order to get
                                        a specific kind of player stat

    Team Data:
        base_url/teams              -- returns list of data about all teams
        base_url/teams/ID           -- returns data for a single team
        base_url/teams/ID/roster    -- returns entire roster for a single team

        Modifiers:
            ?expand=team.roster                     -- roster of active players
            ?expand=person.names                    -- same as above, less info
            ?expand=team.schedule.next              -- returns details of next game
            ?expand=team.schedule.previous          -- returns details of previous game
            ?expand=team.stats                      -- returns team's season's stats
            ?expand=team.roster&season={YYYYYYYY}   -- shows season YYYYYYYY roster
            ?teamID=4,5,29                          -- string team ids together
            ?stats=statsSingleSeasonPlayoffs        -- specify which stats to get

    Players (People):
        base_url/people/ID          -- returns details for a player (must specify ID)
        base_url/people/ID/stats    -- complex endpoint with lots of append
                                        options to change what stats you want

        Modifiers:
            ?stats=stasSingleSeason&season=YYYYYYYY     -- single season stats
            ?stats=homeAndAway&season=YYYYYYYY          -- split between home and away games
            ?stats=winLoss&season=YYYYYYYY              -- split between W/L/OT
            ?stats=byMonth&season=YYYYYYYY              -- split monthly
            ?stats=byDayOfWeek&season=YYYYYYYY          -- split by day of week
            ?stats=vsDivision&season=YYYYYYYY           -- split by division
            ?stats=vsConference&season=YYYYYYYY         -- split by conference
            ?stats=vsTeam&season=YYYYYYYY               -- split by team
            ?stats=gameLog&season=YYYYYYYY              -- game log with stats for
                                                            each game in a given season
            ?stats=regularSeasonStatRankings&season=YYYYYYYY
                                                        -- where someone stands compared
                                                            to others
            ?stats=goalsByGameSituation&season=YYYYYYYY -- number of goals in different
                                                            situations
            ?stats=onPaceRegularSeason&season=YYYYYYYY  -- only works with current season;
                                                            shows projected stat totals

    Game:
        base_url/game/ID/feed/live      -- returns all data about specified game
                                            including play data with on-ice coordinates
                                            and post-game details
        base_url/game/ID/boxscore       -- returns far fewer details than above,
                                            more suitable for post-game analysis
        base_url/game/ID/content        -- complex endpoint returning multiple types
                                            of media, including videos of shots/goals/saves
        base_url/game/ID/feed/live/diffPatch?startTimecode=yyyymmdd_hhmmss
                                        -- returns updates for the specified game
                                            since the given startTimecode

    """

def get_active_teams(base_url='https:/statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for team information and returns a list of active teams.

    Parameters:
        base_url (str): base url to the nhl api

    Returns:
        active_teams (list(tuples)): list containing (team-name, team-id) pairs
            for all currently active teams
    """
    # request teams data
    teams = requests.get(base_url + '/teams').json('teams')

    # extract active team names and ids
    active_teams = [(team['name'], team['id']) for team in teams if team['active']]

    return active_teams

def get_team_roster(team_id, base_url='https:/statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for roster information for a given team

    Parameters:
        team_id (int): nhl api team id number
        base_url (str): base url to the nhl api

    Returns:
        team_roster (list(dicts)): list of dicts; each dictionary contains the
            following information
        {'person': {'id': int,
                    'fullName': str,
                    'link': str
            },
        'jerseyNumber': str,
        'position': {'code': str
                     'name': str
                     'type': str
                     'abbreviation': str
            }
        }
    """
    # get team roster
    team_roster = requests.get(base_url + '/teams/{}/roster'.format(team_id)).json()

    # extract player information
    return team_roster['roster']

def get_player_stats(player_id, base_url='https:/statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for the stats of a player
    """