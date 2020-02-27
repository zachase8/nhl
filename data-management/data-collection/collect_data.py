# collect_data.py
import requests
from pymongo import MongoClient
import pickle
import progressbar
import time
import pandas as pd
import os


def getTeamIDs(base_url='https://statsapi.web.nhl.com/api/v1', active=True):
    """
    Queries the NHL API for (team_name, team_id) pairs.

    Parameters:
        base_url (str): base url to the nhl api
        active (bool): if True, only return data for active teams

    Returns:
        teams (list(tuples)): list containing (team-name, team-id) pairs
            for all (active) teams
    """
    # request teams data
    all_teams = requests.get(base_url + '/teams').json()['teams']

    # extract team names and ids
    if active:
        teams = {team['name']: team['id'] for team in all_teams if team['active']}
    else:
        teams = {team['name']: team['id'] for team in all_teams}

    return teams


def getTeamRoster(team_id, base_url='https://statsapi.web.nhl.com/api/v1',
                        season=None, wait=True):
    """
    Queries the NHL API for roster information for a given team

    Parameters
    ----------
        team_id (int): nhl api team id number
        base_url (str): base url to the nhl api
        season (str): season to request roster; defaults to using active roster
        wait (bool): specifies if we should pause before requesting the data;
                        should only be False if making a single request or if you
                        are explicitly waiting before repeated calls of this function

    Returns
    -------
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
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    if wait:
        # wait a moment to request additional data
        time.sleep(0.1)

    # endpoint to request data from
    endpoint_url = '/teams/{}/roster'.format(team_id)

    if  season:
        # if we want data from a specific season
        endpoint_url += '?expand=team.roster&season={}'.format(season)

    # get team roster
    team_roster = requests.get(base_url + endpoint_url).json()

    # extract player information
    return team_roster['roster']


def getPlayerStats(player_id, base_url='https://statsapi.web.nhl.com/api/v1',
                        season=None, stat_type='statsSingleSeason', wait=True):
    """
    Queries the NHL API for the stats of a player.

    Parameters:
        player_id (int): nhl api player id number
        base_url (str): base url to the nhl api
        stat_type (str): stats type to request
        season (str): season to request stats from
        wait (bool): specifies if we should pause before requesting the data;
                        should only be False if making a single request or if you
                        are explicitly waiting before repeated calls of this function

    Returns:
        player_stats (dict): dictionary of requested stats
        None: if player has no stats in given season
    """
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    if wait:
        time.sleep(0.01)

    # endpoint to query
    endpoint_url = f'/people/{player_id}/stats?stats={stat_type}&season={season}'

    # request player statistics
    player_stats = requests.get(base_url + endpoint_url).json()

    # extract useful part of statistics
    try:
        # if the player has stats, this is where they will be
        player_stats = player_stats['stats'][0]['splits']
    except IndexError:
        # if player has no stats, return None
        return None

    return player_stats


def updatePlayerList(base_url='https://statsapi.web.nhl.com/api/v1',
                        season=None, save_path='data/basic/', active=False):
    """
    Updates the player dictionaries, which associate players/ids with their
        respective teams

    Parameters:
        base_url (str): base url to the nhl api
        save_path (str): relative path to directory where data will be saved
        season (str): season to request players from
        active (bool): if True, only updates the active players info

    Returns:
        None

        Creates pickle files for the following:
            player_ids:     [player_ids]
            team_ids:       [team_ids]
            name_to_id:     {player_name: player_id}
            id_to_name:     {player_id: player_name}
            team_to_player: {team_id: [player_ids]}
            player_to_team: {player_id: team_id}

    """
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    # get list of every team
    all_teams = getTeamIDs(base_url=base_url, active=active)
    all_teams = [name_id_pair for name_id_pair in all_teams.items()]

    # progressbar to track progress
    bar = progressbar.progressbar(all_teams)

    # get team rosters -- list of (roster_dict, team_id) pairs
    team_rosters = [(getTeamRoster(team[1], wait=True), team[1]) for team in bar]

    # create list of player dicts -- dict format like in getTeamRoster docstring
    players = [player for team in team_rosters for player in team[0]]

    # create {player: id} and {id: player} dictionaries
    name_to_id = {player['person']['fullName']: player['person']['id'] for player in players}
    id_to_name = {id: fullName for fullName, id in name_to_id.items()}

    # create {team_id: player_ids} and {player_id: team_id} dictionaries
    team_to_player = {team[1]: [player['person']['id'] for player in team[0]]
                        for team in team_rosters}
    player_to_team = {player: team for team in team_to_player.keys()
                        for player in team_to_player[team]}

    # create {team_id: team_name} and {team_name: team_id} dictionaries
    team_id_to_name = {team[1]: team[0] for team in all_teams}
    team_name_to_id = {team[0]: team[1] for team in all_teams}

    # saving data -- update base-save path to save in the correct year subfolder
    save_path += season[:4] + '-' + season[4:] + '/'
    # check if the subfolder exists, if not, create it
    if not os.path.exists(save_path):
        os.mkdir('./' + save_path)

    # pickle mapping dictionaries
    dicts = [name_to_id, id_to_name, team_to_player, player_to_team,
                team_id_to_name, team_name_to_id]
    dict_names = ['player_name_to_id', 'player_id_to_name', 'team_id_to_players',
                    'player_id_to_team', 'team_id_to_name', 'team_name_to_id']

    for d, n in zip(dicts, dict_names):
        with open(save_path + n, 'wb') as f:
            pickle.dump(d, f)

    # create/pickle player_id and team_id lists
    player_ids = list(player_to_team.keys())
    team_ids = list(team_to_player.keys())
    lists = [player_ids, team_ids]
    list_names = ['player_ids', 'team_ids']

    for lst, name in zip(lists, list_names):
        with open(save_path + name, 'wb') as f:
            pickle.dump(lst, f)

    return


def updatePlayerStats(base_url='https://statsapi.web.nhl.com/api/v1',
                        season=None, save_path='data/stats/',
                        load_path='data/basic/', **kwargs):
    """
    Updates player stats data.

    Parameters:
        base_url (str): base url to the nhl api
        save_path (str): rel path to dir where data will be saved
        load_path (str): rel path to dir where player_id data will be loaded from
        **kwargs: keyword arguments to pass to getPlayerStats
            season (str)
            stat_type (str):
                'statsSingleSeason' (default), 'homeAndAway', 'winLoss', 'byMonth',
                'byDayofWeek', 'vsDivision', 'vsConference', 'vsTeam', 'gameLog'

    Returns:
        None

        Updates the player stats DataFrame object
    """
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    season_sub = season[:4] + '-' + season[4:]
    # load player ids
    with open(load_path + season_sub + '/player_ids', 'rb') as f:
        player_ids = pickle.load(f)

    # progressbar to track process
    bar = progressbar.progressbar(player_ids)

    # request player stats
    player_stats = {p_id: getPlayerStats(p_id, **kwargs) for p_id in bar}

    # remove None entries (players with no stats)
    player_stats = {key: val for key, val in player_stats.items() if val is not None}

    # update player_ids to only include those with statistics
    player_ids = list(player_stats.keys())

    # split into goalie and skater stats
    goalies, skaters = dict(), dict()
    for p_id in player_ids:
        try:
            # check if this is a goalie
            player_stats[p_id]['stat']['ot']
            goalies[p_id] = player_stats[p_id]
        except KeyError:
            # if there was a keyerror, then this is a skater
            skaters[p_id] = player_stats[p_id]

    # get skater and goalie ids to set dataframe index
    goalie_ids, skater_ids = goalies.keys(), skaters.keys()
    goalie_stats = [goalies[g_id] for g_id in goalie_ids]
    skater_stats = [skaters[s_id] for s_id in skater_ids]

    # create pandas dataframe objects
    goalie_df = pd.io.json.json_normalize(goalie_stats)
    skater_df = pd.io.json.json_normalize(skater_stats)

    # set index to be player ids
    goalie_df['player_id'] = goalie_ids
    skater_df['player_id'] = skater_ids
    goalie_df.set_index('player_id', inplace=True)
    skater_df.set_index('player_id', inplace=True)

    # rename columns to no longer have 'stat.----'
    goalie_df.columns = [col.replace('stat.', '') for col in list(goalie_df)]
    skater_df.columns = [col.replace('stat.', '') for col in list(skater_df)]

    # update save_path to save in proper subfolders
    save_path += season_sub + '/'
    if not os.path.exists(save_path):
        os.mkdir('./' + save_path)

    # determine stat type subfolder to save in
    try:
        # check if we are updating a non-default stat file
        if kwargs['stat_type'] != 'statsSingleSeason':
            save_path += kwargs['stat_type'] + '/'
            # s_save_path += 'stats' + kwargs['stat_type']
        else:
            save_path += 'SingleSeason/'
            # s_save_path += 'statsSingleSeason'
    except KeyError:
        # if updating default stat file
        save_path += 'SingleSeason/'
        # s_save_path += 'statsSingleSeason'

    # create separate goalie and skater paths
    g_save_path = save_path
    s_save_path = save_path

    if not os.path.exists('./' + g_save_path):
        os.mkdir(g_save_path)
    if not os.path.exists('./' + s_save_path):
        os.mkdir(s_save_path)

    # pickle goalie and skater stats separately
    with open(save_path + 'goalie_stats', 'wb') as f:
        pickle.dump(goalie_df, f)
    with open(save_path + 'skater_stats', 'wb') as f:
        pickle.dump(skater_df, f)

    return


def batchUpdate(seasons, base_url='https://statsapi.web.nhl.com/api/v1',
                 get_lists=True, **kwargs):
    """
    Allows specification of a range of season to pull/update data from, instead
    of needing to run updatePlayerStats manually over and over.

    Parameters:
        seasons (iterable): iterable containing each season to pull data for.
            Elements of the iterable should be strings of the form '20132014'.
        base_url (str): base url to the NHL Statistics API
        get_lists (bool): if True, calls updatePlayerList() for each
            season before calling updatePlayerStats().
        **kwargs: additional arguments to be passed to updatePlayerLists
            e.g. stat_type

    Returns:
        None
    """
    # number of seasons
    n = len(seasons)
    season_n = 1

    for season in seasons:
        print('\n\nUpdating data from season {}-{} ({}/{})...'.format(season[:4],
                season[4:], season_n, n))

        if get_lists:
            # if we need to update the player lists first
            updatePlayerList(base_url=base_url, season=season, **kwargs)

        # pull and save the given seasons stats
        updatePlayerStats(base_url=base_url, season=season, **kwargs)

        season_n += 1

    return


def getSchedule(team_id, season=None, mongodb=False,
                base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for a team's schedule.

    Parameters
    ----------
    team_id : str
        Team's NHL API id number.

    season : str ('YYYYYYYY', default: None)
        Season to request data from (e.g. '20192020'). If None, defaults to the
        current season.

    mongodb : bool
        If True, save the requested data to the MongoDB collection nhl.schedule.
        Otherwise, returns the requested data
    """
    if type(team_id) is int:
        team_id = str(team_id)

    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    # request schedule information
    schedule = requests.get(base_url + f'/schedule?season={season}&teamId={team_id}')
    # extract useful information
    schedule = schedule.json()['dates']

    if not mongodb:
        # return results if we aren't saving it to the database
        return {team_id: {season: schedule}}

    # connect to mongodb client
    client = MongoClient()
    nhl_schedule = client.nhl.schedule

    # update/create appropriate entry
    ins = f'{team_id}.{season}'
    nhl_schedule.update_one({team_id: {'$exists': True}},
                            {'$set': {ins: schedule}}, upsert=True)

    return None


def getBoxScore(game_id, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for the boxscore for game `game_id`.

    Parameters
    ----------
    game_id : str
        NHL API game_id number for the desired game.

    base_url : str
        URL to the base of the NHL API

    Returns
    -------
    home : dict
        dictionary containing home team information

    away : dict
        dictionary containing away team information
    """
    boxscore = requests.get(base_url + f'/game/{game_id}/boxscore').json()

    return boxscore['teams']['home'], boxscore['teams']['away']




"""
A schedule request returns json of the form
    {
        'copyright':    Copyright info,
        'totalItems:    int,
        'totalEvents':  int,
        'totalGames':   int,
        'totalMatches': int,
        'wait':         int,
        'dates':        list(dict)
    }

where each element of the 'dates' list is of the form
    {
        'date':         'YYYY-MM-DD'
        'totalItems:    int,
        'totalEvents':  int,
        'totalGames':   int,
        'totalMatches': int,
        'games':        list(dict)
        'events':       list(dict - usually empty)
        'matches':      list(dict - usually empty)
    }
where each element of 'games' (typically only the one game) is of the form
    {
    'gamePk':       game id number (?) with form YYYY------
    'link':         /api/v1/game/{gamePk}/feed/live
    'gameType':     string denoting game type (regular season: R, etc.)
    'season':       YYYYYYYY (season game is played in)
    'gameDate':     YYYY-MM-DDTHH:MM:SSZ
    'status':       {
                        'abstractGameState':    str 'Final', etc.
                        'codedGameState':       int (??)
                        'detailedState':        str 'Final', etc.
                        'statusCode':           int (??)
                        'startTimeTBD':         bool
                    }
    'teams':        {
                        'away': {
                                    'leagueRecord': {
                                                        'wins':     num of wins,
                                                        'losses':   num losses,
                                                        'ot':       ot losses,
                                                        'type':     league (as opposed to conference, etc.)
                                                    },
                                    'score':    goals for
                                    'team':     {
                                                    'id':       int - team id
                                                    'name':     str - team name
                                                    'link':     /api/v1/teams/{id}
                                                }
                                }
                        'home': {same as for away}
                    }
    'venue':        {
                        'name': arena name,
                        'link': /api/v1/venues/null
                    },
    'content':      /api/v1/game/{gamePk}/content
    }
"""
